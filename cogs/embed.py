import discord
from config import Config


class EmbedHandler:
    @staticmethod
    def away_acknowledge_embed(message, minutes_away):
        embed = discord.Embed(
            title="# 👋 Away Status",
            description=f"{message.author.mention} is now marked as away",
            color=discord.Color.blue(),
        )

        # Add field with time information
        embed.add_field(
            name="Expected Return", value=f"**In {minutes_away} minutes**", inline=False
        )

        # Add instructions
        embed.add_field(
            name="How to Return",
            value="Type `back` in the channel when you return",
            inline=False,
        )

        # Optional footer
        embed.set_footer(text="Enjoy your break!")

        return embed

    @staticmethod
    def return_on_time_embed(message, actual_minutes):
        embed = discord.Embed(
            title="✅ On-Time Return",
            description=f"{message.author.mention} has returned after {actual_minutes} minutes",
            color=discord.Color.green(),
        )

        # Add a congratulatory message
        embed.add_field(
            name="Status",
            value="**Perfect timing!** Thanks for returning as scheduled.",
            inline=False,
        )

        # Add a footer
        embed.set_footer(text="Keep up the good work!")

        return embed

    @staticmethod
    def return_late_embed(
        message,
        actual_minutes,
        expected_minutes,
        late_minutes,
        accumulated_percentage,
    ):
        embed = discord.Embed(
            title="⏰ Attendance Update",
            description=f"{message.author.mention} you returned after {actual_minutes} minutes",
            color=discord.Color.orange(),  # Orange-red color
        )

        # Add fields with relevant information
        embed.add_field(
            name="Lateness Details",
            value=f"**{late_minutes}** minutes beyond your stated {expected_minutes} min + grace period",
            inline=False,
        )

        embed.add_field(
            name="Penalty", value=f"**{accumulated_percentage:.2%}**", inline=True
        )

        # Add a footer with additional context if needed
        embed.set_footer(text="Try to be on time for your next break!")

        # You can also add a thumbnail image
        # embed.set_thumbnail(url="https://i.imgur.com/YOUR_CLOCK_IMAGE.png")
        return embed

    @staticmethod
    def daily_over_limit_embed(message, daily_over_limit, daily_fee):
        embed = discord.Embed(
            title="⚠️ Daily Limit Exceeded",
            description=f"{message.author.mention} returned on time, but has exceeded their daily away allowance",
            color=0xFFC107,  # Amber/warning color
        )

        # Add fields with relevant information
        embed.add_field(
            name="Limit Exceeded By",
            value=f"**{daily_over_limit}** minutes today",
            inline=True,
        )

        embed.add_field(name="Daily Penalty", value=f"**{daily_fee:.2%}**", inline=True)

        # Add a footer with additional context
        embed.set_footer(text="Please be mindful of your total daily break time")

        return embed

    @staticmethod
    def return_late_and_daily_over_embed(
        message,
        actual_minutes,
        expected_minutes,
        late_minutes,
        accumulated_percentage,
        daily_over_limit,
        total_fee,
        grace_period,
    ):
        embed = discord.Embed(
            title="⏰ Late Return + Daily Limit Exceeded",
            description=f"{message.author.mention} has returned after {actual_minutes} minutes",
            color=discord.Color.dark_red(),  # Deeper red color for double penalty
        )

        # Late return information
        embed.add_field(
            name="Late Return",
            value=f"**{late_minutes}** minutes beyond your stated {expected_minutes} min + {grace_period} min grace period",
            inline=False,
        )

        embed.add_field(
            name="Return Penalty",
            value=f"**{accumulated_percentage:.2%}**",
            inline=True,
        )

        # Daily limit information
        embed.add_field(
            name="Daily Limit Exceeded By",
            value=f"**{daily_over_limit}** minutes",
            inline=True,
        )

        # Total penalty (highlighted)
        embed.add_field(
            name="Total Penalty", value=f"**{total_fee:.2%}**", inline=False
        )

        # Add a footer with additional context
        embed.set_footer(text="Please manage your time more carefully")

        return embed

    @staticmethod
    def already_away_embed(message):
        embed = discord.Embed(
            title="⏳ Already Away",
            description=f"{message.author.mention} is currently on a break",
            color=discord.Color.blue(),  # Blue color
        )

        # Add instruction field
        embed.add_field(
            name="Action Required",
            value="Please type `back` when you return",
            inline=False,
        )

        # Add a footer with additional context if needed
        embed.set_footer(text="Your break timer is still running")

        return embed

    @staticmethod
    def exceeds_single_away_embed(message, minutes_away):
        embed = discord.Embed(
            title="⚠️ Time Away Limit Exceeded",
            description=f"{message.author.mention} requested too much time away",
            color=0xFFD700,  # Gold/yellow warning color
        )

        # Add fields with the important information
        embed.add_field(
            name="Requested Time", value=f"**{minutes_away}** minutes", inline=True
        )

        embed.add_field(
            name="Maximum Allowed",
            value=f"**{Config.MAX_SINGLE_AWAY_MINUTES}** minutes",
            inline=True,
        )

        embed.add_field(
            name="Result",
            value=f"You've been marked away for **{Config.MAX_SINGLE_AWAY_MINUTES}** minutes instead",
            inline=False,
        )

        # Add a footer with additional context
        embed.set_footer(text="Please check the away time limits in the server rules")

        return embed

    @staticmethod
    def exceeded_daily_limit_embed(message):
        embed = discord.Embed(
            title="⚠️ Daily Away Time Limit Reached",
            description=f"{message.author.mention} has reached their daily away time limit",
            color=discord.Color.red(),  # Red color for more serious warning
        )

        # Add fields with the important information
        embed.add_field(
            name="Daily Limit",
            value=f"You have used all **{Config.MAX_DAILY_AWAY_MINUTES}** minutes of allowed away time today",
            inline=False,
        )

        embed.add_field(
            name="Penalty Notice",
            value=f"Additional time away will incur a lateness penalty of **{Config.FEE_PERCENTAGE_PER_MINUTE:.4%}** per minute",
            inline=False,
        )

        # Add a footer with additional context
        embed.set_footer(text="The counter will reset at midnight server time")

        return embed

    @staticmethod
    def away_status_message_embed(
        ctx,
        elapsed_minutes,
        expected_minutes,
        remaining_minutes,
        total_including_current,
        MAX_DAILY_AWAY_MINUTES,
        remaining_today,
    ):
        embed = discord.Embed(
            title="🕒 Away Status Update",
            description=f"{ctx.author.mention} has been away for **{elapsed_minutes}** minutes in this session.",
            color=discord.Color.blue(),
        )

        # Current session information
        embed.add_field(
            name="Current Session",
            value=f"• Expected: **{expected_minutes}** minutes\n• Remaining: **{remaining_minutes}** minutes",
            inline=False,
        )

        # Daily totals
        embed.add_field(
            name="Daily Summary",
            value=f"• Used: **{total_including_current}** / {MAX_DAILY_AWAY_MINUTES} minutes\n• Remaining: **{remaining_today}** minutes",
            inline=False,
        )

        # Progress bar for daily usage (optional)
        progress = min(1.0, total_including_current / MAX_DAILY_AWAY_MINUTES)
        bar_length = 10
        filled_bars = int(progress * bar_length)
        progress_bar = "█" * filled_bars + "░" * (bar_length - filled_bars)

        embed.add_field(
            name="Daily Usage",
            value=f"`{progress_bar}` {int(progress * 100)}%",
            inline=False,
        )

        # You can add a thumbnail if desired
        # embed.set_thumbnail(url="https://i.imgur.com/YOUR_TIMER_IMAGE.png")

        return embed

    @staticmethod
    def send_not_away_status_message_embed(
        ctx, total_today, MAX_DAILY_AWAY_MINUTES, remaining_today
    ):
        embed = discord.Embed(
            title="✅ Status Check",
            description=f"{ctx.author.mention} is currently **not marked as away**.",
            color=discord.Color.green(),
        )

        # Daily usage summary
        embed.add_field(
            name="Daily Away Time",
            value=f"• Used: **{total_today}** / {MAX_DAILY_AWAY_MINUTES} minutes\n• Remaining: **{remaining_today}** minutes",
            inline=False,
        )

        # Progress bar for daily usage
        progress = min(1.0, total_today / MAX_DAILY_AWAY_MINUTES)
        bar_length = 10
        filled_bars = int(progress * bar_length)
        progress_bar = "█" * filled_bars + "░" * (bar_length - filled_bars)

        embed.add_field(
            name="Daily Usage",
            value=f"`{progress_bar}` {int(progress * 100)}%",
            inline=False,
        )

        return embed

    @staticmethod
    def manual_away_message_embed(ctx, user, minutes):
        embed = discord.Embed(
            title="✅ Manual Away Status",
            description=f"{user.mention} has been **manually marked as away**",
            color=discord.Color.yellow(),
        )

        # Away duration
        embed.add_field(name="Duration", value=f"**{minutes}** minutes", inline=False)

        # Optional: Add footer with admin info
        embed.set_footer(text=f"Set by {ctx.author.name}")

        return embed

    @staticmethod
    def status_cleared_message_embed(user):
        embed = discord.Embed(
            title="Status Cleared",
            description=f"✅ {user.mention}'s away status has been cleared.",
            color=discord.Color.green(),
        )
        return embed

    @staticmethod
    def server_info_embed(guild):
        embed = discord.Embed(
            title=f"# {guild.name} Info",
            description="Server information and statistics",
            color=discord.Color.blue(),
        )

        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(
            name="Created On",
            value=guild.created_at.strftime("%B %d, %Y"),
            inline=True,
        )
        embed.add_field(name="Member Count", value=str(guild.member_count), inline=True)
        embed.add_field(name="Channels", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        return embed

    @staticmethod
    def user_info_embed(target_user):
        embed = discord.Embed(
            title=f"# {target_user.display_name}'s Info", color=target_user.color
        )

        embed.add_field(name="Username", value=str(target_user), inline=True)
        embed.add_field(name="ID", value=str(target_user.id), inline=True)
        embed.add_field(
            name="Joined Server",
            value=target_user.joined_at.strftime("%B %d, %Y"),
            inline=True,
        )
        embed.add_field(
            name="Account Created",
            value=target_user.created_at.strftime("%B %d, %Y"),
            inline=True,
        )
        embed.add_field(
            name="Top Role", value=target_user.top_role.mention, inline=True
        )

        if target_user.avatar:
            embed.set_thumbnail(url=target_user.avatar.url)

        return embed

    @staticmethod
    def settings_embed(settings, interaction):
        from datetime import datetime

        embed = discord.Embed(
            title="Server Settings",
            color=discord.Color.blue(),
            timestamp=datetime.now(),
        )

        embed.add_field(
            name="Prefix", value=f"`{settings['command_prefix']}`", inline=True
        )

        channel = interaction.guild.get_channel(
            settings.get("announcement_channel_id") or settings.get("channel_id")
        )
        channel_value = channel.mention if channel else "Not set"
        embed.add_field(name="Announcement Channel", value=channel_value, inline=True)

        embed.add_field(
            name="Grace Period",
            value=f"{settings['grace_period_minutes']} minutes",
            inline=True,
        )

        # Add other fields if they exist in the settings
        if "fee_percentage_per_minute" in settings:
            embed.add_field(
                name="Fee Percentage",
                value=f"{settings['fee_percentage_per_minute']*100:.4f}% per minute",
                inline=True,
            )

        if "max_single_away_minutes" in settings:
            embed.add_field(
                name="Max Single Away",
                value=f"{settings['max_single_away_minutes']} minutes",
                inline=True,
            )

        if "max_daily_away_minutes" in settings:
            embed.add_field(
                name="Max Daily Away",
                value=f"{settings['max_daily_away_minutes']} minutes",
                inline=True,
            )

        if "work_start_hour" in settings and "work_end_hour" in settings:
            embed.add_field(
                name="Work Hours",
                value=f"{settings['work_start_hour']} - {settings['work_end_hour']}",
                inline=True,
            )

        return embed

    @staticmethod
    def bot_setup_complete_embed(settings, selected_channel):
        embed = discord.Embed(
            title="✅ Bot Setup Complete",
            description="Your server has been configured with the following settings:",
            color=discord.Color.green(),
        )

        embed.add_field(
            name="Prefix", value=f"`{settings['command_prefix']}`", inline=True
        )

        embed.add_field(
            name="Announcement Channel",
            value=f"<#{selected_channel.id}>",
            inline=True,
        )

        embed.add_field(
            name="Grace Period",
            value=f"{settings['grace_period_minutes']} minutes",
            inline=True,
        )

        return embed

    @staticmethod
    def welcome_embed():
        embed = discord.Embed(
            title="👋 Thanks for adding me to your server!",
            description="I'm a productivity monitoring bot designed to help track and manage employee time.",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="📝 Getting Started",
            value="Click the Setup button below to configure the bot for your server (Admin only).",
            inline=False,
        )

        embed.add_field(
            name="🔍 Available Actions",
            value="Use the buttons below to access different features:",
            inline=False,
        )

        embed.add_field(
            name="💡 Need Help?",
            value="Click the Help button for more information.",
            inline=False,
        )

        embed.set_footer(text="Setup is required before the bot can start monitoring.")

        return embed

    @staticmethod
    def help_embed():
        """Generate a detailed and user-friendly help embed."""
        embed = discord.Embed(
            title="📘 Bot Help",
            description="Welcome to the Productivity Monitoring Bot! Here's how to use it:",
            color=discord.Color.blue(),
        )

        # General Commands
        embed.add_field(
            name="🛠️ **General Commands**",
            value="Commands available to all users:",
            inline=False,
        )
        embed.add_field(
            name="`!help`",
            value="Displays this help message.",
            inline=True,
        )
        embed.add_field(
            name="`<Int> mins away`",
            value="Mark yourself as away for a specified number of minutes.\nExample: `5 min away`",
            inline=True,
        )
        embed.add_field(
            name="`back`",
            value="Mark yourself as returned from being away.\nExample: `back`",
            inline=True,
        )
        embed.add_field(
            name="`!status`",
            value="Check your current away status and remaining time.\nExample: `!status`",
            inline=True,
        )
        embed.add_field(
            name="`!report <date>`",
            value="Get a report of your away time for a specific date (YYYY-MM-DD).\nExample: `!report 2023-10-01`",
            inline=True,
        )

        # Admin Commands
        embed.add_field(
            name="🔧 **Admin Commands**",
            value="Commands available to server administrators:",
            inline=False,
        )
        embed.add_field(
            name="`!setup`",
            value="Configure the bot for your server.\nExample: `!setup`",
            inline=True,
        )
        embed.add_field(
            name="`!settings`",
            value="Adjust monitoring parameters and notification settings.\nExample: `!settings`",
            inline=True,
        )
        embed.add_field(
            name="`!setaway <user> <minutes>`",
            value="Manually mark a user as away for a specified number of minutes.\nExample: `!setaway @User 30`",
            inline=True,
        )
        embed.add_field(
            name="`!clearaway <user>`",
            value="Manually clear a user's away status.\nExample: `!clearaway @User`",
            inline=True,
        )
        embed.add_field(
            name="`!serverinfo`",
            value="View statistics about your server.\nExample: `!serverinfo`",
            inline=True,
        )

        # Additional Information
        embed.add_field(
            name="📝 **Additional Information**",
            value="For more details, visit the [documentation](https://voltislab.com/docs).",
            inline=False,
        )

        # Footer
        embed.set_footer(text="Need more help? Contact support@voltislab.com.")

        return embed
