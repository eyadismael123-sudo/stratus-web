"""Supabase client connections."""

from __future__ import annotations

from typing import Optional

from supabase import Client, create_client

from app.config import settings

# Service role client — bypasses RLS, used for backend operations
_service_client: Optional[Client] = None

# Anon client — respects RLS, used for auth verification
_anon_client: Optional[Client] = None


def get_service_client() -> Client:
    """Get Supabase client with service role key (bypasses RLS)."""
    global _service_client
    if _service_client is None:
        _service_client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
    return _service_client


def get_anon_client() -> Client:
    """Get Supabase client with anon key (respects RLS)."""
    global _anon_client
    if _anon_client is None:
        _anon_client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key,
        )
    return _anon_client
