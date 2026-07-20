# utils/formatter.py
import html
from datetime import datetime
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def escape_html(text: str) -> str:
    if not text:
        return ""
    return html.escape(text)

def format_post_message(post_data: dict) -> str:
    title = escape_html(post_data.get("title", "Unknown Post Title"))
    website = escape_html(post_data.get("site_name", "Web Portal"))
    episode = escape_html(post_data.get("episode", "1"))
    post_url = post_data.get("post_url", "")
    embed_url = post_data.get("selected_embed", "")
    subtitle = escape_html(post_data.get("subtitle", "English"))
    quality = escape_html(post_data.get("quality", "1080p"))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    message = (
        f"<b>🎬 {title}</b>\n\n"
        f"<b>🌐 Website:</b> {website}\n"
        f"<b>💿 Episode:</b> {episode}\n"
        f"<b>📝 Original Post:</b> <a href='{post_url}'>Link</a>\n"
        f"<b>🔗 Embed Link:</b> " + (f"<a href='{embed_url}'>Watch Player</a>" if embed_url else "N/A") + "\n"
        f"<b>💬 Subtitle:</b> {subtitle}\n"
        f"<b>📺 Quality:</b> {quality}\n"
        f"<b>⏰ Timestamp:</b> {timestamp}"
    )
    return message

def generate_post_buttons(post_url: str, embed_url: str) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    if post_url:
        row.append(InlineKeyboardButton("Original Post 🌐", url=post_url))
    if embed_url:
        row.append(InlineKeyboardButton("Watch Player 🎬", url=embed_url))
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)
