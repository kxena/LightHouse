"""
FastAPI Backend for LightHouse
================================
REST API to serve disaster incidents from MongoDB Atlas.

Endpoints:
- GET  /api/incidents              - Get all active incidents
- GET  /api/incidents/{id}         - Get specific incident
- GET  /api/incidents/type/{type}  - Get incidents by disaster type
- GET  /api/incidents/nearby       - Get incidents near a location
- GET  /api/stats                  - Get database statistics
- POST /api/incidents/update       - Trigger pipeline update (admin)

Usage:
    uvicorn api_server:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from mongodb_handler import MongoDBHandler
import subprocess
from datetime import datetime

app = FastAPI(
    title="LightHouse Disaster API",
    description="Real-time disaster incident tracking from social media",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongo_handler = None

# Pydantic Models
class SourceTweet(BaseModel):
    text: str
    author: str
    timestamp: str
    tweet_id: str
    engagement: dict

class Incident(BaseModel):
    id: str
    title: str
    description: str
    location: str
    lat: float
    lng: float
    severity: str
    incident_type: str
    status: str
    created_at: str
    tags: List[str]
    confidence: float
    casualties_mentioned: bool
    damage_mentioned: bool
    needs_help: bool
    source_tweets: List[SourceTweet]

class Statistics(BaseModel):
    total_incidents: int
    active_incidents: int
    by_type: dict
    by_severity: dict


@app.on_event("startup")
async def startup_event():
    global mongo_handler
    mongo_handler = MongoDBHandler()
    if not mongo_handler.connect():
        print("⚠️  Warning: Failed to connect to MongoDB. API may not work.")
    else:
        print("✓ API server ready and connected to MongoDB")


@app.on_event("shutdown")
async def shutdown_event():
    global mongo_handler
    if mongo_handler:
        mongo_handler.close()


@app.get("/")
async def root():
    return {
        "message": "LightHouse Disaster Tracking API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "incidents": "/api/incidents",
            "statistics": "/api/stats",
            "health": "/api/health"
        }
    }


@app.get("/api/health")
async def health_check():
    if mongo_handler is None:
        raise HTTPException(status_code=503, detail="MongoDB not initialized")
    try:
        stats = mongo_handler.get_statistics()
        return {
            "status": "healthy",
            "mongodb": "connected",
            "timestamp": datetime.now().isoformat(),
            "incidents_count": stats["total_incidents"]
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")


@app.get("/api/incidents", response_model=List[Incident])
async def get_incidents(
    active_only: bool = Query(True, description="Only return active incidents"),
    limit: Optional[int] = Query(None, description="Maximum number of incidents to return")
):
    if mongo_handler is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    try:
        incidents = mongo_handler.get_all_incidents(active_only=active_only)
        if limit:
            incidents = incidents[:limit]
        return incidents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching incidents: {str(e)}")


@app.get("/api/incidents/{incident_id}", response_model=Incident)
async def get_incident(incident_id: str):
    if mongo_handler is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    try:
        result = mongo_handler.get_incident_by_id(incident_id)
        if not result:
            raise HTTPException(status_code=404, detail="Incident not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching incident: {str(e)}")


@app.get("/api/incidents/type/{incident_type}", response_model=List[Incident])
async def get_incidents_by_type(incident_type: str):
    if mongo_handler is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    try:
        return mongo_handler.get_incidents_by_type(incident_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching incidents by type: {str(e)}")


@app.get("/api/incidents/nearby", response_model=List[Incident])
async def get_nearby_incidents(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius_km: float = Query(100, description="Search radius in kilometers", ge=1, le=5000)
):
    if mongo_handler is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    try:
        return mongo_handler.get_incidents_in_radius(lat, lng, radius_km)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching nearby incidents: {str(e)}")


@app.get("/api/stats", response_model=Statistics)
async def get_statistics():
    if mongo_handler is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    try:
        return mongo_handler.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")


@app.get("/api/incident-types")
async def get_incident_types():
    if mongo_handler is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    try:
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$incident_type"}},
            {"$sort": {"_id": 1}}
        ]
        results = list(mongo_handler.collection.aggregate(pipeline))
        incident_types = [r["_id"] for r in results if r.get("_id")]
        return {"incident_types": incident_types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching types: {str(e)}")


@app.get("/api/severity-levels")
async def get_severity_levels():
    if mongo_handler is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    try:
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        results = list(mongo_handler.collection.aggregate(pipeline))
        severity_levels = {r["_id"]: r["count"] for r in results if r.get("_id")}
        return {"severity_levels": severity_levels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching severity: {str(e)}")
    
@app.get("/api/history/dates")
async def get_history_dates():
    """Get list of available historical incident dates"""
    if mongo_handler is None or not mongo_handler.connected:
        return {"dates": []}
    
    try:
        # Get distinct dates from MongoDB using aggregation
        pipeline = [
            {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": {"$toDate": "$created_at"}}}}},
            {"$sort": {"_id": -1}}
        ]
        results = list(mongo_handler.collection.aggregate(pipeline))
        dates = [r["_id"] for r in results if r.get("_id")]
        return {"dates": dates}
    except Exception as e:
        # Return empty list on error instead of failing
        print(f"Error fetching history dates: {e}")
        return {"dates": []}


@app.get("/api/history/incidents/{date}")
async def get_history_incidents(date: str):
    """Get incidents for a specific historical date (format: YYYY-MM-DD)"""
    if mongo_handler is None or not mongo_handler.connected:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    try:
        # Validate date format
        from datetime import datetime as dt
        try:
            dt.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        # Query MongoDB for incidents created on that date
        date_start = f"{date}T00:00:00"
        date_end = f"{date}T23:59:59"
        
        incidents = list(mongo_handler.collection.find({
            "created_at": {
                "$gte": date_start,
                "$lte": date_end
            }
        }, {"_id": 0}))
        
        return {
            "metadata": {
                "date": date,
                "count": len(incidents)
            },
            "incidents": incidents
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching historical incidents: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
