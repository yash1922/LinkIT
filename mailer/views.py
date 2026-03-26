# mailer/views.py
from typing import List
from django.contrib import messages
from django.core.mail import EmailMessage, get_connection
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest
from .forms import EmailTemplateForm, UploadForm, SendEmailForm
from .models import EmailTemplate, Upload, SentEmailLog
from .utils import read_contacts, render_template_string
import os
import csv
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
import csv
from django.utils.dateparse import parse_date


# ensure these are imported (they may already be)
from .models import SentEmailLog, EmailTemplate



def home(request: HttpRequest) -> HttpResponse:
    context = {
        "templates_count": EmailTemplate.objects.count(),
        "uploads_count": Upload.objects.count(),
    }
    return render(request, "mailer/landing.html", context)


def gmail_help(request: HttpRequest) -> HttpResponse:
    return render(request, "mailer/gmail_help.html")


@login_required
def template_list(request: HttpRequest) -> HttpResponse:
    items = EmailTemplate.objects.order_by("-updated_at")
    return render(request, "mailer/template_list.html", {"items": items})


@login_required
def template_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Template created.")
            return redirect("template_list")
    else:
        form = EmailTemplateForm()
    return render(request, "mailer/template_form.html", {"form": form, "mode": "Create"})


@login_required
def template_edit(request: HttpRequest, pk: int) -> HttpResponse:
    item = get_object_or_404(EmailTemplate, pk=pk)
    if request.method == "POST":
        form = EmailTemplateForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Template updated.")
            return redirect("template_list")
    else:
        form = EmailTemplateForm(instance=item)
    return render(request, "mailer/template_form.html", {"form": form, "mode": "Edit"})


@login_required
def upload_contacts(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            up: Upload = form.save(commit=False)
            up.original_name = request.FILES["file"].name
            up.save()
            messages.success(request, "File uploaded.")
            return redirect("send_bulk_emails")
        else:
            messages.error(request, "Please fix errors in the form.")
    else:
        form = UploadForm()
    return render(request, "mailer/upload.html", {"form": form})
@login_required
def sent_log(request):
    """
    Sent email log view with filters and CSV export.
    URL: /sent-log/
    """
    qs = SentEmailLog.objects.select_related("template").order_by("-created_at")

    # Filters
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(to_email__icontains=q) | Q(error__icontains=q))

    status = request.GET.get("status", "").strip()
    if status:
        qs = qs.filter(status__iexact=status)

    template_id = request.GET.get("template", "").strip()
    if template_id.isdigit():
        qs = qs.filter(template_id=int(template_id))

    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    if date_from:
        d = parse_date(date_from)
        if d:
            qs = qs.filter(created_at__date__gte=d)
    if date_to:
        d = parse_date(date_to)
        if d:
            qs = qs.filter(created_at__date__lte=d)

    # CSV export
    if request.GET.get("export", "").lower() == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="sent_email_log.csv"'
        writer = csv.writer(response)
        writer.writerow(["id", "created_at", "template", "to_email", "status", "error"])
        for row in qs:
            writer.writerow([row.id, row.created_at.isoformat(), getattr(row.template, "name", ""), row.to_email, row.status, (row.error or "")[:1000]])
        return response

    # Pagination
    page = int(request.GET.get("page", 1))
    per_page = 25
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page)

    templates = EmailTemplate.objects.order_by("name")

    context = {
        "page_obj": page_obj,
        "paginator": paginator,
        "templates": templates,
        "filter_q": q,
        "filter_status": status,
        "filter_template": template_id,
        "filter_date_from": date_from,
        "filter_date_to": date_to,
    }
    return render(request, "mailer/sent_log.html", context)



@login_required
def send_bulk_emails(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = SendEmailForm(request.POST)
        if form.is_valid():
            # smtp_username optional - fallback to logged-in user's email
            smtp_username = (form.cleaned_data.get("smtp_username") or "").strip()
            if not smtp_username:
                smtp_username = (request.user.email or "").strip()

            if not smtp_username:
                messages.error(request, "No SMTP username provided and your profile has no email. Please enter the Gmail address to use for sending.")
                return render(request, "mailer/send.html", {"form": form})

            app_password = form.cleaned_data["app_password"]
            smtp_host = form.cleaned_data["smtp_host"]
            smtp_port = form.cleaned_data["smtp_port"]
            use_tls = form.cleaned_data["use_tls"]
            use_ssl = form.cleaned_data.get("use_ssl", False)
            timeout = form.cleaned_data.get("timeout") or 30
            template: EmailTemplate = form.cleaned_data["template"]
            subject_override = form.cleaned_data["subject_override"] or template.subject
            upload: Upload = form.cleaned_data["upload"]

            # Read contacts
            file_path = upload.file.path
            try:
                rows, headers = read_contacts(file_path)
            except Exception as e:
                messages.error(request, f"Failed to read file: {e}")
                return render(request, "mailer/send.html", {"form": form})

            if not rows:
                messages.error(request, "No rows found in the file.")
                return render(request, "mailer/send.html", {"form": form})

            # Normalize headers
            normalized_headers = {}
            for h in headers:
                if h is None:
                    continue
                normalized_headers[str(h).strip().lower()] = str(h).strip()

            # find email column
            email_col = None
            for candidate in ["email", "e-mail", "email address", "email_address", "mail"]:
                if candidate in normalized_headers:
                    email_col = normalized_headers[candidate]
                    break
            if email_col is None:
                messages.error(request, "File must include an 'email' column.")
                return render(request, "mailer/send.html", {"form": form})

            # Create SMTP connection using user-provided credentials
            try:
                connection = get_connection(
                    host=smtp_host,
                    port=smtp_port,
                    username=smtp_username,
                    password=app_password,
                    use_tls=use_tls,
                    use_ssl=use_ssl,
                    timeout=timeout,
                    fail_silently=False,
                )
            except Exception as e:
                messages.error(request, f"SMTP connection error: {e}")
                return render(request, "mailer/send.html", {"form": form})

            # Open connection
            try:
                connection.open()
            except Exception as e:
                messages.error(request, f"Failed to open SMTP connection: {e}")
                return render(request, "mailer/send.html", {"form": form})

            # If test send requested
            if "send_test" in request.POST:
                row = rows[0] if rows else {}
                to_addr = request.user.email or smtp_username
                try:
                    body = render_template_string(template.body, row)
                    subject = render_template_string(subject_override, row)
                except Exception as e:
                    messages.error(request, f"Template render error: {e}")
                    connection.close()
                    return render(request, "mailer/send.html", {"form": form})
                email = EmailMessage(subject=subject, body=body, from_email=smtp_username, to=[to_addr], connection=connection)
                email.content_subtype = "html"
                try:
                    email.send(fail_silently=False)
                    SentEmailLog.objects.create(template=template, to_email=to_addr, status="sent", error="")
                    messages.success(request, "Test email sent. Check your inbox and Spam folder.")
                except Exception as e:
                    SentEmailLog.objects.create(template=template, to_email=to_addr, status="failed", error=str(e))
                    messages.error(request, f"Test email failed: {e}")
                try:
                    connection.close()
                except Exception:
                    pass
                return redirect("send_bulk_emails")

            # Send to all rows
            success_count = 0
            fail_count = 0
            for row in rows:
                to_addr = (row.get(email_col) or "").strip()
                if not to_addr:
                    fail_count += 1
                    SentEmailLog.objects.create(template=template, to_email="", status="failed", error="Missing recipient email")
                    continue
                try:
                    body = render_template_string(template.body, row)
                    subject = render_template_string(subject_override, row)
                except Exception as e:
                    fail_count += 1
                    SentEmailLog.objects.create(template=template, to_email=to_addr, status="failed", error=f"Template render error: {e}")
                    continue

                email = EmailMessage(subject=subject, body=body, from_email=smtp_username, to=[to_addr], connection=connection)
                email.content_subtype = "html"
                try:
                    sent = email.send(fail_silently=False)
                    if sent:
                        success_count += 1
                        SentEmailLog.objects.create(template=template, to_email=to_addr, status="sent", error="")
                    else:
                        fail_count += 1
                        SentEmailLog.objects.create(template=template, to_email=to_addr, status="failed", error="Unknown send failure")
                except Exception as e:
                    fail_count += 1
                    SentEmailLog.objects.create(template=template, to_email=to_addr, status="failed", error=str(e))
                    continue

            try:
                connection.close()
            except Exception:
                pass

            messages.success(request, f"Sent: {success_count}, Failed: {fail_count}. If you don't see emails, check Spam.")
            return redirect("home")
    else:
        # prefill smtp_username with logged-in user email if available (optional)
        initial = {}
        if request.user.is_authenticated and request.user.email:
            initial['smtp_username'] = request.user.email
        form = SendEmailForm(initial=initial)
    return render(request, "mailer/send.html", {"form": form, "current_user_email": request.user.email if request.user.is_authenticated else ""})


def sample_contacts(request: HttpRequest) -> HttpResponse:
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="sample_contacts.csv"'
    writer = csv.writer(response)
    writer.writerow(["email", "first_name", "company"])
    writer.writerow(["alice@example.com", "Alice", "Acme Inc"])
    writer.writerow(["bob@example.com", "Bob", "Globex"])
    return response


def signup(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm", "")
        if not username or not email or not password:
            messages.error(request, "All fields are required.")
        elif password != confirm:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect("home")
    return render(request, "mailer/signup.html")


@login_required
def setup(request: HttpRequest) -> HttpResponse:
    template_form = EmailTemplateForm(prefix="tpl")
    upload_form = UploadForm(prefix="up")

    if request.method == "POST":
        if "create_template" in request.POST:
            template_form = EmailTemplateForm(request.POST, prefix="tpl")
            if template_form.is_valid():
                template_form.save()
                messages.success(request, "Template created.")
                return redirect("setup")
            else:
                messages.error(request, "Please fix errors in the template form.")
        elif "upload_contacts" in request.POST:
            upload_form = UploadForm(request.POST, request.FILES, prefix="up")
            if upload_form.is_valid():
                up: Upload = upload_form.save(commit=False)
                # get correct file key under prefix
                file_key = "up-file" if "up-file" in request.FILES else "file"
                up.original_name = request.FILES[file_key].name if file_key in request.FILES else "contacts"
                up.save()
                messages.success(request, "Contacts file uploaded.")
                return redirect("send_bulk_emails")
            else:
                messages.error(request, "Please fix errors in the upload form.")

    context = {
        "template_form": template_form,
        "upload_form": upload_form,
    }
    return render(request, "mailer/setup.html", context)
