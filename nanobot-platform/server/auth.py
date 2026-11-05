"""Authentication: scrypt password hashing, server-side sessions, FastAPI deps."""
import base64
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import db, settings

_bearer = HTTPBearer(auto_error=False)

SCRYPT_N, SCRYPT_R, SCRYPT_P = 2 ** 14, 8, 1


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32)
    return "scrypt$%d$%d$%d$%s$%s" % (
        SCRYPT_N, SCRYPT_R, SCRYPT_P,
        base64.b64encode(salt).decode(), base64.b64encode(dk).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt_b64, hash_b64 = stored.split("$")
        if algo != "scrypt":
            return False
        salt = base64.b64decode(salt_b64)
        want = base64.b64decode(hash_b64)
        got = hashlib.scrypt(password.encode(), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(want))
        return secrets.compare_digest(got, want)
    except Exception:
        return False


def create_session(user_id: int, ip=None, user_agent=None) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=settings.SESSION_TTL_DAYS)
    db.exe(
        "INSERT INTO sessions (token, user_id, created_at, expires_at, ip, user_agent) VALUES (?,?,?,?,?,?)",
        (token, user_id, db.utcnow(), expires.isoformat(timespec="seconds"), ip, user_agent),
    )
    return token


def delete_session(token: str):
    db.exe("DELETE FROM sessions WHERE token=?", (token,))


def get_user_by_token(token: str):
    if not token:
        return None
    row = db.q1(
        """SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id
           WHERE s.token=? AND s.expires_at>?""",
        (token, db.utcnow()),
    )
    return row


def current_user(req: Request, creds: HTTPAuthorizationCredentials = Depends(_bearer)):
    token = None
    if creds and creds.scheme.lower() == "bearer":
        token = creds.credentials
    else:
        token = req.cookies.get("nb_session")
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return dict(user)


def bootstrap_admin():
    """Create the initial admin on first run."""
    row = db.q1("SELECT COUNT(*) AS c FROM users")
    if row and row["c"] > 0:
        return
    username = os.environ.get("NANOBOT_ADMIN_USER", "admin")
    password = os.environ.get("NANOBOT_ADMIN_PASSWORD")
    if not password:
        password = secrets.token_urlsafe(12)
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        (settings.DATA_DIR / "admin-password.txt").write_text(
            f"Generated admin password for '{username}': {password}\n", mode=0o600
        )
    db.exe(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?,?,?,?)",
        (username, hash_password(password), "admin", db.utcnow()),
    )
    db.audit("system", "bootstrap", {"user": username})
