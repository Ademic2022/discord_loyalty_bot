from config import Config


class MessageHandler:
    @staticmethod
    async def already_away(message):
        await message.channel.send(
            f"{message.author.mention} You're already marked as away. Please type 'back' when you return."
        )

    @staticmethod
    async def exceeds_single_away(message, minutes_away):
        await message.channel.send(
            f"⚠️ {message.author.mention} Your requested time away ({minutes_away} minutes) exceeds the maximum single away time "
            f"({Config.MAX_SINGLE_AWAY_MINUTES} minutes). You've been marked as away for {Config.MAX_SINGLE_AWAY_MINUTES} minutes instead."
        )

    @staticmethod
    async def exceeded_daily_limit(message):
        await message.channel.send(
            f"⚠️ {message.author.mention} You have used all your away time for today ({Config.MAX_DAILY_AWAY_MINUTES} minutes). "
            f"Additional time away will incur a lateness penalty of {Config.FEE_PERCENTAGE_PER_MINUTE:.4%} per minute."
        )

    @staticmethod
    async def near_daily_limit(message, remaining_today, minutes_away):
        await message.channel.send(
            f"⚠️ {message.author.mention} You only have {remaining_today} minutes of away time remaining today. "
            f"If you use all {minutes_away} minutes, you'll exceed your daily limit and incur lateness penalties."
        )

    @staticmethod
    async def away_acknowledge(message, minutes_away, channel):
        
        await channel.send(
            f"👋 {message.author.mention} You're marked as away for {minutes_away} minutes. "
            f"Please type 'back' when you return."
        )

    @staticmethod
    async def return_on_time(message, actual_minutes, channel):
        await channel.send(
            f"✅ {message.author.mention} Welcome back on time after {actual_minutes} minutes!"
        )

    @staticmethod
    async def return_late(
        message,
        actual_minutes,
        expected_minutes,
        late_minutes,
        accumulated_percentage,
    ):
        await message.channel.send(
            f"⏰ {message.author.mention} Welcome back after {actual_minutes} minutes! "
            f"You were {late_minutes} minutes late (beyond your stated {expected_minutes} + {Config.GRACE_PERIOD_MINUTES} grace). "
            f"Lateness penalty: {accumulated_percentage:.4%}."
        )

    @staticmethod
    async def daily_over_limit(message, daily_over_limit, daily_fee):
        await message.channel.send(
            f"✅ {message.author.mention} Welcome back on time! However, you've exceeded your daily away limit "
            f"by {daily_over_limit} minutes. Lateness penalty: {daily_fee:.4%}"
        )

    @staticmethod
    async def return_late_and_daily_over(
        message,
        actual_minutes,
        expected_minutes,
        late_minutes,
        accumulated_percentage,
        daily_over_limit,
        total_fee,
        channel,
    ):
        await channel.send(
            f"⏰ {message.author.mention} Welcome back after {actual_minutes} minutes! "
            f"You were {late_minutes} minutes late (beyond your stated {expected_minutes} + {Config.GRACE_PERIOD_MINUTES} grace). "
            f"Lateness penalty: {accumulated_percentage:.4%}.\n"
            f"Additionally, you've exceeded your daily away limit by {daily_over_limit} minutes. "
            f"Total lateness penalty: {total_fee:.4%}"
        )
