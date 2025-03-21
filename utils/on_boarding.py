from discord.ext import commands
from cogs.embed import EmbedHandler
from utils.db_manager import DatabaseManager
import discord
from discord.ui import Button, View
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot.onboarding")


class OnBoarding(commands.Cog):
    def __init__(self, bot, my_commands):
        self.bot = bot
        self.db = DatabaseManager()
        logger.info("OnBoarding cog initialized")
        self.commands = my_commands

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        try:

            logger.info(f"Bot joined guild: {guild.name} (ID: {guild.id})")

            # Save default configuration settings for the new guild
            self.db.save_guild_config(guild.id, {})
            logger.info(
                f"Default configuration saved for guild: {guild.name} (ID: {guild.id})"
            )

            # Find the best channel to send the welcome message
            target_channel = None

            # First check if there's a system channel
            if (
                guild.system_channel
                and guild.system_channel.permissions_for(guild.me).send_messages
            ):
                target_channel = guild.system_channel
                logger.info(f"Using system channel: {target_channel.name}")

            # If no system channel, try to find a general channel
            if not target_channel:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        if channel.name.lower() in [
                            "general",
                            "chat",
                            "main",
                            "lobby",
                            "welcome",
                        ]:
                            target_channel = channel
                            logger.info(f"Using general channel: {target_channel.name}")
                            break

            # If still no channel found, use the first text channel where the bot can send messages
            if not target_channel:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        target_channel = channel
                        logger.info(
                            f"Using first available channel: {target_channel.name}"
                        )
                        break

            if target_channel:
                # Create an embed for the welcome message
                embed = EmbedHandler.welcome_embed()
                # Create buttons for each command
                setup_button = Button(
                    label="Setup",
                    style=discord.ButtonStyle.primary,
                    custom_id="setup_button",
                    emoji="⚙️",
                )
                settings_button = Button(
                    label="Settings",
                    style=discord.ButtonStyle.secondary,
                    custom_id="settings_button",
                    emoji="🔧",
                )
                server_info_button = Button(
                    label="Server Info",
                    style=discord.ButtonStyle.secondary,
                    custom_id="serverinfo_button",
                    emoji="📊",
                )
                user_info_button = Button(
                    label="User Info",
                    style=discord.ButtonStyle.secondary,
                    custom_id="userinfo_button",
                    emoji="👤",
                )
                help_button = Button(
                    label="Help",
                    style=discord.ButtonStyle.success,
                    custom_id="help_button",
                    emoji="❓",
                )

                # Create a view and add the buttons
                view = View(
                    timeout=None
                )  # No timeout means buttons stay active indefinitely
                view.add_item(setup_button)
                view.add_item(settings_button)
                view.add_item(server_info_button)
                view.add_item(user_info_button)
                view.add_item(help_button)

                # Send the welcome message with buttons
                logger.info(
                    f"Attempting to send welcome message to channel: {target_channel.name}"
                )
                await target_channel.send(embed=embed, view=view)
                logger.info("Welcome message sent successfully")

                # Optionally, you can also send a direct message to the server owner
                try:
                    owner = guild.owner
                    if owner:
                        logger.info(
                            f"Attempting to send DM to server owner: {owner.name}"
                        )
                        # Create a simplified button for the DM
                        setup_dm_button = Button(
                            label="Setup Bot",
                            style=discord.ButtonStyle.primary,
                            custom_id="setup_dm_button",
                            emoji="⚙️",
                        )
                        help_dm_button = Button(
                            label="Help",
                            style=discord.ButtonStyle.success,
                            custom_id="help_dm_button",
                            emoji="❓",
                        )

                        dm_view = View(timeout=None)
                        # dm_view.add_item(setup_dm_button)
                        dm_view.add_item(help_dm_button)

                        await owner.send(
                            f"👋 Hello! Your server **{guild.name}** has added me. "
                            f"To get started, please use the Setup button below to configure the bot for your specific needs.",
                            view=dm_view,
                        )
                        logger.info("DM sent successfully to server owner")
                except discord.Forbidden:
                    logger.warning("Cannot send DM to the server owner - forbidden")
                except Exception as e:
                    logger.error(f"Error sending DM to owner: {str(e)}")
            else:
                logger.warning(
                    f"No suitable channel found in guild {guild.name} (ID: {guild.id})"
                )
        except Exception as e:
            logger.error(f"Error in on_guild_join: {str(e)}")
            logger.error(traceback.format_exc())

    # Add button callback handlers
    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        try:
            if not interaction.type == discord.InteractionType.component:
                return

            custom_id = interaction.data.get("custom_id")
            # Handle button clicks
            if custom_id == "setup_button" or custom_id == "setup_dm_button":
                await self.commands.setup(interaction)
            elif custom_id == "settings_button":
                await self.commands.settings(interaction)
            elif custom_id == "serverinfo_button":
                await self.commands.serverinfo(interaction)
            elif custom_id == "userinfo_button":
                await self.commands.userinfo(interaction)
            elif custom_id == "help_button" or custom_id == "help_dm_button":
                await self.commands.help(interaction)

        except Exception as e:
            logger.error(f"Error in on_interaction: {str(e)}")
            logger.error(traceback.format_exc())
