import asyncio
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from app.config import settings

async def test_markdown():
    if not settings.TELEGRAM_BOT_TOKEN:
        print("No token")
        return
    
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2),
    )
    
    # This is exactly what's in misc.py cmd_help
    help_text = (
        "*SyphaKie Bot — Commands*\n\n"
        "⚡ *Quick generate*\n"
        "/q \\[prompt\\]  — Generate text \\(auto model\\)\n"
        "/img \\[prompt\\] — Generate image \\(auto model\\)\n\n"
        "🎛 *Full flow*\n"
        "/generate — Choose modality, model \\+ prompt\n\n"
        "📊 *Account*\n"
        "/profile  — View your account\n"
        "/credits  — Check credit balance\n"
        "/usage    — Generation stats\n"
        "/topup    — Add more credits\n"
        "/history  — Last 5 generations\n\n"
        "⚙️ *Settings*\n"
        "/setdefault \\[modality\\] \\[model\\] — Set default model\n\n"
        "🔧 *Other*\n"
        "/cancel   — Cancel current operation\n"
        "/logout   — Disconnect Telegram\n"
        "/help     — Show this message\n\n"
        "💡 You can also send a *voice message* or *photo* anytime\\!"
    )
    
    try:
        # We can't really "test" it without sending it to a real chat, 
        # but we can try to validate it if aiogram has a validator, 
        # or we just see if we can find unescaped characters.
        print("Help text length:", len(help_text))
        # MarkdownV2 requires escaping: _ * [ ] ( ) ~ ` > # + - = | { } . !
        
        # Let's check for unescaped dots and dashes
        import re
        # Look for . or - NOT preceded by \
        unescaped = re.findall(r'(?<!\\)[.\-]', help_text)
        if unescaped:
            print(f"Found {len(unescaped)} unescaped special characters: {set(unescaped)}")
        else:
            print("No unescaped . or - found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_markdown())
