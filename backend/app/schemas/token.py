"""
Token-related Pydantic schemas.
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema."""
    sub: Optional[str] = None
    exp: Optional[int] = None
    token_type: Optional[str] = None


class TokenRefresh(BaseModel):
    """Token refresh request schema."""
    refresh_token: str
