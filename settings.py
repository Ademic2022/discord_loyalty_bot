import asyncio
import discord
from discord.ext import commands
from datetime import datetime
import re
from utils.db_manager import DatabaseManager


class ServerSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # Create default settings for this server if not already present
        server_settings = self.db.get_server_settings(guild.id)

        # Try to send a welcome message and prompt for settings
        try:
            channel = None
            system_channel = guild.system_channel
            if (
                system_channel
                and system_channel.permissions_for(guild.me).send_messages
            ):
                channel = system_channel
            else:
                for ch in guild.text_channels:
                    if ch.permissions_for(guild.me).send_messages:
                        channel = ch
                        break
                else:
                    # logger.warning(
                    #     f"Could not find a channel to send welcome message in {guild.name}"
                    # )
                    return

            # Retrieve the default prefix from the server settings
            prefix = self.db.get_server_settings(guild.id)["command_prefix"]

            # Send a welcome message
            embed = discord.Embed(
                title="Thanks for adding me!",
                description=f"Use `{prefix}help` to see all available commands.\n"
                f"Let's get started by setting up some configuration options.",
                color=discord.Color.green(),
            )
            await channel.send(embed=embed)

            # Prompt for settings (prefix, announcement channel, grace period)
            admin = guild.owner  # Get the server owner (admin)
            if admin:
                dm_channel = await admin.create_dm()

                # Send a message to the admin asking for the prefix
                await dm_channel.send(
                    "Hello! Thank you for adding me to your server. Let's start with the setup.\n"
                    "What would you like to set as the command prefix for this server? (Reply with the new prefix)"
                )

                def check(msg):
                    return msg.author == admin and isinstance(
                        msg.channel, discord.DMChannel
                    )

                prefix_msg = await self.bot.wait_for(
                    "message", check=check, timeout=300
                )  # 5 minute timeout
                new_prefix = prefix_msg.content
                if len(new_prefix) > 5:
                    await dm_channel.send(
                        "Prefix must be 5 characters or less. Keeping the default prefix."
                    )
                else:
                    self.db.update_server_setting(
                        guild.id, "command_prefix", new_prefix
                    )
                    await dm_channel.send(f"Prefix set to: `{new_prefix}`")

                # Ask for the announcement channel
                await dm_channel.send(
                    "Next, please mention the text channel where you'd like me to send announcements."
                )
                channel_msg = await self.bot.wait_for(
                    "message", check=check, timeout=300
                )
                mention_channel = re.findall(
                    r"<#(\d+)>", channel_msg.content
                )  # Extract channel ID from mention

                if mention_channel:
                    announcement_channel = guild.get_channel(int(mention_channel[0]))
                    self.db.update_server_setting(
                        guild.id, "announcement_channel_id", announcement_channel.id
                    )
                    await dm_channel.send(
                        f"Announcement channel set to: {announcement_channel.mention}"
                    )
                else:
                    await dm_channel.send(
                        "No valid channel mentioned. Keeping the default channel."
                    )

                # Ask for the grace period
                await dm_channel.send(
                    "Finally, please specify the grace period in minutes (0-60):"
                )
                grace_period_msg = await self.bot.wait_for(
                    "message", check=check, timeout=300
                )
                try:
                    grace_period = int(grace_period_msg.content)
                    if 0 <= grace_period <= 60:
                        self.db.update_server_setting(
                            guild.id, "grace_period_minutes", grace_period
                        )
                        await dm_channel.send(
                            f"Grace period set to: {grace_period} minutes"
                        )
                    else:
                        await dm_channel.send(
                            "Invalid grace period value. Keeping the default setting."
                        )
                except ValueError:
                    await dm_channel.send("Invalid input. Keeping the default setting.")

        except asyncio.TimeoutError:
            # logger.error(f"Setup process timed out for {guild.name} (ID: {guild.id})")
            await channel.send(
                "Setup timed out. You can configure the settings manually using the commands later."
            )
        except Exception as e:
            print(f"Error sending setup prompt: {e}")

    @commands.command(name="prefix")
    @commands.has_permissions(administrator=True)
    async def change_prefix(self, ctx, new_prefix):
        """Change the command prefix for this server"""
        if len(new_prefix) > 5:
            await ctx.send("Prefix must be 5 characters or less.")
            return

        print("change_prefix")
        is_success = self.db.update_server_setting(
            ctx.guild.id, "command_prefix", new_prefix
        )
        print("is_success", is_success)
        await ctx.send(f"Command prefix updated to: `{new_prefix}`")

    @commands.command(name="set_channel")
    @commands.has_permissions(administrator=True)
    async def set_announcement_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the announcement channel for this server"""
        if channel is None:
            channel = ctx.channel

        self.db.update_server_setting(
            ctx.guild.id, "announcement_channel_id", channel.id
        )
        await ctx.send(f"Announcement channel set to: {channel.mention}")

    @commands.command(name="set_grace")
    @commands.has_permissions(administrator=True)
    async def set_grace_period(self, ctx, minutes: int):
        """Set the grace period in minutes"""
        if minutes < 0 or minutes > 30:
            await ctx.send("Grace period must be between 0 and 30 minutes.")
            return

        self.db.update_server_setting(ctx.guild.id, "grace_period_minutes", minutes)
        await ctx.send(f"Grace period updated to: {minutes} minutes")

    @commands.command(name="settings")
    @commands.has_permissions(administrator=True)
    async def show_settings(self, ctx):
        """Display all settings for this server"""
        settings = self.db.get_server_settings(ctx.guild.id)
        print("settings", settings)

        embed = discord.Embed(
            title="Server Settings",
            color=discord.Color.blue(),
            timestamp=datetime.now(),
        )

        embed.add_field(
            name="Prefix", value=f"`{settings['command_prefix']}`", inline=True
        )

        channel = ctx.guild.get_channel(settings["channel_id"])
        channel_value = channel.mention if channel else "Not set"
        embed.add_field(name="Announcement Channel", value=channel_value, inline=True)

        embed.add_field(
            name="Grace Period",
            value=f"{settings['grace_period_minutes']} minutes",
            inline=True,
        )
        embed.add_field(
            name="Fee Percentage",
            value=f"{settings['fee_percentage_per_minute']*100:.4f}% per minute",
            inline=True,
        )
        embed.add_field(
            name="Max Single Away",
            value=f"{settings['max_single_away_minutes']} minutes",
            inline=True,
        )
        embed.add_field(
            name="Max Daily Away",
            value=f"{settings['max_daily_away_minutes']} minutes",
            inline=True,
        )
        embed.add_field(
            name="Work Hours",
            value=f"{settings['work_start_hour']} - {settings['work_end_hour']}",
            inline=True,
        )

        await ctx.send(embed=embed)
