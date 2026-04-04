import jwt
import os
import random
import string
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv("JWT_SECRET", "smartshift_super_secret_2026")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 168  # 1 week

security = HTTPBearer()

def generate_worker_id():
    suffix = ''.join(random.choices(string.digits, k=5))
    return f"W-{suffix}"

def generate_otp():
    # In production: send via SMS gateway. For demo, return fixed mock.
    return "123456"

def create_jwt(worker_id: str, phone: str) -> str:
    payload = {
        "sub": worker_id,
        "phone": phone,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please login again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")

def get_current_worker(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency injected into protected routes."""
    return decode_jwt(credentials.credentials)
