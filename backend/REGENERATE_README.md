# Regenerate Incidents Script

## Quick Start

```powershell
cd backend
python regenerate_incidents.py
```

This script automatically:

1. Reads `final_results.json`
2. Filters tweets where both ML and LLM classifications are true
3. Extracts coordinates and creates incidents
4. Merges similar incidents
5. Saves to `incidents.json`

The backend API will automatically serve the updated data.

## When to Use

- After running the tweet collection pipeline
- When you have new data in `final_results.json`
- To rebuild incidents after changing processing logic

## Alternative: API Endpoint

```bash
curl -X POST http://localhost:8000/incidents/regenerate
```
