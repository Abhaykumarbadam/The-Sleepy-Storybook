"""
MongoDB Connection and Helper Functions
Handles database operations for the Bedtime Story app
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from typing import List, Optional
import os
import ssl
import certifi
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class MongoDB:
    def __init__(self):
        """Initialize MongoDB connection with SSL workaround"""
        self.connection_string = os.getenv("MONGODB_URI")
        if not self.connection_string:
            raise ValueError("MONGODB_URI not found in environment variables")
        
        self.client = None
        self.db = None
        self.stories = None
        self.connected = False
        
        try:
            # Create SSL context that bypasses certificate verification
            print("Connecting to MongoDB Atlas...")
            
            # Create custom SSL context to bypass certificate validation
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Create client with custom SSL context
            self.client = MongoClient(
                self.connection_string,
                tls=True,
                tlsAllowInvalidCertificates=True,
                tlsAllowInvalidHostnames=True,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=20000,
                socketTimeoutMS=20000
            )
            
            # Test the connection
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB!")
            self.connected = True
            
            # Get database and collection
            self.db = self.client.bedtime_stories
            self.stories = self.db.stories
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            print("\n⚠️  Windows SSL/TLS compatibility issue detected!")
            print("App will run WITHOUT database persistence")
            print("Stories will NOT be saved, but generation will work!")
            print("\n🔧 To fix MongoDB connection:")
            print("   1. Use MongoDB Compass (supports Windows SSL)")
            print("   2. Or run app in WSL/Linux/Mac")
            print("   3. Or use local MongoDB without SSL\n")
            # Don't raise - allow app to continue without database
            self.connected = False
    
    def save_story(self, story: dict) -> dict:
        """
        Save a story to MongoDB
        
        Args:
            story: Dictionary containing story data
            
        Returns:
            The saved story with MongoDB _id
        """
        if not self.connected:
            print("MongoDB not connected - story not saved")
            return story
            
        try:
            # Add timestamp if not present
            if "created_at" not in story:
                story["created_at"] = datetime.utcnow().isoformat()
            
            # Insert into MongoDB
            result = self.stories.insert_one(story)
            story["_id"] = str(result.inserted_id)
            
            print(f"Story saved with ID: {story['_id']}")
            return story
            
        except OperationFailure as e:
            print(f"❌ Failed to save story: {e}")
            raise
    
    def get_all_stories(self, session_id: Optional[str] = None) -> List[dict]:
        """
        Get all stories from MongoDB
        
        Returns:
            List of all stories
        """
        if not self.connected:
            print("MongoDB not connected - returning empty list")
            return []
            
        try:
            query = {"session_id": session_id} if session_id else {}
            stories = list(self.stories.find(query).sort("created_at", -1))
            
            # Convert ObjectId to string for JSON serialization
            for story in stories:
                story["_id"] = str(story["_id"])
            
            print(f"Retrieved {len(stories)} stories")
            return stories
            
        except OperationFailure as e:
            print(f"❌ Failed to retrieve stories: {e}")
            return []
    
    def get_story_by_id(self, story_id: str) -> Optional[dict]:
        """
        Get a specific story by ID
        
        Args:
            story_id: The story ID
            
        Returns:
            The story or None if not found
        """
        if not self.connected:
            print("⚠️  MongoDB not connected - cannot retrieve story")
            return None
            
        try:
            from bson.objectid import ObjectId
            story = self.stories.find_one({"_id": ObjectId(story_id)})
            
            if story:
                story["_id"] = str(story["_id"])
                return story
            return None
            
        except Exception as e:
            print(f"❌ Failed to get story: {e}")
            return None
    
    def delete_story(self, story_id: str) -> bool:
        """
        Delete a story by ID
        
        Args:
            story_id: The story ID
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.connected:
            print("⚠️  MongoDB not connected - cannot delete story")
            return False
            
        try:
            from bson.objectid import ObjectId
            result = self.stories.delete_one({"_id": ObjectId(story_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"❌ Failed to delete story: {e}")
            return False
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")

# Create a singleton instance
mongodb = MongoDB()
