# scrapers/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
from selectolax.parser import HTMLParser
from utils.logger import logger

class BaseScraper(ABC):
    def __init__(self, site_id: str, base_url: str, default_server_idx: int = 0):
        self.site_id = site_id
        self.base_url = base_url
        self.default_server_idx = default_server_idx
        
        # High-fidelity realistic browser headers to pass CDN protections
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        
        # http2=True is enabled to support connection negotiations with modern CDNs
        self.client = httpx.AsyncClient(
            headers=self.headers, 
            follow_redirects=True, 
            timeout=15.0,
            http2=True
        )

    async def fetch_html(self, url: str) -> Optional[str]:
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                return response.text
            logger.warning(f"Failed to fetch {url}. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error requesting html from {url}: {e}")
        return None

    async def scrape_latest_html(self, url: str) -> List[Dict[str, Any]]:
        """
        Universal fallback HTML scraper. If RSS feeds are blocked or down,
        this will crawl the homepage and extract posts.
        """
        html = await self.fetch_html(url)
        posts = []
        if not html:
            return posts
            
        parser = HTMLParser(html)
        seen_urls = set()
        
        # Reusable listing selectors across all target sites
        selectors = [
            ".listupd a",
            ".list-update a",
            "article h2 a",
            "article h3 a",
            ".post-item a",
            ".post-title a",
            ".entry-title a",
            ".bs a",
            "a[href*='/episode/']",
            "a[href*='/ep/']"
        ]
        
        for selector in selectors:
            for element in parser.css(selector):
                href = element.attributes.get("href")
                title = element.text(strip=True) or element.attributes.get("title")
                if href and title and href.startswith("http") and href not in seen_urls:
                    # Filter out non-episode or static page links to ensure we only scrape actual posts
                    if any(exclude in href for exclude in ["/genre/", "/series/", "/author/", "/tag/", "/category/", "/contact", "/about"]):
                        continue
                    seen_urls.add(href)
                    posts.append({
                        "title": title,
                        "url": href,
                        "guid": href,
                        "pub_date": ""
                    })
        return posts

    @abstractmethod
    async def get_latest(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_post(self, url: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_embed_links(self, parser: HTMLParser, html: str) -> List[str]:
        pass

    @abstractmethod
    def get_thumbnail(self, parser: HTMLParser) -> Optional[str]:
        pass

    @abstractmethod
    def get_description(self, parser: HTMLParser) -> str:
        pass

    @abstractmethod
    def get_episode(self, parser: HTMLParser, title: str) -> str:
        pass

    @abstractmethod
    def get_servers(self, parser: HTMLParser) -> List[Dict[str, Any]]:
        pass

    async def close(self):
        await self.client.aclose()
