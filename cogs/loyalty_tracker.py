import re
import discord
from discord.ext import commands
from datetime import datetime
import logging
from cogs.messages import MessageHandler
from config import Config
from utils.db_manager import DatabaseManager
from utils.utils import generate_report


class LoyaltyTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.logger = logging.getLogger("discord_bot")
        self.away_users = {}
        self.channel = Config.CHANNEL_ID
        self.GRACE_PERIOD_MINUTES = Config.GRACE_PERIOD_MINUTES
        self.FEE_PERCENTAGE_PER_MINUTE = Config.FEE_PERCENTAGE_PER_MINUTE
        self.MAX_SINGLE_AWAY_MINUTES = Config.MAX_SINGLE_AWAY_MINUTES
        self.MAX_DAILY_AWAY_MINUTES = Config.MAX_DAILY_AWAY_MINUTES
        self.WORK_START_TIME = Config.WORK_START_TIME
        self.WORK_END_TIME = Config.WORK_END_TIME

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages indicating a user is going away or returning"""
        # Ignore messages from bots
        if message.author.bot:
            return

        # Process both DMs and messages in designated channels
        is_dm = isinstance(message.channel, discord.DMChannel)
        if not is_dm and not self._should_track_channel(message.channel.id):
            return

        content = message.content.lower()

        # Check if this is a command in DMs
        if is_dm:
            if content.startswith("!awayreport") or content.startswith("/awayreport"):
                date_match = re.search(r"(\d{4}-\d{2}-\d{2})", content)
                date = date_match.group(1) if date_match else None
                await self._handle_direct_awayreport(message, date)
                return

            if content.startswith("!awaystatus") or content.startswith("/awaystatus"):
                await self.away_status(message)
                return

        # Check if this is a "going away" message
        away_match = re.search(r"(\d+)\s*(?:min|mins|minutes?)\s*away", content)
        if away_match:
            await self._handle_away_message(message, away_match)
            return

        # Check if this is a "return" message
        return_indicators = [
            "back",
            "returned",
            "i'm back",
            "i am back",
            "i have returned",
        ]
        if any(indicator in content for indicator in return_indicators):
            await self._handle_return_message(message)
            return

    async def _handle_direct_awayreport(self, message, date=None):
        """Handle direct message requests for away reports"""
        user_id = message.author.id
        is_admin = await self._is_admin(user_id)

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            # Fetch data based on user role
            if is_admin:
                daily_records, session_records = self.db._fetch_away_data(date)
                if not daily_records:
                    await message.author.send(f"No away time records found for {date}")
                    return
                report = generate_report(
                    date, daily_records, session_records, is_admin=True
                )
            else:
                user_record, session_records = self.db._fetch_away_data(date, user_id)
                if not user_record:
                    await message.author.send(
                        f"You don't have any away time records for {date}"
                    )
                    return
                report = generate_report(
                    date, user_record=user_record, session_records=session_records
                )

            await message.author.send(report)
        except Exception as e:
            self.logger.error(f"Error generating away report in DM: {e}")
            await message.author.send(
                "An error occurred while retrieving the away time report."
            )

    @commands.command(name="awayreport")
    async def away_report(self, ctx, date: str = None):
        """Get a report of away time on a specific date

        Args:
            date: Optional date in YYYY-MM-DD format (defaults to today)
        """
        user_id = ctx.author.id
        is_admin = ctx.author.guild_permissions.administrator

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            if is_admin:
                daily_records, session_records = self.db._fetch_away_data(date)

                if not daily_records:
                    await ctx.send(f"No away time records found for {date}")
                    return

                # Format admin report
                report = generate_report(
                    date=date,
                    daily_records=daily_records,
                    session_records=session_records,
                    is_admin=True,
                )

            else:
                user_record, session_records = self.db._fetch_away_data(date, user_id)
                if not user_record:
                    await ctx.send(f"You don't have any away time records for {date}")
                    return
                report = generate_report(
                    date, user_record=user_record, session_records=session_records
                )

            await ctx.send(report)

        except Exception as e:
            self.logger.error(f"Error generating away report: {e}")
            await ctx.send("An error occurred while retrieving the away time report.")

    @commands.command(name="awaystatus")
    async def away_status(self, ctx):
        """Check your current away status and remaining time"""
        user_id = ctx.author.id
        today = datetime.now().strftime("%Y-%m-%d")

        # Check if user is currently away
        if user_id in self.away_users:
            now = datetime.now()
            start_time = self.away_users[user_id]["start_time"]
            expected_minutes = self.away_users[user_id]["expected_minutes"]

            time_diff = now - start_time
            elapsed_minutes = int(time_diff.total_seconds() / 60)
            remaining_minutes = max(0, expected_minutes - elapsed_minutes)

            # Get total away time today from database
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT total_minutes FROM away_daily 
                WHERE user_id = ? AND date = ?
                """,
                (user_id, today),
            )
            result = cursor.fetchone()
            total_today = result[0] if result else 0
            conn.close()

            # Include current session in calculation
            total_including_current = total_today + elapsed_minutes
            remaining_today = max(
                0, self.MAX_DAILY_AWAY_MINUTES - total_including_current
            )

            await ctx.send(
                f"{ctx.author.mention} You've been away for {elapsed_minutes} minutes in this session. "
                f"You stated you'd be away for {expected_minutes} minutes, so you have {remaining_minutes} minutes remaining in this session.\n"
                f"Today's total: {total_including_current} minutes used out of {self.MAX_DAILY_AWAY_MINUTES} minute allowance. "
                f"Daily remaining: {remaining_today} minutes."
            )
        else:
            # Get total away time today from database instead of memory
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT total_minutes FROM away_daily 
                WHERE user_id = ? AND date = ?
                """,
                (user_id, today),
            )
            result = cursor.fetchone()
            total_today = result[0] if result else 0
            conn.close()

            remaining_today = max(0, self.MAX_DAILY_AWAY_MINUTES - total_today)

            await ctx.send(
                f"{ctx.author.mention} You're currently not marked as away. "
                f"You've used {total_today} minutes of your {self.MAX_DAILY_AWAY_MINUTES} minute daily allowance. "
                f"Remaining: {remaining_today} minutes."
            )

    @commands.command(name="setaway")
    @commands.has_permissions(administrator=True)
    async def set_away_status(self, ctx, user: discord.Member, minutes: int):
        """Manually set a user as away (admin only)"""
        user_id = user.id

        # Check if user is already away
        if user_id in self.away_users:
            await ctx.send(f"❌ {user.mention} is already marked as away.")
            return

        # Record away status
        now = datetime.now()
        total_today = self.db.get_today_away_time(user_id)

        self.away_users[user_id] = {
            "start_time": now,
            "expected_minutes": minutes,
            "total_today": total_today,
        }

        await ctx.send(
            f"✅ {user.mention} has been manually marked as away for {minutes} minutes."
        )
        self.logger.info(
            f"Admin {ctx.author.name} marked {user.display_name} as away for {minutes} minutes"
        )

    @commands.command(name="clearaway")
    @commands.has_permissions(administrator=True)
    async def clear_away_status(self, ctx, user: discord.Member):
        """Manually clear a user's away status (admin only)"""
        user_id = user.id

        # Check if user is away
        if user_id not in self.away_users:
            await ctx.send(f"❌ {user.mention} is not currently marked as away.")
            return

        # Clear away status
        del self.away_users[user_id]

        await ctx.send(f"✅ {user.mention}'s away status has been cleared.")
        self.logger.info(
            f"Admin {ctx.author.name} cleared away status for {user.display_name}"
        )

    def _should_track_channel(self, channel_id):
        """Determine if we should track messages in this channel"""
        # List of specific channels to target
        allowed_channel_ids = [self.channel]

        # Check if the channel_id is in the allowed list
        return channel_id in allowed_channel_ids

    async def _is_admin(self, user_id):
        """Check if a user has admin permissions"""
        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if member and member.guild_permissions.administrator:
                return True
        return False

    async def _handle_away_message(self, message, match):
        """Handle when a user announces they're going away"""
        if not self.db.is_work_hours():
            return  # Only track during work hours

        user_id = message.author.id
        user_name = message.author.display_name
        minutes_away = int(match.group(1))

        # Check if user is already away
        if user_id in self.away_users:
            await MessageHandler.already_away(message)
            return

        # Check if exceeds maximum single away time
        if minutes_away > self.MAX_SINGLE_AWAY_MINUTES:
            await MessageHandler.exceeds_single_away(
                message, self.MAX_SINGLE_AWAY_MINUTES
            )
            minutes_away = self.MAX_SINGLE_AWAY_MINUTES

        # Check daily allowance
        total_today = self.db.get_today_away_time(user_id)
        remaining_today = self.MAX_DAILY_AWAY_MINUTES - total_today

        if remaining_today <= 0:
            await MessageHandler.exceeded_daily_limit(message)
        elif minutes_away > remaining_today:
            await MessageHandler.near_daily_limit(
                message, remaining_today, minutes_away
            )

        # Record away status
        now = datetime.now()
        self.away_users[user_id] = {
            "start_time": now,
            "expected_minutes": minutes_away,
            "total_today": total_today,
        }

        # Acknowledge
        channel = self.bot.get_channel(self.channel)
        await MessageHandler.away_acknowledge(message, minutes_away, channel)
        self.logger.info(
            f"User {user_name} ({user_id}) marked away for {minutes_away} minutes at {now}"
        )

    async def _handle_return_message(self, message):
        """Handle when a user announces they've returned"""
        user_id = message.author.id
        user_name = message.author.display_name

        # Check if user was away
        if user_id not in self.away_users:
            # User wasn't marked as away
            return

        # Calculate time away
        now = datetime.now()
        start_time = self.away_users[user_id]["start_time"]
        expected_minutes = self.away_users[user_id]["expected_minutes"]

        time_diff = now - start_time
        actual_minutes = int(time_diff.total_seconds() / 60)

        # Calculate lateness beyond grace period
        late_minutes = max(
            0, actual_minutes - expected_minutes - self.GRACE_PERIOD_MINUTES
        )

        # Calculate percentage fee if applicable
        accumulated_percentage = 0
        if late_minutes > 0:
            accumulated_percentage = late_minutes * self.FEE_PERCENTAGE_PER_MINUTE

        # Record session
        self.db.record_away_session(
            user_id,
            user_name,
            start_time,
            now,
            expected_minutes,
            actual_minutes,
            accumulated_percentage,
        )

        # Update daily totals
        daily_over_limit, daily_fee = self.db.update_daily_totals(
            user_id, user_name, actual_minutes
        )

        # Clear away status
        del self.away_users[user_id]

        # Send response based on outcome
        channel = self.bot.get_channel(self.channel)
        if late_minutes > 0 and daily_over_limit > 0:
            await MessageHandler.return_late_and_daily_over(
                message,
                actual_minutes,
                expected_minutes,
                late_minutes,
                accumulated_percentage,
                daily_over_limit,
                accumulated_percentage + daily_fee,
                channel,
            )
        elif late_minutes > 0:
            await MessageHandler.return_late(
                message,
                actual_minutes,
                expected_minutes,
                late_minutes,
                accumulated_percentage,
                channel,
            )
        elif daily_over_limit > 0:
            await MessageHandler.daily_over_limit(message, daily_over_limit, daily_fee, channel)
        else:
            channel = self.bot.get_channel(self.channel)
            await MessageHandler.return_on_time(message, actual_minutes, channel)

        self.logger.info(
            f"User {user_name} ({user_id}) returned after {actual_minutes} minutes, expected {expected_minutes}"
        )
