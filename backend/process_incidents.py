"""
Process tweets from final_results.json and convert them to incidents.
Only creates incidents where both ml_classification.is_disaster and llm_extraction.llm_classification are true.
"""

import json
import hashlib
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path


def extract_coordinates_from_location(location: str) -> Optional[tuple[float, float]]:
    """
    Extract lat/lng from location strings that may contain coordinates.
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


def severity_map(llm_severity: str) -> int:
    """Map LLM severity to 1-3 scale for frontend"""
    mapping = {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 3
    }
    return mapping.get(llm_severity.lower(), 2)


def disaster_type_normalize(disaster_type: str) -> str:
    """Normalize disaster type to match frontend expectations"""
    type_mapping = {
        "earthquake": "Earthquake",
        "flood": "Flood",
        "hurricane": "Storm",
        "wildfire": "Wildfire",
        "tornado": "Tornado",
        "storm": "Storm",
        "tsunami": "Flood",
        "typhoon": "Storm",
        "cyclone": "Storm",
        "avalanche": "Avalanche",
        "landslide": "Landslide",
        "volcano": "Volcano",
        "volcanic": "Volcano",
        "drought": "Drought",
        "heatwave": "Heatwave",
        "coldwave": "Coldwave",
    }
    return type_mapping.get(disaster_type.lower(), "Storm")


def generate_incident_id(tweet_id: str, location: str) -> str:
    """Generate a unique incident ID"""
    # Use a combination of location and tweet id
    content = f"{location}-{tweet_id}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


def tweet_to_incident(tweet: Dict) -> Optional[Dict]:
    """
    Convert a filtered tweet to an incident format matching the frontend expectations.
    Returns None if critical data is missing.
    """
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


def process_final_results(input_file: str = 'final_results.json', output_file: str = 'incidents.json') -> Dict:
    """
    Process final_results.json and create incidents.json
    Only includes tweets where both ML and LLM classifications are true.
    """
    input_path = Path(__file__).parent / input_file
    output_path = Path(__file__).parent / output_file
    
    # Load tweets
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filter tweets
    filtered_tweets = [
        tweet for tweet in data['tweets']
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
    
    # Save to file
    result = {
        "incidents": merged_incidents,
        "metadata": {
            "total_tweets": len(data['tweets']),
            "filtered_tweets": len(filtered_tweets),
            "incidents_created": len(merged_incidents),
            "skipped_no_coords": skipped,
            "generated_at": datetime.now().isoformat()
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Processed {len(filtered_tweets)} filtered tweets")
    print(f"✓ Created {len(merged_incidents)} incidents")
    print(f"✓ Skipped {skipped} tweets without coordinates")
    print(f"✓ Saved to {output_path}")
    
    return result


def merge_similar_incidents(incidents: List[Dict]) -> List[Dict]:
    """
    Merge incidents that are in the same location and of the same type.
    Combines their source tweets.
    """
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


if __name__ == '__main__':
    result = process_final_results()
    print(f"\nSample incident:")
    if result['incidents']:
        print(json.dumps(result['incidents'][0], indent=2))
