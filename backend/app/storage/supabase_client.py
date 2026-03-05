"""
Supabase client configuration for PulseCast.

Provides a singleton Supabase client for database and storage operations.
"""

from __future__ import annotations

import os
from typing import Optional

from supabase import Client, create_client

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get the singleton Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) "
                "must be set in environment variables"
            )

        _supabase_client = create_client(url, key)

    return _supabase_client


def get_supabase_url() -> str:
    """Get the Supabase project URL."""
    url = os.getenv("SUPABASE_URL")
    if not url:
        raise RuntimeError("SUPABASE_URL must be set in environment variables")
    return url


def get_storage_bucket_name() -> str:
    """Get the storage bucket name for podcast audio."""
    return os.getenv("SUPABASE_STORAGE_BUCKET", "podcast-audio")
