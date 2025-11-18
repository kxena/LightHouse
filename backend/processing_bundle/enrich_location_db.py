"""
Enrich the `location_db.json` by geocoding unresolved location strings from `final_results.json`.
This script uses `try_geocode()` from `process_incidents.py` and will cache results into `location_db.json`.

If `geopy` is not available, the script will raise an informative message.
"""
import json
from pathlib import Path
from process_incidents import load_location_db, save_location_db, try_geocode, extract_coordinates_from_location

FINAL = Path(__file__).parent / 'final_results.json'
DB_PATH = Path(__file__).parent / 'location_db.json'

if not FINAL.exists():
    print('final_results.json not found in backend/processing_bundle/; run pipeline first')
    raise SystemExit(1)

with open(FINAL, 'r', encoding='utf-8') as f:
    data = json.load(f)

location_db = load_location_db()

# Collect candidate location strings: llm_extraction.location for tweets without explicit numeric coords
candidates = {}
for tweet in data.get('tweets', []):
    llm = tweet.get('llm_extraction')
    if not llm or not llm.get('llm_classification'):
        continue
    loc = llm.get('location')
    if not loc:
        continue
    # skip if tweet text includes explicit coords
    if extract_coordinates_from_location(tweet.get('text','')):
        continue
    # skip if already covered by DB
    already = False
    for pid, entry in location_db.items():
        if loc.strip().upper() == entry.get('canonical_name','').strip().upper() or any(loc.strip().upper() == v.strip().upper() for v in entry.get('name_variants', [])):
            already = True
            break
    if already:
        continue
    candidates[loc] = candidates.get(loc, 0) + 1

print(f'Found {len(candidates)} unique candidate location strings to try geocoding')
if len(candidates) == 0:
    print('Nothing to do; location_db is already covering these names or tweets contain coords')
    raise SystemExit(0)

# Try geocoding each candidate
added = 0
failed = []
for loc, count in sorted(candidates.items(), key=lambda x: -x[1]):
    print(f'Geocoding: "{loc}" (appears {count} times)')
    res = try_geocode(loc)
    if res:
        lat, lng, conf, entry = res
        pid = entry['id']
        location_db[pid] = entry
        added += 1
        print(f'  -> added {pid} @ {lat},{lng} (conf {conf})')
        # persist incrementally
        save_location_db(location_db)
    else:
        print('  -> no result')
        failed.append(loc)

print(f'Geocoding complete. Added {added} entries. {len(failed)} failed.')
if failed:
    print('Failed candidates:')
    for f in failed:
        print(' -', f)
"""
Enrich the `location_db.json` by geocoding unresolved location strings from `final_results.json`.
This script uses `try_geocode()` from `process_incidents.py` and will cache results into `location_db.json`.

If `geopy` is not available, the script will raise an informative message.
"""
import json
from pathlib import Path
from process_incidents import load_location_db, save_location_db, try_geocode

FINAL = Path(__file__).parent / 'final_results.json'
DB_PATH = Path(__file__).parent / 'location_db.json'

if not FINAL.exists():
    print('final_results.json not found in backend/; run pipeline first')
    raise SystemExit(1)

with open(FINAL, 'r', encoding='utf-8') as f:
    data = json.load(f)

location_db = load_location_db()

# Collect candidate location strings: llm_extraction.location for tweets without explicit numeric coords
candidates = {}
for tweet in data.get('tweets', []):
    llm = tweet.get('llm_extraction')
    if not llm or not llm.get('llm_classification'):
        continue
    loc = llm.get('location')
    if not loc:
        continue
    # skip if tweet text includes explicit coords
    from process_incidents import extract_coordinates_from_location
    if extract_coordinates_from_location(tweet.get('text','')):
        continue
    # skip if already covered by DB
    already = False
    for pid, entry in location_db.items():
        if loc.strip().upper() == entry.get('canonical_name','').strip().upper() or any(loc.strip().upper() == v.strip().upper() for v in entry.get('name_variants', [])):
            already = True
            break
    if already:
        continue
    candidates[loc] = candidates.get(loc, 0) + 1

print(f'Found {len(candidates)} unique candidate location strings to try geocoding')
if len(candidates) == 0:
    print('Nothing to do; location_db is already covering these names or tweets contain coords')
    raise SystemExit(0)

# Try geocoding each candidate
added = 0
failed = []
for loc, count in sorted(candidates.items(), key=lambda x: -x[1]):
    print(f'Geocoding: "{loc}" (appears {count} times)')
    res = try_geocode(loc)
    if res:
        lat, lng, conf, entry = res
        pid = entry['id']
        location_db[pid] = entry
        added += 1
        print(f'  -> added {pid} @ {lat},{lng} (conf {conf})')
        # persist incrementally
        save_location_db(location_db)
    else:
        print('  -> no result')
        failed.append(loc)

print(f'Geocoding complete. Added {added} entries. {len(failed)} failed.')
if failed:
    print('Failed candidates:')
    for f in failed:
        print(' -', f)
