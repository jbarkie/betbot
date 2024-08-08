from fastapi import FastAPI, HTTPException, Query, Depends
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm
from api.src.config import ACCESS_TOKEN_EXPIRE_MINUTES
from api.src.login import authenticate_user, create_access_token, get_current_user, get_user_by_username
from api.src.models.auth import AuthenticatedUser, LoginResponse, RegisterRequest, RegisterResponse, User
from api.src.games import get_games_by_date
from api.src.models.nba import GamesResponse
import uvicorn
from typing import Any, Annotated
from fastapi.middleware.cors import CORSMiddleware
import traceback
from api.src.register import register_user

app = FastAPI()
__all__ = ["app"]

def configure(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://localhost:4200"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.post("/register", response_model=RegisterResponse)
async def register(register_request: RegisterRequest):
    username = register_request.username
    user = get_user_by_username(username)
    if user:
        raise HTTPException(status_code=403, detail="User already exists")
    register_user(username, register_request.first_name, register_request.last_name, register_request.email, register_request.password)

    access_token = create_access_token(data={"sub": username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    response = RegisterResponse(access_token=access_token)
    return response

@app.post("/login", response_model=LoginResponse)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    response = LoginResponse(access_token=access_token)
    return response

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]):
    return current_user

@app.get("/nba/games", response_model=GamesResponse)
async def games(date: str = Query(..., description="Date in YYYY-MM-DD format")) -> Any:
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
        return get_games_by_date(parsed_date, 'NBA', 'basketball_nba')
    except ValueError as e:
        error_message = f"Invalid date format. Please use YYYY-MM-DD format. Error: {str(e)}"
        traceback_message = traceback.format_exc()
        print(f"Error: {error_message}\nTraceback: {traceback_message}")
        raise HTTPException(status_code=400, detail=error_message)
    except Exception as e:
        error_message = f"An error occurred while processing the request. Error: {str(e)}"
        traceback_message = traceback.format_exc()
        print(f"Error: {error_message}\nTraceback: {traceback_message}")
        raise HTTPException(status_code=500, detail=error_message)
    
def main():
    configure(app)
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()