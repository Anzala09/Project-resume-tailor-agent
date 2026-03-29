"""
emailer.py — Send a tailored resume via Gmail SMTP.

Uses TLS on port 587. Requires a Gmail App Password (not your account password).
See: https://myaccount.google.com/apppasswords
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path


def send_resume_email(
    file_path: str,
    job: dict,
    gmail_user: str,
    gmail_app_password: str,
    recipient: str,
) -> None:
    """
    Send one email with the tailored resume attached.

    Args:
        file_path: Absolute path to the resume file (.docx or .pdf)
        job: Job dict with title, company, url
        gmail_user: Sender Gmail address
        gmail_app_password: Gmail App Password (16-char)
        recipient: Destination email address

    Raises:
        Exception: If SMTP connection or sending fails
    """
    attachment = Path(file_path)
    subject = f"Application: {job['title']} at {job['company']}"

    body = f"""Hi,

Please find attached a tailored resume for the following position:

  Role:    {job['title']}
  Company: {job['company']}
  URL:     {job['url']}

The resume has been customized to highlight the most relevant skills and experience for this specific role.

Best regards,
Alex Morgan
"""

    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Attach the resume file
    with open(attachment, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="{attachment.name}"',
    )
    msg.attach(part)

    # Send via Gmail SMTP with TLS
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(gmail_user, gmail_app_password)
        server.sendmail(gmail_user, recipient, msg.as_string())

    print(f"  Email sent to {recipient} — {subject}")
