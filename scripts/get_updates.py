import asyncio
from aiogram import Bot
from app.config import settings

async def get_updates():
    if not settings.TELEGRAM_BOT_TOKEN:
        print("No token")
        return
    
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    try:
        updates = await bot.get_updates()
        print(f"Pending updates: {len(updates)}")
        for u in updates:
            if u.message:
                print(f"Message from {u.message.from_user.username}: {u.message.text}")
            elif u.callback_query:
                print(f"Callback from {u.callback_query.from_user.username}: {u.callback_query.data}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(get_updates())
