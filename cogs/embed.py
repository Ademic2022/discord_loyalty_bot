import discord
from config import Config


class EmbedHandler:
    @staticmethod
    def away_acknowledge_embed(message, minutes_away):
        embed = discord.Embed(
            title="👋 Away Status",
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
