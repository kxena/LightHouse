# cd backend, fastapi dev main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

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
    author: str
    timestamp: str
    tweet_id: str
    engagement: Optional[dict] = None  # likes, retweets, replies

class TweetAnalysisResult(BaseModel):
    """Result from model analysis of a tweet"""
    tweet: Tweet
    is_disaster_related: bool
    incident_type: Optional[str] = None  # e.g., "Power Outage", "Flood", "Fire", etc.
    severity: Optional[str] = None  # "low", "medium", "high", "critical"
    location: Optional[str] = None
    key_entities: List[str] = Field(default_factory=list)  # extracted entities from LLM
    confidence_score: Optional[float] = None
    # Optional geocoding
    lat: Optional[float] = None
    lng: Optional[float] = None

class IncidentFromTweets(BaseModel):
    """Incident automatically generated from tweet analysis"""
    title: str
    description: str
    location: str
    severity: str
    incident_type: str
    tags: List[str]
    estimated_restoration: Optional[str] = None
    affected_area: Optional[str] = None
    source_tweets: List[Tweet]  # All tweets that contributed to this incident
    # Optional geocoding
    lat: Optional[float] = None
    lng: Optional[float] = None
    
class IncidentResponse(BaseModel):
    id: str
    title: str
    description: str
    location: str
    severity: str
    incident_type: str
    tags: List[str]
    estimated_restoration: Optional[str]
    affected_area: Optional[str]
    created_at: datetime
    status: str
    source_tweets: List[Tweet]  # Associated tweets
    # Optional geocoding
    lat: Optional[float] = None
    lng: Optional[float] = None


class StatusUpdate(BaseModel):
    status: str


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/test")
async def test(input: Tweet):
    return {"message": input}

# In-memory storage for demonstration purposes
incident_reports_db = {}
incident_counter = 1

@app.post("/analyze-tweet")
async def analyze_tweet(tweet_analysis: TweetAnalysisResult):
    """Process analyzed tweet data and potentially create/update incidents"""
    global incident_counter
    
    if not tweet_analysis.is_disaster_related:
        return {"message": "Tweet not disaster-related", "incident_created": False}
    
    # For now, create a new incident for each disaster-related tweet
    # In production, you might want to group similar tweets into existing incidents
    incident_id = f"INC-{incident_counter:06d}"
    incident_counter += 1
    
    # Generate incident from tweet analysis
    incident_response = IncidentResponse(
        id=incident_id,
        title=f"{tweet_analysis.incident_type} - {tweet_analysis.location or 'Location TBD'}",
        description=f"Incident detected from social media analysis: {tweet_analysis.tweet.text[:100]}...",
        location=tweet_analysis.location or "Location being determined",
        severity=tweet_analysis.severity or "medium",
        incident_type=tweet_analysis.incident_type or "General Emergency",
        tags=tweet_analysis.key_entities,
        estimated_restoration=None,
        affected_area=None,
        created_at=datetime.now(),
        status="active",
        source_tweets=[tweet_analysis.tweet],
        lat=tweet_analysis.lat,
        lng=tweet_analysis.lng,
    )
    
    incident_reports_db[incident_id] = incident_response
    return {
        "message": "Incident created from tweet analysis", 
        "incident_created": True,
        "incident_id": incident_id,
        "confidence_score": tweet_analysis.confidence_score
    }

@app.post("/create-incident-from-tweets", response_model=IncidentResponse)
async def create_incident_from_tweets(incident_data: IncidentFromTweets):
    """Create incident from multiple analyzed tweets (for when model groups related tweets)"""
    global incident_counter
    
    incident_id = f"INC-{incident_counter:06d}"
    incident_counter += 1
    
    incident_response = IncidentResponse(
        id=incident_id,
        title=incident_data.title,
        description=incident_data.description,
        location=incident_data.location,
        severity=incident_data.severity,
        incident_type=incident_data.incident_type,
        tags=incident_data.tags,
        estimated_restoration=incident_data.estimated_restoration,
        affected_area=incident_data.affected_area,
        created_at=datetime.now(),
        status="active",
        source_tweets=incident_data.source_tweets,
        lat=incident_data.lat,
        lng=incident_data.lng,
    )
    
    incident_reports_db[incident_id] = incident_response
    return incident_response

@app.get("/incidents")
async def get_all_incidents():
    """Get all incident reports"""
    return list(incident_reports_db.values())

@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Get a specific incident report"""
    if incident_id not in incident_reports_db:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident_reports_db[incident_id]

@app.put("/incidents/{incident_id}/status")
async def update_incident_status(incident_id: str, update: StatusUpdate):
    """Update incident status"""
    if incident_id not in incident_reports_db:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident_reports_db[incident_id].status = update.status
    return incident_reports_db[incident_id]

@app.post("/incidents/{incident_id}/add-tweet")
async def add_tweet_to_incident(incident_id: str, tweet: Tweet):
    """Add a tweet to an existing incident (when model identifies related tweets)"""
    if incident_id not in incident_reports_db:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident = incident_reports_db[incident_id]
    
    # Check if tweet already exists to avoid duplicates
    existing_tweet_ids = [t.tweet_id for t in incident.source_tweets]
    if tweet.tweet_id not in existing_tweet_ids:
        incident.source_tweets.append(tweet)
        return {"message": "Tweet added to incident", "total_tweets": len(incident.source_tweets)}
    
    return {"message": "Tweet already associated with incident", "total_tweets": len(incident.source_tweets)}

# /tweet: collect tweets through bluesky api for real time input AND add cleaning function here

# /classify: feed cleaned tweet to classifer, return result, feed tweet to /llm-analysis if natural disaster

# /llm-analysis: feed tweet to llm for key extractions, feed results to /alerts

# /alerts: send results to front end for respective UI components