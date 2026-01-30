#!/usr/bin/env python3
"""Run the MedContext Telegram bot."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

if __name__ == "__main__":
    print("🤖 Starting MedContext Telegram Bot...")
    print("📝 Make sure TELEGRAM_BOT_TOKEN is set in your .env file")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    from app.telegram_bot.bot import create_application

    try:
        # Create and run the application
        application = create_application()

        print("✅ Bot is running! Press Ctrl+C to stop.")
        print("📱 Open Telegram and send /start to your bot\n")

        # Run the bot (this blocks until stopped)
        application.run_polling(
            allowed_updates=None,
            drop_pending_updates=True,
        )

    except KeyboardInterrupt:
        print("\n✋ Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
