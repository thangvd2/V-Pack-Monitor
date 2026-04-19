import time

import pytest

import auth
import database


class TestJWT:
    def test_create_decode_roundtrip(self):
        token = auth.create_access_token({"sub": "1", "role": "ADMIN"})
        payload = auth.decode_token(token)
        assert payload["sub"] == "1"
        assert payload["role"] == "ADMIN"

    def test_token_has_jti(self):
        token = auth.create_access_token({"sub": "1"})
        payload = auth.decode_token(token)
        assert "jti" in payload
        assert len(payload["jti"]) == 32

    def test_token_jti_unique(self):
        t1 = auth.create_access_token({"sub": "1"})
        t2 = auth.create_access_token({"sub": "1"})
        p1 = auth.decode_token(t1)
        p2 = auth.decode_token(t2)
        assert p1["jti"] != p2["jti"]

    def test_token_has_expiry(self):
        token = auth.create_access_token({"sub": "1"})
        payload = auth.decode_token(token)
        assert "exp" in payload
        assert payload["exp"] > time.time()

    def test_expired_token_raises(self):
        import jwt as _jwt

        expired = _jwt.encode(
            {"sub": "1", "exp": time.time() - 3600, "jti": "old"},
            auth.SECRET_KEY,
            algorithm=auth.ALGORITHM,
        )
        with pytest.raises(_jwt.ExpiredSignatureError):
            auth.decode_token(expired)

    def test_invalid_token_raises(self):
        import jwt as _jwt

        with pytest.raises(_jwt.PyJWTError):
            auth.decode_token("invalid.token.string")

    def test_wrong_secret_raises(self):
        import jwt as _jwt

        token = _jwt.encode(
            {"sub": "1", "exp": time.time() + 3600},
            "wrong_secret_key",
            algorithm=auth.ALGORITHM,
        )
        with pytest.raises(_jwt.PyJWTError):
            auth.decode_token(token)


class TestTokenRevocation:
    def test_revoke_token(self, isolate_db):
        token = auth.create_access_token({"sub": "1", "role": "ADMIN"})
        auth.revoke_token(token)
        payload = auth.decode_token(token)
        assert auth.is_token_revoked(payload["jti"]) is True

    def test_non_revoked_token(self):
        assert auth.is_token_revoked("never_seen_jti_12345") is False

    def test_revoke_invalid_token_no_error(self):
        auth.revoke_token("not_a_real_token")

    def test_revoke_expired_token_no_error(self):
        import jwt as _jwt

        expired = _jwt.encode(
            {"sub": "1", "exp": time.time() - 3600, "jti": "expired_jti"},
            auth.SECRET_KEY,
            algorithm=auth.ALGORITHM,
        )
        auth.revoke_token(expired)


class TestGetCurrentUser:
    def test_valid_token_active_user(self, isolate_db, admin_user_id):
        token = auth.create_access_token({"sub": str(admin_user_id), "role": "ADMIN"})
        user = auth.get_current_user(token=token)
        assert user["id"] == admin_user_id
        assert user["role"] == "ADMIN"

    def test_revoked_token_raises_401(self, isolate_db, admin_user_id):
        from fastapi import HTTPException

        token = auth.create_access_token({"sub": str(admin_user_id), "role": "ADMIN"})
        auth.revoke_token(token)
        with pytest.raises(HTTPException) as exc_info:
            auth.get_current_user(token=token)
        assert exc_info.value.status_code == 401

    def test_inactive_user_raises_401(self, isolate_db, admin_user_id):
        from fastapi import HTTPException

        database.update_user(admin_user_id, is_active=0)
        token = auth.create_access_token({"sub": str(admin_user_id), "role": "ADMIN"})
        with pytest.raises(HTTPException) as exc_info:
            auth.get_current_user(token=token)
        assert exc_info.value.status_code == 401

    def test_deleted_user_raises_401(self, isolate_db, admin_user_id):
        from fastapi import HTTPException

        token = auth.create_access_token({"sub": str(admin_user_id), "role": "ADMIN"})
        database.delete_user(admin_user_id)
        with pytest.raises(HTTPException) as exc_info:
            auth.get_current_user(token=token)
        assert exc_info.value.status_code == 401

    def test_invalid_token_raises_401(self, isolate_db):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            auth.get_current_user(token="invalid_token")
        assert exc_info.value.status_code == 401


class TestRequireAdmin:
    def test_admin_passes(self, isolate_db, admin_user_id):
        user = database.get_user_by_id(admin_user_id)
        result = auth.require_admin(current_user=user)
        assert result["role"] == "ADMIN"

    def test_operator_raises_403(self, isolate_db, operator_user_id):
        from fastapi import HTTPException

        user = database.get_user_by_id(operator_user_id)
        with pytest.raises(HTTPException) as exc_info:
            auth.require_admin(current_user=user)
        assert exc_info.value.status_code == 403
