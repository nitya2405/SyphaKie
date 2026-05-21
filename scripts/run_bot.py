import asyncio
import logging
import sys
from app.config import settings
from app.telegram import start_bot

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

async def main():
    if not settings.TELEGRAM_BOT_TOKEN:
        print("No TELEGRAM_BOT_TOKEN")
        return
    
    print(f"Starting bot with token: {settings.TELEGRAM_BOT_TOKEN[:10]}...")
    await start_bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        webhook_url=settings.TELEGRAM_WEBHOOK_URL,
        webhook_secret=settings.TELEGRAM_WEBHOOK_SECRET
    )
    
    print("Bot task started. Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
