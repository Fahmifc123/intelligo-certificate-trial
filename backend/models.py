"""
Data models module.
Contains Pydantic models for request/response validation.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class CertificateRequest(BaseModel):
    """Request model for certificate generation."""
    name: str
    email: EmailStr
    project_title: str
    social_link: str


class CertificateResponse(BaseModel):
    """Response model for certificate API."""
    status: str
    certificate_url: Optional[str] = None
    message: Optional[str] = None
    ocr_text: Optional[str] = None
    ai_validation: Optional[bool] = None
