# backend/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB configuration
MONGODB_URI = os.getenv('MONGODB_URI')
DATABASE_NAME = 'lighthouse'
COLLECTION_NAME = 'incidents'  # Your Atlas collection name

# Create async MongoDB client
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

async def get_collection():
    """Get the incidents collection"""
    return collection

async def init_db():
    """Initialize database and create indexes"""
    try:
        # Test connection
        await client.server_info()
        print(f"Connected to MongoDB Atlas")
        print(f"   Database: {DATABASE_NAME}")
        print(f"   Collection: {COLLECTION_NAME}")
        
        # Create indexes for better query performance
        await collection.create_index([("created_at", DESCENDING)])
        await collection.create_index([("incident_type", 1)])
        await collection.create_index([("status", 1)])
        
        # Count documents
        count = await collection.count_documents({})
        print(f"   Total documents: {count}\n")
        
    except Exception as e:
        print(f"MongoDB connection error: {e}\n")

async def close_db():
    """Close database connection"""
    client.close()
    print("MongoDB connection closed")