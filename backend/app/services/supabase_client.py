"""Supabase client initialization.

Provides a singleton instance of the Supabase client for backend services.
"""

from supabase import create_client, Client
from backend.app.config import settings
import logging

logger = logging.getLogger(__name__)

def init_supabase() -> Client | None:
    """Initialize and return the Supabase client."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        logger.warning("Supabase URL or Service Role Key is missing. Supabase client will not be initialized.")
        return None
    try:
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None

# Export a single reusable instance
supabase: Client | None = init_supabase()
