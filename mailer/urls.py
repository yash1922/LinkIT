from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("setup/", views.setup, name="setup"),
    path("send/", views.send_bulk_emails, name="send_bulk_emails"),
    path("upload/", views.upload_contacts, name="upload_contacts"),

    path("templates/", views.template_list, name="template_list"),
    path("templates/create/", views.template_create, name="template_create"),
    path("templates/<int:pk>/edit/", views.template_edit, name="template_edit"),

    path("gmail-help/", views.gmail_help, name="gmail_help"),
    path("sample-contacts/", views.sample_contacts, name="sample_contacts"),
    path("sent-log/", views.sent_log, name="sent_log"),
]
