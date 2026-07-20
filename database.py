# database.py
import aiosqlite
from typing import List, Dict, Any, Optional
import config
from utils.logger import logger

class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path

    async def connect(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA foreign_keys=ON;")
            await db.commit()
            logger.info("Database connected in WAL mode.")

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sites (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    rss_url TEXT,
                    default_server_index INTEGER DEFAULT 0
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    channel_id INTEGER,
                    site_id TEXT,
                    PRIMARY KEY (channel_id, site_id),
                    FOREIGN KEY(site_id) REFERENCES sites(id) ON DELETE CASCADE
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS rss (
                    site_id TEXT PRIMARY KEY,
                    last_guid TEXT,
                    last_url TEXT,
                    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(site_id) REFERENCES sites(id) ON DELETE CASCADE
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_id TEXT,
                    post_url TEXT UNIQUE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS servers (
                    site_id TEXT,
                    server_name TEXT,
                    server_index INTEGER,
                    PRIMARY KEY (site_id, server_name),
                    FOREIGN KEY(site_id) REFERENCES sites(id) ON DELETE CASCADE
                )
            """)
            await db.commit()
            logger.info("Database schema initialized.")

    async def add_site(self, site_id: str, name: str, url: str, rss_url: str, default_server_idx: int = 0):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO sites (id, name, url, rss_url, default_server_index)
                VALUES (?, ?, ?, ?, ?)
            """, (site_id, name, url, rss_url, default_server_idx))
            await db.commit()

    async def remove_site(self, site_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM sites WHERE id = ?", (site_id,))
            await db.commit()

    async def get_sites(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM sites") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_site(self, site_id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM sites WHERE id = ?", (site_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def add_channel(self, channel_id: int, site_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO channels (channel_id, site_id)
                VALUES (?, ?)
            """, (channel_id, site_id))
            await db.commit()

    async def remove_channel(self, channel_id: int, site_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM channels WHERE channel_id = ? AND site_id = ?
            """, (channel_id, site_id))
            await db.commit()

    async def get_channels_for_site(self, site_id: str) -> List[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT channel_id FROM channels WHERE site_id = ?", (site_id,)) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_all_channel_mappings(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM channels") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def update_rss_state(self, site_id: str, last_guid: Optional[str], last_url: Optional[str]):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO rss (site_id, last_guid, last_url, last_checked)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (site_id, last_guid, last_url))
            await db.commit()

    async def get_rss_state(self, site_id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM rss WHERE site_id = ?", (site_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def is_duplicate(self, site_id: str, post_url: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT 1 FROM uploads WHERE site_id = ? AND post_url = ?
            """, (site_id, post_url)) as cursor:
                row = await cursor.fetchone()
                return row is not None

    async def add_upload(self, site_id: str, post_url: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO uploads (site_id, post_url)
                VALUES (?, ?)
            """, (site_id, post_url))
            await db.commit()

    async def set_setting(self, key: str, value: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            """, (key, value))
            await db.commit()

    async def get_setting(self, key: str) -> Optional[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def set_site_server(self, site_id: str, default_server_idx: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE sites SET default_server_index = ? WHERE id = ?
            """, (default_server_idx, site_id))
            await db.commit()

db = Database()
