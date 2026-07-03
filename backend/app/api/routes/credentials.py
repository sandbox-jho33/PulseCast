"""Authenticated BYOK credential management routes."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from ...auth import CurrentUser
from ...services.credentials import (
    CredentialProvider,
    CredentialStatusResponse,
    CredentialUpsertRequest,
    delete_user_credential,
    list_user_credentials,
    save_user_credential,
)

router = APIRouter()


@router.get("", response_model=CredentialStatusResponse)
async def get_credentials(user: CurrentUser) -> CredentialStatusResponse:
    """List configured BYOK providers for the signed-in user."""
    return await list_user_credentials(user.user_id)


@router.put("", response_model=CredentialStatusResponse)
async def upsert_credential(
    request: CredentialUpsertRequest,
    user: CurrentUser,
) -> CredentialStatusResponse:
    """Create or replace one encrypted BYOK credential."""
    await save_user_credential(user.user_id, request.provider, request.api_key)
    return await list_user_credentials(user.user_id)


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    provider: CredentialProvider,
    user: CurrentUser,
) -> Response:
    """Delete one BYOK credential."""
    await delete_user_credential(user.user_id, provider)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
