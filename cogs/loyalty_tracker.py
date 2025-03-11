import re
import discord
from discord.ext import commands
from datetime import datetime
import logging
from config import Config
from utils.db_manager import DatabaseManager


class LoyaltyTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.logger = logging.getLogger("discord_bot")
        self.away_users = {}
        self.channel = Config.CHANNEL_ID
        self.GRACE_PERIOD_MINUTES = Config.GRACE_PERIOD_MINUTES
        self.FEE_PER_MINUTE = Config.FEE_PER_MINUTE
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

        # Only process messages in designated channels
        if not self._should_track_channel(message.channel.id):
            return

        # Convert message content to lowercase for easier matching
        content = message.content.lower()

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

    @commands.command(name="awayreport")
    @commands.has_permissions(administrator=True)
    async def away_report(self, ctx, date: str = None):
        """Get a report of away time for all users on a specific date

        Args:
            date: Optional date in YYYY-MM-DD format (defaults to today)
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get daily summary
            cursor.execute(
                """
            SELECT user_name, total_minutes, over_limit_minutes, fee_amount
            FROM away_daily
            WHERE date = ?
            ORDER BY total_minutes DESC
            """,
                (date,),
            )

            daily_records = cursor.fetchall()

            if not daily_records:
                await ctx.send(f"No away time records found for {date}")
                return

            # Format report using Discord code blocks for better table formatting
            report = f"📊 **Away Time Report - {date}**\n"

            # Daily summary table with proper Discord markdown
            report += "```\n"  # Start code block for table
            report += "Name             | Total Away | Over Limit | Fees    \n"
            report += "-----------------|------------|------------|--------\n"

            for record in daily_records:
                name, total, over_limit, fee = record
                # Pad each column for alignment
                report += f"{name:<16} | {total:^10} | {over_limit:^10} | ₦{fee:<7}\n"

            report += "```\n"  # End code block

            # Get individual sessions
            cursor.execute(
                """
            SELECT user_name, start_time, end_time, expected_minutes, actual_minutes, fee_amount
            FROM away_time
            WHERE date = ?
            ORDER BY start_time
            """,
                (date,),
            )

            session_records = cursor.fetchall()

            report += "\n**Individual Away Sessions**\n"

            # Individual sessions table
            report += "```\n"  # Start code block
            report += "Name             | Start      | End        | Expected  | Actual    | Fees    \n"
            report += "-----------------|------------|------------|-----------|-----------|--------\n"

            for record in session_records:
                name, start, end, expected, actual, fee = record
                # Pad each column for alignment
                report += f"{name:<16} | {start:<10} | {end:<10} | {expected:^9} | {actual:^9} | ₦{fee:<7}\n"

            report += "```"  # End code block

            conn.close()
            await ctx.send(report)

        except Exception as e:
            self.logger.error(f"Error generating away report: {e}")
            await ctx.send("An error occurred while retrieving the away time report.")

    @commands.command(name="awaystatus")
    async def away_status(self, ctx):
        """Check your current away status and remaining time"""
        user_id = ctx.author.id
        # user_name = ctx.author.display_name
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

    async def _handle_away_message(self, message, match):
        """Handle when a user announces they're going away"""
        if not self.db.is_work_hours():
            return  # Only track during work hours

        user_id = message.author.id
        user_name = message.author.display_name
        minutes_away = int(match.group(1))

        # Check if user is already away
        if user_id in self.away_users:
            await message.channel.send(
                f"{message.author.mention} You're already marked as away. Please type 'back' when you return."
            )
            return

        # Check if exceeds maximum single away time
        if minutes_away > self.MAX_SINGLE_AWAY_MINUTES:
            await message.channel.send(
                f"⚠️ {message.author.mention} Your requested time away ({minutes_away} minutes) exceeds the maximum single away time "
                f"({self.MAX_SINGLE_AWAY_MINUTES} minutes). You've been marked as away for {self.MAX_SINGLE_AWAY_MINUTES} minutes instead."
            )
            minutes_away = self.MAX_SINGLE_AWAY_MINUTES

        # Check daily allowance
        total_today = self.db.get_today_away_time(user_id)
        remaining_today = self.MAX_DAILY_AWAY_MINUTES - total_today

        if remaining_today <= 0:
            await message.channel.send(
                f"⚠️ {message.author.mention} You have used all your away time for today ({self.MAX_DAILY_AWAY_MINUTES} minutes). "
                f"Additional time away will incur a fee of ₦{self.FEE_PER_MINUTE} per minute."
            )
        elif minutes_away > remaining_today:
            await message.channel.send(
                f"⚠️ {message.author.mention} You only have {remaining_today} minutes of away time remaining today. "
                f"If you use all {minutes_away} minutes, you'll exceed your daily limit and incur fees."
            )

        # Record away status
        now = datetime.now()
        self.away_users[user_id] = {
            "start_time": now,
            "expected_minutes": minutes_away,
            "total_today": total_today,
        }

        # Acknowledge
        await message.channel.send(
            f"👋 {message.author.mention} You're marked as away for {minutes_away} minutes. "
            f"Please type 'back' when you return. Grace period: {self.GRACE_PERIOD_MINUTES} minutes."
        )
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

        # Calculate fee if applicable
        fee_amount = 0
        if late_minutes > 0:
            fee_amount = late_minutes * self.FEE_PER_MINUTE

        # Record session
        self.db.record_away_session(
            user_id,
            user_name,
            start_time,
            now,
            expected_minutes,
            actual_minutes,
            fee_amount,
        )

        # Update daily totals
        daily_over_limit, daily_fee = self.db.update_daily_totals(
            user_id, user_name, actual_minutes
        )

        # Clear away status
        del self.away_users[user_id]

        # Send response based on outcome
        if late_minutes > 0 and daily_over_limit > 0:
            # Both late and over daily limit
            await message.channel.send(
                f"⏰ {message.author.mention} Welcome back after {actual_minutes} minutes! "
                f"You were {late_minutes} minutes late (beyond your stated {expected_minutes} + {self.GRACE_PERIOD_MINUTES} grace). "
                f"Fee: ₦{fee_amount}.\n"
                f"Additionally, you've exceeded your daily away limit by {daily_over_limit} minutes. "
                f"Total fees: ₦{fee_amount + daily_fee}"
            )
        elif late_minutes > 0:
            # Just late
            await message.channel.send(
                f"⏰ {message.author.mention} Welcome back after {actual_minutes} minutes! "
                f"You were {late_minutes} minutes late (beyond your stated {expected_minutes} + {self.GRACE_PERIOD_MINUTES} grace). "
                f"Fee: ₦{fee_amount}"
            )
        elif daily_over_limit > 0:
            # Just over daily limit
            await message.channel.send(
                f"✅ {message.author.mention} Welcome back on time! However, you've exceeded your daily away limit "
                f"by {daily_over_limit} minutes. Fee: ₦{daily_fee}"
            )
        else:
            # On time and within limits
            await message.channel.send(
                f"✅ {message.author.mention} Welcome back on time after {actual_minutes} minutes!"
            )

        self.logger.info(
            f"User {user_name} ({user_id}) returned after {actual_minutes} minutes, expected {expected_minutes}"
        )
