# =============================================================================
# V-Pack Monitor - CamDongHang
# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================

import time

import auth
import database
from auth import AdminUser, CurrentUser
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator
from vpack import state

# --- AUTH API ---


class LoginPayload(BaseModel):
    username: str
    password: str


_login_attempts = {}
_LOGIN_MAX = 5
_LOGIN_WINDOW = 300


class UserAuthModel(BaseModel):
    id: int
    username: str
    role: str
    full_name: str
    must_change_password: int | None = 0


class LoginResponse(BaseModel):
    status: str
    access_token: str | None = None
    token_type: str | None = None
    user: UserAuthModel | None = None
    message: str | None = None


class UserFullModel(BaseModel):
    id: int
    username: str
    role: str
    full_name: str
    is_active: int
    created_at: str | None = None


class UsersResponse(BaseModel):
    data: list[UserFullModel]


def register_routes(app):
    @app.post("/api/auth/login", response_model=LoginResponse)
    def login(payload: LoginPayload, request: Request):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        with state._login_attempts_lock:
            if len(_login_attempts) > 100:
                expired_ips = [k for k, v in _login_attempts.items() if not v or now - v[-1] > _LOGIN_WINDOW]
                for k in expired_ips:
                    del _login_attempts[k]
            attempts = [t for t in _login_attempts.get(ip, []) if now - t < _LOGIN_WINDOW]
            _login_attempts[ip] = attempts
            if len(attempts) >= _LOGIN_MAX:
                return JSONResponse(
                    status_code=429,
                    content={
                        "status": "error",
                        "message": "Quá nhiều lần đăng nhập sai. Thử lại sau 5 phút.",
                    },
                )
        user = database.get_user_by_username(payload.username)
        if not user or not auth.verify_password(payload.password, user["password_hash"]):
            with state._login_attempts_lock:
                _login_attempts.setdefault(ip, []).append(now)
            database.log_audit(
                user["id"] if user else 0,
                "LOGIN_FAILED",
                f"username={payload.username}, ip={ip}",
            )
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "message": "Sai tên đăng nhập hoặc mật khẩu.",
                },
            )
        if not user.get("is_active"):
            return JSONResponse(
                status_code=403,
                content={"status": "error", "message": "Tài khoản đã bị khóa."},
            )
        token = auth.create_access_token({"sub": str(user["id"]), "role": user["role"]})
        database.log_audit(user["id"], "LOGIN")
        return {
            "status": "success",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "full_name": user["full_name"],
                "must_change_password": user.get("must_change_password", 0),
            },
        }

    @app.get("/api/auth/me")
    def get_me(current_user: CurrentUser):
        return {"status": "success", "user": current_user}

    @app.post("/api/auth/logout")
    def logout(current_user: CurrentUser, request: Request):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
        if token:
            auth.revoke_token(token)
        database.log_audit(current_user["id"], "LOGOUT")
        return {"status": "success", "message": "Đã đăng xuất."}

    class ChangePasswordPayload(BaseModel):
        old_password: str
        new_password: str

        @model_validator(mode="after")
        def validate_pwd(self):
            if len(self.new_password) < 6:
                raise ValueError("Mật khẩu phải có ít nhất 6 ký tự.")
            return self

    @app.put("/api/auth/change-password")
    def change_password(payload: ChangePasswordPayload, current_user: CurrentUser):
        user = database.get_user_by_id(current_user["id"])
        if not user:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "Người dùng không tồn tại."},
            )
        full_user = database.get_user_by_username(user["username"])
        if not full_user or not auth.verify_password(payload.old_password, full_user["password_hash"]):
            return JSONResponse(
                status_code=401,
                content={"status": "error", "message": "Mật khẩu cũ không đúng."},
            )
        database.update_user_password(user["id"], payload.new_password)
        database.clear_must_change_password(user["id"])
        database.log_audit(user["id"], "CHANGE_PASSWORD")
        return {"status": "success", "message": "Đã đổi mật khẩu thành công."}

    # --- USER MANAGEMENT API (ADMIN ONLY) ---

    @app.get("/api/users", response_model=UsersResponse)
    def list_users(admin: AdminUser):
        return {"data": database.get_all_users()}

    class UserCreatePayload(BaseModel):
        username: str = Field(..., min_length=2, max_length=50)
        password: str = Field(..., min_length=6)
        role: str = "OPERATOR"
        full_name: str = ""

    @app.post("/api/users")
    def create_user(payload: UserCreatePayload, admin: AdminUser):
        if payload.role not in ("ADMIN", "OPERATOR"):
            return JSONResponse(
                status_code=422,
                content={
                    "status": "error",
                    "message": "Role phải là ADMIN hoặc OPERATOR.",
                },
            )
        new_id = database.create_user(payload.username, payload.password, payload.role, payload.full_name)
        if new_id is None:
            return JSONResponse(
                status_code=422,
                content={"status": "error", "message": "Username đã tồn tại."},
            )
        database.log_audit(admin["id"], "CREATE_USER", f"username={payload.username}")
        return {"status": "success", "id": new_id}

    class UserUpdatePayload(BaseModel):
        role: str | None = None
        full_name: str | None = None
        is_active: int | None = None

    @app.put("/api/users/{user_id}")
    def update_user_api(user_id: int, payload: UserUpdatePayload, admin: AdminUser):
        kwargs = payload.model_dump(exclude_none=True)
        if not kwargs:
            return JSONResponse(
                status_code=422,
                content={"status": "error", "message": "Không có dữ liệu cập nhật."},
            )
        # Prevent admin from locking themselves out
        if payload.is_active == 0 and user_id == admin["id"]:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Không thể khoá tài khoản của chính mình.",
                },
            )
        if payload.is_active is not None:
            old_user = database.get_user_by_id(user_id)
            if old_user and old_user["is_active"] != payload.is_active:
                action = "LOCK_USER" if payload.is_active == 0 else "UNLOCK_USER"
                database.log_audit(admin["id"], action, f"user_id={user_id}")
        database.update_user(user_id, **kwargs)
        database.log_audit(admin["id"], "UPDATE_USER", f"user_id={user_id}")
        return {"status": "success"}

    class ResetPasswordPayload(BaseModel):
        password: str

        @model_validator(mode="after")
        def validate_pwd(self):
            if len(self.password) < 6:
                raise ValueError("Mật khẩu phải có ít nhất 6 ký tự.")
            return self

    @app.put("/api/users/{user_id}/password")
    def reset_password(user_id: int, payload: ResetPasswordPayload, admin: AdminUser):
        database.update_user_password(user_id, payload.password)
        database.log_audit(admin["id"], "RESET_PASSWORD", f"user_id={user_id}")
        return {"status": "success"}

    @app.delete("/api/users/{user_id}")
    def delete_user_api(user_id: int, admin: AdminUser):
        if user_id == admin["id"]:
            return JSONResponse(
                status_code=403,
                content={"status": "error", "message": "Không thể xoá chính mình."},
            )
        database.delete_user(user_id)
        database.log_audit(admin["id"], "DELETE_USER", f"user_id={user_id}")
        return {"status": "success"}
