from django.contrib import admin
from .models import EmailTemplate, Upload, SentEmailLog


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
	list_display = ("name", "updated_at")
	search_fields = ("name", "subject")


@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
	list_display = ("original_name", "uploaded_at")


@admin.register(SentEmailLog)
class SentEmailLogAdmin(admin.ModelAdmin):
	list_display = ("to_email", "status", "sent_at", "template")
	search_fields = ("to_email", "status")


