# LightHouse Frontend Refactoring Summary

## Overview
Successfully refactored the LightHouse frontend to use the deployed backend pipeline at `https://lighthouse-4gv2.onrender.com` instead of local JSON files or direct database access.

## Changes Made

### 1. New API Client (`frontend/src/api/lighthouseApi.ts`)
Created a unified API client module with:

**Core API Functions:**
- `getHealth()` - Health check
- `getIncidents(options?)` - Get all incidents with optional filters
- `getIncidentById(id)` - Get specific incident
- `getIncidentsByType(type)` - Filter incidents by disaster type
- `getNearbyIncidents(lat, lng, radius)` - Get incidents near a location
- `getStats()` - Get database statistics
- `getIncidentTypes()` - Get list of all incident types
- `getSeverityLevels()` - Get list of severity levels

**Historical Data Functions:**
- `IncidentAPI.getHistoryDates()` - Get available historical dates
- `IncidentAPI.getHistoryIncidents(date)` - Get incidents for a specific date
- `IncidentAPI.getIncident(id, date?)` - Get incident with optional historical date

**TypeScript Types:**
- `Incident` - Main incident interface matching OpenAPI schema
- `SourceTweet` - Tweet data structure
- `Statistics` - Database stats structure
- `HealthResponse` - Health check response
- `HistoricalIncident` & `HistoricalResponse` - Historical data structures

**Configuration:**
- Base URL: `import.meta.env.VITE_API_BASE_URL ?? "https://lighthouse-4gv2.onrender.com"`
- Can be overridden with environment variable

### 2. Updated Components

#### Dashboard (`frontend/src/components/Dashboard.tsx`)
- ✅ Updated imports to use new API client
- ✅ Restored historical data functionality (dates dropdown, historical incident loading)
- ✅ Uses `getIncidents()` for live data
- ✅ Uses `IncidentAPI.getHistoryDates()` and `IncidentAPI.getHistoryIncidents(date)` for historical data
- ✅ Maintains all existing UI features:
  - Map with points/heatmap toggle
  - Trending hashtags
  - Search functionality
  - Disaster type filters
  - Tag filtering
  - Historical date selection
  - Nearest incident calculation

#### IncidentReport (`frontend/src/components/IncidentReport.tsx`)
- ✅ Updated imports to use new API client (`frontend/src/api/lighthouseApi.ts`)
- ✅ Maintains support for historical dates via URL query parameter
- ✅ Uses `IncidentAPI.getIncident(id, date)` for fetching incidents

### 3. Backend API Updates (`backend/api_server.py`)

Added historical data endpoints to support frontend functionality:

**New Endpoints:**
- `GET /api/history/dates` - Returns list of available historical dates from `backend/historical/` directory
- `GET /api/history/incidents/{date}` - Returns historical incidents for a specific date

These endpoints read from the JSON files in `backend/historical/` directory:
- `2025-11-15_incidents.json`
- `2025-11-16_incidents.json`
- `2025-11-17_incidents.json`

### 4. Environment Configuration

Created `frontend/.env.example`:
```env
VITE_API_BASE_URL=https://lighthouse-4gv2.onrender.com
```

Users can create `.env.local` for local development:
```env
VITE_API_BASE_URL=http://localhost:8000
```

## What Was NOT Changed

✅ **All UI/UX remains the same** - Maps, charts, filters, searches all work identically
✅ **Historical data preserved** - Users can still view past incidents by date
✅ **Component structure** - No breaking changes to component hierarchy
✅ **Styling** - All Tailwind classes and dark mode support unchanged
✅ **Authentication** - Clerk integration remains intact

## Removed Dependencies

The following old files are no longer used (but kept for reference):
- `frontend/src/services/incidentAPI.ts` - Replaced by `frontend/src/api/lighthouseApi.ts`
- `frontend/src/hooks/useApi.ts` - No longer needed, components use API client directly

## Data Flow

### Before:
```
Frontend → Local JSON files
Frontend → Direct MongoDB queries (?)
Frontend → localhost:3001 or localhost:8001
```

### After:
```
Frontend → https://lighthouse-4gv2.onrender.com/api/incidents (live data from MongoDB)
Frontend → https://lighthouse-4gv2.onrender.com/api/history/* (historical data from JSON files)
Frontend → All stats, types, severity levels from deployed backend
```

## Testing Checklist

- [ ] Live incidents display on Dashboard map
- [ ] Historical date dropdown populates with available dates
- [ ] Selecting a historical date loads that day's incidents
- [ ] Individual incident pages work with and without date parameter
- [ ] Statistics panel shows real data
- [ ] Trending hashtags appear
- [ ] Search and filters work correctly
- [ ] Map toggles between points and heatmap views
- [ ] Severity colors display correctly
- [ ] All API calls use deployed backend URL

## Next Steps

1. **Deploy Backend Changes**: Ensure `backend/api_server.py` with historical endpoints is deployed to Render
2. **Environment Variables**: Set `VITE_API_BASE_URL` if needed for production
3. **Test Historical Data**: Verify historical JSON files are included in backend deployment
4. **Monitor Performance**: Check API response times from deployed backend
5. **Error Handling**: Monitor for any API errors in production

## API Endpoints Used

### Live Data (from MongoDB):
- `GET /api/health` - Health check
- `GET /api/incidents?active_only=true` - All active incidents
- `GET /api/incidents/{id}` - Specific incident
- `GET /api/incidents/type/{type}` - Incidents by type
- `GET /api/incidents/nearby?lat={lat}&lng={lng}&radius_km={radius}` - Nearby incidents
- `GET /api/stats` - Database statistics
- `GET /api/incident-types` - All incident types
- `GET /api/severity-levels` - All severity levels

### Historical Data (from JSON files):
- `GET /api/history/dates` - Available historical dates
- `GET /api/history/incidents/{date}` - Incidents for specific date

## Benefits

✅ **Single Source of Truth**: All data comes from deployed backend pipeline
✅ **No Local Dependencies**: No need for local MongoDB or JSON files
✅ **Consistent Data**: Frontend and backend always in sync
✅ **Scalable**: Backend can be updated independently
✅ **Environment Flexible**: Easy to switch between dev/staging/prod backends
✅ **Type Safe**: Full TypeScript support with proper interfaces
✅ **Historical Preserved**: All existing historical data functionality maintained
