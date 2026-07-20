# handlers/commands.py
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
import config
from database import db
from utils.logger import logger
import asyncio

async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        "👋 Welcome to the <b>Telegram RSS Automation Bot</b>!\n\n"
        "Use /help to view all available settings and control commands."
    )

async def help_cmd(client: Client, message: Message):
    help_text = (
        "⚙️ <b>Settings Commands:</b>\n\n"
        "👉 <code>/sites</code> - List registered website scrapers\n"
        "👉 <code>/addsite &lt;id&gt; &lt;name&gt; &lt;url&gt; &lt;rss_url&gt;</code> - Add/Update site\n"
        "👉 <code>/removesite &lt;id&gt;</code> - Remove a site scraper\n\n"
        "👉 <code>/channels</code> - List channel-site mappings\n"
        "👉 <code>/addchannel &lt;channel_id&gt; &lt;site_id&gt;</code> - Map channel to site\n"
        "👉 <code>/removechannel &lt;channel_id&gt; &lt;site_id&gt;</code> - Remove mapping\n\n"
        "👉 <code>/defaultchannel &lt;channel_id&gt;</code> - Define default channel (0 to disable)\n"
        "👉 <code>/setserver &lt;site_id&gt; &lt;server_index&gt;</code> - Change default server index\n"
        "👉 <code>/setinterval &lt;minutes&gt;</code> - Update loop interval\n"
        "👉 <code>/status</code> - Current runtime metrics\n"
        "👉 <code>/reload</code> - Run immediate check on all sites\n"
    )
    await message.reply_text(help_text)

async def add_site_cmd(client: Client, message: Message):
    parts = message.text.split(maxsplit=4)
    if len(parts) < 5:
        return await message.reply_text("❌ Usage: <code>/addsite &lt;id&gt; &lt;name&gt; &lt;url&gt; &lt;rss_url&gt;</code>")
    
    site_id, name, url, rss_url = parts[1], parts[2], parts[3], parts[4]
    await db.add_site(site_id, name, url, rss_url)
    await message.reply_text(f"✅ Website <b>{name}</b> ({site_id}) added/updated successfully.")

async def remove_site_cmd(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text("❌ Usage: <code>/removesite &lt;id&gt;</code>")
    
    site_id = parts[1]
    await db.remove_site(site_id)
    await message.reply_text(f"✅ Website <code>{site_id}</code> removed from scraping engine.")

async def sites_cmd(client: Client, message: Message):
    sites = await db.get_sites()
    if not sites:
        return await message.reply_text("⚠️ No websites registered in DB.")
    
    msg = "🌐 <b>Registered Websites:</b>\n\n"
    for site in sites:
        msg += (
            f"🔹 <b>{site['name']}</b> (<code>{site['id']}</code>)\n"
            f"🔗 URL: {site['url']}\n"
            f"📡 RSS: {site['rss_url']}\n"
            f"⚙️ Default Server Index: {site['default_server_index']}\n\n"
        )
    await message.reply_text(msg)

async def add_channel_cmd(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) < 3:
        return await message.reply_text("❌ Usage: <code>/addchannel &lt;channel_id&gt; &lt;site_id&gt;</code>")
    
    try:
        channel_id = int(parts[1])
    except ValueError:
        return await message.reply_text("❌ Channel ID must be an integer (e.g. -1001234567890).")
    
    site_id = parts[2]
    site = await db.get_site(site_id)
    if not site:
        return await message.reply_text(f"❌ Site <code>{site_id}</code> does not exist.")
        
    await db.add_channel(channel_id, site_id)
    await message.reply_text(f"✅ Channel <code>{channel_id}</code> mapped to receive posts from <b>{site['name']}</b>.")

async def remove_channel_cmd(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) < 3:
        return await message.reply_text("❌ Usage: <code>/removechannel &lt;channel_id&gt; &lt;site_id&gt;</code>")
    
    try:
        channel_id = int(parts[1])
    except ValueError:
        return await message.reply_text("❌ Channel ID must be an integer.")
    
    site_id = parts[2]
    await db.remove_channel(channel_id, site_id)
    await message.reply_text(f"✅ Channel mapping for <code>{channel_id}</code> -> <code>{site_id}</code> removed.")

async def channels_cmd(client: Client, message: Message):
    mappings = await db.get_all_channel_mappings()
    if not mappings:
        return await message.reply_text("⚠️ No channel mappings found.")
    
    msg = "📢 <b>Channel Mapping Rules:</b>\n\n"
    for map_rule in mappings:
        msg += f"🔸 <code>{map_rule['channel_id']}</code> ➡️ receives <code>{map_rule['site_id']}</code>\n"
    await message.reply_text(msg)

async def default_channel_cmd(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text("❌ Usage: <code>/defaultchannel &lt;channel_id&gt;</code> (Use 0 to disable)")
    
    try:
        channel_id = int(parts[1])
    except ValueError:
        return await message.reply_text("❌ Channel ID must be an integer.")
        
    if channel_id == 0:
        await db.set_setting("default_channel", "")
        await message.reply_text("✅ Default owner channel disabled.")
    else:
        await db.set_setting("default_channel", str(channel_id))
        await message.reply_text(f"✅ Default owner channel updated to: <code>{channel_id}</code>.")

async def set_server_cmd(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) < 3:
        return await message.reply_text("❌ Usage: <code>/setserver &lt;site_id&gt; &lt;server_index&gt;</code> (where server_index starts at 0)")
    
    site_id = parts[1]
    try:
        srv_idx = int(parts[2])
    except ValueError:
        return await message.reply_text("❌ Server index must be an integer.")
        
    site = await db.get_site(site_id)
    if not site:
        return await message.reply_text(f"❌ Site <code>{site_id}</code> does not exist.")
        
    await db.set_site_server(site_id, srv_idx)
    await message.reply_text(f"✅ Default server index for <b>{site['name']}</b> set to: <code>{srv_idx}</code>.")

async def set_interval_cmd(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text("❌ Usage: <code>/setinterval &lt;minutes&gt;</code>")
        
    try:
        minutes = int(parts[1])
        if minutes < 1:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Interval must be an integer greater than 0.")
        
    await db.set_setting("check_interval", str(minutes))
    await message.reply_text(f"✅ Scraping check interval updated to <b>{minutes}</b> minutes.")

async def status_cmd(client: Client, message: Message):
    interval_str = await db.get_setting("default_channel")
    def_ch = interval_str if interval_str else "Not Set"
    loop_interval = await db.get_setting("check_interval") or str(config.DEFAULT_CHECK_INTERVAL)
    
    import aiosqlite
    async with aiosqlite.connect(db.db_path) as conn:
        async with conn.execute("SELECT COUNT(*) FROM uploads") as cursor:
            up_count = (await cursor.fetchone())[0]
        async with conn.execute("SELECT COUNT(*) FROM channels") as cursor:
            ch_count = (await cursor.fetchone())[0]
                
    status_text = (
        "📈 <b>Bot Status & Metrics:</b>\n\n"
        f"⏱️ <b>Loop Interval:</b> {loop_interval} mins\n"
        f"📢 <b>Default Channel:</b> <code>{def_ch}</code>\n"
        f"📊 <b>Total Uploaded Posts:</b> {up_count}\n"
        f"👥 <b>Active Channel Mappings:</b> {ch_count}\n"
        f"🐍 <b>Runtime environment:</b> Python 3.12\n"
        f"⚙️ <b>Architecture:</b> Async, Koyeb Optimized (&lt;250MB RAM)"
    )
    await message.reply_text(status_text)

async def reload_cmd(client: Client, message: Message):
    status_msg = await message.reply_text("🔄 <i>Manual check initiated... Scraping sites...</i>")
    
    sites = await db.get_sites()
    if not sites:
        return await status_msg.edit_text("❌ No registered websites found.")
        
    from scheduler import process_site_updates
    for site in sites:
        await process_site_updates(client, site["id"])
        
    await status_msg.edit_text("✅ <i>Manual check complete. All channels updated!</i>")

def register_command_handlers(app: Client):
    app.add_handler(MessageHandler(start_cmd, filters.command("start")))
    app.add_handler(MessageHandler(help_cmd, filters.command("help")))
    app.add_handler(MessageHandler(sites_cmd, filters.command("sites")))
    app.add_handler(MessageHandler(add_site_cmd, filters.command("addsite")))
    app.add_handler(MessageHandler(remove_site_cmd, filters.command("removesite")))
    app.add_handler(MessageHandler(add_channel_cmd, filters.command("addchannel")))
    app.add_handler(MessageHandler(remove_channel_cmd, filters.command("removechannel")))
    app.add_handler(MessageHandler(channels_cmd, filters.command("channels")))
    app.add_handler(MessageHandler(default_channel_cmd, filters.command("defaultchannel")))
    app.add_handler(MessageHandler(set_server_cmd, filters.command("setserver")))
    app.add_handler(MessageHandler(set_interval_cmd, filters.command("setinterval")))
    app.add_handler(MessageHandler(status_cmd, filters.command("status")))
    app.add_handler(MessageHandler(reload_cmd, filters.command("reload")))
