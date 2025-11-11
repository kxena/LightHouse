"""
Process tweets from final_results.json and convert them to incidents.
Only includes tweets where both ML and LLM classifications are true.

WORKFLOW OVERVIEW
=================

This script transforms classified tweets into map-displayable incidents:

1. LOAD & FILTER
- Reads final_results.json (contains 200+ classified tweets)
- Filters to only tweets where BOTH conditions are true:
    -- ML model classified it as a disaster (is_disaster: true)
    -- LLM confirmed it's a real, current/recent disaster (llm_classification: true)

2. EXTRACT COORDINATES
- Each tweet has a location (e.g., "Tokyo, Japan")
- extract_coordinates_from_location() converts to (lat, lng) for the map
- Tries two methods:
    -- Parse coordinates if embedded in location string: "Tokyo (35.67, 139.65)"
    -- Look up location in hardcoded database of known places
- Tweets without valid coordinates are skipped (can't display on map)

3. NORMALIZE DATA
- disaster_type_normalize(): Convert "hurricane" → "Hurricane" for consistency
- severity_map(): Convert "high" → 3 for standardized severity scale
- Both ensure frontend receives predictable data formats

4. CREATE INCIDENTS
- tweet_to_incident() converts each tweet to an incident object
- Includes: title, description, location, coordinates, severity, disaster type
- Preserves original tweet as "source_tweet" for reference
- Each incident gets a unique ID based on location + tweet ID

5. MERGE SIMILAR INCIDENTS
- merge_similar_incidents() groups incidents by (location, disaster_type)
- Multiple tweets about same disaster type in same location → 1 merged incident
- Example: 5 earthquake reports in California → 1 incident with 5 source tweets
- Takes highest severity level when merging

6. OUTPUT
- Saves incidents.json with:
    -- incidents: Array of 12 merged incidents ready for frontend map display
    -- metadata: Stats about processing (total tweets, filtered, created, skipped)
- Frontend loads this file and displays incidents on interactive map

KEY CONCEPT: DOUBLE VALIDATION
==============================
This script ONLY includes tweets that pass BOTH classifiers:
- ML model: Fast, pattern-based classification
- LLM: Slower but more intelligent validation

This two-step process reduces false positives and ensures only high-confidence
disaster reports make it to the frontend map.
"""

import json
import hashlib
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

# extract coordinates from location strings
def extract_coordinates_from_location(location: str) -> Optional[tuple[float, float]]:
    """
    Examples:
        "Tokyo, Japan (35.6762, 139.6503)"
        "DODECANESE ISLANDS, GREECE"
    """
    import re
    # Try to find coordinates in parentheses
    pattern = r'\((-?\d+\.?\d*),\s*(-?\d+\.?\d*)\)'
    match = re.search(pattern, location)
    if match:
        lat, lng = float(match.group(1)), float(match.group(2))
        return (lat, lng)
    
    # Fallback: use known location database
    location_db = {
        # US States
        "NEVADA": (39.8, -117.0),
        "CALIFORNIA": (36.7783, -119.4179),
        "ALASKA": (64.2008, -149.4937),
        "OKLAHOMA": (35.4676, -97.5164),
        "TEXAS": (31.9686, -99.9018),
        
        # Countries
        "GREECE": (39.0742, 21.8243),
        "DODECANESE ISLANDS, GREECE": (36.4341, 27.2005),
        "INDONESIA": (-0.7893, 113.9213),
        "West Papua, Indonesia": (-1.3361, 133.1747),
        "JAPAN": (36.2048, 138.2529),
        "AFGHANISTAN": (33.9391, 67.7100),
        "TURKEY": (38.9637, 35.2433),
        "CHILE": (-35.6751, -71.5430),
        "NEW ZEALAND": (-40.9006, 174.8860),
        "PERU": (-9.1900, -75.0152),
        "MEXICO": (23.6345, -102.5528),
        "INDIA": (20.5937, 78.9629),
        "CHINA": (35.8617, 104.1954),
        "IRAN": (32.4279, 53.6880),
        "ITALY": (41.8719, 12.5674),
        "PAKISTAN": (30.3753, 69.3451),
        "PHILIPPINES": (12.8797, 121.7740),
        "VANUATU": (-15.3767, 166.9592),
        "FIJI": (-17.7134, 178.0650),
        "TAIWAN": (23.6978, 120.9605),
        "SOLOMON ISLANDS": (-9.6457, 160.1562),
    }
    
    # Try to match location
    location_upper = location.upper()
    for key, coords in location_db.items():
        if key.upper() in location_upper:
            return coords
    
    return None


# Map LLM severity to 1-3 scale for frontend
def severity_map(llm_severity: str) -> int:
    mapping = {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 3
    }
    return mapping.get(llm_severity.lower(), 2)


# Normalize disaster type to match frontend expectations
def disaster_type_normalize(disaster_type: str) -> str:
    type_mapping = {
        "earthquake": "Earthquake",
        "flood": "Flood",
        "hurricane": "Hurricane",
        "wildfire": "Wildfire",
        # "tornado": "Tornado",
        # "storm": "Storm",
        # "tsunami": "Flood",
        # "typhoon": "Storm",
        # "cyclone": "Storm",
        # "avalanche": "Avalanche",
        # "landslide": "Landslide",
        # "volcano": "Volcano",
        # "volcanic": "Volcano",
        # "drought": "Drought",
        # "heatwave": "Heatwave",
        # "coldwave": "Coldwave",
    }
    return type_mapping.get(disaster_type.lower(), "Storm")


# Generate a unique incident ID
def generate_incident_id(tweet_id: str, location: str) -> str:
    # Use a combination of location and tweet id
    content = f"{location}-{tweet_id}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


# Convert a filtered tweet to an incident format matching the frontend expectations.
# Returns None if critical data is missing.
def tweet_to_incident(tweet: Dict) -> Optional[Dict]:
    llm = tweet.get('llm_extraction', {})
    ml = tweet.get('ml_classification', {})
    
    location = llm.get('location', 'Location TBD')
    if not location or location.strip() == '':
        location = 'Location TBD'
    
    # Try to extract coordinates
    coords = extract_coordinates_from_location(location)
    lat, lng = coords if coords else (None, None)
    
    # Skip if no valid coordinates (can't show on map)
    if lat is None or lng is None:
        return None
    
    disaster_type = disaster_type_normalize(llm.get('disaster_type', ml.get('disaster_type', 'unknown')))
    severity = severity_map(llm.get('severity', 'medium'))
    
    # Generate incident ID
    incident_id = generate_incident_id(tweet['id'], location)
    
    # Create title from key details or text
    key_details = llm.get('key_details', '')
    text_snippet = tweet['text'][:100] + ('...' if len(tweet['text']) > 100 else '')
    title = key_details[:80] if key_details else text_snippet
    
    # Extract location name (remove coordinates)
    location_display = location.split('(')[0].strip() if '(' in location else location
    
    # Create source tweet
    source_tweet = {
        "text": tweet['text'],
        "author": tweet['author']['handle'],
        "timestamp": tweet['createdAt'],
        "tweet_id": tweet['id'],
        "engagement": {
            "likes": tweet.get('like_count', 0),
            "retweets": tweet.get('repost_count', 0),
            "replies": tweet.get('reply_count', 0)
        }
    }
    
    incident = {
        "id": incident_id,
        "title": title,
        "description": llm.get('key_details', tweet['text']),
        "location": location_display,
        "lat": lat,
        "lng": lng,
        "severity": llm.get('severity', 'medium'),
        "incident_type": disaster_type,
        "tags": [
            disaster_type,
            llm.get('severity', 'medium'),
            tweet.get('keyword', ''),
        ],
        "status": "active",
        "created_at": tweet['createdAt'],
        "source_tweets": [source_tweet],
        # Additional metadata
        "confidence": ml.get('confidence', 0),
        "casualties_mentioned": llm.get('casualties_mentioned', False),
        "damage_mentioned": llm.get('damage_mentioned', False),
        "needs_help": llm.get('needs_help', False),
    }
    
    return incident


# Merge incidents that are in the same location and of the same type.
# Combines their source tweets.
def merge_similar_incidents(incidents: List[Dict]) -> List[Dict]:
    from collections import defaultdict
    
    # Group by location and incident type
    groups = defaultdict(list)
    for incident in incidents:
        key = (incident['location'], incident['incident_type'])
        groups[key].append(incident)
    
    merged = []
    for (location, incident_type), group in groups.items():
        if len(group) == 1:
            merged.append(group[0])
        else:
            # Merge multiple incidents
            base = group[0].copy()
            all_tweets = []
            for inc in group:
                all_tweets.extend(inc['source_tweets'])
            
            # Update with combined data
            base['source_tweets'] = all_tweets
            base['title'] = f"Multiple {incident_type} reports in {location}"
            base['description'] = f"{len(all_tweets)} reports of {incident_type.lower()} activity in {location}"
            
            # Take highest severity
            severities = [inc['severity'] for inc in group]
            if 'critical' in severities or 'high' in severities:
                base['severity'] = 'high'
            elif 'medium' in severities:
                base['severity'] = 'medium'
            else:
                base['severity'] = 'low'
            
            merged.append(base)
    
    return merged


# Process final_results.json and create incidents.json
# Only includes tweets where both ML and LLM classifications are true.
def process_final_results(input_file: str = 'final_results.json', output_file: str = 'incidents.json') -> Dict:
    input_path = Path(__file__).parent / input_file
    output_path = Path(__file__).parent / output_file
    
    # Load tweets from final_results.json
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract metadata and tweets from final_results.json
    api_metadata = data.get('metadata', {})
    tweets = data.get('tweets', [])
    
    # Filter tweets
    filtered_tweets = [
        tweet for tweet in tweets
        if tweet.get('ml_classification') 
        and tweet['ml_classification'].get('is_disaster') 
        and tweet.get('llm_extraction')
        and tweet['llm_extraction'].get('llm_classification')
    ]
    
    # Convert to incidents
    incidents = []
    skipped = 0
    for tweet in filtered_tweets:
        incident = tweet_to_incident(tweet)
        if incident:
            incidents.append(incident)
        else:
            skipped += 1
    
    # Group by location and merge similar incidents
    merged_incidents = merge_similar_incidents(incidents)
    
    # Save to file with combined metadata
    result = {
        "metadata": {
            # API metadata from final_results.json
            "api": {
                "generated_at": api_metadata.get('generated_at'),
                "pipeline_last_run": api_metadata.get('pipeline_last_run'),
                "total_tweets_from_pipeline": api_metadata.get('total_tweets')
            },
            # Processing metadata from this script
            "processing": {
                "processed_at": datetime.now().isoformat(),
                "total_tweets": len(tweets),
                "filtered_tweets": len(filtered_tweets),
                "incidents_created": len(merged_incidents),
                "skipped_no_coords": skipped,
            }
        },
        "incidents": merged_incidents
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Processed {len(filtered_tweets)} filtered tweets")
    print(f"✓ Created {len(merged_incidents)} incidents")
    print(f"✓ Skipped {skipped} tweets without coordinates")
    print(f"✓ Saved to {output_path}")
    
    return result


if __name__ == '__main__':
    result = process_final_results()
    print(f"\nSample incident:")
    if result['incidents']:
        print(json.dumps(result['incidents'][0], indent=2))
