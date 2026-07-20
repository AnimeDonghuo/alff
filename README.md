# README.md
# Telegram RSS Automation Bot

A production-ready, highly resource-efficient RSS & scraping automated Telegram bot designed specifically to run seamlessly on the Koyeb Free Tier with a RAM usage footprint below 250MB.

## Tech Stack & Architecture
- **Runtime**: Python 3.12
- **Telegram Framework**: Pyrogram
- **Asynchronous Engine**: Asyncio & HTTPX
- **High-Performance Parser**: Selectolax (Lxml-equivalent high-speed engine)
- **Feeds**: Feedparser
- **Storage**: SQLite with Write-Ahead Logging (WAL) Mode enabled for transactional isolation and speed.

## How to Configure
Setup the environment variables:
- `BOT_TOKEN`: Telegram bot token from @BotFather.
- `API_ID`: Telegram API App ID.
- `API_HASH`: Telegram API Hash.
- `OWNER_ID`: Numeric Telegram user ID of the bot owner.
- `CHECK_INTERVAL`: RSS checks frequency in minutes (defaults to 15).

## Commands Available for Owner
- `/sites`: Displays registered crawlers.
- `/addsite <id> <name> <url> <rss_url>`: Registers a new custom domain.
- `/removesite <id>`: Unregisters a domain.
- `/channels`: Displays active channel rules.
- `/addchannel <channel_id> <site_id>`: Rules to broadcast postings.
- `/removechannel <channel_id> <site_id>`: Removes broadcast mapping.
- `/defaultchannel <channel_id>`: Sets default broadcast channel.
- `/setserver <site_id> <server_idx>`: Sets fallback/preferred video stream player priority.
- `/setinterval <minutes>`: Dynamically adjusts schedule loop interval.
- `/status`: Runtime statistics.
- `/reload`: Forces manual reload checks across crawlers.
- `/help`: Detailed configuration guide.
