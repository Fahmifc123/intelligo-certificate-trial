"""
Outbound email service. Sends the generated certificate PDF to a
participant via Resend's HTTP API (https://resend.com).
"""
import base64
import os
import requests

from config import RESEND_API_KEY, MAIL_FROM, logger

RESEND_API_URL = "https://api.resend.com/emails"


def send_certificate_email(to_email: str, to_name: str, pdf_path: str, certificate_id: str) -> tuple[bool, str]:
    """
    Email the generated certificate PDF to a participant.

    Args:
        to_email: Recipient email address
        to_name: Recipient name (used in the email greeting)
        pdf_path: Local filesystem path to the generated certificate PDF
        certificate_id: Certificate ID, used in the subject/filename

    Returns:
        tuple: (success, message)
    """
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, skipping certificate email")
        return False, "Email sending is not configured on this server (RESEND_API_KEY missing)."

    try:
        with open(pdf_path, "rb") as f:
            pdf_b64 = base64.b64encode(f.read()).decode("ascii")
    except OSError as e:
        logger.error(f"Could not read certificate PDF for emailing: {str(e)}")
        return False, f"Could not read certificate file: {str(e)}"

    payload = {
        "from": MAIL_FROM,
        "to": [to_email],
        "subject": "Sertifikat Trial Bootcamp Intelligo ID",
        "html": (
            f"<p>Hai {to_name},</p>"
            "<p>Selamat! Berikut sertifikat Trial Bootcamp kamu dari Intelligo ID.</p>"
            f"<p>Certificate ID: <strong>{certificate_id}</strong></p>"
            "<p>Terima kasih sudah mengikuti trial bootcamp bersama kami.</p>"
            "<p>Salam,<br/>Tim Intelligo ID</p>"
        ),
        "attachments": [
            {
                "filename": f"Sertifikat-{certificate_id}.pdf",
                "content": pdf_b64,
            }
        ],
    }

    try:
        response = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        if response.status_code >= 300:
            logger.error(f"Resend API error {response.status_code}: {response.text}")
            return False, f"Failed to send email (HTTP {response.status_code}): {response.text}"

        logger.info(f"Certificate email sent to {to_email}")
        return True, "Email sent successfully."
    except requests.RequestException as e:
        logger.error(f"Error sending certificate email: {str(e)}")
        return False, f"Error sending email: {str(e)}"
