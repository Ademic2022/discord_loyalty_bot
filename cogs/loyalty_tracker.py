import re
import logging
import traceback
import discord
from discord.ext import commands
from datetime import datetime
from cogs.embed import EmbedHandler
from cogs.messages import MessageHandler
from utils.db_manager import DatabaseManager
from utils.report import ReportGenerator


class LoyaltyTracker(commands.Cog):
    def __init__(self, bot, my_commands):
        self.bot = bot
        self.db = DatabaseManager()
        self.logger = logging.getLogger("discord_bot")
        self.report = ReportGenerator()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages indicating a user is going away or returning"""
        try:
            # Ignore messages from bots
            if message.author.bot:
                return

            # Process both DMs and messages in designated channels
            is_dm = isinstance(message.channel, discord.DMChannel)
            # if not is_dm and not self._should_track_channel(
            #     message.channel.id, settings
            # ):
            #     return

            content = message.content.lower()
            # Check if this is a command in DMs
            if is_dm:
                if content.startswith("!awayreport") or content.startswith(
                    "/awayreport"
                ):
                    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", content)
                    date = date_match.group(1) if date_match else None
                    await self._handle_direct_awayreport(message, date)
                    return

                if content.startswith("!awaystatus") or content.startswith(
                    "/awaystatus"
                ):
                    await self.away_status(message)
                    return

            settings = self.db.get_server_settings(message.guild.id)
            # Check if this is a "going away" message
            away_match = re.search(r"(\d+)\s*(?:min|mins|minutes?)\s*away", content)
            if away_match:
                await self._handle_away_message(message, away_match, settings)
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
                await self._handle_return_message(message, settings)
                return
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"Error in on_message: {e}")
            await message.channel.send(
                "An error occurred while processing your message."
            )

    async def _handle_direct_awayreport(self, message, date=None):
        """Handle direct message requests for away reports"""
        try:
            user_id = message.author.id
            is_admin = await self._is_admin(user_id)

            if not date:
                date = datetime.now().strftime("%Y-%m-%d")

            # Fetch data based on user role
            if is_admin:
                daily_records, session_records = self.db._fetch_away_data(
                    date, message.guild.id
                )
                if not daily_records:
                    await message.author.send(f"No away time records found for {date}")
                    return
                report, is_pdf = self.report.generate_report(
                    date=date,
                    daily_records=daily_records,
                    session_records=session_records,
                    is_admin=True,
                )
            else:
                user_record, session_records = self.db._fetch_away_data(
                    date, message.guild.id, user_id
                )
                if not user_record:
                    await message.author.send(
                        f"You don't have any away time records for {date}"
                    )
                    return
                report, is_pdf = self.report.generate_report(
                    date=date, user_record=user_record, session_records=session_records
                )

            # Send report
            if is_pdf:
                with open(report, "rb") as f:
                    await message.author.send(file=discord.File(f, report))
            else:
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
        try:
            user_id = ctx.author.id
            is_admin = ctx.author.guild_permissions.administrator

            if not date:
                date = datetime.now().strftime("%Y-%m-%d")

            if is_admin:
                daily_records, session_records = self.db._fetch_away_data(
                    date, ctx.guild.id
                )
                if not daily_records:
                    await ctx.send(f"No away time records found for {date}")
                    return

                # Format admin report
                report, is_pdf = self.report.generate_report(
                    date=date,
                    daily_records=daily_records,
                    session_records=session_records,
                    is_admin=True,
                )

            else:
                user_record, session_records = self.db._fetch_away_data(
                    date, ctx.guild.id, user_id
                )
                if not user_record:
                    await ctx.send(f"You don't have any away time records for {date}")
                    return
                report, is_pdf = self.report.generate_report(
                    date, user_record=user_record, session_records=session_records
                )

            if is_pdf:
                with open(report, "rb") as f:
                    await ctx.send(file=discord.File(f, report))
            else:
                await ctx.send(report)

        except Exception as e:
            self.logger.error(f"Error generating away report: {e}")
            await ctx.send("An error occurred while retrieving the away time report.")

    @commands.command(name="awaystatus")
    async def away_status(self, ctx, settings=None):
        """Check your current away status and remaining time"""
        try:
            guild_id = ctx.guild.id
            if not settings:
                settings = self.db.get_server_settings(guild_id)

            user_id = ctx.author.id
            today = datetime.now().strftime("%Y-%m-%d")

            # Check if user is currently away
            active_session = self.db.get_active_away_session(user_id, guild_id)
            if active_session:
                now = datetime.now().time()
                start_time = active_session["start_time"]
                expected_minutes = active_session["expected_minutes"]

                time_diff = datetime.combine(datetime.today(), now) - datetime.combine(
                    datetime.today(), start_time
                )
                elapsed_minutes = int(time_diff.total_seconds() / 60)
                remaining_minutes = max(0, expected_minutes - elapsed_minutes)

                # Get total away time today from database
                total_today = self.db.get_today_away_time(user_id, guild_id)

                # Include current session in calculation
                total_including_current = total_today + elapsed_minutes
                remaining_today = max(
                    0, settings["max_daily_away_minutes"] - total_including_current
                )
                embed = EmbedHandler.away_status_message_embed(
                    ctx,
                    elapsed_minutes,
                    expected_minutes,
                    remaining_minutes,
                    total_including_current,
                    settings["max_daily_away_minutes"],
                    remaining_today,
                )
                await ctx.send(embed=embed)
            else:
                # User is not currently away
                total_today = self.db.get_today_away_time(user_id, guild_id)
                remaining_today = max(
                    0, settings["max_daily_away_minutes"] - total_today
                )

                embed = EmbedHandler.send_not_away_status_message_embed(
                    ctx,
                    total_today,
                    settings["max_daily_away_minutes"],
                    remaining_today,
                )
                await ctx.send(embed=embed)
        except Exception as e:
            self.logger.error(f"Error in away_status: {e}")
            await ctx.send("An error occurred while checking your away status.")

    @commands.command(name="setaway")
    @commands.has_permissions(administrator=True)
    async def set_away_status(self, ctx, user: discord.Member, minutes: int):
        """Manually set a user as away (admin only)"""
        try:
            user_id = user.id
            guild_id = ctx.guild.id

            # Check if user is already away
            active_session = self.db.get_active_away_session(user_id, guild_id)
            if active_session:
                await ctx.send(f"❌ {user.mention} is already marked as away.")
                return

            # Add the active away session to the database
            self.db.add_active_away_session(
                user_id, user.display_name, guild_id, minutes
            )
            embed = EmbedHandler.manual_away_message_embed(ctx, user, minutes)
            await ctx.send(embed=embed)

            self.logger.info(
                f"Admin {ctx.author.name} marked {user.display_name} as away for {minutes} minutes"
            )
        except Exception as e:
            self.logger.error(f"Error in set_away_status: {e}")
            await ctx.send("An error occurred while setting the away status.")

    @commands.command(name="clearaway")
    @commands.has_permissions(administrator=True)
    async def clear_away_status(self, ctx, user: discord.Member):
        """Manually clear a user's away status (admin only)"""
        try:
            user_id = user.id

            # Check if user is away
            if user_id not in self.away_users:
                await ctx.send(f"❌ {user.mention} is not currently marked as away.")
                return

            # Clear away status
            del self.away_users[user_id]
            embed = EmbedHandler.status_cleared_message_embed(user)
            await ctx.send(embed=embed)
            self.logger.info(
                f"Admin {ctx.author.name} cleared away status for {user.display_name}"
            )
        except Exception as e:
            self.logger.error(f"Error in clear_away_status: {e}")
            await ctx.send("An error occurred while clearing the away status.")

    def _should_track_channel(self, channel_id, settings):
        """Determine if we should track messages in this channel"""
        # List of specific channels to target
        allowed_channel_ids = [settings["channel_id"]]

        # Check if the channel_id is in the allowed list
        return channel_id in allowed_channel_ids

    async def _is_admin(self, user_id):
        """Check if a user has admin permissions"""
        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if member and member.guild_permissions.administrator:
                return True
        return False

    async def _handle_away_message(self, message, match, settings):
        """Handle when a user announces they're going away"""
        try:
            if not self.db.is_work_hours(settings):
                await message.channel.send(
                    "⏰ **Sorry, I can only track away time during work hours!**\n"
                    f"Work hours are from **{settings['work_start_hour']}** to **{settings['work_end_hour']}** on weekdays."
                )
                return  # Only track during work hours

            user_id = message.author.id
            user_name = message.author.display_name
            minutes_away = int(match.group(1))
            guild_id = message.guild.id

            # Check if user is already away
            active_session = self.db.get_active_away_session(user_id, guild_id)
            if active_session:
                await MessageHandler.already_away(message)
                return

            # Check if exceeds maximum single away time
            if minutes_away > settings["max_single_away_minutes"]:
                await MessageHandler.exceeds_single_away(message, minutes_away)
                minutes_away = settings["max_single_away_minutes"]

            # Check daily allowance
            total_today = self.db.get_today_away_time(user_id, guild_id)
            remaining_today = settings["max_daily_away_minutes"] - total_today

            if remaining_today <= 0:
                await MessageHandler.exceeded_daily_limit(message)
            elif minutes_away > remaining_today:
                await MessageHandler.near_daily_limit(
                    message, remaining_today, minutes_away
                )

            # Record away status in the database
            self.db.add_active_away_session(user_id, user_name, guild_id, minutes_away)

            # Acknowledge
            channel = self.bot.get_channel(settings["channel_id"])
            await MessageHandler.away_acknowledge(message, minutes_away, channel)
            self.logger.info(
                f"User {user_name} ({user_id}) marked away for {minutes_away} minutes at {datetime.now()}"
            )
        except Exception as e:
            self.logger.error(f"Error in _handle_away_message: {e}")
            await message.channel.send(
                "An error occurred while processing your away message."
            )

    async def _handle_return_message(self, message, settings):
        """Handle when a user announces they've returned"""
        try:
            user_id = message.author.id
            user_name = message.author.display_name
            guild_id = message.guild.id

            # Check if user was away
            active_session = self.db.get_active_away_session(user_id, guild_id)
            if not active_session:
                return  # User wasn't marked as away

            # Calculate time away
            now = datetime.now().time()
            start_time = active_session["start_time"] # Time object

            expected_minutes = active_session["expected_minutes"]

            time_diff = datetime.combine(datetime.today(), now) - datetime.combine(
                datetime.today(), start_time
            )
            actual_minutes = int(time_diff.total_seconds() / 60)

            # Calculate lateness beyond grace period
            late_minutes = max(
                0,
                actual_minutes - expected_minutes - settings["grace_period_minutes"],
            )

            # Calculate percentage fee if applicable
            accumulated_percentage = 0
            if late_minutes > 0:
                accumulated_percentage = (
                    late_minutes * settings["fee_percentage_per_minute"]
                )

            # Record session
            self.db.record_away_session(
                user_id,
                user_name,
                message.guild.id,
                datetime.combine(datetime.today(), start_time).strftime("%H:%M:%S"), # Time string
                now.strftime("%H:%M:%S"),
                expected_minutes,
                actual_minutes,
                accumulated_percentage,
            )

            # Update daily totals
            daily_over_limit, daily_fee = self.db.update_daily_totals(
                user_id,
                user_name,
                message.guild.id,
                actual_minutes,
                settings["max_daily_away_minutes"],
                settings["fee_percentage_per_minute"],
            )

            # Clear away status
            self.db.remove_active_away_session(user_id, guild_id)

            # Send response based on outcome
            channel = self.bot.get_channel(settings["channel_id"])
            if late_minutes > 0 and daily_over_limit > 0:
                await MessageHandler.return_late_and_daily_over(
                    message,
                    actual_minutes,
                    expected_minutes,
                    late_minutes,
                    accumulated_percentage,
                    daily_over_limit,
                    accumulated_percentage + daily_fee,
                    settings["grace_period_minutes"],
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
                await MessageHandler.daily_over_limit(
                    message, daily_over_limit, daily_fee
                )
            else:
                channel = self.bot.get_channel(settings["channel_id"])
                await MessageHandler.return_on_time(message, actual_minutes, channel)

            self.logger.info(
                f"User {user_name} ({user_id}) returned after {actual_minutes} minutes, expected {expected_minutes}"
            )
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"Error in _handle_return_message: {e}")
            await message.channel.send(
                "An error occurred while processing your return message."
            )
