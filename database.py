# database.py
import motor.motor_asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import config
from utils.logger import logger

class Database:
    def __init__(self, uri: str = config.MONGO_URI):
        self.uri = uri
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db: Any = None

    async def connect(self):
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.uri)
            # Auto-resolves database name from the connection URI string
            self.db = self.client.get_default_database()
            logger.info("Database connection successfully established with MongoDB Atlas.")
        except Exception as e:
            logger.critical(f"Failed to connect to MongoDB engine: {e}")

    async def init_db(self):
        try:
            await self.db.uploads.create_index([("site_id", 1), ("post_url", 1)], unique=True)
            await self.db.channels.create_index([("channel_id", 1), ("site_id", 1)], unique=True)
            logger.info("Database unique constraints initialized.")
        except Exception as e:
            logger.warning(f"Indices setup skipped/completed: {e}")

    def _map_site(self, doc: dict) -> dict:
        return {
            "id": doc["_id"],
            "name": doc["name"],
            "url": doc["url"],
            "rss_url": doc["rss_url"],
            "default_server_index": doc.get("default_server_index", 0)
        }

    async def add_site(self, site_id: str, name: str, url: str, rss_url: str, default_server_index: int = 0):
        await self.db.sites.update_one(
            {"_id": site_id},
            {"$set": {
                "name": name,
                "url": url,
                "rss_url": rss_url,
                "default_server_index": default_server_index
            }},
            upsert=True
        )

    async def remove_site(self, site_id: str):
        await self.db.sites.delete_one({"_id": site_id})

    async def get_sites(self) -> List[Dict[str, Any]]:
        cursor = self.db.sites.find()
        return [self._map_site(doc) async for doc in cursor]

    async def get_site(self, site_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.db.sites.find_one({"_id": site_id})
        return self._map_site(doc) if doc else None

    async def add_channel(self, channel_id: int, site_id: str):
        await self.db.channels.update_one(
            {"channel_id": channel_id, "site_id": site_id},
            {"$set": {"channel_id": channel_id, "site_id": site_id}},
            upsert=True
        )

    async def remove_channel(self, channel_id: int, site_id: str):
        await self.db.channels.delete_one({"channel_id": channel_id, "site_id": site_id})

    async def get_channels_for_site(self, site_id: str) -> List[int]:
        cursor = self.db.channels.find({"site_id": site_id})
        return [doc["channel_id"] async for doc in cursor]

    async def get_all_channel_mappings(self) -> List[Dict[str, Any]]:
        cursor = self.db.channels.find()
        return [{"channel_id": doc["channel_id"], "site_id": doc["site_id"]} async for doc in cursor]

    async def update_rss_state(self, site_id: str, last_guid: Optional[str], last_url: Optional[str]):
        await self.db.rss.update_one(
            {"_id": site_id},
            {"$set": {
                "last_guid": last_guid,
                "last_url": last_url,
                "last_checked": datetime.now()
            }},
            upsert=True
        )

    async def get_rss_state(self, site_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.db.rss.find_one({"_id": site_id})
        if doc:
            return {
                "site_id": doc["_id"],
                "last_guid": doc.get("last_guid"),
                "last_url": doc.get("last_url")
            }
        return None

    async def is_duplicate(self, site_id: str, post_url: str) -> bool:
        doc = await self.db.uploads.find_one({"site_id": site_id, "post_url": post_url})
        return doc is not None

    async def add_upload(self, site_id: str, post_url: str):
        try:
            await self.db.uploads.insert_one({
                "site_id": site_id,
                "post_url": post_url,
                "timestamp": datetime.now()
            })
        except Exception:
            pass

    async def set_setting(self, key: str, value: str):
        await self.db.settings.update_one(
            {"_id": key},
            {"$set": {"value": value}},
            upsert=True
        )

    async def get_setting(self, key: str) -> Optional[str]:
        doc = await self.db.settings.find_one({"_id": key})
        return doc["value"] if doc else None

    async def set_site_server(self, site_id: str, default_server_idx: int):
        await self.db.sites.update_one(
            {"_id": site_id},
            {"$set": {"default_server_index": default_server_idx}}
        )

    async def get_uploads_count(self) -> int:
        return await self.db.uploads.count_documents({})

    async def get_channels_count(self) -> int:
        return await self.db.channels.count_documents({})

db = Database()
