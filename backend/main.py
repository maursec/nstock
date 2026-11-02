
from fastapi import FastAPI

app = FastAPI(title="NStock API")

@app.get("/")
def home():
    return {"message": "Welcome to NStock API"}

@app.get("/health")
def health():
    return {"status": "ok"}
