"""
Economics Bot - Main Entry Point
Run this file to start the bot
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import bot instance
from bot import bot

# Import all commands (this registers them)
import bot_commands
import bot_commands2

# Import configuration
from config import BOT_TOKEN

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("=" * 60)
        print("ERROR: DISCORD_BOT_TOKEN environment variable not set!")
        print("=" * 60)
        print("\nPlease set your Discord bot token:")
        print("export DISCORD_BOT_TOKEN='your_token_here'")
        print("\nOr create a .env file with:")
        print("DISCORD_BOT_TOKEN=your_token_here")
        print("MONGODB_URI=your_mongodb_uri_here")
        print("=" * 60)
        sys.exit(1)
    
    print("=" * 60)
    print("Economics Bot - Enterprise Edition")
    print("=" * 60)
    print("Starting bot...")
    print(f"Python version: {sys.version}")
    print("=" * 60)
    
    try:
        bot.run(BOT_TOKEN)
    except KeyboardInterrupt:
        print("\n\nBot stopped by user")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
