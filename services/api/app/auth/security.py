"""
Real password hashing (bcrypt directly — passlib is unmaintained and breaks
on bcrypt>=4.1) + JWT session tokens. No plaintext password is ever stored,
only the bcrypt hash.

JWT_SECRET must be set in production; a per-process random fallback is used
if it isn't, which means every restart invalidates all issued tokens (a
loud, safe failure mode instead of a shared default secret you'd forget to
change). Set it in .env.
"""
import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

_SECRET = os.environ.get("JWT_SECRET")
if not _SECRET:
    _SECRET = secrets.token_urlsafe(32)
    print("[warn] JWT_SECRET is not set — using a random per-process secret. "
          "Every restart will invalidate existing login sessions. Set JWT_SECRET in .env for production.")

_ALGORITHM = "HS256"
_TOKEN_TTL_HOURS = 24 * 30  # 30 days — a farmer shouldn't have to re-login constantly


def hash_password(password: str) -> str:
    # bcrypt's own 72-byte input limit — truncate rather than error, same as
    # every mainstream bcrypt wrapper does.
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=_TOKEN_TTL_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
