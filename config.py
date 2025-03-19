from decouple import config
from datetime import time


class Config:
    TOKEN = config("DISCORD_TOKEN")  # Bot token from .env
    PREFIX = config("COMMAND_PREFIX", "!")
    LOG_PATH = config("LOG_PATH", "logs")
    CHANNEL_ID = int(config("ANNOUNCEMENT_CHANNEL_ID"))  # Channel ID for the bot
    GRACE_PERIOD_MINUTES = 1
    FEE_PERCENTAGE_PER_MINUTE = 0.0007  # 0.07% per minute
    MAX_SINGLE_AWAY_MINUTES = 40
    MAX_DAILY_AWAY_MINUTES = 90  # 1 hours 30 minutes
    WORK_START_TIME = time(9, 0)  # 9:00 AM
    WORK_END_TIME = time(17, 0)  # 5:00 PM

# from decouple import config
# from datetime import time


# class Config:
#     # Static configurations that don't change per server
#     TOKEN = config("DISCORD_TOKEN")  # Bot token from .env
#     LOG_PATH = config("LOG_PATH", "logs")

#     # Default values - these will be used if database values aren't available
#     DEFAULT_PREFIX = config("COMMAND_PREFIX", "!")
#     DEFAULT_GRACE_PERIOD_MINUTES = 5
#     DEFAULT_FEE_PERCENTAGE_PER_MINUTE = 0.0007  # 0.07% per minute
#     DEFAULT_MAX_SINGLE_AWAY_MINUTES = 40
#     DEFAULT_MAX_DAILY_AWAY_MINUTES = 90  # 1 hours 30 minutes
#     DEFAULT_WORK_START_TIME = time(9, 0)  # 9:00 AM
#     DEFAULT_WORK_END_TIME = time(17, 0)  # 5:00 PM

#     @staticmethod
#     def get_server_config(guild_id):
#         """
#         Load server-specific configuration from the database.
#         Falls back to defaults if values aren't found.
#         """
#         from utils.db_manager import DatabaseManager

#         db = DatabaseManager()
#         settings = db.get_server_settings(guild_id)

#         if not settings:
#             return {
#                 "prefix": Config.DEFAULT_PREFIX,
#                 "channel_id": None,
#                 "grace_period_minutes": Config.DEFAULT_GRACE_PERIOD_MINUTES,
#                 "fee_percentage_per_minute": Config.DEFAULT_FEE_PERCENTAGE_PER_MINUTE,
#                 "max_single_away_minutes": Config.DEFAULT_MAX_SINGLE_AWAY_MINUTES,
#                 "max_daily_away_minutes": Config.DEFAULT_MAX_DAILY_AWAY_MINUTES,
#                 "work_start_time": Config.DEFAULT_WORK_START_TIME,
#                 "work_end_time": Config.DEFAULT_WORK_END_TIME,
#             }

#         # Parse time strings from DB into time objects
#         work_start = Config.DEFAULT_WORK_START_TIME
#         work_end = Config.DEFAULT_WORK_END_TIME

#         if "work_start_time" in settings and settings["work_start_time"]:
#             try:
#                 parts = settings["work_start_time"].split(":")
#                 work_start = time(int(parts[0]), int(parts[1]))
#             except (ValueError, IndexError):
#                 pass

#         if "work_end_time" in settings and settings["work_end_time"]:
#             try:
#                 parts = settings["work_end_time"].split(":")
#                 work_end = time(int(parts[0]), int(parts[1]))
#             except (ValueError, IndexError):
#                 pass

#         return {
#             "prefix": settings.get("command_prefix", Config.DEFAULT_PREFIX),
#             "channel_id": settings.get("announcement_channel_id"),
#             "grace_period_minutes": settings.get(
#                 "grace_period_minutes", Config.DEFAULT_GRACE_PERIOD_MINUTES
#             ),
#             "fee_percentage_per_minute": settings.get(
#                 "fee_percentage_per_minute", Config.DEFAULT_FEE_PERCENTAGE_PER_MINUTE
#             ),
#             "max_single_away_minutes": settings.get(
#                 "max_single_away_minutes", Config.DEFAULT_MAX_SINGLE_AWAY_MINUTES
#             ),
#             "max_daily_away_minutes": settings.get(
#                 "max_daily_away_minutes", Config.DEFAULT_MAX_DAILY_AWAY_MINUTES
#             ),
#             "work_start_time": work_start,
#             "work_end_time": work_end,
#         }
