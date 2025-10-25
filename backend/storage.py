"""
JSON File Storage for The Sleepy Storybook
Simple file-based storage for stories and conversations
"""

import json
import os
from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path
import uuid

class JSONStorage:
    def __init__(self, storage_dir: str = "data"):
        """
        Initialize JSON storage
        
        Args:
            storage_dir: Directory to store JSON files (default: 'data')
        """
        self.storage_dir = Path(__file__).parent / storage_dir
        self.stories_file = self.storage_dir / "stories.json"
        self.conversations_file = self.storage_dir / "conversations.json"
        self.connected = False
        
        try:
            # Create storage directory if it doesn't exist
            self.storage_dir.mkdir(exist_ok=True)
            
            # Initialize JSON files if they don't exist
            self._init_file(self.stories_file)
            self._init_file(self.conversations_file)
            
            self.connected = True
            print(f"✅ JSON Storage initialized at: {self.storage_dir}")
            
        except Exception as e:
            print(f"❌ Failed to initialize storage: {e}")
            self.connected = False
    
    def _init_file(self, filepath: Path):
        """Initialize a JSON file if it doesn't exist"""
        if not filepath.exists():
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def _read_file(self, filepath: Path) -> List[Dict]:
        """Read data from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _write_file(self, filepath: Path, data: List[Dict]):
        """Write data to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    # ==================== STORY OPERATIONS ====================
    
    def save_story(self, story: Dict) -> Dict:
        """
        Save a story to JSON storage
        
        Args:
            story: Dictionary containing story data
            
        Returns:
            The saved story with _id
        """
        if not self.connected:
            print("⚠️  Storage not connected - story not saved")
            return story
        
        try:
            stories = self._read_file(self.stories_file)
            
            # Add metadata
            if "_id" not in story:
                story["_id"] = str(uuid.uuid4())
            if "created_at" not in story:
                story["created_at"] = datetime.utcnow().isoformat()
            
            # Append and save
            stories.append(story)
            self._write_file(self.stories_file, stories)
            
            print(f"✅ Story saved with ID: {story['_id']}")
            return story
            
        except Exception as e:
            print(f"❌ Failed to save story: {e}")
            return story
    
    def get_all_stories(self, session_id: Optional[str] = None) -> List[Dict]:
        """
        Get all stories from storage
        
        Args:
            session_id: Optional session ID to filter by
            
        Returns:
            List of stories
        """
        if not self.connected:
            print("⚠️  Storage not connected - returning empty list")
            return []
        
        try:
            stories = self._read_file(self.stories_file)
            
            # Filter by session_id if provided
            if session_id:
                stories = [s for s in stories if s.get("session_id") == session_id]
            
            # Sort by created_at (newest first)
            stories.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            print(f"✅ Retrieved {len(stories)} stories")
            return stories
            
        except Exception as e:
            print(f"❌ Failed to retrieve stories: {e}")
            return []
    
    def get_story_by_id(self, story_id: str) -> Optional[Dict]:
        """
        Get a specific story by ID
        
        Args:
            story_id: The story ID
            
        Returns:
            The story or None if not found
        """
        if not self.connected:
            print("⚠️  Storage not connected - cannot retrieve story")
            return None
        
        try:
            stories = self._read_file(self.stories_file)
            
            for story in stories:
                if story.get("_id") == story_id:
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
            print("⚠️  Storage not connected - cannot delete story")
            return False
        
        try:
            stories = self._read_file(self.stories_file)
            
            # Filter out the story to delete
            original_count = len(stories)
            stories = [s for s in stories if s.get("_id") != story_id]
            
            if len(stories) < original_count:
                self._write_file(self.stories_file, stories)
                print(f"✅ Story {story_id} deleted")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Failed to delete story: {e}")
            return False
    
    # ==================== CONVERSATION OPERATIONS ====================
    
    def save_conversation(self, session_id: str, messages: List[Dict], user_name: Optional[str] = None) -> bool:
        """
        Save or update a conversation
        
        Args:
            session_id: Unique session identifier
            messages: List of message dictionaries
            user_name: Optional user name
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("⚠️  Storage not connected - conversation not saved")
            return False
        
        try:
            conversations = self._read_file(self.conversations_file)
            
            # Find existing conversation or create new
            conversation = None
            for i, conv in enumerate(conversations):
                if conv.get("session_id") == session_id:
                    conversation = conv
                    conversation_index = i
                    break
            
            if conversation:
                # Update existing
                conversation["messages"] = messages
                conversation["updated_at"] = datetime.utcnow().isoformat()
                if user_name:
                    conversation["user_name"] = user_name
                conversations[conversation_index] = conversation
                action = "updated"
            else:
                # Create new
                conversation = {
                    "_id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "messages": messages,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                if user_name:
                    conversation["user_name"] = user_name
                conversations.append(conversation)
                action = "created"
            
            self._write_file(self.conversations_file, conversations)
            print(f"✅ Conversation {action} for session: {session_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save conversation: {e}")
            return False
    
    def get_conversation(self, session_id: str) -> Optional[Dict]:
        """
        Get a conversation by session ID
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Conversation dict or None
        """
        if not self.connected:
            print("⚠️  Storage not connected - cannot retrieve conversation")
            return None
        
        try:
            conversations = self._read_file(self.conversations_file)
            
            for conv in conversations:
                if conv.get("session_id") == session_id:
                    return conv
            
            return None
            
        except Exception as e:
            print(f"❌ Failed to get conversation: {e}")
            return None
    
    def get_all_conversations(self) -> List[Dict]:
        """
        Get all conversations
        
        Returns:
            List of all conversations
        """
        if not self.connected:
            print("⚠️  Storage not connected - returning empty list")
            return []
        
        try:
            conversations = self._read_file(self.conversations_file)
            conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return conversations
        except Exception as e:
            print(f"❌ Failed to get conversations: {e}")
            return []
    
    def delete_conversation(self, session_id: str) -> bool:
        """
        Delete a conversation by session ID
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.connected:
            print("⚠️  Storage not connected - cannot delete conversation")
            return False
        
        try:
            conversations = self._read_file(self.conversations_file)
            
            original_count = len(conversations)
            conversations = [c for c in conversations if c.get("session_id") != session_id]
            
            if len(conversations) < original_count:
                self._write_file(self.conversations_file, conversations)
                print(f"✅ Conversation {session_id} deleted")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Failed to delete conversation: {e}")
            return False
    
    # ==================== UTILITY OPERATIONS ====================
    
    def health_check(self) -> Dict:
        """
        Check storage health
        
        Returns:
            Dict with storage status and details
        """
        if not self.connected:
            return {
                "connected": False,
                "status": "disconnected",
                "message": "Storage not connected"
            }
        
        try:
            stories = self._read_file(self.stories_file)
            conversations = self._read_file(self.conversations_file)
            
            return {
                "connected": True,
                "status": "healthy",
                "storage_type": "JSON File Storage",
                "storage_dir": str(self.storage_dir),
                "counts": {
                    "stories": len(stories),
                    "conversations": len(conversations)
                },
                "files": {
                    "stories": str(self.stories_file),
                    "conversations": str(self.conversations_file)
                }
            }
        except Exception as e:
            return {
                "connected": False,
                "status": "error",
                "error": str(e)
            }
    
    def clear_all_data(self) -> bool:
        """
        Clear all data (USE WITH CAUTION!)
        
        Returns:
            True if successful
        """
        try:
            self._write_file(self.stories_file, [])
            self._write_file(self.conversations_file, [])
            print("✅ All data cleared")
            return True
        except Exception as e:
            print(f"❌ Failed to clear data: {e}")
            return False
    
    def close(self):
        """Close storage (no-op for JSON storage)"""
        self.connected = False
        print("✅ JSON Storage closed")


# Create a singleton instance
storage = JSONStorage()
