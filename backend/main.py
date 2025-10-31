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

# /results: send results from LLM analysis to front end for respective UI components

# /retrieve_tweets: collect tweets from database for frontend "Live tweets" component

# /search_same: search database and return tweets talking about same disaster