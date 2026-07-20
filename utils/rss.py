# utils/rss.py
from typing import List, Dict, Any, Optional
from database import db
from scrapers.myanime import MyAnimeScraper
from scrapers.luciferdonghua import LuciferDonghuaScraper
from scrapers.donghuastream import DonghuaStreamScraper
from scrapers.animexin import AnimeXinScraper
from scrapers.anime4i import Anime4iScraper
from utils.logger import logger

def get_scraper_by_id(site_id: str, default_server_idx: int = 0, site_url: str = "") -> Any:
    site_id = site_id.lower()
    site_url = site_url.lower() if site_url else ""
    
    # Exact mapping
    scrapers_map = {
        "myanime": MyAnimeScraper,
        "luciferdonghua": LuciferDonghuaScraper,
        "donghuastream": DonghuaStreamScraper,
        "animexin": AnimeXinScraper,
        "anime4i": Anime4iScraper
    }
    
    if site_id in scrapers_map:
        return scrapers_map[site_id](default_server_idx=default_server_idx)
        
    # Auto-matching by custom string patterns inside ID or URL
    if "myanime" in site_id or "myanime" in site_url:
        logger.info(f"Auto-mapped custom site {site_id} to MyAnimeScraper.")
        return MyAnimeScraper(default_server_idx=default_server_idx)
    elif "lucifer" in site_id or "lucifer" in site_url:
        logger.info(f"Auto-mapped custom site {site_id} to LuciferDonghuaScraper.")
        return LuciferDonghuaScraper(default_server_idx=default_server_idx)
    elif "donghua" in site_id or "donghua" in site_url:
        logger.info(f"Auto-mapped custom site {site_id} to DonghuaStreamScraper.")
        return DonghuaStreamScraper(default_server_idx=default_server_idx)
    elif "animexin" in site_id or "animexin" in site_url:
        logger.info(f"Auto-mapped custom site {site_id} to AnimeXinScraper.")
        return AnimeXinScraper(default_server_idx=default_server_idx)
    elif "anime4i" in site_id or "anime4i" in site_url:
        logger.info(f"Auto-mapped custom site {site_id} to Anime4iScraper.")
        return Anime4iScraper(default_server_idx=default_server_idx)
        
    # Standard fallback
    logger.warning(f"No direct scraper found for {site_id}. Falling back to default scraper.")
    return MyAnimeScraper(default_server_idx=default_server_idx)

async def check_site_updates(site_id: str) -> List[Dict[str, Any]]:
    site_info = await db.get_site(site_id)
    if not site_info:
        logger.error(f"Site metadata for {site_id} not registered.")
        return []

    default_server_idx = site_info.get("default_server_index", 0)
    scraper = get_scraper_by_id(site_id, default_server_idx=default_server_idx, site_url=site_info.get("url", ""))
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
