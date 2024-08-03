from datetime import datetime, timedelta, timezone
from typing import Union
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from api.src.config import ALGORITHM, SECRET_KEY
from api.src.models.auth import AuthenticatedUser
from api.src.models.tables import Users
from api.src.utils import connect_to_db
import jwt
from jwt.exceptions import InvalidTokenError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_user_by_username(username: str) -> AuthenticatedUser:
    session = connect_to_db()
    user = session.query(Users).filter_by(username=username).first()
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