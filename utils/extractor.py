# utils/extractor.py
import re
import base64
import urllib.parse
from typing import List, Set
from selectolax.parser import HTMLParser

EMBED_PATTERNS = [
    re.compile(r"https?://(?:www\.)?dailymotion\.com/(?:embed/video/|video/)[a-zA-Z0-9]+"),
    re.compile(r"https?://(?:www\.)?rumble\.com/embed/[a-zA-Z0-9_.-]+"),
    re.compile(r"https?://(?:www\.)?filemoon\.(?:sx|org|com|net|co)/[e/]/[a-zA-Z0-9]+"),
    re.compile(r"https?://(?:www\.)?vidhide\.(?:to|com|net|org|co|cc|pro|vip|click|link)/[e/]/[a-zA-Z0-9]+"),
    re.compile(r"https?://(?:www\.)?yourupload\.com/embed/[a-zA-Z0-9]+"),
    re.compile(r"https?://(?:www\.)?streamwish\.(?:to|com|net|org|co|click)/[e/]/[a-zA-Z0-9]+"),
    re.compile(r"https?://(?:www\.)?ok\.ru/videoembed/\d+"),
    re.compile(r"https?://(?:www\.)?mp4upload\.com/embed-[a-zA-Z0-9]+"),
    re.compile(r"https?://(?:www\.)?voe\.sx/embed/[a-zA-Z0-9]+"),
    re.compile(r"https?://(?:www\.)?sendvid\.com/embed/[a-zA-Z0-9]+"),
    re.compile(r"https?://(?:www\.)?vidoza\.net/embed/[a-zA-Z0-9]+"),
    re.compile(r"https?://(?:www\.)?dood(?:stream)?\.(?:com|to|so|la|sh|ws|pm|wf|re|cx)/e/[a-zA-Z0-9]+"),
    re.compile(r"https?://(?:www\.)?mixdrop\.(?:co|to|ag|sx)/e/[a-zA-Z0-9]+"),
    re.compile(r"https?://(?:www\.)?streamtape\.com/e/[a-zA-Z0-9]+"),
    re.compile(r"https?://(?:www\.)?fembed\.com/v/[a-zA-Z0-9_-]+"),
    re.compile(r"https?://(?:www\.)?sibnet\.ru/video/embed/\d+")
]

GENERAL_URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)

def decode_base64_links(text: str) -> List[str]:
    links = []
    b64_matches = re.findall(r"(?:[A-Za-z0-9+/]{40,}(?:==| =)?)+", text)
    for match in b64_matches:
        try:
            decoded = base64.b64decode(match).decode("utf-8", errors="ignore")
            for url in GENERAL_URL_PATTERN.findall(decoded):
                links.append(url)
        except Exception:
            continue
    return links

def deobfuscate_packer(text: str) -> str:
    packer_match = re.search(r"eval\(function\(p,a,c,k,e,d\).+?split\('\|'\)\)\)", text, re.DOTALL)
    if not packer_match:
        return text
    try:
        args_match = re.search(r"}\((.+?)\)\s*$", text.strip(), re.DOTALL)
        if args_match:
            args_str = args_match.group(1)
            parts = re.findall(r"'(.*?)'", args_str)
            if len(parts) >= 2:
                payload = parts[0]
                keywords = parts[1].split("|")
                def replace_func(m):
                    word = m.group(0)
                    try:
                        val = int(word, 36)
                        if val < len(keywords) and keywords[val]:
                            return keywords[val]
                    except ValueError:
                        pass
                    return word
                return re.sub(r"\b[0-9a-zA-Z]+\b", replace_func, payload)
    except Exception:
        pass
    return text

def extract_embeds(html: str) -> List[str]:
    found_urls: Set[str] = set()
    parser = HTMLParser(html)
    
    for iframe in parser.css("iframe"):
        src = iframe.attributes.get("src")
        if src:
            found_urls.add(src)
        for attr, value in iframe.attributes.items():
            if value and ("http" in value or "embed" in value):
                found_urls.add(value)

    for elem in parser.css("[data-player], [data-src], [data-video], [data-link], [data-href]"):
        for attr in ["data-player", "data-src", "data-video", "data-link", "data-href"]:
            val = elem.attributes.get(attr)
            if val:
                if val.startswith("//"):
                    val = "https:" + val
                found_urls.add(val)

    for script in parser.css("script"):
        script_text = script.text()
        if not script_text:
            continue
        unpacked_js = deobfuscate_packer(script_text)
        for match in GENERAL_URL_PATTERN.findall(unpacked_js):
            found_urls.add(match)
        for b64_link in decode_base64_links(unpacked_js):
            found_urls.add(b64_link)

    for match in GENERAL_URL_PATTERN.findall(html):
        decoded_url = urllib.parse.unquote(match)
        found_urls.add(decoded_url)
        found_urls.add(match)

    cleaned_embeds: List[str] = []
    for url in found_urls:
        url = url.strip().strip("'\"\\><")
        if url.startswith("//"):
            url = "https:" + url
        
        for pattern in EMBED_PATTERNS:
            if pattern.search(url):
                cleaned_embeds.append(url)
                break
                
    unique_embeds: List[str] = []
    seen = set()
    for u in cleaned_embeds:
        if u not in seen:
            seen.add(u)
            unique_embeds.append(u)
            
    return unique_embeds
