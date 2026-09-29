from fastapi import APIRouter, Depends, HTTPException

from ..auth.deps import get_current_user_required
from ..auth.security import create_access_token, hash_password, verify_password
from ..schemas import LoginRequest, RegisterRequest
from ..storage import db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(req: RegisterRequest):
    username = req.username.strip().lower()
    if not username or len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Username required and password must be at least 6 characters")
    if db.get_user_by_username(username):
        raise HTTPException(status_code=409, detail="That username is already taken")

    user = db.create_user(req.name.strip(), username, hash_password(req.password))
    token = create_access_token(user["id"])
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
def login(req: LoginRequest):
    user = db.get_user_by_username(req.username.strip().lower())
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(user["id"])
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def me(user: dict = Depends(get_current_user_required)):
    return user
