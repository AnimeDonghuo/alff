# scrapers/myanime.py
from scrapers.base import BaseScraper
from selectolax.parser import HTMLParser
from typing import List, Dict, Any, Optional
import feedparser
import re
from utils.extractor import extract_embeds
from utils.logger import logger

class MyAnimeScraper(BaseScraper):
    def __init__(self, default_server_idx: int = 0):
        super().__init__("myanime", "https://myanime.live", default_server_idx)

    async def get_latest(self) -> List[Dict[str, Any]]:
        posts = []
        rss_url = f"{self.base_url}/feed/"
        try:
            resp = await self.client.get(rss_url)
            if resp.status_code == 200:
                feed = feedparser.parse(resp.text)
                for entry in feed.entries:
                    posts.append({
                        "title": entry.title,
                        "url": entry.link,
                        "guid": getattr(entry, "id", entry.link),
                        "pub_date": getattr(entry, "published", "")
                    })
        except Exception as e:
            logger.error(f"Error fetching RSS for MyAnime: {e}")

        if not posts:
            html = await self.fetch_html(self.base_url)
            if html:
                parser = HTMLParser(html)
                for a in parser.css("article h2 a, .post-title a, a.post-link"):
                    title = a.text(strip=True)
                    url = a.attributes.get("href")
                    if title and url:
                        posts.append({
                            "title": title,
                            "url": url,
                            "guid": url,
                            "pub_date": ""
                        })
        return posts

    async def get_post(self, url: str) -> Optional[Dict[str, Any]]:
        html = await self.fetch_html(url)
        if not html:
            return None
        
        parser = HTMLParser(html)
        title_elem = parser.css_first("h1.entry-title, h1.post-title, h1")
        title = title_elem.text(strip=True) if title_elem else "Unknown Title"
        
        embeds = self.get_embed_links(parser, html)
        servers = self.get_servers(parser)
        
        if not servers and embeds:
            for i, embed in enumerate(embeds):
                servers.append({"name": f"Server {i+1}", "url": embed})

        selected_embed = ""
        if servers:
            idx = min(self.default_server_idx, len(servers) - 1)
            selected_embed = servers[idx]["url"]

        return {
            "title": title,
            "episode": self.get_episode(parser, title),
            "thumbnail": self.get_thumbnail(parser),
            "description": self.get_description(parser),
            "post_url": url,
            "pub_date": "",
            "embeds": embeds,
            "servers": servers,
            "selected_embed": selected_embed,
            "download_links": self.get_download_links(parser),
            "subtitle": "English",
            "quality": "1080p"
        }

    def get_embed_links(self, parser: HTMLParser, html: str) -> List[str]:
        return extract_embeds(html)

    def get_thumbnail(self, parser: HTMLParser) -> Optional[str]:
        meta_og = parser.css_first("meta[property='og:image']")
        if meta_og:
            return meta_og.attributes.get("content")
        img = parser.css_first("article img, .post-thumbnail img, .entry-content img")
        if img:
            return img.attributes.get("src")
        return None

    def get_description(self, parser: HTMLParser) -> str:
        meta_desc = parser.css_first("meta[name='description'], meta[property='og:description']")
        if meta_desc:
            return meta_desc.attributes.get("content", "")
        content = parser.css_first(".entry-content, .post-content")
        if content:
            p = content.css_first("p")
            if p:
                return p.text(strip=True)
        return ""

    def get_episode(self, parser: HTMLParser, title: str) -> str:
        match = re.search(r"(?:Episode|Ep)\s*(\d+)", title, re.IGNORECASE)
        if match:
            return match.group(1)
        match2 = re.search(r"\b(\d+)\b(?!.*\b\d+\b)", title)
        if match2:
            return match2.group(1)
        return "1"

    def get_servers(self, parser: HTMLParser) -> List[Dict[str, Any]]:
        servers = []
        for btn in parser.css(".player-option, .server-option, .play-opt, option"):
            name = btn.text(strip=True)
            url = btn.attributes.get("data-src") or btn.attributes.get("data-post") or btn.attributes.get("value")
            if name and url and ("http" in url or url.startswith("//")):
                servers.append({"name": name, "url": url})
        return servers

    def get_download_links(self, parser: HTMLParser) -> List[Dict[str, str]]:
        downloads = []
        for a in parser.css("a[href*='drive.google.com'], a[href*='mega.nz'], a[href*='mediafire.com'], .download-link"):
            url = a.attributes.get("href")
            name = a.text(strip=True) or "Download Link"
            if url:
                downloads.append({"name": name, "url": url})
        return downloads
