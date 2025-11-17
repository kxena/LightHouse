#!/usr/bin/env python3
"""
Quick script to regenerate incidents from final_results.json
Run this after updating the tweet data.
"""

import sys
from pathlib import Path

# Add bundle to path
sys.path.insert(0, str(Path(__file__).parent))

from process_incidents import process_final_results

if __name__ == '__main__':
    print("=" * 60)
    print("LightHouse Incident Regeneration (bundle)")
    print("=" * 60)
    print()
    
    try:
        result = process_final_results()
        print()
        print("=" * 60)
        print("SUCCESS! Summary:")
        print("=" * 60)
        metadata = result.get('metadata', {})
        print(f"Total tweets:        {metadata.get('total_tweets', 0)}")
        print(f"Filtered tweets:     {metadata.get('filtered_tweets', 0)}")
        print(f"Incidents created:   {metadata.get('incidents_created', 0)}")
        print(f"Skipped (no coords): {metadata.get('skipped_no_coords', 0)}")
        print(f"Generated at:        {metadata.get('generated_at', 'N/A')}")
        print()
        print("✓ incidents.json has been updated in processing_bundle")
        print()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
#!/usr/bin/env python3
"""
Quick script to regenerate incidents from final_results.json
Run this after updating the tweet data.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from process_incidents import process_final_results

if __name__ == '__main__':
    print("=" * 60)
    print("LightHouse Incident Regeneration")
    print("=" * 60)
    print()
    
    try:
        result = process_final_results()
        print()
        print("=" * 60)
        print("SUCCESS! Summary:")
        print("=" * 60)
        metadata = result.get('metadata', {})
        print(f"Total tweets:        {metadata.get('total_tweets', 0)}")
        print(f"Filtered tweets:     {metadata.get('filtered_tweets', 0)}")
        print(f"Incidents created:   {metadata.get('incidents_created', 0)}")
        print(f"Skipped (no coords): {metadata.get('skipped_no_coords', 0)}")
        print(f"Generated at:        {metadata.get('generated_at', 'N/A')}")
        print()
        print("✓ incidents.json has been updated")
        print("✓ Backend API will serve the new data automatically")
        print()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
