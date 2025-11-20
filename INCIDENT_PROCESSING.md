# Incident Processing System

This document describes how tweets are processed into incidents and displayed in the LightHouse application.

## Overview

The system filters tweets from `final_results.json` and creates incidents only when **both** classification methods agree that it's a real disaster:

1. **ML Classification**: `ml_classification.is_disaster` = `true`
2. **LLM Classification**: `llm_extraction.llm_classification` = `true`

## Data Flow

```
final_results.json (214 tweets)
        ↓
Filter: Both ML & LLM = true (96 tweets)
        ↓
Extract coordinates & merge duplicates
        ↓
incidents.json (32 incidents)
        ↓
FastAPI /incidents endpoint
        ↓
Frontend Dashboard & IncidentReport
```

## Backend Components

### 1. process_incidents.py

**Purpose**: Convert filtered tweets to incident format

**Key Functions**:

- `tweet_to_incident()`: Converts a single tweet to incident format
- `extract_coordinates_from_location()`: Parses lat/lng from location strings
- `merge_similar_incidents()`: Combines incidents in same location
- `process_final_results()`: Main processing function

**Filtering Criteria**:

- `ml_classification.is_disaster` must be `true`
- `llm_extraction.llm_classification` must be `true`
- Must have valid coordinates (lat/lng)

**Output**: `backend/incidents.json`

### 2. main.py (FastAPI Endpoints)

#### GET /incidents

Returns all incidents as an array.

**Response**:

```json
[
  {
    "id": "6bc508924a8e",
    "title": "A 2.1 magnitude earthquake occurred...",
    "description": "Full details...",
    "location": "DODECANESE ISLANDS, GREECE",
    "lat": 39.0742,
    "lng": 21.8243,
    "severity": "low",
    "incident_type": "Earthquake",
    "tags": ["Earthquake", "low", "earthquake"],
    "status": "active",
    "created_at": "2025-11-04T19:33:10.374Z",
    "source_tweets": [...]
  }
]
```

#### GET /incidents/{incident_id}

Returns a specific incident by ID.

#### GET /incidents/stats/summary

Returns statistics about incidents (by type, severity, location).

#### POST /incidents/regenerate

Regenerates incidents from `final_results.json` (use after running the tweet pipeline).

## Frontend Components

### 1. incidentAPI.ts

TypeScript client for backend API calls.

**Interface**: `IncidentResponse`

```typescript
interface IncidentResponse {
  id: string;
  title: string;
  description: string;
  location: string;
  severity: string;
  incident_type: string;
  tags: string[];
  lat?: number;
  lng?: number;
  created_at: string;
  status: string;
  source_tweets: Tweet[];
}
```

### 2. Dashboard.tsx

Displays incidents on a map with statistics cards and live feed.

**Data Source**: `IncidentAPI.getAllIncidents()`

**Key Features**:

- Interactive map (points or heatmap view)
- Statistics cards (Active Incidents, Posts/Min, Most Affected Region)
- Trending hashtags
- Live tweet feed

### 3. IncidentReport.tsx

Detailed view of individual incidents.

**Data Source**:

- `IncidentAPI.getAllIncidents()` (for list)
- `IncidentAPI.getIncident(id)` (for specific incident)

**Key Features**:

- Map showing incident location
- Source tweets with engagement metrics
- Incident details and timeline

## Running the System

### Step 1: Process Tweets

```bash
cd backend
python process_incidents.py
```

This creates `backend/incidents.json` with 32 incidents from 96 filtered tweets.

### Step 2: Start Backend

```bash
cd backend
fastapi dev main.py
```

Server runs at http://localhost:8000

### Step 3: Start Frontend

```bash
cd frontend
npm run dev
```

Server runs at http://localhost:5173 (or 5174 if 5173 is in use)

### Step 4: View Application

Open http://localhost:5173 in your browser.

## Data Processing Details

### Coordinate Extraction

The system tries multiple methods to get coordinates:

1. **Parse from location string**: `"Tokyo (35.6762, 139.6503)"`
2. **Location database lookup**: Predefined coordinates for ~25 locations
3. **Skip if no coordinates**: Incidents without coords are filtered out

### Incident Merging

Incidents in the same location with the same type are merged:

- Combines source tweets
- Takes highest severity
- Creates summary title/description

### Disaster Type Normalization

Maps various disaster types to frontend categories:

```
earthquake → Earthquake
flood/tsunami → Flood
hurricane/typhoon/cyclone/storm → Storm
wildfire → Wildfire
etc.
```

### Severity Mapping

LLM severity is mapped to numeric scale:

- low → 1
- medium → 2
- high/critical → 3

## Statistics

From the latest processing run:

- **Total tweets**: 214
- **Filtered tweets** (both ML & LLM true): 96
- **Incidents created**: 32
- **Skipped** (no coordinates): 49

## File Structure

```
backend/
├── final_results.json        # Raw tweet data (214 tweets)
├── incidents.json            # Processed incidents (32 incidents)
├── process_incidents.py      # Processing script
├── main.py                   # FastAPI server with /incidents endpoints
└── qdrant_storage.py         # Vector search (future enhancement)

frontend/
├── src/
│   ├── services/
│   │   └── incidentAPI.ts    # API client
│   ├── components/
│   │   ├── Dashboard.tsx     # Main dashboard
│   │   ├── IncidentReport.tsx # Incident details
│   │   └── MapWidget.tsx     # Map component
│   └── data/
│       └── incidents.ts      # Type definitions only (no dummy data)
```

## Future Enhancements

1. **Real-time Updates**: WebSocket for live incident updates
2. **Vector Search**: Use Qdrant for semantic search of similar incidents
3. **Clustering**: Smart grouping of related incidents across regions
4. **Severity Escalation**: Auto-update severity as more reports come in
5. **Alert System**: Push notifications for high-severity incidents
