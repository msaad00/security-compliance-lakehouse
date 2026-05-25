"""Browser session tokens and cookie helpers.

Sessions are opaque tokens (``tops_sess_<hex>``) delivered to the browser in an
httpOnly cookie. Only the SHA-256 hash is persisted, mirroring API keys, so a
database leak never exposes a live session.
"""

from __future__ import annotations

import hashlib
import secrets

SESSION_COOKIE = "trustops_session"
SESSION_TOKEN_PREFIX = "tops_sess_"
DEFAULT_SESSION_TTL_HOURS = 12


def generate_session_token() -> tuple[str, str]:
    """Return ``(token, token_hash)`` for a new browser session."""
    token = f"{SESSION_TOKEN_PREFIX}{secrets.token_hex(32)}"
    return token, hash_session_token(token)


def hash_session_token(token: str) -> str:
    """SHA-256 hex digest of a session token (the only form persisted)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
