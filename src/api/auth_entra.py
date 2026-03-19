"""
Microsoft Entra ID (Azure AD) JWT verification for FastAPI.

Validates Bearer tokens against Entra ID's OIDC JWKS endpoint.
Returns decoded claims (oid, tid, roles) or raises HTTPException(401).

Environment variables:
    ENTRA_CLIENT_ID   – Application (client) ID registered in Entra ID
    ENTRA_TENANT_ID   – Azure AD tenant ID
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any

import jwt
import requests
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# JWKS cache: stores (keys_dict, fetched_at) per tenant
_jwks_cache: dict[str, tuple[dict[str, Any], float]] = {}
_jwks_lock = threading.Lock()
_JWKS_TTL_SECONDS = 300  # 5 minutes


def _get_entra_config() -> tuple[str, str]:
    """Return (client_id, tenant_id) from environment or raise."""
    client_id = os.environ.get("ENTRA_CLIENT_ID", "").strip()
    tenant_id = os.environ.get("ENTRA_TENANT_ID", "").strip()
    if not client_id or not tenant_id:
        raise HTTPException(
            status_code=401,
            detail="Entra ID authentication is not configured",
        )
    return client_id, tenant_id


def _oidc_discovery_url(tenant_id: str) -> str:
    return (
        f"https://login.microsoftonline.com/{tenant_id}"
        f"/v2.0/.well-known/openid-configuration"
    )


def _fetch_jwks_uri(tenant_id: str) -> str:
    """Fetch the jwks_uri from the OIDC discovery document."""
    url = _oidc_discovery_url(tenant_id)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()["jwks_uri"]
    except Exception as exc:
        logger.error("Failed to fetch OIDC discovery from %s: %s", url, exc)
        raise HTTPException(
            status_code=401,
            detail="Unable to reach Entra ID OIDC discovery endpoint",
        ) from exc


def _get_signing_keys(tenant_id: str) -> dict[str, Any]:
    """
    Return a dict mapping kid -> key data from the JWKS endpoint.
    Results are cached with a TTL to avoid hitting the endpoint on every request.
    """
    now = time.time()
    with _jwks_lock:
        cached = _jwks_cache.get(tenant_id)
        if cached and (now - cached[1]) < _JWKS_TTL_SECONDS:
            return cached[0]

    jwks_uri = _fetch_jwks_uri(tenant_id)
    try:
        resp = requests.get(jwks_uri, timeout=10)
        resp.raise_for_status()
        jwks_data = resp.json()
    except Exception as exc:
        logger.error("Failed to fetch JWKS from %s: %s", jwks_uri, exc)
        # Fall back to cache if available
        with _jwks_lock:
            cached = _jwks_cache.get(tenant_id)
            if cached:
                return cached[0]
        raise HTTPException(
            status_code=401,
            detail="Unable to fetch Entra ID signing keys",
        ) from exc

    keys_by_kid: dict[str, Any] = {}
    for key_data in jwks_data.get("keys", []):
        kid = key_data.get("kid")
        if kid:
            keys_by_kid[kid] = key_data

    with _jwks_lock:
        _jwks_cache[tenant_id] = (keys_by_kid, time.time())

    return keys_by_kid


def _get_public_key_for_token(token: str, tenant_id: str) -> Any:
    """Extract the signing key matching the token's kid header."""
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.exceptions.DecodeError as exc:
        raise HTTPException(
            status_code=401, detail="Invalid token header"
        ) from exc

    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(status_code=401, detail="Token missing kid header")

    keys = _get_signing_keys(tenant_id)
    key_data = keys.get(kid)
    if not key_data:
        # Key rotation may have happened — force refresh once
        with _jwks_lock:
            _jwks_cache.pop(tenant_id, None)
        keys = _get_signing_keys(tenant_id)
        key_data = keys.get(kid)
        if not key_data:
            raise HTTPException(
                status_code=401, detail="Token signing key not found"
            )

    return jwt.algorithms.RSAAlgorithm.from_jwk(key_data)


def verify_entra_token(bearer: str) -> dict[str, Any]:
    """
    Validate a Bearer token issued by Microsoft Entra ID.

    Args:
        bearer: The full ``Authorization`` header value, e.g. ``"Bearer eyJ..."``.

    Returns:
        Decoded JWT claims dict containing at least ``oid``, ``tid``, and
        optionally ``roles``.

    Raises:
        HTTPException(401): If the token is missing, malformed, expired, or
            fails audience/issuer validation.
    """
    if not bearer or not bearer.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = bearer[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty Bearer token")

    client_id, tenant_id = _get_entra_config()
    issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"

    public_key = _get_public_key_for_token(token, tenant_id)

    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=issuer,
            options={"verify_exp": True},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=401, detail="Token has expired"
        ) from exc
    except jwt.InvalidAudienceError as exc:
        raise HTTPException(
            status_code=401, detail="Invalid token audience"
        ) from exc
    except jwt.InvalidIssuerError as exc:
        raise HTTPException(
            status_code=401, detail="Invalid token issuer"
        ) from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=401, detail="Invalid token"
        ) from exc

    # Extract standard Entra ID claims
    return {
        "oid": payload.get("oid", ""),
        "tid": payload.get("tid", ""),
        "roles": payload.get("roles", []),
        "email": payload.get("preferred_username") or payload.get("email") or "",
        "name": payload.get("name", ""),
        "sub": payload.get("sub", ""),
        "raw": payload,
    }


def clear_jwks_cache() -> None:
    """Clear the JWKS cache. Useful for testing."""
    with _jwks_lock:
        _jwks_cache.clear()
