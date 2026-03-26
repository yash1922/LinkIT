# mailer/forms.py
from django import forms
from .models import EmailTemplate, Upload


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ["name", "subject", "body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 8}),
        }


class UploadForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields = ["file"]

    def clean_file(self):
        f = self.cleaned_data["file"]
        valid_exts = [".xlsx", ".csv"]
        if not any(str(f.name).lower().endswith(ext) for ext in valid_exts):
            raise forms.ValidationError("Only .xlsx and .csv files are supported.")
        return f


class SendEmailForm(forms.Form):
    smtp_username = forms.EmailField(
        required=False,
        help_text="Gmail address to use for SMTP. Leave blank to use your logged-in email.",
        label="SMTP Username (Gmail address, optional)",
    )
    app_password = forms.CharField(
        widget=forms.PasswordInput,
        help_text="16-character Gmail App Password (not your normal password).",
        label="Gmail App Password",
    )
    smtp_host = forms.CharField(initial="smtp.gmail.com", label="SMTP Host")
    smtp_port = forms.IntegerField(initial=587, label="SMTP Port")
    use_tls = forms.BooleanField(initial=True, required=False, label="Use TLS (port 587)")
    use_ssl = forms.BooleanField(initial=False, required=False, help_text="For port 465", label="Use SSL (port 465)")
    timeout = forms.IntegerField(initial=30, required=False, help_text="Seconds")
    template = forms.ModelChoiceField(queryset=EmailTemplate.objects.all())
    subject_override = forms.CharField(required=False, help_text="Optional: override template subject")
    message_variables_help = forms.CharField(
        required=False,
        disabled=True,
        label="Tip",
        initial="Excel/CSV must have an 'email' column for recipients. Use {{column_name}} in template.",
    )
    upload = forms.ModelChoiceField(queryset=Upload.objects.all(), help_text="Choose the uploaded contacts file")

    def clean_app_password(self):
        pwd = self.cleaned_data.get("app_password", "")
        if not pwd or len(pwd.strip()) != 16:
            raise forms.ValidationError("App Password must be exactly 16 characters. (No spaces.)")
        return pwd.strip()

    def clean(self):
        cleaned = super().clean()
        use_tls = cleaned.get("use_tls")
        use_ssl = cleaned.get("use_ssl")
        if use_tls and use_ssl:
            raise forms.ValidationError("Select either TLS (port 587) or SSL (port 465), not both.")
        return cleaned
