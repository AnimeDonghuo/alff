# utils/rss.py
from typing import List, Dict, Any, Optional
from database import db
from scrapers.myanime import MyAnimeScraper
from scrapers.luciferdonghua import LuciferDonghuaScraper
from scrapers.donghuastream import DonghuaStreamScraper
from scrapers.animexin import AnimeXinScraper
from scrapers.anime4i import Anime4iScraper
from utils.logger import logger

def get_scraper_by_id(site_id: str, default_server_idx: int = 0):
    scrapers_map = {
        "myanime": MyAnimeScraper,
        "luciferdonghua": LuciferDonghuaScraper,
        "donghuastream": DonghuaStreamScraper,
        "animexin": AnimeXinScraper,
        "anime4i": Anime4iScraper
    }
    scraper_cls = scrapers_map.get(site_id)
    if scraper_cls:
        return scraper_cls(default_server_idx=default_server_idx)
    return None

async def check_site_updates(site_id: str) -> List[Dict[str, Any]]:
    site_info = await db.get_site(site_id)
    if not site_info:
        logger.error(f"Site metadata for {site_id} not registered.")
        return []

    default_server_idx = site_info.get("default_server_index", 0)
    scraper = get_scraper_by_id(site_id, default_server_idx=default_server_idx)
    if not scraper:
        logger.error(f"No scraper implementation registered for site: {site_id}")
        return []

    try:
        latest_posts = await scraper.get_latest()
        if not latest_posts:
            logger.info(f"No updates fetched for {site_id}.")
            return []

        new_posts = []
        for post in latest_posts:
            url = post["url"]
            is_dup = await db.is_duplicate(site_id, url)
            if not is_dup:
                new_posts.append(post)

        return new_posts
    except Exception as e:
        logger.error(f"Failed checking updates for {site_id}: {e}")
    finally:
        await scraper.close()

    return []
