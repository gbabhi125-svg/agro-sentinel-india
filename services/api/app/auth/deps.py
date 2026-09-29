from fastapi import Header, HTTPException

from ..storage import db
from .security import decode_access_token


def get_current_user_required(authorization: str | None = Header(default=None)) -> dict:
    user = _user_from_header(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def get_current_user_optional(authorization: str | None = Header(default=None)) -> dict | None:
    return _user_from_header(authorization)


def _user_from_header(authorization: str | None) -> dict | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    user_id = decode_access_token(token)
    if not user_id:
        return None
    return db.get_user_by_id(user_id)
