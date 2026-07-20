# handlers/callback.py
from pyrogram import Client
from pyrogram.handlers import CallbackQueryHandler
from pyrogram.types import CallbackQuery
from utils.logger import logger

async def main_callback_handler(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    logger.info(f"[UPDATE] Received callback payload: {data}")
    await callback_query.answer("Payload registered.", show_alert=False)

def register_callback_handlers(app: Client):
    app.add_handler(CallbackQueryHandler(main_callback_handler))
