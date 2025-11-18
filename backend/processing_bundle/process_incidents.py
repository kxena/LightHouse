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

    # Prefer patterns that include directional suffixes (N/S/E/W), e.g. '54.51N 160.13W'
    dir_pattern = r'(-?\d{1,2}\.\d+)\s*°?\s*([NSns])[,;\s]+(-?\d{1,3}\.\d+)\s*°?\s*([EeWw])'
    mdir = re.search(dir_pattern, location)
    if mdir:
        lat = float(mdir.group(1))
        lat_dir = mdir.group(2).upper()
        lng = float(mdir.group(3))
        lng_dir = mdir.group(4).upper()
        if lat_dir == 'S':
            lat = -lat
        if lng_dir == 'W':
            lng = -lng
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            return (lat, lng)

    # Also accept patterns where N/S/E/W are attached directly without separators
    compact_dir = r'(-?\d{1,2}\.\d+)[NSns]\s+(-?\d{1,3}\.\d+)[EeWw]'
    mcomp = re.search(compact_dir, location)
    if mcomp:
        lat = float(mcomp.group(1))
        # extract the directional letters from the match span
        span_text = location[mcomp.start():mcomp.end()]
        lat_dir_match = re.search(r'[NSns]', span_text)
        lng_dir_match = re.search(r'[EeWw]', span_text)
        lat_dir = lat_dir_match.group(0).upper() if lat_dir_match else 'N'
        lng = float(mcomp.group(2))
        lng_dir = lng_dir_match.group(0).upper() if lng_dir_match else 'E'
        if lat_dir == 'S':
            lat = -lat
        if lng_dir == 'W':
            lng = -lng
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            return (lat, lng)

    # Try to find any lat,lng pair like '1.849900, 126.994300' or 'lat: -23.36 lon: -70.60'
    # Keep this as a fallback but ensure we don't accidentally capture magnitude+lat patterns
    pair_pattern = r'(-?\d{1,3}\.\d+)[,\s]+(-?\d{1,3}\.\d+)'
    match2 = re.search(pair_pattern, location)
    if match2:
        # Heuristic: if the first matched number seems like a magnitude (very small < 5) and
        # the second number is followed by a directional letter later in the text, prefer parsing
        # the pair that includes a directional suffix instead (handled above). Otherwise accept.
        lat, lng = float(match2.group(1)), float(match2.group(2))
        if -90 <= lat <= 90 and -180 <= lng <= 180:
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


def load_location_db(path: str = 'location_db.json') -> Dict[str, Dict]:
    p = Path(__file__).parent / path
    if not p.exists():
        return {}
    try:
        return json.load(open(p, 'r', encoding='utf-8'))
    except Exception:
        return {}


def save_location_db(db: Dict[str, Dict], path: str = 'location_db.json') -> None:
    p = Path(__file__).parent / path
    json.dump(db, open(p, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)


def try_geocode(text: str):
    """Attempt geocoding using geopy.Nominatim if available. Returns (lat,lng,source_confidence,entry) or None."""
    try:
        from geopy.geocoders import Nominatim
    except Exception:
        return None
    try:
        geolocator = Nominatim(user_agent='lighthouse_incident_processor', timeout=10)
        loc = geolocator.geocode(text, addressdetails=True)
        if not loc:
            return None
        entry = {
            'id': f'nominatim:{loc.raw.get("place_id")}',
            'canonical_name': loc.address,
            'name_variants': [text],
            'centroid': {'lat': loc.latitude, 'lng': loc.longitude},
            'bbox': None,
            'admin': loc.raw.get('address', {}),
            'level': 'unknown',
            'source': 'nominatim',
            'confidence': 0.8,
            'first_seen': datetime.utcnow().isoformat()
        }
        return (loc.latitude, loc.longitude, 0.8, entry)
    except Exception:
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

    # Load location DB once per call (small DB expected)
    location_db = load_location_db()

    # 1) Try to extract explicit coordinates from tweet text
    original_lat = None
    original_lng = None
    if tweet.get('text'):
        coords = extract_coordinates_from_location(tweet['text'])
        if coords:
            original_lat, original_lng = coords

    # 2) If not found in text, try the structured location string
    if original_lat is None:
        coords2 = extract_coordinates_from_location(location)
        if coords2:
            original_lat, original_lng = coords2

    resolved_place_id = None
    resolved_place_name = None
    resolved_source = None
    resolved_confidence = None

    # 3) If we still don't have coords, try to resolve location string via DB
    final_lat, final_lng = (None, None)
    if original_lat is not None:
        final_lat, final_lng = (original_lat, original_lng)
        resolved_source = 'tweet_text_coords'
        resolved_confidence = 1.0
    else:
        # Normalize key and try exact/variant matches
        loc_key = (location or '').strip()
        for pid, entry in location_db.items():
            try:
                if loc_key.upper() == entry.get('canonical_name', '').upper() or any(loc_key.upper() == v.upper() for v in entry.get('name_variants', [])):
                    resolved_place_id = pid
                    resolved_place_name = entry.get('canonical_name')
                    centroid = entry.get('centroid')
                    if centroid:
                        final_lat, final_lng = (centroid.get('lat'), centroid.get('lng'))
                    resolved_source = 'location_db'
                    resolved_confidence = entry.get('confidence', 0.8)
                    break
            except Exception:
                continue

    # 4) If still unresolved, try geocoder and cache result
    if final_lat is None:
        geocode_result = try_geocode(location)
        if geocode_result:
            g_lat, g_lng, g_conf, g_entry = geocode_result
            # add to DB and save
            new_id = g_entry['id']
            location_db[new_id] = g_entry
            try:
                save_location_db(location_db)
            except Exception:
                pass
            resolved_place_id = new_id
            resolved_place_name = g_entry.get('canonical_name')
            final_lat, final_lng = (g_lat, g_lng)
            resolved_source = 'geocoder'
            resolved_confidence = g_conf

    # If still missing coordinates, skip (can't show on map)
    if final_lat is None or final_lng is None:
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
        # original coords if present
        "original_lat": original_lat,
        "original_lng": original_lng,
        # resolved place provenance
        "resolved_place_id": resolved_place_id,
        "resolved_place_name": resolved_place_name,
        "resolved_source": resolved_source,
        "resolved_confidence": resolved_confidence,
        # final coords used for mapping
        "lat": final_lat,
        "lng": final_lng,
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


def process_final_results(input_file: str = 'final_results.json', output_file: str = 'incidents.json', cluster_threshold_km: float = 50.0, write_output: bool = True) -> Dict:
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
    
    # Group by location and merge similar incidents using configurable threshold
    merged_incidents = merge_similar_incidents(incidents, threshold_km=cluster_threshold_km)
    
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
    
    if write_output:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Processed {len(filtered_tweets)} filtered tweets")
    print(f"✓ Created {len(merged_incidents)} incidents")
    print(f"✓ Skipped {skipped} tweets without coordinates")
    print(f"✓ Saved to {output_path}")
    
    return result


def merge_similar_incidents(incidents: List[Dict], threshold_km: float = 50.0) -> List[Dict]:
    """
    Merge incidents that are in the same location and of the same type.
    Combines their source tweets.
    """
    import math

    def haversine_km(a_lat, a_lng, b_lat, b_lng):
        R = 6371.0
        phi1 = math.radians(a_lat)
        phi2 = math.radians(b_lat)
        dphi = math.radians(b_lat - a_lat)
        dlambda = math.radians(b_lng - a_lng)
        x = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
        c = 2 * math.atan2(math.sqrt(x), math.sqrt(1-x))
        return R * c

    threshold_km = threshold_km
    clusters: List[Dict] = []

    for inc in incidents:
        placed = False
        for cluster in clusters:
            if cluster['incident_type'] != inc['incident_type']:
                continue
            dist = haversine_km(cluster['centroid_lat'], cluster['centroid_lng'], inc['lat'], inc['lng'])
            if dist <= threshold_km:
                cluster['members'].append(inc)
                lats = [m['lat'] for m in cluster['members']]
                lngs = [m['lng'] for m in cluster['members']]
                cluster['centroid_lat'] = sum(lats) / len(lats)
                cluster['centroid_lng'] = sum(lngs) / len(lngs)
                placed = True
                break
        if not placed:
            clusters.append({
                'incident_type': inc['incident_type'],
                'members': [inc],
                'centroid_lat': inc['lat'],
                'centroid_lng': inc['lng']
            })

    merged: List[Dict] = []
    for cluster in clusters:
        members = cluster['members']
        if len(members) == 1:
            merged.append(members[0])
            continue
        base = members[0].copy()
        all_tweets = []
        for m in members:
            all_tweets.extend(m.get('source_tweets', []))
        centroid_lat = cluster['centroid_lat']
        centroid_lng = cluster['centroid_lng']
        base['source_tweets'] = all_tweets
        base['title'] = f"Multiple {cluster['incident_type']} reports in {base.get('location','region')}"
        base['description'] = f"{len(all_tweets)} reports of {cluster['incident_type'].lower()} activity"
        base['lat'] = centroid_lat
        base['lng'] = centroid_lng
        # include cluster member coords and ids for frontend inspection
        base['cluster_member_coords'] = [ { 'id': m.get('id'), 'lat': m.get('lat'), 'lng': m.get('lng') } for m in members ]
        base['cluster_member_ids'] = [ m.get('id') for m in members ]
        severity_order = {'low': 1, 'medium': 2, 'high': 3, 'critical': 3}
        sev_vals = [severity_order.get(m.get('severity','medium'), 2) for m in members]
        maxsev = max(sev_vals)
        rev_map = {1: 'low', 2: 'medium', 3: 'high'}
        base['severity'] = rev_map.get(maxsev, 'medium')
        merged.append(base)

    return merged


if __name__ == '__main__':
    result = process_final_results()
    print(f"\nSample incident:")
    if result['incidents']:
        print(json.dumps(result['incidents'][0], indent=2))
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

    # Prefer patterns that include directional suffixes (N/S/E/W), e.g. '54.51N 160.13W'
    dir_pattern = r'(-?\d{1,2}\.\d+)\s*°?\s*([NSns])[,;\s]+(-?\d{1,3}\.\d+)\s*°?\s*([EeWw])'
    mdir = re.search(dir_pattern, location)
    if mdir:
        lat = float(mdir.group(1))
        lat_dir = mdir.group(2).upper()
        lng = float(mdir.group(3))
        lng_dir = mdir.group(4).upper()
        if lat_dir == 'S':
            lat = -lat
        if lng_dir == 'W':
            lng = -lng
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            return (lat, lng)

    # Also accept patterns where N/S/E/W are attached directly without separators
    compact_dir = r'(-?\d{1,2}\.\d+)[NSns]\s+(-?\d{1,3}\.\d+)[EeWw]'
    mcomp = re.search(compact_dir, location)
    if mcomp:
        lat = float(mcomp.group(1))
        # extract the directional letters from the match span
        span_text = location[mcomp.start():mcomp.end()]
        lat_dir_match = re.search(r'[NSns]', span_text)
        lng_dir_match = re.search(r'[EeWw]', span_text)
        lat_dir = lat_dir_match.group(0).upper() if lat_dir_match else 'N'
        lng = float(mcomp.group(2))
        lng_dir = lng_dir_match.group(0).upper() if lng_dir_match else 'E'
        if lat_dir == 'S':
            lat = -lat
        if lng_dir == 'W':
            lng = -lng
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            return (lat, lng)

    # Try to find any lat,lng pair like '1.849900, 126.994300' or 'lat: -23.36 lon: -70.60'
    # Keep this as a fallback but ensure we don't accidentally capture magnitude+lat patterns
    pair_pattern = r'(-?\d{1,3}\.\d+)[,\s]+(-?\d{1,3}\.\d+)'
    match2 = re.search(pair_pattern, location)
    if match2:
        # Heuristic: if the first matched number seems like a magnitude (very small < 5) and
        # the second number is followed by a directional letter later in the text, prefer parsing
        # the pair that includes a directional suffix instead (handled above). Otherwise accept.
        lat, lng = float(match2.group(1)), float(match2.group(2))
        if -90 <= lat <= 90 and -180 <= lng <= 180:
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


def load_location_db(path: str = 'location_db.json') -> Dict[str, Dict]:
    p = Path(__file__).parent / path
    if not p.exists():
        return {}
    try:
        return json.load(open(p, 'r', encoding='utf-8'))
    except Exception:
        return {}


def save_location_db(db: Dict[str, Dict], path: str = 'location_db.json') -> None:
    p = Path(__file__).parent / path
    json.dump(db, open(p, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)


def try_geocode(text: str):
    """Attempt geocoding using geopy.Nominatim if available. Returns (lat,lng,source_confidence,entry) or None."""
    try:
        from geopy.geocoders import Nominatim
    except Exception:
        return None
    try:
        geolocator = Nominatim(user_agent='lighthouse_incident_processor', timeout=10)
        loc = geolocator.geocode(text, addressdetails=True)
        if not loc:
            return None
        entry = {
            'id': f'nominatim:{loc.raw.get("place_id")}',
            'canonical_name': loc.address,
            'name_variants': [text],
            'centroid': {'lat': loc.latitude, 'lng': loc.longitude},
            'bbox': None,
            'admin': loc.raw.get('address', {}),
            'level': 'unknown',
            'source': 'nominatim',
            'confidence': 0.8,
            'first_seen': datetime.utcnow().isoformat()
        }
        return (loc.latitude, loc.longitude, 0.8, entry)
    except Exception:
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

    # Load location DB once per call (small DB expected)
    location_db = load_location_db()

    # 1) Try to extract explicit coordinates from tweet text
    original_lat = None
    original_lng = None
    if tweet.get('text'):
        coords = extract_coordinates_from_location(tweet['text'])
        if coords:
            original_lat, original_lng = coords

    # 2) If not found in text, try the structured location string
    if original_lat is None:
        coords2 = extract_coordinates_from_location(location)
        if coords2:
            original_lat, original_lng = coords2

    resolved_place_id = None
    resolved_place_name = None
    resolved_source = None
    resolved_confidence = None

    # 3) If we still don't have coords, try to resolve location string via DB
    final_lat, final_lng = (None, None)
    if original_lat is not None:
        final_lat, final_lng = (original_lat, original_lng)
        resolved_source = 'tweet_text_coords'
        resolved_confidence = 1.0
    else:
        # Normalize key and try exact/variant matches
        loc_key = (location or '').strip()
        for pid, entry in location_db.items():
            try:
                if loc_key.upper() == entry.get('canonical_name', '').upper() or any(loc_key.upper() == v.upper() for v in entry.get('name_variants', [])):
                    resolved_place_id = pid
                    resolved_place_name = entry.get('canonical_name')
                    centroid = entry.get('centroid')
                    if centroid:
                        final_lat, final_lng = (centroid.get('lat'), centroid.get('lng'))
                    resolved_source = 'location_db'
                    resolved_confidence = entry.get('confidence', 0.8)
                    break
            except Exception:
                continue

    # 4) If still unresolved, try geocoder and cache result
    if final_lat is None:
        geocode_result = try_geocode(location)
        if geocode_result:
            g_lat, g_lng, g_conf, g_entry = geocode_result
            # add to DB and save
            new_id = g_entry['id']
            location_db[new_id] = g_entry
            try:
                save_location_db(location_db)
            except Exception:
                pass
            resolved_place_id = new_id
            resolved_place_name = g_entry.get('canonical_name')
            final_lat, final_lng = (g_lat, g_lng)
            resolved_source = 'geocoder'
            resolved_confidence = g_conf

    # If still missing coordinates, skip (can't show on map)
    if final_lat is None or final_lng is None:
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
        # original coords if present
        "original_lat": original_lat,
        "original_lng": original_lng,
        # resolved place provenance
        "resolved_place_id": resolved_place_id,
        "resolved_place_name": resolved_place_name,
        "resolved_source": resolved_source,
        "resolved_confidence": resolved_confidence,
        # final coords used for mapping
        "lat": final_lat,
        "lng": final_lng,
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


def process_final_results(input_file: str = 'final_results.json', output_file: str = 'incidents.json', cluster_threshold_km: float = 50.0, write_output: bool = True) -> Dict:
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
    
    # Group by location and merge similar incidents using configurable threshold
    merged_incidents = merge_similar_incidents(incidents, threshold_km=cluster_threshold_km)
    
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
    
    if write_output:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Processed {len(filtered_tweets)} filtered tweets")
    print(f"✓ Created {len(merged_incidents)} incidents")
    print(f"✓ Skipped {skipped} tweets without coordinates")
    print(f"✓ Saved to {output_path}")
    
    return result


def merge_similar_incidents(incidents: List[Dict], threshold_km: float = 50.0) -> List[Dict]:
    """
    Merge incidents that are in the same location and of the same type.
    Combines their source tweets.
    """
    import math

    def haversine_km(a_lat, a_lng, b_lat, b_lng):
        R = 6371.0
        phi1 = math.radians(a_lat)
        phi2 = math.radians(b_lat)
        dphi = math.radians(b_lat - a_lat)
        dlambda = math.radians(b_lng - a_lng)
        x = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
        c = 2 * math.atan2(math.sqrt(x), math.sqrt(1-x))
        return R * c

    threshold_km = threshold_km
    clusters: List[Dict] = []

    for inc in incidents:
        placed = False
        for cluster in clusters:
            if cluster['incident_type'] != inc['incident_type']:
                continue
            dist = haversine_km(cluster['centroid_lat'], cluster['centroid_lng'], inc['lat'], inc['lng'])
            if dist <= threshold_km:
                cluster['members'].append(inc)
                lats = [m['lat'] for m in cluster['members']]
                lngs = [m['lng'] for m in cluster['members']]
                cluster['centroid_lat'] = sum(lats) / len(lats)
                cluster['centroid_lng'] = sum(lngs) / len(lngs)
                placed = True
                break
        if not placed:
            clusters.append({
                'incident_type': inc['incident_type'],
                'members': [inc],
                'centroid_lat': inc['lat'],
                'centroid_lng': inc['lng']
            })

    merged: List[Dict] = []
    for cluster in clusters:
        members = cluster['members']
        if len(members) == 1:
            merged.append(members[0])
            continue
        base = members[0].copy()
        all_tweets = []
        for m in members:
            all_tweets.extend(m.get('source_tweets', []))
        centroid_lat = cluster['centroid_lat']
        centroid_lng = cluster['centroid_lng']
        base['source_tweets'] = all_tweets
        base['title'] = f"Multiple {cluster['incident_type']} reports in {base.get('location','region')}"
        base['description'] = f"{len(all_tweets)} reports of {cluster['incident_type'].lower()} activity"
        base['lat'] = centroid_lat
        base['lng'] = centroid_lng
        # include cluster member coords and ids for frontend inspection
        base['cluster_member_coords'] = [ { 'id': m.get('id'), 'lat': m.get('lat'), 'lng': m.get('lng') } for m in members ]
        base['cluster_member_ids'] = [ m.get('id') for m in members ]
        severity_order = {'low': 1, 'medium': 2, 'high': 3, 'critical': 3}
        sev_vals = [severity_order.get(m.get('severity','medium'), 2) for m in members]
        maxsev = max(sev_vals)
        rev_map = {1: 'low', 2: 'medium', 3: 'high'}
        base['severity'] = rev_map.get(maxsev, 'medium')
        merged.append(base)

    return merged


if __name__ == '__main__':
    result = process_final_results()
    print(f"\nSample incident:")
    if result['incidents']:
        print(json.dumps(result['incidents'][0], indent=2))
