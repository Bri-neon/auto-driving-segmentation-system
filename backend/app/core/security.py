from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import time
from typing import Any

from app.core.config import settings

PBKDF2_PREFIX = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 120000
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,32}$")


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str, iterations: int = PBKDF2_ITERATIONS) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
    return (
        f"{PBKDF2_PREFIX}${iterations}$"
        f"{base64.b64encode(salt).decode('ascii')}$"
        f"{base64.b64encode(digest).decode('ascii')}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algo, iteration_text, salt_b64, digest_b64 = password_hash.split("$", 3)
        if algo != PBKDF2_PREFIX:
            return False
        iterations = int(iteration_text)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected_digest = base64.b64decode(digest_b64.encode("ascii"))
    except Exception:
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations, dklen=len(expected_digest)
    )
    return hmac.compare_digest(actual_digest, expected_digest)


def create_access_token(user_id: int, username: str, role: str) -> tuple[str, int]:
    now = int(time.time())
    expire_seconds = settings.jwt_expire_minutes * 60
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + expire_seconds,
    }
    token = _encode_jwt(payload, settings.jwt_secret_key)
    return token, expire_seconds


def decode_access_token(token: str) -> dict[str, Any]:
    payload = _decode_jwt(token, settings.jwt_secret_key)
    exp = int(payload.get("exp", 0))
    if exp <= int(time.time()):
        raise ValueError("token 已过期")
    return payload


def _encode_jwt(payload: dict[str, Any], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    signing_input = f"{_b64url_encode(header_bytes)}.{_b64url_encode(payload_bytes)}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{signing_input.decode('ascii')}.{_b64url_encode(signature)}"


def _decode_jwt(token: str, secret: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".", 2)
    except ValueError as ex:
        raise ValueError("token 格式错误") from ex

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    actual_sig = _b64url_decode(signature_b64)
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("token 签名无效")

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception as ex:
        raise ValueError("token 载荷无效") from ex
    return payload


def validate_username(username: str) -> bool:
    return bool(USERNAME_PATTERN.fullmatch(username))
