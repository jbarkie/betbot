from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException, Query, Depends
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from api.src.config import ACCESS_TOKEN_EXPIRE_MINUTES
from api.src.login import authenticate_user, create_access_token, get_current_user, get_user_by_username
from api.src.models.auth import AuthenticatedUser, LoginResponse, RegisterRequest, RegisterResponse, User
from api.src.games import get_games_for_sport
from api.src.models.games import GamesResponse
import uvicorn
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
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
async def nba_games(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    return await get_games_for_sport(date, "NBA", "basketball_nba")

@app.get("/mlb/games", response_model=GamesResponse)
async def mlb_games(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    return await get_games_for_sport(date, "MLB", "baseball_mlb")

@app.get("/nfl/games", response_model=GamesResponse)
async def nfl_games(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    return await get_games_for_sport(date, "NFL", "americanfootball_nfl")

@app.get("/nhl/games", response_model=GamesResponse)
async def nhl_games(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    return await get_games_for_sport(date, "NHL", "icehockey_nhl")
    
def main():
    configure(app)
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()