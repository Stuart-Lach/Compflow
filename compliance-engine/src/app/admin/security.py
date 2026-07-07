"""Administrator authentication helpers for the desktop operations console."""

import base64
import getpass
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass

from fastapi import HTTPException, Request, status

from app.config import settings

ADMIN_COOKIE_NAME = "compflow_admin_session"
_PASSWORD_ALGORITHM = "pbkdf2_sha256"
_PASSWORD_ITERATIONS = 390_000


@dataclass(frozen=True)
class AdminSession:
    """Authenticated administrator session details."""

    username: str
    expires_at: int


def hash_admin_password(password: str, salt_hex: str | None = None) -> str:
    """Hash an administrator password using PBKDF2-SHA256."""
    if not password:
        raise ValueError("Password must not be empty")

    salt = bytes.fromhex(salt_hex) if salt_hex is not None else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PASSWORD_ITERATIONS,
    )
    return (
        f"{_PASSWORD_ALGORITHM}${_PASSWORD_ITERATIONS}$"
        f"{salt.hex()}${digest.hex()}"
    )


def verify_admin_password(password: str, stored_hash: str) -> bool:
    """Verify an administrator password against a stored PBKDF2 hash."""
    try:
        algorithm, iterations_raw, salt_hex, expected_hex = stored_hash.split("$", 3)
        iterations = int(iterations_raw)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
    except (ValueError, TypeError):
        return False

    if algorithm != _PASSWORD_ALGORITHM or iterations <= 0:
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return secrets.compare_digest(digest, expected)


def verify_admin_credentials(username: str, password: str) -> bool:
    """Return whether the provided credentials match the configured administrator."""
    if not settings.admin_dashboard_configured:
        return False

    return secrets.compare_digest(username, settings.ADMIN_USERNAME) and verify_admin_password(
        password,
        settings.ADMIN_PASSWORD_HASH,
    )


def create_admin_session_token(username: str, issued_at: int | None = None) -> str:
    """Create a signed, expiring administrator session token."""
    if not settings.ADMIN_SESSION_SECRET:
        raise RuntimeError("ADMIN_SESSION_SECRET is not configured")

    now = int(issued_at if issued_at is not None else time.time())
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + settings.ADMIN_SESSION_TTL_SECONDS,
    }
    encoded_payload = _base64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = _sign(encoded_payload)
    return f"{encoded_payload}.{signature}"


def verify_admin_session_token(token: str | None, now: int | None = None) -> AdminSession | None:
    """Verify a signed administrator session token and return its session."""
    if not token or not settings.ADMIN_SESSION_SECRET:
        return None

    try:
        encoded_payload, provided_signature = token.split(".", 1)
    except ValueError:
        return None

    expected_signature = _sign(encoded_payload)
    if not secrets.compare_digest(provided_signature, expected_signature):
        return None

    try:
        payload = json.loads(_base64url_decode(encoded_payload).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None

    username = payload.get("sub")
    expires_at = payload.get("exp")
    if not isinstance(username, str) or not isinstance(expires_at, int):
        return None
    if not secrets.compare_digest(username, settings.ADMIN_USERNAME):
        return None
    if expires_at <= int(now if now is not None else time.time()):
        return None

    return AdminSession(username=username, expires_at=expires_at)


def get_admin_session(request: Request) -> AdminSession | None:
    """Read and verify the administrator session from the request cookie."""
    return verify_admin_session_token(request.cookies.get(ADMIN_COOKIE_NAME))


async def require_admin_session(request: Request) -> AdminSession:
    """FastAPI dependency requiring an authenticated administrator session."""
    session = get_admin_session(request)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator login required",
        )
    request.state.admin_username = session.username
    return session


def _sign(encoded_payload: str) -> str:
    signature = hmac.new(
        settings.ADMIN_SESSION_SECRET.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(signature)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def main() -> None:
    """Print a password hash suitable for ADMIN_PASSWORD_HASH."""
    password = getpass.getpass("Admin password: ")
    confirm = getpass.getpass("Confirm admin password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match")
    print(hash_admin_password(password))


if __name__ == "__main__":
    main()
