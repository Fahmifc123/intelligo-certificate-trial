import csv
import io
import os
from fastapi import APIRouter, File, Header, HTTPException, UploadFile
from pydantic import BaseModel, EmailStr

from config import ADMIN_API_KEY, PROGRAM_TITLE, CERTIFICATES_DIRECTORY, BASE_URL, logger
from database import get_all_submissions, delete_submission_by_email, upsert_certificate_submission
from services.certificate import generate_certificate
from services.mailer import send_certificate_email

router = APIRouter(prefix="/admin", tags=["admin"])

# CSV columns accepted by /admin/generate-bulk: "name" and "email" are
# required, "program_title" is optional (falls back to PROGRAM_TITLE per row
# when blank/absent).
BULK_REQUIRED_COLUMNS = {"name", "email"}


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


def _generate_and_send_one(name: str, email: str, program_title: str | None) -> dict:
    """
    Generate one certificate for name/email, save/overwrite the submission
    row, and email the PDF. Shared by /generate-manual (one row) and
    /generate-bulk (many rows via CSV) so both behave identically.

    Returns a dict describing what happened; never raises — errors are
    captured so a bulk run can keep going past a single bad row.
    """
    resolved_program_title = program_title or PROGRAM_TITLE

    try:
        cert_filename = generate_certificate(name, resolved_program_title)
    except Exception as e:
        logger.error(f"Certificate generation failed for {email}: {str(e)}")
        return {
            "name": name,
            "email": email,
            "success": False,
            "error": f"Certificate generation failed: {str(e)}"
        }

    cert_id = cert_filename.replace(".pdf", "")
    cert_path = os.path.join(CERTIFICATES_DIRECTORY, "generate", cert_filename)
    cert_url = f"{BASE_URL}/static/certificates/generate/{cert_filename}"

    upsert_certificate_submission(
        email=email,
        full_name=name,
        program_title=resolved_program_title,
        certificate_id=cert_id
    )

    email_sent, email_message = send_certificate_email(
        to_email=email,
        to_name=name,
        pdf_path=cert_path,
        certificate_id=cert_id
    )

    return {
        "name": name,
        "email": email,
        "success": True,
        "certificate_id": cert_id,
        "certificate_url": cert_url,
        "email_sent": email_sent,
        "email_message": email_message
    }


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
    result = _generate_and_send_one(request.name, request.email, request.program_title)
    return result


@router.post("/generate-bulk")
async def generate_bulk(file: UploadFile = File(...), x_admin_key: str | None = Header(default=None)):
    """
    Generate + email certificates for every row in an uploaded CSV.

    Required columns: "name", "email". Optional column: "program_title"
    (falls back to the default program per-row when blank/absent). Rows are
    processed one at a time and never abort the whole batch — each row's
    result (including failures) is reported individually so the admin can
    see exactly which rows to fix and re-upload, without needing to guess
    which of the already-succeeded rows to skip on retry.
    """
    _check_admin_key(x_admin_key)

    if not file.filename or not file.filename.lower().endswith(".csv"):
        return {"success": False, "error": "File harus berformat .csv"}

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return {"success": False, "error": "File CSV tidak bisa dibaca (encoding tidak didukung, gunakan UTF-8)."}

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        return {"success": False, "error": "File CSV kosong."}

    header = {(h or "").strip().lower() for h in reader.fieldnames}
    missing = BULK_REQUIRED_COLUMNS - header
    if missing:
        return {
            "success": False,
            "error": f"Kolom wajib tidak ditemukan di CSV: {', '.join(sorted(missing))}. "
                     f"Kolom yang dibutuhkan: name, email (program_title opsional)."
        }

    # Normalize each row's keys to lowercase/stripped so header casing/spacing
    # ("Name", " Email ") doesn't matter.
    rows = [
        {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        for row in reader
    ]

    results = []
    for i, row in enumerate(rows, start=2):  # row 1 is the header
        name = row.get("name", "")
        email = row.get("email", "")
        program_title = row.get("program_title") or None

        if not name or not email:
            results.append({
                "name": name,
                "email": email,
                "success": False,
                "error": f"Baris {i}: 'name' dan 'email' wajib diisi."
            })
            continue

        results.append(_generate_and_send_one(name, email, program_title))

    succeeded = sum(1 for r in results if r["success"])
    return {
        "success": True,
        "total": len(results),
        "succeeded": succeeded,
        "failed": len(results) - succeeded,
        "results": results
    }
