from fastapi import FastAPI, HTTPException, Query, Depends
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from api.src.login import get_user_by_username
from api.src.models.auth import LoginResponse
from api.src.nba import get_games_by_date
from api.src.models.nba import GamesResponse
import uvicorn
from typing import Any, Annotated
from fastapi.middleware.cors import CORSMiddleware
import traceback

app = FastAPI()
__all__ = ["app"]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def configure(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://localhost:4200"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/status")
async def status():
    return {"status": "ok"}

@app.post("/login", response_model=LoginResponse)
async def login(login_request: Annotated[OAuth2PasswordRequestForm, Depends()]):
    username = login_request.username
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    response = LoginResponse(access_token=user.username)
    return response

@app.get("/nba/games", response_model=GamesResponse)
async def games(date: str = Query(..., description="Date in YYYY-MM-DD format")) -> Any:
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
        return get_games_by_date(parsed_date)
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