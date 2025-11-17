# cd backend, fastapi dev main.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys
import json
from typing import List, Dict, Any, Optional

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

# Incident Management Endpoints

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