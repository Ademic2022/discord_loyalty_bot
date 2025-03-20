import logging
from cogs.embed import EmbedHandler


class MessageHandler:
    _logger = logging.getLogger("discord_bot")

    @staticmethod
    async def already_away(message):
        try:
            embed = EmbedHandler.already_away_embed(message)
            await message.channel.send(embed=embed)
        except Exception as e:
            MessageHandler._logger.error(f"Error in already_away: {e}")
            await message.channel.send("An error occurred while processing your request.")

    @staticmethod
    async def exceeds_single_away(message, minutes_away):
        try:
            embed = EmbedHandler.exceeds_single_away_embed(message, minutes_away)
            await message.channel.send(embed=embed)
        except Exception as e:
            MessageHandler._logger.error(f"Error in exceeds_single_away: {e}")
            await message.channel.send("An error occurred while processing your request.")

    @staticmethod
    async def exceeded_daily_limit(message):
        try:
            embed = EmbedHandler.exceeded_daily_limit_embed(message)
            await message.channel.send(embed=embed)
        except Exception as e:
            MessageHandler._logger.error(f"Error in exceeded_daily_limit: {e}")
            await message.channel.send("An error occurred while processing your request.")

    @staticmethod
    async def near_daily_limit(message, remaining_today, minutes_away):
        try:
            await message.channel.send(
                f"⚠️ {message.author.mention} You only have {remaining_today} minutes of away time remaining today. "
                f"If you use all {minutes_away} minutes, you'll exceed your daily limit and incur lateness penalties."
            )
        except Exception as e:
            MessageHandler._logger.error(f"Error in near_daily_limit: {e}")
            await message.channel.send("An error occurred while processing your request.")

    @staticmethod
    async def away_acknowledge(message, minutes_away, channel):
        try:
            embed = EmbedHandler.away_acknowledge_embed(message, minutes_away)
            await channel.send(embed=embed)
        except Exception as e:
            MessageHandler._logger.error(f"Error in away_acknowledge: {e}")
            await channel.send("An error occurred while processing your request.")

    @staticmethod
    async def return_on_time(message, actual_minutes, channel):
        try:
            embed = EmbedHandler.return_on_time_embed(message, actual_minutes)
            await channel.send(embed=embed)
        except Exception as e:
            MessageHandler._logger.error(f"Error in return_on_time: {e}")
            await channel.send("An error occurred while processing your request.")

    @staticmethod
    async def return_late(
        message,
        actual_minutes,
        expected_minutes,
        late_minutes,
        accumulated_percentage,
        channel,
    ):
        try:
            embed = EmbedHandler.return_late_embed(
                message,
                actual_minutes,
                expected_minutes,
                late_minutes,
                accumulated_percentage,
            )
            await channel.send(embed=embed)
        except Exception as e:
            MessageHandler._logger.error(f"Error in return_late: {e}")
            await channel.send("An error occurred while processing your request.")

    @staticmethod
    async def daily_over_limit(message, daily_over_limit, daily_fee):
        try:
            embed = EmbedHandler.daily_over_limit_embed(
                message, daily_over_limit, daily_fee
            )
            await message.channel.send(embed=embed)
        except Exception as e:
            MessageHandler._logger.error(f"Error in daily_over_limit: {e}")
            await message.channel.send("An error occurred while processing your request.")

    @staticmethod
    async def return_late_and_daily_over(
        message,
        actual_minutes,
        expected_minutes,
        late_minutes,
        accumulated_percentage,
        daily_over_limit,
        total_fee,
        grace_period,
        channel,
    ):
        try:
            embed = EmbedHandler.return_late_and_daily_over_embed(
                message,
                actual_minutes,
                expected_minutes,
                late_minutes,
                accumulated_percentage,
                daily_over_limit,
                total_fee,
                grace_period,
            )
            await channel.send(embed=embed)
        except Exception as e:
            MessageHandler._logger.error(f"Error in return_late_and_daily_over: {e}")
            await channel.send("An error occurred while processing your request.")