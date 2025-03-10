import os
from decouple import config


class Config:
    TOKEN = config("DISCORD_TOKEN")  # Bot token from .env
    CHANNEL_ID = int(config("ANNOUNCEMENT_CHANNEL_ID"))  # Channel ID for the bot
    GRACE_PERIOD_MINUTES = 1
    FEE_PER_MINUTE = 100  # ₦100 per minute
    MAX_SINGLE_AWAY_MINUTES = 40
    MAX_DAILY_AWAY_MINUTES = 120  # 2 hours
    WORK_START_TIME = (9, 0)  # 9:00 AM
    WORK_END_TIME = (17, 0)  # 5:00 PM
