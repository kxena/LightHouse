# cd backend, fastapi dev main.py

from fastapi import FastAPI
from pydantic import BaseModel

class Input(BaseModel):
    text: str

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/test")
async def test(input: Input):
    return {"message": input}