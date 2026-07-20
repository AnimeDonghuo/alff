# bot.py
import asyncio
import os
from pyrogram import Client, idle
import config
from database import db
from utils.logger import logger
from scheduler import scheduler_loop

# Import explicit programmatic bindings
from handlers.commands import register_command_handlers
from handlers.callback import register_callback_handlers

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

async def handle_health_check(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        await reader.read(1024)
    except Exception:
        pass

    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain\r\n"
        "Content-Length: 2\r\n"
        "Connection: close\r\n\r\n"
        "OK"
    )
    try:
        writer.write(response.encode("utf-8"))
        await writer.drain()
    except Exception:
        pass
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass

async def start_health_check_server():
    port = int(os.getenv("PORT", "8000"))
    try:
        server = await asyncio.start_server(handle_health_check, "0.0.0.0", port)
        logger.info(f"Health Check server active on port {port}")
        async with server:
            await server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start Health Check server: {e}")

class TelegramBot:
    def __init__(self):
        self.app = Client(
            "rss_bot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN
        )
        self.scheduler_task = None
        self.health_server_task = None

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
            else:
                # Dynamically update domain url if it's pointing to the old org.cn domain
                if "org.cn" in existing.get("url", ""):
                    await db.add_site(
                        site_id=site["id"],
                        name=site["name"],
                        url=site["url"],
                        rss_url=site["rss_url"]
                    )
                    logger.info(f"Updated domain mapping for: {site['name']}")

        # Register Handlers Programmatically
        register_command_handlers(self.app)
        register_callback_handlers(self.app)

        self.health_server_task = asyncio.create_task(start_health_check_server())

        await self.app.start()
        logger.info("Bot started successfully (Polling Mode with Programmatic Handlers).")

        self.scheduler_task = asyncio.create_task(scheduler_loop(self.app))
        await idle()

    async def stop(self):
        logger.info("Shutting down...")
        if self.scheduler_task:
            self.scheduler_task.cancel()
        if self.health_server_task:
            self.health_server_task.cancel()
        
        try:
            await self.app.stop(block=False)
        except Exception as e:
            logger.warning(f"Error while stopping Pyrogram client: {e}")
        logger.info("Bot execution terminated successfully.")

async def main():
    bot = TelegramBot()
    try:
        await bot.start()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
