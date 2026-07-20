# bot.py
import asyncio
from pyrogram import Client, idle
import config
from database import db
from utils.logger import logger
from scheduler import scheduler_loop

DEFAULT_SITES = [
    {
        "id": "myanime",
        "name": "Myanime.live",
        "url": "https://myanime.live",
        "rss_url": "https://myanime.live/feed/"
    },
    {
        "id": "luciferdonghua",
        "name": "Lucifer Donghua",
        "url": "https://luciferdonghua.com",
        "rss_url": "https://luciferdonghua.com/feed/"
    },
    {
        "id": "donghuastream",
        "name": "Donghuastream",
        "url": "https://donghuastream.org",
        "rss_url": "https://donghuastream.org/feed/"
    },
    {
        "id": "animexin",
        "name": "Animexin",
        "url": "https://animexin.dev",
        "rss_url": "https://animexin.dev/feed/"
    },
    {
        "id": "anime4i",
        "name": "Anime4i",
        "url": "https://anime4i.com",
        "rss_url": "https://anime4i.com/feed/"
    }
]

class TelegramBot:
    def __init__(self):
        self.app = Client(
            "rss_bot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            plugins=dict(root="handlers")
        )
        self.scheduler_task = None

    async def start(self):
        logger.info("Initializing RSS Automation Bot...")
        await db.connect()
        await db.init_db()

        for site in DEFAULT_SITES:
            existing = await db.get_site(site["id"])
            if not existing:
                await db.add_site(
                    site_id=site["id"],
                    name=site["name"],
                    url=site["url"],
                    rss_url=site["rss_url"]
                )
                logger.info(f"Registered default site: {site['name']}")

        await self.app.start()
        logger.info("Bot started successfully (Polling Mode).")

        self.scheduler_task = asyncio.create_task(scheduler_loop(self.app))
        await idle()

        logger.info("Shutting down...")
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        await self.app.stop()
        logger.info("Bot execution terminated successfully.")

if __name__ == "__main__":
    bot = TelegramBot()
    asyncio.run(bot.start())
