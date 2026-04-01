from __future__ import annotations

from http import HTTPStatus
from typing import Any

import pymysql

from app.core.database import db_cursor, fetch_one_dict
from app.core.exceptions import AppException
from app.core.security import hash_password, validate_username, verify_password

ROLE_ADMIN = "admin"
ROLE_USER = "user"
_ALLOWED_ROLES = {ROLE_ADMIN, ROLE_USER}


class UserService:
    @staticmethod
    def _normalize_email(email: str | None) -> str | None:
        if email is None:
            return None
        normalized = email.strip()
        if not normalized:
            return None
        if "@" not in normalized or len(normalized) > 255:
            raise AppException("邮箱格式不正确", status_code=HTTPStatus.BAD_REQUEST)
        return normalized

    @staticmethod
    def _normalize_nickname(nickname: str | None) -> str | None:
        if nickname is None:
            return None
        normalized = nickname.strip()
        if not normalized:
            return None
        if len(normalized) > 64:
            raise AppException("昵称长度不能超过 64", status_code=HTTPStatus.BAD_REQUEST)
        return normalized

    @staticmethod
    def _validate_password(password: str, *, field_name: str = "密码") -> None:
        if len(password) < 8:
            raise AppException(f"{field_name}长度至少 8 位", status_code=HTTPStatus.BAD_REQUEST)
        if len(password) > 128:
            raise AppException(f"{field_name}长度不能超过 128 位", status_code=HTTPStatus.BAD_REQUEST)

    @staticmethod
    def _translate_integrity_error(ex: pymysql.err.IntegrityError) -> AppException:
        message = str(ex).lower()
        if "uk_users_username" in message or "for key 'username'" in message:
            return AppException("用户名已存在", status_code=HTTPStatus.CONFLICT)
        if "uk_users_email" in message or "for key 'email'" in message:
            return AppException("邮箱已存在", status_code=HTTPStatus.CONFLICT)
        return AppException("用户操作失败", status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

    def create_user(
        self,
        username: str,
        password: str,
        email: str | None = None,
        nickname: str | None = None,
    ) -> dict[str, Any]:
        normalized_username = username.strip()
        if not validate_username(normalized_username):
            raise AppException(
                "用户名仅支持字母/数字/下划线，长度 3-32",
                status_code=HTTPStatus.BAD_REQUEST,
            )

        normalized_email = self._normalize_email(email)
        normalized_nickname = self._normalize_nickname(nickname)
        self._validate_password(password)
        password_hash = hash_password(password)

        try:
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (username, email, password_hash, nickname, role, is_active)
                    VALUES (%s, %s, %s, %s, %s, 1)
                    """,
                    (normalized_username, normalized_email, password_hash, normalized_nickname, ROLE_USER),
                )
                user_id = int(cursor.lastrowid)
                cursor.execute(
                    """
                    SELECT id, username, email, nickname, avatar_url, role, is_active, created_at, updated_at, last_login_at
                    FROM users
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (user_id,),
                )
                row = fetch_one_dict(cursor)
        except pymysql.err.IntegrityError as ex:
            raise self._translate_integrity_error(ex) from ex

        if row is None:
            raise AppException("用户创建失败", status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
        return row

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, email, nickname, avatar_url, role, is_active, created_at, updated_at, last_login_at, password_hash
                FROM users
                WHERE username = %s
                LIMIT 1
                """,
                (username.strip(),),
            )
            return fetch_one_dict(cursor)

    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, email, nickname, avatar_url, role, is_active, created_at, updated_at, last_login_at
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            return fetch_one_dict(cursor)

    def get_user_by_id_with_password(self, user_id: int) -> dict[str, Any] | None:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, email, nickname, avatar_url, role, is_active, created_at, updated_at, last_login_at, password_hash
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            return fetch_one_dict(cursor)

    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        user = self.get_user_by_username(username)
        if user is None:
            return None
        if not verify_password(password, str(user.get("password_hash", ""))):
            return None
        user.pop("password_hash", None)
        return user

    def update_last_login(self, user_id: int) -> None:
        with db_cursor() as cursor:
            cursor.execute(
                "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = %s",
                (user_id,),
            )

    def update_avatar(self, user_id: int, avatar_url: str) -> dict[str, Any] | None:
        with db_cursor() as cursor:
            cursor.execute(
                "UPDATE users SET avatar_url = %s WHERE id = %s",
                (avatar_url, user_id),
            )
            cursor.execute(
                """
                SELECT id, username, email, nickname, avatar_url, role, is_active, created_at, updated_at, last_login_at
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            return fetch_one_dict(cursor)

    def update_profile(
        self,
        user_id: int,
        *,
        email: str | None,
        nickname: str | None,
    ) -> dict[str, Any] | None:
        normalized_email = self._normalize_email(email)
        normalized_nickname = self._normalize_nickname(nickname)

        try:
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users
                    SET email = %s, nickname = %s
                    WHERE id = %s
                    """,
                    (normalized_email, normalized_nickname, user_id),
                )
                cursor.execute(
                    """
                    SELECT id, username, email, nickname, avatar_url, role, is_active, created_at, updated_at, last_login_at
                    FROM users
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (user_id,),
                )
                return fetch_one_dict(cursor)
        except pymysql.err.IntegrityError as ex:
            raise self._translate_integrity_error(ex) from ex

    def change_password(self, user_id: int, current_password: str, new_password: str) -> None:
        self._validate_password(new_password, field_name="新密码")
        user = self.get_user_by_id_with_password(user_id)
        if user is None:
            raise AppException("用户不存在", status_code=HTTPStatus.NOT_FOUND)

        old_hash = str(user.get("password_hash", ""))
        if not verify_password(current_password, old_hash):
            raise AppException("当前密码错误", status_code=HTTPStatus.UNAUTHORIZED)
        if verify_password(new_password, old_hash):
            raise AppException("新密码不能与当前密码相同", status_code=HTTPStatus.BAD_REQUEST)

        new_hash = hash_password(new_password)
        with db_cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (new_hash, user_id),
            )

    def admin_list_users(
        self,
        *,
        page: int,
        page_size: int,
        keyword: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[int, list[dict[str, Any]]]:
        filters: list[str] = []
        params: list[Any] = []

        if keyword:
            kw = keyword.strip()
            if kw:
                filters.append("(username LIKE %s OR email LIKE %s OR nickname LIKE %s)")
                params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%"])

        if role:
            role_value = role.strip().lower()
            if role_value not in _ALLOWED_ROLES:
                raise AppException("role 仅支持 admin/user", status_code=HTTPStatus.BAD_REQUEST)
            filters.append("role = %s")
            params.append(role_value)

        if is_active is not None:
            filters.append("is_active = %s")
            params.append(1 if is_active else 0)

        where_clause = "WHERE " + " AND ".join(filters) if filters else ""
        offset = (page - 1) * page_size

        with db_cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) AS total FROM users {where_clause}",  # nosec B608
                tuple(params),
            )
            total_row = fetch_one_dict(cursor) or {"total": 0}
            total = int(total_row["total"])

            cursor.execute(
                f"""
                SELECT id, username, email, nickname, avatar_url, role, is_active, created_at, updated_at, last_login_at
                FROM users
                {where_clause}
                ORDER BY id ASC
                LIMIT %s OFFSET %s
                """,  # nosec B608
                tuple(params + [page_size, offset]),
            )
            rows = [dict(row) for row in cursor.fetchall()]

        return total, rows

    def admin_update_user(self, user_id: int, updates: dict[str, Any]) -> dict[str, Any] | None:
        db_updates: dict[str, Any] = {}

        if "email" in updates:
            db_updates["email"] = self._normalize_email(updates.get("email"))
        if "nickname" in updates:
            db_updates["nickname"] = self._normalize_nickname(updates.get("nickname"))
        if "role" in updates:
            role = str(updates.get("role") or "").strip().lower()
            if role not in _ALLOWED_ROLES:
                raise AppException("role 仅支持 admin/user", status_code=HTTPStatus.BAD_REQUEST)
            db_updates["role"] = role
        if "is_active" in updates:
            db_updates["is_active"] = 1 if bool(updates.get("is_active")) else 0

        if not db_updates:
            raise AppException("缺少可更新字段", status_code=HTTPStatus.BAD_REQUEST)

        set_clause = ", ".join(f"{field} = %s" for field in db_updates.keys())
        params = list(db_updates.values()) + [user_id]

        try:
            with db_cursor() as cursor:
                cursor.execute(
                    f"UPDATE users SET {set_clause} WHERE id = %s",  # nosec B608
                    tuple(params),
                )
                cursor.execute(
                    """
                    SELECT id, username, email, nickname, avatar_url, role, is_active, created_at, updated_at, last_login_at
                    FROM users
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (user_id,),
                )
                return fetch_one_dict(cursor)
        except pymysql.err.IntegrityError as ex:
            raise self._translate_integrity_error(ex) from ex

    def admin_reset_user_password(self, user_id: int, new_password: str) -> None:
        self._validate_password(new_password, field_name="新密码")
        new_hash = hash_password(new_password)
        with db_cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (new_hash, user_id),
            )

    def record_login_log(
        self,
        user_id: int | None,
        is_success: bool,
        reason: str | None,
        login_ip: str | None,
        user_agent: str | None,
    ) -> None:
        with db_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_login_logs (user_id, login_ip, user_agent, is_success, reason)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    (login_ip or "")[:45] or None,
                    (user_agent or "")[:255] or None,
                    1 if is_success else 0,
                    (reason or "")[:255] or None,
                ),
            )


user_service = UserService()
