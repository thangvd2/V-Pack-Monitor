# =============================================================================
# V-Pack Monitor - CamDongHang v2.1.0
# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================

import os
import secrets
import jwt
import bcrypt
import time as _time
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
import database


def _load_or_create_secret():
    env_secret = os.environ.get("VPACK_SECRET")
    if env_secret:
        return env_secret
    db_secret = database.get_setting("JWT_SECRET")
    if db_secret:
        return db_secret
    new_secret = secrets.token_hex(32)
    database.set_setting("JWT_SECRET", new_secret)
    return new_secret


SECRET_KEY = _load_or_create_secret()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def revoke_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"leeway": 5})
        jti = payload.get("jti")
        exp = payload.get("exp", 0)
        if jti and exp:
            database.revoke_jti(jti, exp)
    except Exception:
        pass


def is_token_revoked(jti: str) -> bool:
    return database.is_jti_revoked(jti)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["jti"] = secrets.token_hex(16)
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"leeway": 5})


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực. Vui lòng đăng nhập lại.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        jti = payload.get("jti")
        if user_id is None:
            raise credentials_exception
        if jti and is_token_revoked(jti):
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = database.get_user_by_id(int(user_id))
    if user is None or not user.get("is_active"):
        raise credentials_exception
    return user


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Yêu cầu quyền Administrator.",
        )
    return current_user


CurrentUser = Annotated[dict, Depends(get_current_user)]
AdminUser = Annotated[dict, Depends(require_admin)]
