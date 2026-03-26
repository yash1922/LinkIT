# send_contacts_script.py
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


SENDER_EMAIL = "yourloggedin@gmail.com"          # Gmail address you used on site
APP_PASSWORD = "your_16_char_app_password"       # 16-char App Password
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


df = pd.read_excel("trial for django.xlsx")    # or path to your file
if 'email' not in [c.lower() for c in df.columns]:
    raise SystemExit("No 'email' column found in Excel. Header must be 'email'.")

SUBJECT = "Test email from BulkMailer"
BODY_TEMPLATE = """
Hi {first_name},

This is a test message sent from BulkMailer.

Company: {company}

Regards,
{sender}
"""

server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
server.set_debuglevel(1)
server.ehlo()
server.starttls()
server.ehlo()
try:
    server.login(SENDER_EMAIL, APP_PASSWORD)
except Exception as e:
    print("Login failed:", e)
    server.quit()
    raise SystemExit(1)

sent = 0
for _, row in df.iterrows():
    to_addr = row.get('email') or row.get('Email') or row.get('EMAIL')
    if not to_addr or str(to_addr).strip() == "":
        print("Skipping row with no email:", row.to_dict())
        continue
    first_name = row.get('first_name', '') or row.get('First_name', '') or ''
    company = row.get('company', '') or ''
    body = BODY_TEMPLATE.format(first_name=first_name, company=company, sender=SENDER_EMAIL)
    msg = MIMEMultipart('alternative')
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_addr
    msg['Subject'] = SUBJECT
    part = MIMEText(body, 'plain')
    msg.attach(part)
    try:
        server.sendmail(SENDER_EMAIL, [to_addr], msg.as_string())
        print("Sent to", to_addr)
        sent += 1
    except Exception as e:
        print("Failed to send to", to_addr, ":", e)

server.quit()
print("Done. Sent:", sent)
