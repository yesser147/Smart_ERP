"""
Authentication for the AI API: every request must carry the JWT the Spring
backend issued at login (Authorization: Bearer <token>), and the user must
have an HR role. The token is checked locally with the shared JWT_SECRET,
using only the standard library (the backend signs with HMAC-SHA).
"""

import base64
import hashlib
import hmac
import json
import time

from fastapi import Depends, Header, HTTPException

import config

ALLOWED_ROLES = {"ROLE_ADMIN", "ROLE_HR_MANAGER", "ROLE_MANAGER"}
_HASHES = {"HS256": hashlib.sha256, "HS384": hashlib.sha384, "HS512": hashlib.sha512}


def _b64url_decode(part: str) -> bytes:
    return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))


def decode_token(token: str) -> dict:
    """Returns the claims of a valid token, raises ValueError otherwise."""
    if not config.JWT_SECRET:
        raise ValueError("JWT_SECRET is not configured")
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        header = json.loads(_b64url_decode(header_b64))
        payload = json.loads(_b64url_decode(payload_b64))
        signature = _b64url_decode(signature_b64)
    except Exception:
        raise ValueError("malformed token")

    digest = _HASHES.get(header.get("alg"))
    if digest is None:
        raise ValueError("unsupported algorithm")

    # The backend base64-decodes the secret to get the key (jjwt Decoders.BASE64)
    key = base64.b64decode(config.JWT_SECRET)
    expected = hmac.new(key, f"{header_b64}.{payload_b64}".encode(), digest).digest()
    if not hmac.compare_digest(expected, signature):
        raise ValueError("bad signature")

    if "exp" in payload and time.time() > float(payload["exp"]):
        raise ValueError("token expired")
    return payload


def require_hr_user(authorization: str | None = Header(default=None)) -> dict:
    """FastAPI dependency: 401 without a valid token, 403 without an HR role."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        claims = decode_token(authorization[7:].strip())
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")
    if claims.get("role") not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="Reserved for HR staff.")
    return claims


def require_admin(claims: dict = Depends(require_hr_user)) -> dict:
    """FastAPI dependency: HR check + ROLE_ADMIN (model retraining)."""
    if claims.get("role") != "ROLE_ADMIN":
        raise HTTPException(status_code=403, detail="Reserved for administrators.")
    return claims
