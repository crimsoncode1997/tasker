"""
Authentication-related Pydantic schemas.
"""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str

