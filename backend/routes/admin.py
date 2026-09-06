from fastapi import APIRouter, Header, HTTPException
from config import ADMIN_API_KEY, logger
from database import get_all_submissions, delete_submission_by_email

router = APIRouter(prefix="/admin", tags=["admin"])


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
