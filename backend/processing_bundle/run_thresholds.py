"""
Run processing with several clustering thresholds and save outputs for comparison.
Generates: incidents_10km.json, incidents_25km.json, incidents_50km.json and prints counts.
"""
from process_incidents import process_final_results

thresholds = [10.0, 25.0, 50.0]
outputs = []
for t in thresholds:
    out_file = f"incidents_{int(t)}km.json"
    print(f"Running cluster threshold {t} km -> {out_file}")
    res = process_final_results(input_file='final_results.json', output_file=out_file, cluster_threshold_km=t, write_output=True)
    meta = res.get('metadata', {})
    print(f"  Filtered tweets: {meta.get('filtered_tweets')}  Incidents: {meta.get('incidents_created')}  Skipped: {meta.get('skipped_no_coords')}")
    outputs.append((t, out_file, meta.get('incidents_created')))

print('\nSummary:')
for t, f, c in outputs:
    print(f"  {t} km -> {c} incidents saved in {f}")
"""
Run processing with several clustering thresholds and save outputs for comparison.
Generates: incidents_10km.json, incidents_25km.json, incidents_50km.json and prints counts.
"""
from process_incidents import process_final_results

thresholds = [10.0, 25.0, 50.0]
outputs = []
for t in thresholds:
    out_file = f"incidents_{int(t)}km.json"
    print(f"Running cluster threshold {t} km -> {out_file}")
    res = process_final_results(input_file='final_results.json', output_file=out_file, cluster_threshold_km=t, write_output=True)
    meta = res.get('metadata', {})
    print(f"  Filtered tweets: {meta.get('filtered_tweets')}  Incidents: {meta.get('incidents_created')}  Skipped: {meta.get('skipped_no_coords')}")
    outputs.append((t, out_file, meta.get('incidents_created')))

print('\nSummary:')
for t, f, c in outputs:
    print(f"  {t} km -> {c} incidents saved in {f}")
