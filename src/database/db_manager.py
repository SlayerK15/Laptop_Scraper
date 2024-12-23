# src/database/db_manager.py

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
from ..utils.config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME

class DatabaseManager:
    def __init__(self, connection_string: str = MONGODB_URI):
        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        self.logger = logging.getLogger('DatabaseManager')
        
    async def save_raw_data(self, url: str, html_content: str, metadata: Dict[str, Any]) -> bool:
        """Save raw HTML content with metadata to MongoDB."""
        try:
            result = await self.collection.update_one(
                {"url": url},
                {
                    "$set": {
                        "html_content": html_content,
                        "metadata": metadata,
                        "last_updated": datetime.utcnow()
                    }
                },
                upsert=True
            )
            return bool(result.acknowledged)
            
        except Exception as e:
            self.logger.error(f"Error saving data for {url}: {str(e)}")
            return False
            
    async def get_raw_data(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieve raw data for a specific URL."""
        try:
            return await self.collection.find_one({"url": url})
        except Exception as e:
            self.logger.error(f"Error retrieving data for {url}: {str(e)}")
            return None
            
    async def cleanup_old_data(self, days: int = 30) -> int:
        """Remove data older than specified days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = await self.collection.delete_many({
                "last_updated": {"$lt": cutoff_date}
            })
            return result.deleted_count
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {str(e)}")
            return 0

    async def get_all_urls(self) -> list:
        """Get all URLs in the database."""
        try:
            cursor = self.collection.find({}, {"url": 1})
            return [doc["url"] async for doc in cursor]
        except Exception as e:
            self.logger.error(f"Error retrieving URLs: {str(e)}")
            return []

    async def close(self):
        """Close database connection."""
        self.client.close()