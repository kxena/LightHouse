from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MDB_URI")

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    print("Attempting connection...")
    client.server_info()  # Forces a real connection attempt
    print("Connected successfully!")
except Exception as e:
    print("MongoDB connection error:")
    print(e)  # FULL error message
