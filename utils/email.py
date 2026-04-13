"""Email sending and PDF generation utilities."""

import io
import smtplib
import socket
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from models.app_settings import AppSettings


def get_smtp_config():
    """Return SMTP settings dict from AppSettings."""
    s = AppSettings.get()
    return {
        "enabled": s.smtp_enabled,
        "host": s.smtp_host,
        "port": s.smtp_port,
        "username": s.smtp_username,
        "password": s.smtp_password,
        "from_address": s.smtp_from_address,
        "use_tls": s.smtp_use_tls,
    }


def test_smtp_connection(config=None):
    """Try connecting to SMTP server. Returns (success, message)."""
    if config is None:
        config = get_smtp_config()

    if not config["host"]:
        return False, "SMTP host is not configured."

    try:
        if config["use_tls"]:
            server = smtplib.SMTP(config["host"], config["port"], timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(config["host"], config["port"], timeout=10)

        if config["username"] and config["password"]:
            server.login(config["username"], config["password"])

        server.quit()
        return True, "Connection successful."
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Check username and password."
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {e}"
    except socket.error as e:
        return False, f"Connection failed: {e}"


def send_email(to_addresses, subject, body_html, attachments=None):
    """Send email with optional attachments.

    to_addresses: list of email strings
    subject: str
    body_html: str (HTML body)
    attachments: list of (filename, content_bytes, mime_type) tuples

    Returns (success, error_message).
    """
    config = get_smtp_config()
    if not config["enabled"]:
        return False, "Email is not enabled."
    if not config["host"]:
        return False, "SMTP host is not configured."

    msg = MIMEMultipart()
    msg["From"] = config["from_address"] or config["username"]
    msg["To"] = ", ".join(to_addresses)
    msg["Subject"] = subject

    msg.attach(MIMEText(body_html, "html"))

    if attachments:
        for filename, content, mime_type in attachments:
            part = MIMEApplication(content, Name=filename)
            part["Content-Disposition"] = f'attachment; filename="{filename}"'
            msg.attach(part)

    try:
        if config["use_tls"]:
            server = smtplib.SMTP(config["host"], config["port"], timeout=15)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(config["host"], config["port"], timeout=15)

        if config["username"] and config["password"]:
            server.login(config["username"], config["password"])

        server.sendmail(
            config["from_address"] or config["username"],
            to_addresses,
            msg.as_string(),
        )
        server.quit()
        return True, None
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {e}"
    except socket.error as e:
        return False, f"Connection failed: {e}"


def render_report_pdf(html_string):
    """Convert an HTML string to PDF bytes using xhtml2pdf.

    Returns PDF bytes or None on error.
    """
    from xhtml2pdf import pisa

    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(html_string), dest=result)

    if pisa_status.err:
        return None

    return result.getvalue()
