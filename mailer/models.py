from django.db import models


class EmailTemplate(models.Model):
	name = models.CharField(max_length=120, unique=True)
	subject = models.CharField(max_length=200)
	body = models.TextField(help_text="Use {{column_name}} placeholders from your Excel/CSV")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return self.name


class Upload(models.Model):
	file = models.FileField(upload_to="uploads/")
	uploaded_at = models.DateTimeField(auto_now_add=True)
	original_name = models.CharField(max_length=255)

	def __str__(self) -> str:
		return self.original_name


class SentEmailLog(models.Model):
	template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
	to_email = models.EmailField()
	status = models.CharField(max_length=20, choices=[("sent", "sent"), ("failed", "failed")])
	error = models.TextField(blank=True, default="")
	sent_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"{self.to_email} - {self.status}"


