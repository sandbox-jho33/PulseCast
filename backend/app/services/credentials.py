"""Encrypted BYOK credential storage and retrieval."""

from __future__ import annotations

import os
from datetime import datetime
from enum import Enum
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel, Field


class CredentialProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    ELEVENLABS = "elevenlabs"


class CredentialStatus(BaseModel):
    provider: CredentialProvider
    configured: bool
    updated_at: Optional[datetime] = None


class CredentialUpsertRequest(BaseModel):
    provider: CredentialProvider = Field(..., description="Provider to configure.")
    api_key: str = Field(..., min_length=8, description="Provider API key.")


class CredentialStatusResponse(BaseModel):
    credentials: list[CredentialStatus]


def _get_fernet() -> Fernet:
    key = os.getenv("CREDENTIAL_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError(
            "CREDENTIAL_ENCRYPTION_KEY must be configured. Generate one with: "
            "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    return Fernet(key.encode("utf-8"))


def encrypt_secret(secret: str) -> str:
    """Encrypt a secret for database storage."""
    return _get_fernet().encrypt(secret.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt a database-stored secret."""
    try:
        return _get_fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError("Stored credential cannot be decrypted") from exc


async def save_user_credential(
    user_id: str,
    provider: CredentialProvider,
    api_key: str,
) -> None:
    """Store or replace a user's encrypted provider credential."""
    from ..storage.repository import get_repository

    await get_repository().save_user_credential(
        user_id=user_id,
        provider=provider.value,
        encrypted_api_key=encrypt_secret(api_key.strip()),
    )


async def delete_user_credential(
    user_id: str,
    provider: CredentialProvider,
) -> None:
    """Delete one provider credential for a user."""
    from ..storage.repository import get_repository

    await get_repository().delete_user_credential(user_id, provider.value)


async def get_user_api_key(
    user_id: str,
    provider: CredentialProvider | str,
) -> str:
    """Return a decrypted user API key, or raise with a safe user-facing message."""
    from ..storage.repository import get_repository

    provider_value = provider.value if isinstance(provider, CredentialProvider) else provider
    encrypted = await get_repository().load_user_credential(user_id, provider_value)
    if not encrypted:
        raise RuntimeError(f"Configure your {provider_value} API key before using this provider")
    return decrypt_secret(encrypted)


async def list_user_credentials(user_id: str) -> CredentialStatusResponse:
    """Return which BYOK providers are configured for a user."""
    from ..storage.repository import get_repository

    configured = await get_repository().list_user_credentials(user_id)
    by_provider = {item["provider"]: item.get("updated_at") for item in configured}
    return CredentialStatusResponse(
        credentials=[
            CredentialStatus(
                provider=provider,
                configured=provider.value in by_provider,
                updated_at=by_provider.get(provider.value),
            )
            for provider in CredentialProvider
        ]
    )
