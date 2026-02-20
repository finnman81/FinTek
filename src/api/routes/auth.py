"""
Auth routes. Placeholder until Clerk webhook/JWT verification is added.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.deps import get_current_user
from src.db.models import User

router = APIRouter()


class MeResponse(BaseModel):
    user_id: str
    tenant_id: str
    email: str
    role: str


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)):
    """Return current user info (from JWT or headers)."""
    return MeResponse(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=user.email,
        role=user.role,
    )
