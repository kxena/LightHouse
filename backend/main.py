# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime, timedelta
import os
import json

# Import MongoDB functions
from database import get_collection, init_db, close_db

app = FastAPI()

# CORS Configuration
origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Run when server starts"""
    print("\n" + "="*70)
    print("FastAPI Server Starting")
    print("="*70 + "\n")
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Run when server stops"""
    await close_db()

# Timestamp management
TIMESTAMP_FILE = Path(__file__).parent / 'pipeline_output' / 'last_update.json'

def save_timestamp():
    """Save the current timestamp after pipeline runs"""
    TIMESTAMP_FILE.parent.mkdir(exist_ok=True)
    timestamp_data = {
        "last_update": datetime.now().isoformat(),
        "next_update": (datetime.now() + timedelta(hours=6)).isoformat()
    }
    with open(TIMESTAMP_FILE, 'w') as f:
        json.dump(timestamp_data, f, indent=2)
    return timestamp_data

def load_timestamp():
    """Load the last update timestamp"""
    if not TIMESTAMP_FILE.exists():
        return None
    try:
        with open(TIMESTAMP_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

# Models
class Tweet(BaseModel):
    text: str

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LightHouse API",
        "version": "1.0",
        "status": "active"
    }

@app.post("/test")
async def test(input: Tweet):
    """Test endpoint"""
    return {"message": input}

@app.get("/timestamp")
async def get_timestamp():
    """
    Get timestamp of last data update.
    Frontend polls this to check for new data.
    """
    timestamp_data = load_timestamp()
    
    if not timestamp_data:
        # Fallback: check MongoDB for latest entry
        try:
            collection = await get_collection()
            latest = await collection.find_one(
                sort=[("created_at", -1)]
            )
            
            if latest and 'created_at' in latest:
                return {
                    "last_update": latest['created_at'],
                    "next_update": None,
                    "has_data": True
                }
        except:
            pass
        
        return {
            "last_update": None,
            "next_update": None,
            "has_data": False
        }
    
    return {
        "last_update": timestamp_data.get("last_update"),
        "next_update": timestamp_data.get("next_update"),
        "has_data": True
    }

@app.get("/results")
async def get_results():
    """
    Get all incidents from MongoDB.
    This is what your dashboard calls to load data.
    """
    try:
        collection = await get_collection()
        
        # Get all incidents, sorted by most recent
        cursor = collection.find({}).sort("created_at", -1)
        incidents = await cursor.to_list(length=None)
        
        # Convert MongoDB ObjectId to string for JSON
        for incident in incidents:
            if '_id' in incident:
                incident['_id'] = str(incident['_id'])
        
        # Calculate statistics
        total_count = len(incidents)
        
        # Count by incident type
        incident_types = {}
        for incident in incidents:
            itype = incident.get('incident_type', 'unknown')
            incident_types[itype] = incident_types.get(itype, 0) + 1
        
        # Count by status
        active_count = sum(1 for i in incidents if i.get('status') == 'active')
        
        # Load timestamp
        timestamp_data = load_timestamp()
        
        # Build response
        response_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "last_update": timestamp_data.get("last_update") if timestamp_data else None,
                "next_update": timestamp_data.get("next_update") if timestamp_data else None,
                "total_incidents": total_count,
                "active_incidents": active_count,
                "incident_types": incident_types
            },
            "incidents": incidents
        }
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching from MongoDB: {str(e)}"
        )

@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Get a specific incident by ID"""
    try:
        collection = await get_collection()
        
        # Try to find by custom id field first, then by _id
        incident = await collection.find_one({"id": incident_id})
        
        if not incident:
            from bson import ObjectId
            try:
                incident = await collection.find_one({"_id": ObjectId(incident_id)})
            except:
                pass
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Convert ObjectId to string
        if '_id' in incident:
            incident['_id'] = str(incident['_id'])
        
        return incident
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching incident: {str(e)}"
        )

@app.get("/incidents/type/{incident_type}")
async def get_incidents_by_type(incident_type: str):
    """Get all incidents of a specific type"""
    try:
        collection = await get_collection()
        
        cursor = collection.find({
            "incident_type": incident_type
        }).sort("created_at", -1)
        
        incidents = await cursor.to_list(length=None)
        
        # Convert ObjectId to string
        for incident in incidents:
            if '_id' in incident:
                incident['_id'] = str(incident['_id'])
        
        return {
            "incident_type": incident_type,
            "count": len(incidents),
            "incidents": incidents
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching incidents: {str(e)}"
        )

@app.get("/stats")
async def get_stats():
    """Get database statistics"""
    try:
        collection = await get_collection()
        
        total = await collection.count_documents({})
        
        # Aggregate by type
        pipeline = [
            {"$group": {
                "_id": "$incident_type",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        type_stats = []
        async for doc in collection.aggregate(pipeline):
            type_stats.append({
                "type": doc["_id"],
                "count": doc["count"]
            })
        
        return {
            "total_incidents": total,
            "by_type": type_stats,
            "last_checked": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats: {str(e)}"
        )

# Keep your existing /results_jsonl endpoint if needed for backwards compatibility
@app.get("/results_jsonl")
async def get_results_jsonl():
    """Legacy endpoint - returns JSONL file if it exists"""
    try:
        file_path = Path(__file__).parent / 'pipeline_output' / '04_final_results.jsonl'
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="JSONL file not found"
            )
        
        return FileResponse(
            path=file_path,
            filename="04_final_results.jsonl",
            media_type="application/x-jsonlines"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error accessing file: {str(e)}"
        )