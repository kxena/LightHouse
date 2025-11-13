#!/usr/bin/env python3
"""
Quick script to regenerate incidents from final_results.json
Run this after updating the tweet data.

NOW WITH MONGODB INTEGRATION!
==============================
This script will:
1. Process final_results.json 
2. Create incidents.json
3. Upload all incidents to MongoDB Atlas

Usage:
    python regenerate_incidents.py              # Save to both JSON and MongoDB
    python regenerate_incidents.py --no-mongo   # Save only to JSON file
    python regenerate_incidents.py --update     # Update MongoDB instead of replacing
"""

import sys
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from process_incidents import process_final_results

def main():
    parser = argparse.ArgumentParser(
        description='Regenerate incidents from final_results.json and save to MongoDB'
    )
    parser.add_argument(
        '--no-mongo', 
        action='store_true',
        help='Skip MongoDB upload (only create JSON file)'
    )
    parser.add_argument(
        '--update',
        action='store_true', 
        help='Update existing MongoDB data instead of replacing all'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='final_results.json',
        help='Input file path (default: final_results.json)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='incidents.json',
        help='Output file path (default: incidents.json)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("LightHouse Incident Regeneration")
    print("=" * 70)
    print()
    
    if args.no_mongo:
        print("⚠️  MongoDB upload is DISABLED")
    else:
        print("✓ MongoDB upload is ENABLED")
        if args.update:
            print("  Mode: UPDATE existing incidents")
        else:
            print("  Mode: REPLACE all incidents")
    
    print()
    
    try:
        result = process_final_results(
            input_file=args.input,
            output_file=args.output,
            save_to_mongodb=not args.no_mongo,
            replace_mongodb=not args.update
        )
        
        print()
        print("=" * 70)
        print("SUCCESS! Summary:")
        print("=" * 70)
        
        # Display processing metadata
        processing = result.get('metadata', {}).get('processing', {})
        print(f"Total tweets:        {processing.get('total_tweets', 0)}")
        print(f"Filtered tweets:     {processing.get('filtered_tweets', 0)}")
        print(f"Incidents created:   {processing.get('incidents_created', 0)}")
        print(f"Skipped (no coords): {processing.get('skipped_no_coords', 0)}")
        print(f"Processed at:        {processing.get('processed_at', 'N/A')}")
        
        # Display MongoDB metadata if available
        if 'mongodb' in result.get('metadata', {}):
            mongo = result['metadata']['mongodb']
            print()
            print("MongoDB Upload:")
            if mongo.get('saved'):
                stats = mongo.get('stats', {})
                print(f"  ✓ Inserted:  {stats.get('inserted', 0)}")
                print(f"  ✓ Updated:   {stats.get('updated', 0)}")
                if stats.get('failed', 0) > 0:
                    print(f"  ⚠️  Failed:    {stats.get('failed', 0)}")
            else:
                print(f"  ❌ Failed: {mongo.get('error', 'Unknown error')}")
        
        print()
        print("✓ incidents.json has been updated")
        if not args.no_mongo:
            print("✓ MongoDB has been updated")
        print("✓ Backend API will serve the new data automatically")
        print()
        
    except FileNotFoundError as e:
        print(f"❌ Error: Could not find input file '{args.input}'")
        print(f"   Make sure to run the unified pipeline first!")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()