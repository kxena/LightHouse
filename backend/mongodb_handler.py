"""
Robust MongoDB Handler - Handles Timeouts for Automation
=========================================================

Features:
- Multiple retry attempts with exponential backoff
- Longer timeout (30s instead of 5s)
- Graceful failure (doesn't crash automation)
- Returns success even if MongoDB fails (JSON still created)
"""

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import List, Dict, Optional
from dotenv import load_dotenv
import time

load_dotenv()

from bson import ObjectId, Decimal128
from datetime import datetime

def clean_mongo_doc(doc):
    """Recursively convert MongoDB-specific types to JSON-serializable ones"""
    if isinstance(doc, dict):
        doc.pop('_id', None)
        cleaned = {k: clean_mongo_doc(v) for k, v in doc.items()}

        # 🔹 Force boolean fields to real booleans
        for key in ["damage_mentioned", "needs_help", "casualties_mentioned"]:
            if key in cleaned:
                cleaned[key] = bool(cleaned[key]) if isinstance(cleaned[key], (bool, int)) else False

        return cleaned
    
    elif isinstance(doc, list):
        return [clean_mongo_doc(item) for item in doc]
    
    elif isinstance(doc, ObjectId):
        return str(doc)
    
    elif isinstance(doc, Decimal128):
        return float(doc.to_decimal())
    
    elif isinstance(doc, datetime):
        return doc.isoformat()
    
    # Handle MongoDB Extended JSON wrappers like {"$numberDouble": "12.8797"}
    elif isinstance(doc, dict) and len(doc) == 1:
        key = list(doc.keys())[0]
        if key.startswith("$number"):
            try:
                return float(doc[key])
            except:
                return doc
        if key == "$oid":
            return doc[key]
    
    return doc



class MongoDBHandler:
    """Handle MongoDB Atlas operations with robust error handling for automation"""
    
    def __init__(self):
        self.uri = os.getenv('MDB_URI')
        self.client = None
        self.db = None
        self.collection = None
        self.connected = False
        
        # Database and collection names
        self.db_name = 'lighthouse'
        self.collection_name = 'incidents'
    
    def connect(self, retry_count: int = 3, timeout_ms: int = 30000) -> bool:
        """
        Connect to MongoDB Atlas with retries and exponential backoff
        
        Args:
            retry_count: Number of connection attempts (default: 3)
            timeout_ms: Connection timeout in milliseconds (default: 30000 = 30s)
        
        Returns:
            True if connected, False otherwise (graceful failure)
        """
        if not self.uri:
            print("⚠️  MONGODB_URI not found in environment variables")
            print("   Skipping MongoDB upload (incidents.json still created)")
            return False
        
        print("Connecting to MongoDB Atlas...")
        
        for attempt in range(1, retry_count + 1):
            try:
                if attempt > 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 4s, 8s, 16s
                    print(f"   Retry {attempt}/{retry_count} (waiting {wait_time}s)...")
                    time.sleep(wait_time)
                
                # Create client with longer timeout
                self.client = MongoClient(
                    self.uri,
                    serverSelectionTimeoutMS=timeout_ms,
                    connectTimeoutMS=timeout_ms,
                    socketTimeoutMS=timeout_ms,
                    retryWrites=True,
                    retryReads=True
                )
                
                # Test connection
                self.client.admin.command('ping')
                
                # Get database and collection
                self.db = self.client[self.db_name]
                self.collection = self.db[self.collection_name]
                
                self.connected = True
                print(f"✓ Connected to MongoDB Atlas (attempt {attempt})")
                
                # Show current document count
                try:
                    count = self.collection.count_documents({})
                    print(f"✓ Current documents in collection: {count}")
                except:
                    pass  # Don't fail on count error
                
                return True
                
            except ServerSelectionTimeoutError:
                if attempt == retry_count:
                    print(f"⚠️  MongoDB connection timed out after {retry_count} attempts")
                    print(f"   This is OK - incidents.json was still created successfully")
                    print(f"   MongoDB will be updated on next successful run")
                    return False
                    
            except ConnectionFailure:
                if attempt == retry_count:
                    print(f"⚠️  MongoDB connection failed after {retry_count} attempts")
                    print(f"   This is OK - incidents.json was still created successfully")
                    return False
                    
            except Exception as e:
                if attempt == retry_count:
                    print(f"⚠️  MongoDB error: {str(e)[:100]}")
                    print(f"   This is OK - incidents.json was still created successfully")
                    return False
        
        return False
    
    def insert_incidents(self, incidents: List[Dict], replace_all: bool = False) -> Dict:
        """
        Insert or update incidents in MongoDB
        
        Returns stats even on failure (won't crash automation)
        """
        if not self.connected:
            return {
                'inserted': 0,
                'updated': 0,
                'failed': 0,
                'errors': ['MongoDB not connected - incidents.json still created']
            }
        
        stats = {
            'inserted': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            # Replace all if requested
            if replace_all:
                delete_result = self.collection.delete_many({})
                print(f"   Deleted {delete_result.deleted_count} existing incidents")
            
            # Insert or update each incident
            for incident in incidents:
                try:
                    incident_id = incident.get('id')
                    if not incident_id:
                        stats['failed'] += 1
                        continue
                    
                    # Update or insert
                    result = self.collection.update_one(
                        {'id': incident_id},
                        {'$set': incident},
                        upsert=True
                    )
                    
                    if result.upserted_id:
                        stats['inserted'] += 1
                    elif result.modified_count > 0:
                        stats['updated'] += 1
                    
                except Exception as e:
                    stats['failed'] += 1
                    if len(stats['errors']) < 5:  # Only keep first 5 errors
                        stats['errors'].append(str(e)[:100])
            
            return stats
            
        except Exception as e:
            print(f"⚠️  MongoDB bulk operation error: {str(e)[:100]}")
            print(f"   This is OK - incidents.json was still created successfully")
            stats['errors'].append(f"Bulk error: {str(e)[:100]}")
            return stats
    
    def get_all_incidents(self, limit: Optional[int] = None, active_only: bool = False) -> List[Dict]:
        """Get incidents from database, with optional filtering for only active ones"""
        if not self.connected:
            return []
        
        try:
            # Dynamically adjust query based on active_only flag
            query = {"status": "active"} if active_only else {}

            cursor = self.collection.find(query)

            if limit:
                cursor = cursor.limit(limit)

            incidents = [clean_mongo_doc(doc) for doc in cursor]
            return incidents
                    
        except Exception as e:
            print(f"Error fetching incidents: {str(e)}")
            return []


    def get_incident_by_id(self, incident_id: str) -> Optional[Dict]:
        """Get a specific incident by its ID"""
        if not self.connected:
            return None
        
        try:
            incident = self.collection.find_one({'id': incident_id})
            if incident:
                return clean_mongo_doc(incident)
            return None
        except Exception as e:
            print(f"Error fetching incident by ID: {str(e)}")
            return None


    def get_incidents_by_type(self, incident_type: str) -> List[Dict]:
        """Get all active incidents of a specific type (case-insensitive)"""
        if not self.connected:
            return []
        
        try:
            # Use case-insensitive regex to match incident type
            query = {
                'incident_type': {'$regex': f'^{incident_type}$', '$options': 'i'},
                'status': 'active'
            }
            incidents = self.collection.find(query)
            return [clean_mongo_doc(doc) for doc in incidents]
        except Exception as e:
            print(f"Error fetching incidents by type: {str(e)}")
            return []


    def get_incidents_in_radius(self, lat: float, lng: float, radius_km: float) -> List[Dict]:
        """
        Get all active incidents within a specified radius of a location
        Uses simple distance calculation (Haversine formula approximation)
        
        Args:
            lat: Latitude of center point
            lng: Longitude of center point
            radius_km: Search radius in kilometers
        
        Returns:
            List of incidents within the radius
        """
        if not self.connected:
            return []
        
        try:
            from math import radians, cos, sin, asin, sqrt
            
            def haversine(lon1, lat1, lon2, lat2):
                """Calculate the great circle distance between two points on Earth"""
                # Convert decimal degrees to radians
                lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                
                # Haversine formula
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                
                # Radius of earth in kilometers
                r = 6371
                return c * r
            
            # Get all active incidents
            all_incidents = self.collection.find({'status': 'active'})
            
            # Filter by distance
            nearby_incidents = []
            for incident in all_incidents:
                try:
                    incident_lat = incident.get('lat')
                    incident_lng = incident.get('lng')
                    
                    if incident_lat is not None and incident_lng is not None:
                        distance = haversine(lng, lat, incident_lng, incident_lat)
                        
                        if distance <= radius_km:
                            cleaned_incident = clean_mongo_doc(incident)
                            cleaned_incident['distance_km'] = round(distance, 2)
                            nearby_incidents.append(cleaned_incident)
                except Exception as e:
                    # Skip incidents with invalid coordinates
                    continue
            
            # Sort by distance (closest first)
            nearby_incidents.sort(key=lambda x: x.get('distance_km', float('inf')))
            
            return nearby_incidents
            
        except Exception as e:
            print(f"Error fetching nearby incidents: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        if not self.connected:
            return {
                'total_incidents': 0,
                'active_incidents': 0,
                'by_type': {}
            }
        
        try:
            total = self.collection.count_documents({})
            active = self.collection.count_documents({'status': 'active'})

            pipeline = [
                {'$group': {'_id': '$incident_type', 'count': {'$sum': 1}}}
            ]
            by_type_cursor = self.collection.aggregate(pipeline)
            by_type = clean_mongo_doc({item['_id']: item['count'] for item in by_type_cursor})

            return clean_mongo_doc({
                'total_incidents': total,
                'active_incidents': active,
                'by_type': by_type
            })

        except Exception:
            return {
                'total_incidents': 0,
                'active_incidents': 0,
                'by_type': {}
            }
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            try:
                self.client.close()
                self.connected = False
            except:
                pass  # Ignore errors on close


if __name__ == '__main__':
    print("Testing MongoDB connection...")
    handler = MongoDBHandler()
    
    if handler.connect():
        print("\n✅ Connection successful!")
        stats = handler.get_statistics()
        print(f"\nDatabase Statistics:")
        print(f"  Total incidents: {stats['total_incidents']}")
        print(f"  Active incidents: {stats['active_incidents']}")
        print(f"  By type: {stats['by_type']}")
        handler.close()
    else:
        print("\n⚠️  Connection failed - but this is OK for automation!")
        print("   incidents.json will still be created")