import asyncio
import os
from aiogram import Bot
from app.config import settings

async def check_bot():
    if not settings.TELEGRAM_BOT_TOKEN:
        print("No TELEGRAM_BOT_TOKEN found in settings")
        return
    
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    try:
        me = await bot.get_me()
        print(f"Bot connected: @{me.username} (ID: {me.id})")
        
        webhook = await bot.get_webhook_info()
        print(f"Webhook info: {webhook}")
        
    except Exception as e:
        print(f"Error connecting to Telegram: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(check_bot())
