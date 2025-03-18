from discord.ext import commands
from utils.commands import MyCommands
from utils.db_manager import DatabaseManager
import discord
from discord.ui import Button, View
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot.onboarding")


class OnBoarding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        logger.info("OnBoarding cog initialized")
        # self.command = MyCommands(bot)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        try:
            logger.info(f"Bot joined guild: {guild.name} (ID: {guild.id})")

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

                embed.set_footer(
                    text="Setup is required before the bot can start monitoring."
                )

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
                        dm_view.add_item(setup_dm_button)
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
            
            custom_id = interaction.data.get('custom_id')

            logger.info(
                f"Button pressed: {custom_id} by {interaction.user.name}"
            )

            # Handle button clicks
            if (
                custom_id == "setup_button"
                or custom_id == "setup_dm_button"
            ):
                # Only allow admins to use setup
                if interaction.user.guild_permissions.administrator:
                    # Acknowledge the interaction first
                    await interaction.response.defer(ephemeral=True)

                    # Call your setup command logic here
                    await interaction.followup.send(
                        "Starting setup wizard...", ephemeral=True
                    )
                    # self.command._register_setup_command()
                    # You would typically call your actual setup command logic here
                else:
                    await interaction.response.send_message(
                        "You need administrator permissions to use this command.",
                        ephemeral=True,
                    )

            elif custom_id == "settings_button":
                await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(
                    "Opening settings menu...", ephemeral=True
                )
                # self.command._register_setup_command()

            elif custom_id == "serverinfo_button":
                await interaction.response.defer(ephemeral=True)
                # Get server info
                guild = interaction.guild
                embed = discord.Embed(
                    title=f"{guild.name} Information", color=discord.Color.blue()
                )
                embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
                embed.add_field(
                    name="Members", value=str(guild.member_count), inline=True
                )
                embed.add_field(
                    name="Created On",
                    value=guild.created_at.strftime("%Y-%m-%d"),
                    inline=True,
                )

                await interaction.followup.send(embed=embed, ephemeral=True)

            elif custom_id == "userinfo_button":
                await interaction.response.defer(ephemeral=True)
                # Get user info
                user = interaction.user
                embed = discord.Embed(
                    title=f"{user.name} Information", color=discord.Color.blue()
                )
                embed.add_field(
                    name="Joined Server",
                    value=user.joined_at.strftime("%Y-%m-%d"),
                    inline=True,
                )
                embed.add_field(
                    name="Discord Member Since",
                    value=user.created_at.strftime("%Y-%m-%d"),
                    inline=True,
                )
                embed.add_field(
                    name="Roles",
                    value=", ".join([role.name for role in user.roles[1:]]) or "None",
                    inline=False,
                )

                await interaction.followup.send(embed=embed, ephemeral=True)

            elif (
                custom_id == "help_button"
                or custom_id == "help_dm_button"
            ):
                await interaction.response.defer(ephemeral=True)

                help_embed = discord.Embed(
                    title="Bot Help",
                    description="Here's how to use the productivity monitoring bot:",
                    color=discord.Color.green(),
                )

                help_embed.add_field(
                    name="Setup",
                    value="Configure the bot for your server. Admin only.",
                    inline=False,
                )

                help_embed.add_field(
                    name="Settings",
                    value="Adjust monitoring parameters and notification settings.",
                    inline=False,
                )

                help_embed.add_field(
                    name="Server Info",
                    value="View statistics about your server.",
                    inline=False,
                )

                help_embed.add_field(
                    name="User Info",
                    value="View information about a specific user.",
                    inline=False,
                )

                await interaction.followup.send(embed=help_embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in on_interaction: {str(e)}")
            logger.error(traceback.format_exc())
