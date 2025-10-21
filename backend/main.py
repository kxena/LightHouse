# cd backend, fastapi dev main.py

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
from pathlib import Path

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
    key_entities: List[str] = []  # extracted entities from LLM
    confidence_score: Optional[float] = None

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


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/test")
async def test(input: Tweet):
    return {"message": input}

# In-memory storage for demonstration purposes
incident_reports_db = {}
incident_counter = 1

def load_manual_labeled_data():
    """Load incidents from manual_labeled_mc.jsonl on startup"""
    global incident_counter, incident_reports_db
    
    jsonl_path = Path(__file__).parent.parent / "manual_labeled_mc.jsonl"
    
    if not jsonl_path.exists():
        print(f"Warning: {jsonl_path} not found")
        return
    
    # Map labels to incident types
    incident_types = {
        0: None,  # No useful info
        1: "Earthquake",
        2: "Tornado", 
        3: "Flood",
        4: "Hurricane",
        5: "Wildfire"
    }
    
    incidents_loaded = 0
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    
                    # Get label (prefer manual_label, fallback to initial_label)
                    label = data.get('manual_label', data.get('initial_label', 0))
                    incident_type = incident_types.get(label)
                    
                    # Only process disaster-related posts (label != 0)
                    if incident_type and label != 0:
                        # Create Tweet object
                        tweet = Tweet(
                            text=data['text'],
                            author=data['author']['handle'],
                            timestamp=data['createdAt'],
                            tweet_id=data.get('uri', f"tweet_{incident_counter}"),
                            engagement=None
                        )
                        
                        # Extract location from text
                        location = "Location TBD"
                        text_lower = data['text'].lower()
                        
                        locations_to_check = [
                            'Alaska', 'Indonesia', 'New Zealand', 'Japan', 'Afghanistan', 
                            'Oklahoma', 'Chile', 'Austin', 'Texas', 'California', 'Florida',
                            'Louisiana', 'North Carolina', 'Philippines', 'Italy', 'Namibia',
                            'Spain', 'Bolivia', 'Colombia', 'Nova Scotia', 'Fiji Islands'
                        ]
                        
                        for place in locations_to_check:
                            if place.lower() in text_lower:
                                location = place
                                break
                        
                        # Determine severity
                        severity = "medium"
                        if any(word in text_lower for word in ['major', 'severe', 'critical', 'devastating', 'massive']):
                            severity = "high"
                        elif any(word in text_lower for word in ['minor', 'small']):
                            severity = "low"
                        
                        # Create incident
                        incident_id = f"INC-{incident_counter:06d}"
                        incident_counter += 1
                        
                        description = data['text'][:300] + "..." if len(data['text']) > 300 else data['text']
                        
                        incident_response = IncidentResponse(
                            id=incident_id,
                            title=f"{incident_type} - {location}",
                            description=description,
                            location=location,
                            severity=severity,
                            incident_type=incident_type,
                            tags=[incident_type.lower(), location.lower().replace(' ', '_')],
                            estimated_restoration=None,
                            affected_area=location,
                            created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')),
                            status="active",
                            source_tweets=[tweet]
                        )
                        
                        incident_reports_db[incident_id] = incident_response
                        incidents_loaded += 1
                        
                except Exception as e:
                    print(f"Error processing line: {e}")
                    continue
    
    print(f"✅ Loaded {incidents_loaded} incidents from manual_labeled_mc.jsonl")

@app.on_event("startup")
async def startup_event():
    """Load data when the server starts"""
    print("🚀 Starting FastAPI server...")
    load_manual_labeled_data()
    print("✅ Server ready!")

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
        source_tweets=[tweet_analysis.tweet]
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
        source_tweets=incident_data.source_tweets
    )
    
    incident_reports_db[incident_id] = incident_response
    return incident_response

@app.get("/incidents")
async def get_all_incidents():
    """Get all incident reports"""
    return list(incident_reports_db.values())

@app.get("/api/dashboard")
async def get_dashboard_stats():
    """Get dashboard statistics for the frontend"""
    incidents = list(incident_reports_db.values())
    
    # Count active incidents
    active_incidents = len([i for i in incidents if i.status == "active"])
    
    # Calculate total tweets from all incidents
    total_tweets = sum(len(inc.source_tweets) for inc in incidents)
    posts_per_min = total_tweets * 100  # Mock calculation for demo
    
    # Calculate unique locations/states
    locations = [inc.location for inc in incidents if inc.location and inc.location != "Location being determined"]
    active_states = len(set(locations))
    
    # Format incidents for map display
    formatted_incidents = [
        {
            "id": inc.id,
            "title": inc.title,
            "description": inc.description,
            "location": inc.location,
            "severity": inc.severity,
            "incident_type": inc.incident_type,
            "status": inc.status,
            "tags": inc.tags,
            "created_at": inc.created_at.isoformat(),
            "latitude": 0,  # TODO: Add geocoding to get actual coordinates
            "longitude": 0,
            "tweet_count": len(inc.source_tweets)
        }
        for inc in incidents
    ]
    
    return {
        "incidents": formatted_incidents,
        "activeIncidents": active_incidents,
        "postsPerMin": posts_per_min,
        "activeStates": active_states
    }

@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Get a specific incident report"""
    if incident_id not in incident_reports_db:
        return {"error": "Incident not found"}, 404
    return incident_reports_db[incident_id]

@app.put("/incidents/{incident_id}/status")
async def update_incident_status(incident_id: str, status: str):
    """Update incident status"""
    if incident_id not in incident_reports_db:
        return {"error": "Incident not found"}, 404
    
    incident_reports_db[incident_id].status = status
    return incident_reports_db[incident_id]

@app.post("/incidents/{incident_id}/add-tweet")
async def add_tweet_to_incident(incident_id: str, tweet: Tweet):
    """Add a tweet to an existing incident (when model identifies related tweets)"""
    if incident_id not in incident_reports_db:
        return {"error": "Incident not found"}, 404
    
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