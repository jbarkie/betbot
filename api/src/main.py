from fastapi import FastAPI
from api.src.nba import get_todays_games
from api.src.models.nba import GamesResponse
import uvicorn
from typing import Any
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/status")
async def status():
    return {"status": "ok"}

@app.get("/nba/games", response_model=GamesResponse)
async def games() -> Any :
    return get_todays_games()

def main():
    configure(app)
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()