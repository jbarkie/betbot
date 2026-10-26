from datetime import datetime, timedelta, timezone
import math
import time
from typing import Union
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from api.src.config import ALGORITHM, SECRET_KEY
from api.src.models.auth import AuthenticatedUser
from api.src.models.tables import Users
from shared.database import connect_to_db
import jwt
import bcrypt
from jwt.exceptions import InvalidTokenError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

LOGIN_MAX_FAILED_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60

# Failed login times keyed by (client address, username). Held in memory, so it
# is per process and resets on restart, which suits the single-process server.
_failed_logins = {}

def _recent_failures(key, now):
    attempts = [t for t in _failed_logins.get(key, []) if now - t < LOGIN_LOCKOUT_SECONDS]
    if attempts:
        _failed_logins[key] = attempts
    else:
        _failed_logins.pop(key, None)
    return attempts

def login_retry_after(client_host: str, username: str) -> int:
    """Seconds until this client may try this username again; 0 when allowed."""
    now = time.monotonic()
    attempts = _recent_failures((client_host, username.lower()), now)
    if len(attempts) < LOGIN_MAX_FAILED_ATTEMPTS:
        return 0
    return max(1, math.ceil(LOGIN_LOCKOUT_SECONDS - (now - attempts[-LOGIN_MAX_FAILED_ATTEMPTS])))

def record_failed_login(client_host: str, username: str):
    key = (client_host, username.lower())
    now = time.monotonic()
    _failed_logins[key] = _recent_failures(key, now) + [now]

def clear_failed_logins(client_host: str, username: str):
    _failed_logins.pop((client_host, username.lower()), None)

def get_user_by_username(username: str) -> AuthenticatedUser:
    session = connect_to_db()
    user = session.query(Users).filter_by(username=username).first()
    session.close()
    
    if user:
        user = AuthenticatedUser(
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            hashed_password=user.password
        )
    return user

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        return False
    
    try:
        if not bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
            return False
    except ValueError:
        return False
    
    return user