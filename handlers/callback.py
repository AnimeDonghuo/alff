# handlers/callback.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from utils.logger import logger

@Client.on_callback_query()
async def main_callback_handler(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    logger.info(f"Received callback payload: {data}")
    await callback_query.answer("Payload registered.", show_alert=False)
