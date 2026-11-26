import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def get_secret_key():
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret or len(secret.encode("utf-8")) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be at least 32 bytes")
    return secret


def hash_password(password: str):
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, password_hash: str):
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except ValueError:
        return False


def create_access_token(user_id: int, role: str):
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    }

    return jwt.encode(
        payload,
        get_secret_key(),
        algorithm=ALGORITHM
    )


def decode_access_token(token: str):
    try:
        return jwt.decode(
            token,
            get_secret_key(),
            algorithms=[ALGORITHM],
            options={"require": ["sub", "role", "exp"]}
        )
    except jwt.InvalidTokenError:
        return None

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = decode_access_token(credentials.credentials)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if payload.get("role") not in ("owner", "staff"):
        raise HTTPException(
            status_code=403,
            detail="Invalid user role"
        )

    return payload


def require_owner(user: dict = Depends(get_current_user)):
    if user.get("role") != "owner":
        raise HTTPException(
            status_code=403,
            detail="Owner access required"
        )

    return user