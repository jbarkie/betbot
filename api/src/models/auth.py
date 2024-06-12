from pydantic import BaseModel

class User(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: str
    disabled: bool = False

class AuthenticatedUser(User):
    hashed_password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"