# cd backend, fastapi dev main.py

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


origins = [
    "http://localhost",
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Tweet(BaseModel):
    text: str


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/test")
async def test(input: Tweet):
    return {"message": input}

# /tweet: collect tweets through bluesky api for real time input AND add cleaning function here

# /classify: feed cleaned tweet to classifer, return result, feed tweet to /llm-analysis if natural disaster

# /llm-analysis: feed tweet to llm for key extractions, feed results to /alerts

# /alerts: send results to front end for respective UI components