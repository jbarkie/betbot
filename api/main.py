from fastapi import FastAPI
import uvicorn

def main():
    app = FastAPI()

    @app.get("/status")
    async def status():
        return {"status": "ok"}
    
    @app.get("/")

    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()