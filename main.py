import logging
import asyncio
import discord
from discord.ext import commands
from config import Config
from utils.commands import MyCommands
from utils.db_manager import DatabaseManager
from utils.logger import setup_logger
from cogs.loyalty_tracker import LoyaltyTracker
from utils.on_boarding import OnBoarding

# Initialize logging
setup_logger()
logger = logging.getLogger("discord_bot")


# Initialize bot with intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix=Config.PREFIX, intents=intents)

# Initialize MyCommands
my_commands = MyCommands(bot)


# Load loyalty tracking cog
@bot.event
async def on_ready():
    logger.info(f"Bot is ready! Logged in as {bot.user.name}")
    # Initialize database
    db = DatabaseManager()
    db.initialize()

    try:
        await bot.add_cog(LoyaltyTracker(bot, my_commands))
        logger.info("Loyalty tracker cog loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load LoyaltyTracker cog: {e}")

    try:
        await bot.add_cog(OnBoarding(bot, my_commands))
        logger.info("Server settings cog loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load ServerSettings cog: {e}")

    # Sync commands with Discord
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")


async def main():
    async with bot:
        await bot.start(Config.TOKEN)


# Run bot
if __name__ == "__main__":
    asyncio.run(main())
