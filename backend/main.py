# cd backend, fastapi dev main.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json

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

# /results: convert pipeline JSONL results file to JSON file for frontend to retrieve
@app.get("/results")
async def get_results():
    try:
        # Define input and output paths
        input_file = Path(__file__).parent / 'pipeline_output' / '04_final_results.jsonl'
        output_file = Path(__file__).parent / 'final_results.json'
        
        if not input_file.exists():
            raise HTTPException(
                status_code=404,
                detail="Results file not found. Please run the pipeline first."
            )
        
        # Convert JSONL to JSON array
        results = []
        with open(input_file, 'r') as f:
            for line in f:
                try:
                    tweet = json.loads(line)
                    results.append(tweet)
                except json.JSONDecodeError:
                    continue
        
        # Write to JSON file
        with open(output_file, 'w') as f:
            json.dump({"tweets": results}, f, indent=2)
        
        # Return the same data to the API caller
        return {"tweets": results}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing results: {str(e)}"
        )

# /results_jsonl: return the raw JSONL results file
@app.get("/results_jsonl")
async def get_results_jsonl():
    try:
        # Define file path
        file_path = Path(__file__).parent / 'pipeline_output' / '04_final_results.jsonl'
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Results file not found. Please run the pipeline first."
            )
        
        # Return the file directly
        return FileResponse(
            path=file_path,
            filename="04_final_results.jsonl",
            media_type="application/x-jsonlines"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error accessing file: {str(e)}"
        )

# /retrieve_tweets: collect tweets from database for frontend "Live tweets" component

# /search_same: search database and return tweets talking about same disaster