import smtplib

SMTP_HOST = 'smtp.gmail.com'
PORT = 587
USER = 'yourgmail@gmail.com'
PASSWORD = 'your_16_char_app_password'

server = smtplib.SMTP(SMTP_HOST, PORT, timeout=10)
server.set_debuglevel(1)
server.ehlo()
server.starttls()
server.ehlo()
try:
    server.login(USER, PASSWORD)
    server.sendmail(USER, [USER], 'Subject: SMTP test\n\nHello from test_smtp')
    print("Sent ok")
except Exception as e:
    print("ERROR:", e)
finally:
    server.quit()
