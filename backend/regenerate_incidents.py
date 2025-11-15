#!/usr/bin/env python3
"""
Quick script to regenerate incidents from pipeline output
Run this after updating the tweet data.

NOW WITH MONGODB INTEGRATION!
==============================
This script will:
1. Process pipeline_output/04_final_results.jsonl (NEW)
2. OVERWRITE incidents.json with fresh data
3. APPEND new incidents to MongoDB Atlas (accumulates over time)

Usage:
    python regenerate_incidents_fixed.py                    # Append to MongoDB (default)
    python regenerate_incidents_fixed.py --replace-db       # Replace ALL MongoDB data
    python regenerate_incidents_fixed.py --no-mongo         # Only create JSON file
    python regenerate_incidents_fixed.py --input custom.jsonl  # Use custom input file

IMPORTANT:
- incidents.json is ALWAYS overwritten (contains only latest run)
- MongoDB is APPENDED to by default (accumulates all incidents over time)
- Use --replace-db to clear the database and start fresh
"""

import sys
import json
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from process_incidents import (
    tweet_to_incident,
    merge_similar_incidents
)
from mongodb_handler import MongoDBHandler
from datetime import datetime


def load_jsonl(filepath: Path) -> list:
    """Load tweets from JSONL file (pipeline output format)"""
    tweets = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                tweets.append(json.loads(line))
    return tweets


def process_pipeline_results(
    input_file: str = 'pipeline_output/04_final_results.jsonl',
    output_file: str = 'incidents.json',
    save_to_mongodb: bool = True,
    replace_mongodb: bool = True
) -> dict:
    """
    Process pipeline output JSONL and create incidents.json
    
    Args:
        input_file: Path to 04_final_results.jsonl
        output_file: Path to output incidents.json
        save_to_mongodb: Whether to save to MongoDB
        replace_mongodb: Whether to replace all existing MongoDB data
        
    Returns:
        Dictionary with processing results and metadata
    """
    # Resolve paths
    if Path(input_file).is_absolute():
        input_path = Path(input_file)
    else:
        # Try relative to current directory first
        input_path = Path(input_file)
        if not input_path.exists():
            # Try relative to script directory
            input_path = Path(__file__).parent / input_file
    
    output_path = Path(__file__).parent / output_file
    
    print(f"Reading from: {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load tweets from JSONL
    tweets = load_jsonl(input_path)
    
    print(f"✓ Loaded {len(tweets)} tweets from pipeline output")
    
    # Filter tweets: both ML and LLM must classify as disaster
    filtered_tweets = []
    for tweet in tweets:
        ml_cls = tweet.get('ml_classification', {})
        llm_ext = tweet.get('llm_extraction', {})
        
        # Check if both classifiers agree it's a disaster
        ml_is_disaster = ml_cls.get('is_disaster', False)
        llm_is_disaster = llm_ext.get('llm_classification', False) if llm_ext else False
        
        if ml_is_disaster and llm_is_disaster:
            filtered_tweets.append(tweet)
    
    print(f"✓ Filtered to {len(filtered_tweets)} disaster tweets (both ML and LLM agree)")
    
    # Convert to incidents
    incidents = []
    skipped = 0
    for tweet in filtered_tweets:
        incident = tweet_to_incident(tweet)
        if incident:
            incidents.append(incident)
        else:
            skipped += 1
    
    print(f"✓ Created {len(incidents)} incidents")
    print(f"✓ Skipped {skipped} tweets without valid coordinates")
    
    # Merge similar incidents
    merged_incidents = merge_similar_incidents(incidents)
    
    print(f"✓ Merged to {len(merged_incidents)} unique incidents")
    
    # Prepare result dictionary
    result = {
        "metadata": {
            "api": {
                "generated_at": datetime.now().isoformat(),
                "pipeline_last_run": datetime.now().isoformat(),
                "total_tweets_from_pipeline": len(tweets),
                "source_file": str(input_path)
            },
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
    
    # Save to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved to {output_path}")
    
    # Save to MongoDB if requested
    if save_to_mongodb and merged_incidents:
        print("\n" + "=" * 60)
        print("SAVING TO MONGODB")
        print("=" * 60)
        
        try:
            mongo_handler = MongoDBHandler()
            
            if mongo_handler.connect():
                # Insert incidents
                stats = mongo_handler.insert_incidents(
                    merged_incidents, 
                    replace_all=replace_mongodb
                )
                
                print(f"\n✓ MongoDB operation complete:")
                print(f"  Inserted: {stats['inserted']}")
                print(f"  Updated: {stats['updated']}")
                print(f"  Failed: {stats['failed']}")
                
                if stats['errors']:
                    print(f"\nErrors:")
                    for error in stats['errors'][:5]:
                        print(f"  - {error}")
                
                # Show database statistics
                db_stats = mongo_handler.get_statistics()
                print(f"\nDatabase statistics:")
                print(f"  Total incidents: {db_stats['total_incidents']}")
                print(f"  Active incidents: {db_stats['active_incidents']}")
                if db_stats['by_type']:
                    print(f"  By type: {db_stats['by_type']}")
                
                # Add MongoDB info to result
                result['metadata']['mongodb'] = {
                    'saved': True,
                    'stats': stats,
                    'database_stats': db_stats
                }
                
                mongo_handler.close()
            else:
                print("❌ Failed to connect to MongoDB")
                result['metadata']['mongodb'] = {'saved': False, 'error': 'Connection failed'}
                
        except Exception as e:
            print(f"❌ MongoDB error: {e}")
            import traceback
            traceback.print_exc()
            result['metadata']['mongodb'] = {'saved': False, 'error': str(e)}
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Regenerate incidents.json (overwrite) and append to MongoDB (accumulate)'
    )
    parser.add_argument(
        '--no-mongo', 
        action='store_true',
        help='Skip MongoDB upload (only create JSON file)'
    )
    parser.add_argument(
        '--replace-db',
        action='store_true', 
        help='Replace ALL database data (default: append new incidents)'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='pipeline_output/04_final_results.jsonl',
        help='Input file path (default: pipeline_output/04_final_results.jsonl)'
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
    print("JSON: OVERWRITE | MongoDB: APPEND (default)")
    print("=" * 70)
    print()
    
    if args.no_mongo:
        print("⚠️  MongoDB upload is DISABLED")
    else:
        print("✓ MongoDB upload is ENABLED")
        if args.replace_db:
            print("  Mode: REPLACE all database data (delete old, insert new)")
        else:
            print("  Mode: APPEND to database (keep old, add new)")
    
    print()
    print(f"Input file: {args.input}")
    print(f"Output file: {args.output}")
    print()
    
    try:
        result = process_pipeline_results(
            input_file=args.input,
            output_file=args.output,
            save_to_mongodb=not args.no_mongo,
            replace_mongodb=args.replace_db  # Changed: default is False (append mode)
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
                print(f"  ✓ Inserted:  {stats.get('inserted', 0)} new incidents")
                print(f"  ✓ Updated:   {stats.get('updated', 0)} existing incidents")
                if stats.get('failed', 0) > 0:
                    print(f"  ⚠️  Failed:    {stats.get('failed', 0)}")
                
                # Show what happened
                db_stats = mongo.get('database_stats', {})
                total = db_stats.get('total_incidents', 0)
                print(f"\n  Database now has: {total} total incidents")
                if not args.replace_db:
                    print(f"  (Appended to existing data)")
            else:
                print(f"  ❌ Failed: {mongo.get('error', 'Unknown error')}")
        
        print()
        print("✓ incidents.json has been OVERWRITTEN with new data")
        if not args.no_mongo:
            if args.replace_db:
                print("✓ MongoDB has been REPLACED with new data")
            else:
                print("✓ MongoDB has been APPENDED with new data")
        print("✓ Backend API will serve the data from MongoDB")
        print()
        
        # Show sample incident
        if result.get('incidents'):
            print("Sample incident:")
            sample = result['incidents'][0].copy()
            if 'source_tweets' in sample and len(sample['source_tweets']) > 1:
                sample['source_tweets'] = [sample['source_tweets'][0], f"... and {len(sample['source_tweets'])-1} more"]
            print(json.dumps(sample, indent=2)[:500] + "...")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print(f"\nMake sure you've run the pipeline first:")
        print(f"  python unified_pipeline_multitoken.py")
        print(f"\nThe pipeline creates: pipeline_output/04_final_results.jsonl")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()