"""
Optional Clerk JWT verification for FastAPI.

When CLERK_JWT_ISSUER is set, Bearer tokens are verified against Clerk's JWKS.
Returns payload (sub, etc.) or None if not configured or invalid.
"""

from __future__ import annotations

import os
import logging

logger = logging.getLogger(__name__)


def get_clerk_issuer() -> str | None:
    """Return Clerk JWT issuer URL if configured."""
    return os.environ.get("CLERK_JWT_ISSUER") or os.environ.get("CLERK_ISSUER")


def verify_clerk_token(bearer: str | None) -> dict | None:
    """
    Verify a Bearer token with Clerk JWKS. Returns payload (sub, org_id, etc.) or None.
    """
    if not bearer or not bearer.startswith("Bearer "):
        return None
    token = bearer[7:].strip()
    if not token:
        return None
    issuer = get_clerk_issuer()
    if not issuer:
        return None
    try:
        from jwt import PyJWKClient, decode
        jwks_url = issuer.rstrip("/") + "/.well-known/jwks.json"
        client = PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=300)
        signing_key = client.get_signing_key_from_jwt(token)
        payload = decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            options={"verify_exp": True},
        )
        return payload
    except Exception as e:
        logger.debug("Clerk JWT verification failed: %s", e)
        return None
