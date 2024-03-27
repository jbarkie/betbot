from fastapi import FastAPI
from nba import get_todays_games
from models.game import Game
import uvicorn
from typing import Any
from fastapi.middleware.cors import CORSMiddleware

def main():
    app = FastAPI()
    configure(app)

    @app.get("/status")
    async def status():
        return {"status": "ok"}
    
    @app.get("/nba/games", response_model=list[Game])
    async def games() -> Any :
        return get_todays_games()

    uvicorn.run(app, host="0.0.0.0", port=8000)

def configure(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://localhost:4200"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if __name__ == "__main__":
    main()