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

# Initialize FastAPI app
app = FastAPI(
    title="LightHouse Disaster API",
    description="Real-time disaster incident tracking from social media",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global MongoDB handler
mongo_handler = None


# Pydantic models for API responses
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
    casualties_mentioned: Optional[bool] = False
    damage_mentioned: Optional[bool] = False
    needs_help: Optional[bool] = False
    source_tweets: List[SourceTweet]


class Statistics(BaseModel):
    total_incidents: int
    active_incidents: int
    by_type: dict
    by_severity: dict


# Startup/shutdown events
@app.on_event("startup")
async def startup_event():
    """Connect to MongoDB on startup"""
    global mongo_handler
    mongo_handler = MongoDBHandler()
    
    if not mongo_handler.connect():
        print("⚠️  Warning: Failed to connect to MongoDB. API will not work.")
    else:
        print("✓ API server ready and connected to MongoDB")


@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on shutdown"""
    global mongo_handler
    if mongo_handler is not None:
        mongo_handler.close()


# API Endpoints
@app.get("/")
async def root():
    """API welcome message"""
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
    """Check API and database health"""
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
    """Get all incidents"""
    if mongo_handler is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    try:
        incidents = mongo_handler.get_all_incidents(limit=limit)
        
        # Filter for active only if requested
        if active_only:
            incidents = [inc for inc in incidents if inc.get('status') != 'resolved']
        
        return incidents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching incidents: {str(e)}")


@app.get("/api/incidents/{incident_id}", response_model=Incident)
async def get_incident(incident_id: str):
    """Get a specific incident by ID"""
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
    """Get incidents by disaster type (Earthquake, Flood, etc.)"""
    if mongo_handler is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    try:
        incidents = mongo_handler.get_incidents_by_type(incident_type)
        return incidents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching incidents: {str(e)}")


@app.get("/api/incidents/nearby", response_model=List[Incident])
async def get_nearby_incidents(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius_km: float = Query(100, description="Search radius in kilometers", ge=1, le=5000)
):
    """Get incidents within a radius of a location"""
    if mongo_handler is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    try:
        incidents = mongo_handler.get_incidents_in_radius(lat, lng, radius_km)
        return incidents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching nearby incidents: {str(e)}")


@app.get("/api/stats", response_model=Statistics)
async def get_statistics():
    """Get database statistics"""
    if mongo_handler is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    try:
        stats = mongo_handler.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")


@app.post("/api/admin/update")
async def trigger_update(api_key: str = Query(..., description="Admin API key")):
    """
    Trigger pipeline update (admin only).
    This will run the unified pipeline and regenerate incidents.
    
    In production, protect this endpoint with proper authentication!
    """
    # Simple API key check (in production, use proper auth)
    if api_key != "your_secret_key_here":  # Change this!
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    try:
        # Run the pipeline
        print("Starting pipeline update...")
        subprocess.run(["python", "unified_pipeline.py"], check=True)
        subprocess.run(["python", "regenerate_incidents_mongodb.py"], check=True)
        
        # Get updated stats
        stats = mongo_handler.get_statistics()
        
        return {
            "status": "success",
            "message": "Pipeline updated successfully",
            "timestamp": datetime.now().isoformat(),
            "incidents_count": stats["total_incidents"]
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


# Additional utility endpoints
@app.get("/api/incident-types")
async def get_incident_types():
    """Get list of all incident types in database"""
    if mongo_handler is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    try:
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$incident_type"}},
            {"$sort": {"_id": 1}}
        ]
        
        results = list(mongo_handler.incidents_collection.aggregate(pipeline))
        types = [r["_id"] for r in results]
        
        return {"incident_types": types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching types: {str(e)}")


@app.get("/api/severity-levels")
async def get_severity_levels():
    """Get list of all severity levels in database"""
    if mongo_handler is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    try:
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        
        results = list(mongo_handler.incidents_collection.aggregate(pipeline))
        levels = {r["_id"]: r["count"] for r in results}
        
        return {"severity_levels": levels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching severity: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("LightHouse API Server")
    print("=" * 70)
    print("\nStarting server on http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("=" * 70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")