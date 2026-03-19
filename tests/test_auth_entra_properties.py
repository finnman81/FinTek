"""
Property-based tests for Entra ID JWT validation and claim extraction.

**Validates: Requirements 12.1, 12.5**

Property 8: Entra ID JWT validation and claim extraction
For any valid JWT issued by Microsoft Entra ID (matching the configured
tenant ID and client ID), the auth middleware should accept the token and
correctly extract oid, tid, and roles claims. For any invalid or expired
JWT, the middleware should reject with 401.
"""

from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from src.api.auth_entra import verify_entra_token, clear_jwks_cache


# ---------------------------------------------------------------------------
# Shared RSA key pair (module-level for performance)
# ---------------------------------------------------------------------------

_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)

_CLIENT_ID = "prop-test-client-id"
_TENANT_ID = "prop-test-tenant-id"
_ISSUER = f"https://login.microsoftonline.com/{_TENANT_ID}/v2.0"
_KID = "prop-test-kid"


def _make_jwk(private_key, kid: str) -> dict:
    pub = private_key.public_key().public_numbers()

    def _b64url(n: int, length: int) -> str:
        return base64.urlsafe_b64encode(
            n.to_bytes(length, "big")
        ).rstrip(b"=").decode()

    return {
        "kty": "RSA",
        "kid": kid,
        "use": "sig",
        "alg": "RS256",
        "n": _b64url(pub.n, 256),
        "e": _b64url(pub.e, 3),
    }


def _mock_endpoints(mock_get, private_key, kid=_KID):
    """Set up requests.get to return OIDC discovery + JWKS."""
    oidc = MagicMock()
    oidc.json.return_value = {
        "jwks_uri": f"https://login.microsoftonline.com/{_TENANT_ID}/discovery/v2.0/keys",
    }
    oidc.raise_for_status = MagicMock()

    jwks = MagicMock()
    jwks.json.return_value = {"keys": [_make_jwk(private_key, kid)]}
    jwks.raise_for_status = MagicMock()

    mock_get.side_effect = [oidc, jwks]


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Object IDs: UUID-like strings
_oid_st = st.from_regex(
    r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
    fullmatch=True,
)

# Roles: list of 0-5 role strings
_role_st = st.lists(
    st.sampled_from(["Admin", "Reader", "Writer", "Owner", "Viewer"]),
    min_size=0,
    max_size=5,
)

# Email-like usernames
_email_st = st.from_regex(
    r"[a-z]{3,10}@[a-z]{3,8}\.[a-z]{2,4}", fullmatch=True
)

# Display names
_name_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "Zs")),
    min_size=1,
    max_size=40,
).filter(lambda s: s.strip())

# Expiry offset for valid tokens: 1 minute to 2 hours in the future
_valid_exp_st = st.integers(min_value=60, max_value=7200).map(
    lambda s: timedelta(seconds=s)
)

# Expiry offset for expired tokens: 1 minute to 2 hours in the past
_expired_exp_st = st.integers(min_value=60, max_value=7200).map(
    lambda s: timedelta(seconds=-s)
)


def _encode(
    key,
    kid: str,
    oid: str,
    tid: str,
    roles: list[str],
    email: str,
    name: str,
    exp_delta: timedelta,
    audience: str = _CLIENT_ID,
    issuer: str = _ISSUER,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "nbf": now,
        "exp": now + exp_delta,
        "oid": oid,
        "tid": tid,
        "sub": f"sub-{oid}",
        "preferred_username": email,
        "name": name,
        "roles": roles,
    }
    return pyjwt.encode(payload, key, algorithm="RS256", headers={"kid": kid})


# ---------------------------------------------------------------------------
# Feature: aws-cdk-deployment, Property 8: Entra ID JWT validation and claim extraction
# ---------------------------------------------------------------------------


class TestProperty8EntraJWTValidation:
    """
    **Validates: Requirements 12.1, 12.5**

    For any valid JWT matching the configured tenant/client, the middleware
    accepts and extracts oid, tid, roles. For any invalid/expired JWT, it
    rejects with 401.
    """

    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch):
        clear_jwks_cache()
        monkeypatch.setenv("ENTRA_CLIENT_ID", _CLIENT_ID)
        monkeypatch.setenv("ENTRA_TENANT_ID", _TENANT_ID)
        yield
        clear_jwks_cache()

    # --- Property 8a: valid tokens are accepted with correct claims ---

    @given(
        oid=_oid_st,
        roles=_role_st,
        email=_email_st,
        name=_name_st,
        exp_delta=_valid_exp_st,
    )
    @settings(max_examples=100, deadline=None)
    @patch("src.api.auth_entra.requests.get")
    def test_valid_jwt_accepted_with_correct_claims(
        self, mock_get, oid, roles, email, name, exp_delta
    ):
        """Valid JWTs are accepted; oid, tid, and roles are extracted."""
        clear_jwks_cache()
        _mock_endpoints(mock_get, _PRIVATE_KEY)

        token = _encode(
            _PRIVATE_KEY, _KID, oid, _TENANT_ID, roles, email, name, exp_delta
        )
        result = verify_entra_token(f"Bearer {token}")

        assert result["oid"] == oid
        assert result["tid"] == _TENANT_ID
        assert result["roles"] == roles
        assert result["email"] == email

    # --- Property 8b: expired tokens are rejected with 401 ---

    @given(
        oid=_oid_st,
        roles=_role_st,
        email=_email_st,
        name=_name_st,
        exp_delta=_expired_exp_st,
    )
    @settings(max_examples=100, deadline=None)
    @patch("src.api.auth_entra.requests.get")
    def test_expired_jwt_rejected(
        self, mock_get, oid, roles, email, name, exp_delta
    ):
        """Expired JWTs are rejected with 401."""
        clear_jwks_cache()
        _mock_endpoints(mock_get, _PRIVATE_KEY)

        token = _encode(
            _PRIVATE_KEY, _KID, oid, _TENANT_ID, roles, email, name, exp_delta
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_entra_token(f"Bearer {token}")
        assert exc_info.value.status_code == 401

    # --- Property 8c: wrong-key tokens are rejected with 401 ---

    @given(
        oid=_oid_st,
        roles=_role_st,
        email=_email_st,
        name=_name_st,
        exp_delta=_valid_exp_st,
    )
    @settings(max_examples=100, deadline=None)
    @patch("src.api.auth_entra.requests.get")
    def test_wrong_key_jwt_rejected(
        self, mock_get, oid, roles, email, name, exp_delta
    ):
        """Tokens signed with a different key are rejected with 401."""
        clear_jwks_cache()
        _mock_endpoints(mock_get, _PRIVATE_KEY)

        # Sign with _OTHER_KEY but JWKS has _PRIVATE_KEY's public key
        token = _encode(
            _OTHER_KEY, _KID, oid, _TENANT_ID, roles, email, name, exp_delta
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_entra_token(f"Bearer {token}")
        assert exc_info.value.status_code == 401

    # --- Property 8d: random garbage strings are rejected ---

    @given(garbage=st.text(min_size=1, max_size=500))
    @settings(max_examples=100, deadline=None)
    @patch("src.api.auth_entra.requests.get")
    def test_garbage_bearer_rejected(self, mock_get, garbage):
        """Random non-JWT strings are rejected with 401."""
        # Don't test strings that happen to start with "Bearer " and are empty after
        bearer = f"Bearer {garbage}"
        with pytest.raises(HTTPException) as exc_info:
            verify_entra_token(bearer)
        assert exc_info.value.status_code == 401
