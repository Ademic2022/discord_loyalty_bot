import logging
import asyncio
import discord
from discord.ext import commands
from config import Config
from utils.db_manager import DatabaseManager
from utils.logger import setup_logger
from cogs.loyalty_tracker import LoyaltyTracker

# Initialize logging
setup_logger()
logger = logging.getLogger("discord_bot")


# Initialize bot with intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix=Config.PREFIX, intents=intents)


# Load loyalty tracking cog
@bot.event
async def on_ready():
    logger.info(f"Bot is ready! Logged in as {bot.user.name}")
    # Initialize database
    db = DatabaseManager()
    db.initialize()

    # Load cogs
    await bot.add_cog(LoyaltyTracker(bot))
    logger.info("Loyalty tracker cog loaded")


async def main():
    async with bot:
        await bot.start(Config.TOKEN)


# Run bot
if __name__ == "__main__":
    asyncio.run(main())
