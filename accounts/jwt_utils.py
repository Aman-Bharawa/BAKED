import base64
import hashlib
import hmac
import json
import time

from django.conf import settings


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(message: bytes) -> str:
    secret = settings.JWT_SECRET_KEY.encode("utf-8")
    signature = hmac.new(secret, message, hashlib.sha256).digest()
    return _b64url_encode(signature)


def generate_jwt(user) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "iat": now,
        "exp": now + settings.JWT_EXPIRATION_SECONDS,
    }

    encoded_header = _b64url_encode(
        json.dumps(header, separators=(",", ":")).encode("utf-8")
    )
    encoded_payload = _b64url_encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = _sign(signing_input)
    return f"{encoded_header}.{encoded_payload}.{signature}"


def decode_jwt(token: str) -> dict | None:
    try:
        encoded_header, encoded_payload, signature = token.split(".")
        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        expected_signature = _sign(signing_input)
        if not hmac.compare_digest(signature, expected_signature):
            return None

        payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None
