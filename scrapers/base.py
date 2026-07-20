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
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.client = httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=15.0)

    async def fetch_html(self, url: str) -> Optional[str]:
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                return response.text
            logger.warning(f"Failed to fetch {url}. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error requesting html from {url}: {e}")
        return None

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
