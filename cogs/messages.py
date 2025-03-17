from cogs.embed import EmbedHandler


class MessageHandler:
    @staticmethod
    async def already_away(message):
        embed = EmbedHandler.already_away_embed(message)
        await message.channel.send(embed=embed)

    @staticmethod
    async def exceeds_single_away(message, minutes_away):
        embed = EmbedHandler.exceeds_single_away_embed(message, minutes_away)
        await message.channel.send(embed=embed)

    @staticmethod
    async def exceeded_daily_limit(message):
        embed = EmbedHandler.exceeded_daily_limit_embed()
        await message.channel.send(embed=embed)

    @staticmethod
    async def near_daily_limit(message, remaining_today, minutes_away):
        await message.channel.send(
            f"⚠️ {message.author.mention} You only have {remaining_today} minutes of away time remaining today. "
            f"If you use all {minutes_away} minutes, you'll exceed your daily limit and incur lateness penalties."
        )

    @staticmethod
    async def away_acknowledge(message, minutes_away, channel):

        embed = EmbedHandler.away_acknowledge_embed(message, minutes_away)

        await channel.send(embed=embed)

    @staticmethod
    async def return_on_time(message, actual_minutes, channel):
        embed = EmbedHandler.return_on_time_embed(message, actual_minutes)
        await channel.send(embed=embed)

    @staticmethod
    async def return_late(
        message,
        actual_minutes,
        expected_minutes,
        late_minutes,
        accumulated_percentage,
        channel,
    ):
        embed = EmbedHandler.return_late_embed(
            message,
            actual_minutes,
            expected_minutes,
            late_minutes,
            accumulated_percentage,
        )
        await channel.send(embed=embed)

    @staticmethod
    async def daily_over_limit(message, daily_over_limit, daily_fee):
        embed = EmbedHandler.daily_over_limit_embed(
            message, daily_over_limit, daily_fee
        )
        await message.channel.send(embed=embed)

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
        embed = EmbedHandler.return_late_and_daily_over_embed(
            message,
            actual_minutes,
            expected_minutes,
            late_minutes,
            accumulated_percentage,
            daily_over_limit,
            total_fee,
        )
        await channel.send(embed=embed)
