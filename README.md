# LinkIT (Django Web Application)

LinkIT is a Django-based application that allows users to manage email templates, upload contact files, personalize messages using placeholders, and send emails securely using Gmail SMTP with App Password authentication.

This README provides complete setup instructions so anyone can clone the repository and run the project locally.

---

# 📁 Project File Structure

A simplified version of the project structure for understanding:

LinkIT/
│
├── linkit/ # Main Django project folder
│ ├── pycache/
│ ├── settings.py
│ ├── urls.py
│ ├── wsgi.py
│ └── asgi.py
│
├── app/ # Main application folder
│ ├── migrations/
│ ├── templates/ # HTML templates
│ ├── static/ # App-specific static files
│ ├── views.py
│ ├── models.py
│ ├── forms.py
│ └── urls.py
│
├── media/ # User-uploaded files (create manually)
│
├── static/ # Collected static files (create manually)
│
├── .env # Environment configuration file (create manually)
├── .gitignore
├── db.sqlite3 # Auto-created after migrations
├── manage.py
└── requirements.txt

### 📝 The following items MUST be created manually after cloning:
- `media/`
- `static/`
- `.env` file
- `venv/` or `.venv/` (virtual environment)

---

# 🚀 Quickstart Guide (Windows / PowerShell)

## Follow these steps
```bash
py -m venv .venv
.venv\Scripts\Activate.ps1

Install Dependencies
pip install -r requirements.txt

3. Create Required Folders

These folders are ignored in Git and will not exist when you clone the project.

Create media/:
mkdir media

Create static/:
mkdir static

4. Create Your .env File

Inside the project root (same level as manage.py), create a file named:

.env


Add the following content:

DEBUG=True
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=


Important:

EMAIL_HOST_USER = your Gmail address

EMAIL_HOST_PASSWORD = your Gmail App Password

Do NOT use your regular Gmail password

🔐 Gmail App Password Setup

To use Gmail SMTP, you must create an App Password:

Go to Google Account → Security

Enable 2-Step Verification

Go to App Passwords

Generate a new password for Mail

Use this 16-character code in your .env file

🗄 Database Setup
Step 1 — Run Migrations
python manage.py makemigrations
python manage.py migrate

Step 2 (Optional) — Create Superuser
python manage.py createsuperuser

▶️ Run the Development Server
python manage.py runserver


Open the application in your browser:

http://127.0.0.1:8000/

📁 Supported Contact File Formats

You can upload:

.xlsx

.csv

Your file must include:

email


You may add additional fields such as:

first_name
last_name
company
phone


You can use these in templates:

Hello {{first_name}}, welcome from {{company}}!

🛠 Production Database (Optional)

The default database is:

SQLite (db.sqlite3)


For production, switch to PostgreSQL by updating the DATABASES setting inside:

linkit/settings.py

🎉 You're All Set!

This README includes:

Complete setup instructions

Environment file creation

Required folder creation

Gmail App Password setup

File structure overview

Database configuration

Run instructions

Happy coding 🚀