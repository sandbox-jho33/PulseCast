"""Clerk authentication helpers for FastAPI routes."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from jwt import PyJWKClient


@dataclass(frozen=True)
class AuthenticatedUser:
    """Authenticated Clerk principal."""

    user_id: str
    session_id: str | None = None


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be configured")
    return value


@lru_cache(maxsize=1)
def _get_jwks_client() -> PyJWKClient:
    jwks_url = os.getenv("CLERK_JWKS_URL")
    if not jwks_url:
        issuer = _get_required_env("CLERK_ISSUER").rstrip("/")
        jwks_url = f"{issuer}/.well-known/jwks.json"
    return PyJWKClient(jwks_url)


def _verify_clerk_token(token: str) -> dict[str, Any]:
    issuer = _get_required_env("CLERK_ISSUER").rstrip("/")
    audience = os.getenv("CLERK_AUDIENCE")

    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        options = {"verify_aud": bool(audience)}
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            audience=audience,
            options=options,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        ) from exc


async def require_user(request: Request) -> AuthenticatedUser:
    """Require a valid Clerk bearer token and return the user identity."""
    auth_header = request.headers.get("authorization", "")
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer authentication token",
        )

    claims = _verify_clerk_token(token)
    user_id = claims.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing a user subject",
        )

    session_id = claims.get("sid")
    return AuthenticatedUser(
        user_id=user_id,
        session_id=session_id if isinstance(session_id, str) else None,
    )


CurrentUser = Annotated[AuthenticatedUser, Depends(require_user)]
