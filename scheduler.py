# scheduler.py
import asyncio
from typing import Optional
from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError
from database import db
import config
from utils.logger import logger
from utils.rss import check_site_updates, get_scraper_by_id
from utils.formatter import format_post_message, generate_post_buttons
import httpx

async def download_image(url: str, headers: dict) -> Optional[bytes]:
    if not url:
        return None
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.content
    except Exception as e:
        logger.error(f"Image download failure for {url}: {e}")
    return None

async def send_post_with_retry(app: Client, chat_id: int, text: str, reply_markup, photo: Optional[bytes]):
    while True:
        try:
            if photo:
                import io
                photo_file = io.BytesIO(photo)
                photo_file.name = "thumbnail.jpg"
                await app.send_photo(
                    chat_id=chat_id,
                    photo=photo_file,
                    caption=text,
                    reply_markup=reply_markup
                )
            else:
                await app.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    disable_web_page_preview=False
                )
            break
        except FloodWait as e:
            logger.warning(f"FloodWait rate limit. Waiting {e.value}s.")
            await asyncio.sleep(e.value)
        except RPCError as e:
            logger.error(f"Telegram RPC error delivering to chat {chat_id}: {e}")
            break
        except Exception as e:
            logger.error(f"Error publishing post message to {chat_id}: {e}")
            break

async def process_site_updates(app: Client, site_id: str):
    new_posts = await check_site_updates(site_id)
    if not new_posts:
        return

    site_info = await db.get_site(site_id)
    if not site_info:
        return

    site_name = site_info["name"]
    default_server_idx = site_info["default_server_index"]
    scraper = get_scraper_by_id(site_id, default_server_idx=default_server_idx)
    if not scraper:
        return

    try:
        channels = await db.get_channels_for_site(site_id)
        default_channel_str = await db.get_setting("default_channel")
        default_channel = int(default_channel_str) if default_channel_str else None

        all_target_channels = set(channels)
        if default_channel:
            all_target_channels.add(default_channel)

        if not all_target_channels:
            logger.warning(f"No publication channel targets bound to {site_name}.")
            return

        for post in reversed(new_posts):
            post_url = post["url"]
            if await db.is_duplicate(site_id, post_url):
                continue

            logger.info(f"Extracting metadata: [{site_name}] {post_url}")
            post_data = await scraper.get_post(post_url)
            if not post_data:
                logger.error(f"Metadata scrap failure for: {post_url}")
                continue

            post_data["site_name"] = site_name
            message_text = format_post_message(post_data)
            reply_markup = generate_post_buttons(post_url, post_data.get("selected_embed", ""))
            
            thumbnail_url = post_data.get("thumbnail")
            photo_bytes = None
            if thumbnail_url:
                photo_bytes = await download_image(thumbnail_url, scraper.headers)

            for channel in all_target_channels:
                await send_post_with_retry(app, channel, message_text, reply_markup, photo_bytes)
                await asyncio.sleep(1.0)

            await db.add_upload(site_id, post_url)
            await db.update_rss_state(site_id, post.get("guid"), post_url)
            await asyncio.sleep(2.0)
            
    except Exception as e:
        logger.error(f"Error processing updates for {site_id}: {e}")
    finally:
        await scraper.close()

async def scheduler_loop(app: Client):
    logger.info("Initializing task scheduler loop.")
    while True:
        try:
            interval_str = await db.get_setting("check_interval")
            interval = int(interval_str) if interval_str else config.DEFAULT_CHECK_INTERVAL
            logger.info(f"Checking updates. Sleep cycle: {interval} minutes.")
            
            sites = await db.get_sites()
            for site in sites:
                await process_site_updates(app, site["id"])
                await asyncio.sleep(5.0)

            await asyncio.sleep(interval * 60)
        except asyncio.CancelledError:
            logger.info("Scheduler task cancelled.")
            break
        except Exception as e:
            logger.error(f"Critical scheduler error: {e}")
            await asyncio.sleep(60)
