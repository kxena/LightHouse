# cd backend, fastapi dev main.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys
import json
import os
import glob
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

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
    return {"message": "LightHouse API - Disaster Incident Tracking"}

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
        
        file_modified_time = datetime.fromtimestamp(os.path.getmtime(input_file))
        
        # Convert JSONL to JSON array
        results = []
        with open(input_file, 'r') as f:
            for line in f:
                try:
                    tweet = json.loads(line)
                    results.append(tweet)
                except json.JSONDecodeError:
                    continue

        response_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),  # When this API call was made
                "pipeline_last_run": file_modified_time.isoformat(),  # When pipeline last generated results
                "total_tweets": len(results)
            },
            "tweets": results
        }
        
        # Write to JSON file
        with open(output_file, 'w') as f:
            json.dump(response_data, f, indent=2)
        
        # Return the same data to the API caller
        return response_data
    
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

# INCIDENT ENDPOINTS

def load_incidents() -> Dict[str, Any]:
    """Load incidents from incidents_validation.json file"""
    incidents_file = Path(__file__).parent / 'incidents_validation.json'
    
    if not incidents_file.exists():
        # Try to generate incidents if they don't exist
        try:
            # Prefer processing code from the `processing_bundle` folder if present
            bundle = Path(__file__).parent / 'processing_bundle'
            if bundle.exists():
                sys.path.insert(0, str(bundle))
            from process_incidents import process_final_results
            process_final_results()
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Incidents file not found and could not be generated: {str(e)}"
            )
    
    with open(incidents_file, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.get("/incidents")
async def get_all_incidents() -> List[Dict[str, Any]]:
    """
    Get all incidents created from tweets where both ML and LLM classifications are true.
    Returns incidents in format compatible with frontend IncidentResponse interface.
    """
    try:
        data = load_incidents()
        return data.get('incidents', [])
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading incidents: {str(e)}"
        )

@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str) -> Dict[str, Any]:
    """Get a specific incident by ID"""
    try:
        data = load_incidents()
        incidents = data.get('incidents', [])
        
        # Find incident by ID
        for incident in incidents:
            if incident['id'] == incident_id:
                return incident
        
        raise HTTPException(
            status_code=404,
            detail=f"Incident with ID '{incident_id}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading incident: {str(e)}"
        )

@app.get("/incidents/stats/summary")
async def get_incidents_summary() -> Dict[str, Any]:
    """Get summary statistics about incidents"""
    try:
        data = load_incidents()
        incidents = data.get('incidents', [])
        metadata = data.get('metadata', {})
        
        # Calculate statistics
        by_type = {}
        by_severity = {}
        by_location = {}
        
        for incident in incidents:
            # Count by type
            inc_type = incident.get('incident_type', 'Unknown')
            by_type[inc_type] = by_type.get(inc_type, 0) + 1
            
            # Count by severity
            severity = incident.get('severity', 'unknown')
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # Count by location
            location = incident.get('location', 'Unknown')
            by_location[location] = by_location.get(location, 0) + 1
        
        return {
            "total_incidents": len(incidents),
            "by_type": by_type,
            "by_severity": by_severity,
            "top_locations": dict(sorted(by_location.items(), key=lambda x: x[1], reverse=True)[:10]),
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating summary: {str(e)}"
        )

@app.post("/incidents/regenerate")
async def regenerate_incidents() -> Dict[str, Any]:
    """
    Regenerate incidents from final_results.json.
    Useful after running the pipeline with new tweet data.
    """
    try:
        # Ensure processing_bundle is on path when regenerating from the API
        bundle = Path(__file__).parent / 'processing_bundle'
        if bundle.exists():
            sys.path.insert(0, str(bundle))
        from process_incidents import process_final_results
        result = process_final_results()
        return {
            "message": "Incidents regenerated successfully",
            "metadata": result.get('metadata', {})
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error regenerating incidents: {str(e)}"
        )


# Historical data endpoints
def history_dir() -> Path:
    """Return path to historical data folder."""
    return Path(__file__).parent / 'historical'


@app.get("/history/dates")
async def list_history_dates() -> Dict[str, Any]:
    """List available dates for historical data (based on files in `backend/historical`)."""
    hd = history_dir()
    if not hd.exists():
        return {"dates": []}

    # Only consider precomputed incidents files as the source of truth for history
    pattern = str(hd / '*_incidents.json')
    files = glob.glob(pattern)
    dates = []
    for fp in files:
        name = os.path.basename(fp)
        if name.endswith('_incidents.json'):
            date_part = name.replace('_incidents.json', '')
            dates.append(date_part)

    dates.sort()
    return {"dates": dates}


@app.get("/history/results/{date}")
async def get_history_results(date: str) -> Dict[str, Any]:
    """Return the `final_results` JSON for a given date (format YYYY-MM-DD)."""
    # For this deployment we only store precomputed incidents. Raw final_results
    # are not kept in the historical folder. Requesting raw results will return
    # a helpful 404 directing clients to use the incidents endpoint.
    raise HTTPException(
        status_code=404,
        detail=(
            "Historical raw results are not stored. "
            "Please request precomputed incidents with /history/incidents/{date}."
        ),
    )


@app.get("/history/incidents/{date}")
async def get_history_incidents(date: str) -> Dict[str, Any]:
    """Return incidents for a given date if precomputed and stored under `backend/historical`."""
    file_path = history_dir() / f"{date}_incidents.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Historical incidents not found")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading historical incidents: {str(e)}")