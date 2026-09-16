import os
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr

from config import ADMIN_API_KEY, PROGRAM_TITLE, CERTIFICATES_DIRECTORY, BASE_URL, logger
from database import get_all_submissions, delete_submission_by_email, upsert_certificate_submission
from services.certificate import generate_certificate
from services.mailer import send_certificate_email

router = APIRouter(prefix="/admin", tags=["admin"])


class ManualGenerateRequest(BaseModel):
    name: str
    email: EmailStr
    program_title: str | None = None


def _check_admin_key(x_admin_key: str | None) -> None:
    """
    Raise if the request isn't authorized for admin endpoints.

    Fails closed: if ADMIN_API_KEY isn't configured on the server, admin
    endpoints refuse every request (503) instead of accepting any key
    (or no key) as valid.
    """
    if not ADMIN_API_KEY:
        raise HTTPException(status_code=503, detail="Admin dashboard is not configured on this server.")
    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key.")


@router.get("/submissions")
async def list_submissions(x_admin_key: str | None = Header(default=None)):
    """List all certificate submissions."""
    _check_admin_key(x_admin_key)
    try:
        submissions = get_all_submissions()
        return {"success": True, "submissions": submissions}
    except Exception as e:
        logger.error(f"Error listing submissions for admin: {str(e)}")
        return {"success": False, "error": str(e)}


@router.delete("/submissions/{email}")
async def reset_submission(email: str, x_admin_key: str | None = Header(default=None)):
    """
    Delete a submission by email, allowing that email to generate a
    certificate again.
    """
    _check_admin_key(x_admin_key)
    try:
        deleted = delete_submission_by_email(email)
        if not deleted:
            return {"success": False, "error": f"No submission found for {email}"}
        return {"success": True, "message": f"Submission for {email} has been reset."}
    except Exception as e:
        logger.error(f"Error resetting submission for admin: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/generate-manual")
async def generate_manual(request: ManualGenerateRequest, x_admin_key: str | None = Header(default=None)):
    """
    Manually generate a certificate for an arbitrary name/email (bypassing
    registration/OCR/AI validation entirely, since this is admin-triggered)
    and email the PDF to the recipient.

    Always overwrites any existing submission row for the email, and always
    attempts to email the certificate — but generation success and email
    success are reported separately, since a certificate can be generated
    fine even if RESEND_API_KEY isn't configured or the send fails.
    """
    _check_admin_key(x_admin_key)

    program_title = request.program_title or PROGRAM_TITLE

    try:
        cert_filename = generate_certificate(request.name, program_title)
    except Exception as e:
        logger.error(f"Admin manual certificate generation failed: {str(e)}")
        return {"success": False, "error": f"Certificate generation failed: {str(e)}"}

    cert_id = cert_filename.replace(".pdf", "")
    cert_path = os.path.join(CERTIFICATES_DIRECTORY, "generate", cert_filename)
    cert_url = f"{BASE_URL}/static/certificates/generate/{cert_filename}"

    upsert_certificate_submission(
        email=request.email,
        full_name=request.name,
        program_title=program_title,
        certificate_id=cert_id
    )

    email_sent, email_message = send_certificate_email(
        to_email=request.email,
        to_name=request.name,
        pdf_path=cert_path,
        certificate_id=cert_id
    )

    return {
        "success": True,
        "certificate_id": cert_id,
        "certificate_url": cert_url,
        "email_sent": email_sent,
        "email_message": email_message
    }
