"""
MongoDB Handler for LightHouse Incidents
=========================================
Handles connection and data insertion to MongoDB Atlas.
"""

from pymongo import MongoClient, GEOSPHERE
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()


class MongoDBHandler:
    """Handle MongoDB operations for incident storage"""
    
    def __init__(self, uri: Optional[str] = None):
        """
        Initialize MongoDB connection
        
        Args:
            uri: MongoDB connection string. If None, reads from MDB_URI environment variable
        """
        if uri is None:
            uri = os.getenv('MDB_URI')
        
        if not uri:
            raise ValueError(
                "MongoDB URI not provided. Either pass uri parameter or set MDB_URI environment variable"
            )
        
        self.uri = uri
        self.client = None
        self.db = None
        self.incidents_collection = None
        
    def connect(self) -> bool:
        """Establish connection to MongoDB"""
        try:
            # Debug: Check if URI is valid
            if not self.uri or self.uri.strip() == '':
                print("❌ Error: MongoDB URI is empty or None")
                print("   Make sure MDB_URI is set in your .env file")
                return False
            
            # Don't print the full URI for security, just confirm it's loaded
            print("Connecting to MongoDB Atlas...")
            print(f"✓ URI loaded (length: {len(self.uri)} characters)")
            
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.admin.command('ping')
            
            # Select database and collection
            self.db = self.client['lighthouse']
            self.incidents_collection = self.db['incidents']
            
            # Create indexes for better query performance
            self._create_indexes()
            
            print("✓ Connected to MongoDB Atlas")
            return True
            
        except ConnectionFailure as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            print(f"❌ MongoDB connection error: {e}")
            print(f"   Error type: {type(e).__name__}")
            return False
    
    def _create_indexes(self):
        """Create database indexes for optimized queries"""
        try:
            # Create geospatial index for location queries
            self.incidents_collection.create_index([("location_geo", GEOSPHERE)])
            
            # Create index for incident_type and severity for filtering
            self.incidents_collection.create_index("incident_type")
            self.incidents_collection.create_index("severity")
            self.incidents_collection.create_index("status")
            
            # Create unique index on incident ID to prevent duplicates
            self.incidents_collection.create_index("id", unique=True)
            
            # Create index on created_at for time-based queries
            self.incidents_collection.create_index("created_at")
            
            print("✓ Database indexes created")
        except Exception as e:
            print(f"Warning: Could not create indexes: {e}")
    
    def prepare_incident_for_mongodb(self, incident: Dict) -> Dict:
        """
        Convert incident to MongoDB-compatible format.
        Adds GeoJSON format for geospatial queries.
        """
        mongo_incident = incident.copy()
        
        # Add GeoJSON location for geospatial queries
        if 'lat' in incident and 'lng' in incident:
            mongo_incident['location_geo'] = {
                "type": "Point",
                "coordinates": [incident['lng'], incident['lat']]  # MongoDB uses [lng, lat]
            }
        
        # Ensure proper data types
        if 'confidence' in mongo_incident:
            mongo_incident['confidence'] = float(mongo_incident['confidence'])
        
        # Add metadata
        mongo_incident['updated_at'] = datetime.now().isoformat()
        
        return mongo_incident
    
    def insert_incidents(self, incidents: List[Dict], replace_all: bool = False) -> Dict:
        """
        Insert incidents into MongoDB.
        
        Args:
            incidents: List of incident dictionaries
            replace_all: If True, clear existing incidents before inserting
            
        Returns:
            Dictionary with insertion statistics
        """
        if self.incidents_collection is None:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        stats = {
            "total": len(incidents),
            "inserted": 0,
            "updated": 0,
            "failed": 0,
            "errors": []
        }
        
        # Optionally clear existing data
        if replace_all:
            deleted_count = self.incidents_collection.delete_many({}).deleted_count
            print(f"✓ Cleared {deleted_count} existing incidents")
        
        # Process each incident
        for incident in incidents:
            try:
                # Prepare incident for MongoDB
                mongo_incident = self.prepare_incident_for_mongodb(incident)
                
                # Use upsert to insert or update
                result = self.incidents_collection.update_one(
                    {"id": mongo_incident['id']},
                    {"$set": mongo_incident},
                    upsert=True
                )
                
                if result.upserted_id:
                    stats["inserted"] += 1
                elif result.modified_count > 0:
                    stats["updated"] += 1
                    
            except DuplicateKeyError:
                stats["failed"] += 1
                stats["errors"].append(f"Duplicate incident ID: {incident.get('id')}")
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(f"Error inserting {incident.get('id')}: {str(e)}")
        
        return stats
    
    def get_all_incidents(self, active_only: bool = True) -> List[Dict]:
        """Retrieve all incidents from MongoDB"""
        if self.incidents_collection is None:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        query = {"status": "active"} if active_only else {}
        
        incidents = list(self.incidents_collection.find(query, {"_id": 0}))
        return incidents
    
    def get_incidents_by_type(self, incident_type: str) -> List[Dict]:
        """Get incidents by disaster type"""
        if self.incidents_collection is None:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        incidents = list(self.incidents_collection.find(
            {"incident_type": incident_type, "status": "active"},
            {"_id": 0}
        ))
        return incidents
    
    def get_incidents_in_radius(self, lat: float, lng: float, radius_km: float) -> List[Dict]:
        """Get incidents within a radius (in kilometers) of a point"""
        if self.incidents_collection is None:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        incidents = list(self.incidents_collection.find({
            "location_geo": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    },
                    "$maxDistance": radius_km * 1000  # Convert km to meters
                }
            },
            "status": "active"
        }, {"_id": 0}))
        
        return incidents
    
    def update_incident_status(self, incident_id: str, new_status: str) -> bool:
        """Update the status of an incident"""
        if self.incidents_collection is None:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        result = self.incidents_collection.update_one(
            {"id": incident_id},
            {"$set": {
                "status": new_status,
                "updated_at": datetime.now().isoformat()
            }}
        )
        
        return result.modified_count > 0
    
    def delete_incident(self, incident_id: str) -> bool:
        """Delete an incident by ID"""
        if self.incidents_collection is None:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        result = self.incidents_collection.delete_one({"id": incident_id})
        return result.deleted_count > 0
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        if self.incidents_collection is None:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        total = self.incidents_collection.count_documents({})
        active = self.incidents_collection.count_documents({"status": "active"})
        
        # Count by type
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$incident_type", "count": {"$sum": 1}}}
        ]
        by_type = {doc["_id"]: doc["count"] for doc in self.incidents_collection.aggregate(pipeline)}
        
        # Count by severity
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
        ]
        by_severity = {doc["_id"]: doc["count"] for doc in self.incidents_collection.aggregate(pipeline)}
        
        return {
            "total_incidents": total,
            "active_incidents": active,
            "by_type": by_type,
            "by_severity": by_severity
        }
    
    def close(self):
        """Close MongoDB connection"""
        if self.client is not None:
            self.client.close()
            print("✓ MongoDB connection closed")


def test_connection():
    """Test MongoDB connection"""
    print("=" * 70)
    print("MongoDB Connection Test")
    print("=" * 70)
    print()
    
    # Check if MDB_URI is set
    uri = os.getenv('MDB_URI')
    if not uri:
        print("❌ ERROR: MDB_URI environment variable not set!")
        print()
        print("Please add to your .env file:")
        print("MDB_URI=mongodb+srv://username:password@cluster.xxx.mongodb.net/?appName=Cluster0")
        print()
        return False
    
    print(f"✓ Found MDB_URI in environment (length: {len(uri)} characters)")
    print()
    
    handler = MongoDBHandler()
    
    if handler.connect():
        print("\n✓ MongoDB connection test successful!")
        
        # Show current statistics
        try:
            stats = handler.get_statistics()
            print(f"\nCurrent database statistics:")
            print(f"  Total incidents: {stats['total_incidents']}")
            print(f"  Active incidents: {stats['active_incidents']}")
            if stats['by_type']:
                print(f"  By type: {stats['by_type']}")
            if stats['by_severity']:
                print(f"  By severity: {stats['by_severity']}")
        except Exception as e:
            print(f"Could not fetch statistics: {e}")
        
        handler.close()
        print()
        return True
    else:
        print("\n❌ MongoDB connection test failed!")
        print()
        print("Troubleshooting steps:")
        print("1. Check your .env file has: MDB_URI=your_connection_string")
        print("2. Make sure there are no extra spaces or quotes around the URI")
        print("3. Verify the URI format: mongodb+srv://user:pass@cluster.mongodb.net/...")
        print("4. Check if your IP is whitelisted in MongoDB Atlas")
        print()
        return False


if __name__ == "__main__":
    test_connection()