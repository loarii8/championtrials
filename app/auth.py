import hashlib
import os
import secrets
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Role

_INSECURE_SECRET_KEYS = {
    "change-this-secret-key-in-production",
    "pejamarket-development-secret",
}


def _resolve_secret_key(configured_key: str | None, app_env: str) -> str:
    if configured_key and len(configured_key) >= 32 and configured_key not in _INSECURE_SECRET_KEYS:
        return configured_key
    if app_env.lower() in {"production", "prod", "staging"}:
        raise RuntimeError(
            "Set SECRET_KEY to a unique random value of at least 32 characters "
            "before running in production or staging."
        )
    return secrets.token_urlsafe(48)


SECRET_KEY = _resolve_secret_key(os.getenv("SECRET_KEY"), os.getenv("APP_ENV", "development"))
ALGORITHM = "HS256"
security = HTTPBearer()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, digest = password_hash.split("$", 1)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
        return secrets.compare_digest(candidate, digest)
    except ValueError:
        return False


def create_access_token(user: User, remember_me: bool = False) -> str:
    expire = datetime.utcnow() + timedelta(days=30 if remember_me else 7)
    return jwt.encode({"sub": str(user.id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(*roles: Role):
    def dependency(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return dependency
