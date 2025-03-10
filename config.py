from decouple import config
from datetime import time


class Config:
    TOKEN = config("DISCORD_TOKEN")  # Bot token from .env
    PREFIX = config("COMMAND_PREFIX", "!")
    LOG_PATH = config("LOG_PATH", "logs")
    CHANNEL_ID = int(config("ANNOUNCEMENT_CHANNEL_ID"))  # Channel ID for the bot
    GRACE_PERIOD_MINUTES = 1
    FEE_PER_MINUTE = 100  # ₦100 per minute
    MAX_SINGLE_AWAY_MINUTES = 40
    MAX_DAILY_AWAY_MINUTES = 90  # 1 hours 30 minutes
    WORK_START_TIME = time(9, 0)  # 9:00 AM
    WORK_END_TIME = time(17, 0)  # 5:00 PM
