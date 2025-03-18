import discord
import logging
from discord import app_commands
from cogs.embed import EmbedHandler

logger = logging.getLogger("discord_bot")


class MyCommands:
    def __init__(self, bot):
        """Initialize the commands class with the bot instance."""
        self.bot = bot
        self._register_commands()

    def _register_commands(self):
        """Register all slash commands."""

        # Setup Command
        self._register_setup_command()

        # You can organize more command categories here
        self._register_utility_commands()
        self._register_moderation_commands()
        # self._register_fun_commands()

        logger.info("All commands registered successfully")

    def _register_setup_command(self):
        # Create a setup modal for the initial settings
        class SetupModal(discord.ui.Modal, title="Bot Setup"):
            prefix = discord.ui.TextInput(
                label="Command Prefix",
                placeholder="Enter a prefix (max 5 characters)",
                default="!",
                max_length=5,
                required=True,
            )

            grace_period = discord.ui.TextInput(
                label="Grace Period (minutes)",
                placeholder="Enter a value between 0-60",
                default="5",
                required=True,
            )

            # fee_percentage = discord.ui.TextInput(
            #     label="Fee Percentage per Minute",
            #     placeholder="Enter a value like 0.0007",
            #     default="0.0007",
            #     required=True,
            # )

            # max_single_away = discord.ui.TextInput(
            #     label="Max Single Away Minutes",
            #     placeholder="Enter a value like 40",
            #     default="40",
            #     required=False,
            # )

            # max_daily_away = discord.ui.TextInput(
            #     label="Max Daily Away Minutes",
            #     placeholder="Enter a value like 90",
            #     default="90",
            #     required=False,
            # )

            # work_start_time = discord.ui.TextInput(
            #     label="Work Start Time (24-hour format, HH:MM)",
            #     placeholder="Enter a value like 09:00",
            #     default="09:00",
            #     required=False,
            # )

            # work_end_time = discord.ui.TextInput(
            #     label="Work End Time (24-hour format, HH:MM)",
            #     placeholder="Enter a value like 17:00",
            #     default="17:00",
            #     required=False,
            # )

            async def on_submit(self, modal_interaction: discord.Interaction):
                try:
                    # Import here to avoid circular import issues
                    from utils.db_manager import DatabaseManager

                    db = DatabaseManager()
                    guild = modal_interaction.guild

                    # Update prefix
                    db.update_server_setting(
                        guild.id, "command_prefix", self.prefix.value
                    )

                    # Validate and update grace period
                    try:
                        grace_minutes = int(self.grace_period.value)
                        if 0 <= grace_minutes <= 60:
                            db.update_server_setting(
                                guild.id, "grace_period_minutes", grace_minutes
                            )
                        else:
                            await modal_interaction.response.send_message(
                                "Grace period must be between 0 and 60 minutes. Using default value.",
                                ephemeral=True,
                            )
                            return
                    except ValueError:
                        await modal_interaction.response.send_message(
                            "Invalid grace period value. Using default value.",
                            ephemeral=True,
                        )
                        return

                    await modal_interaction.response.send_message(
                        f"✅ Initial settings saved!\n"
                        f"• Prefix: `{self.prefix.value}`\n"
                        f"• Grace Period: {grace_minutes} minutes\n\n"
                        f"Now, please select an announcement channel using the dropdown below.",
                        view=ChannelSelectView(guild, modal_interaction.user),
                        ephemeral=True,
                    )
                except Exception as e:
                    logger.error(f"Error in setup modal submission: {e}")
                    await modal_interaction.response.send_message(
                        f"An error occurred during setup: {str(e)}", ephemeral=True
                    )

        # Create channel selection view
        class ChannelSelectView(discord.ui.View):
            def __init__(self, guild, user):
                super().__init__(timeout=300)  # 5 minute timeout
                self.guild = guild
                self.user = user

            @discord.ui.select(
                cls=discord.ui.ChannelSelect,
                channel_types=[discord.ChannelType.text],
                placeholder="Select announcement channel",
                min_values=1,
                max_values=1,
            )
            async def channel_select(
                self, select_interaction: discord.Interaction, select
            ):
                # Import here to avoid circular import issues
                from utils.db_manager import DatabaseManager

                db = DatabaseManager()

                selected_channel = select.values[0]

                # Update the announcement channel in the database
                db.update_server_setting(
                    self.guild.id, "announcement_channel_id", selected_channel.id
                )

                # Disable the select menu after selection
                select.disabled = True
                await select_interaction.response.edit_message(
                    content=f"✅ Announcement channel set to: {selected_channel.mention}\n\nSetup is now complete! You can adjust these settings later with `/settings`.",
                    view=self,
                )

                # Create settings embed for feedback
                settings = db.get_server_settings(self.guild.id)

                embed = EmbedHandler.bot_setup_complete_embed(
                    settings, selected_channel
                )

                # Send the settings summary
                try:
                    await self.user.send(embed=embed)
                except discord.Forbidden:
                    # If we can't DM the user, send to the channel
                    system_channel = self.guild.system_channel
                    if (
                        system_channel
                        and system_channel.permissions_for(self.guild.me).send_messages
                    ):
                        await system_channel.send(embed=embed)
                    else:
                        # Try to send to the selected announcement channel
                        await selected_channel.send(embed=embed)

        @self.bot.tree.command(
            name="setup", description="Walk through first time bot setup"
        )
        @app_commands.checks.has_permissions(administrator=True)
        async def setup(interaction: discord.Interaction):
            # Show the setup modal
            await interaction.response.send_modal(SetupModal())

        # Register a command to view and update settings
        @self.bot.tree.command(
            name="settings", description="View or update bot settings"
        )
        @app_commands.checks.has_permissions(administrator=True)
        async def settings(interaction: discord.Interaction):
            from utils.db_manager import DatabaseManager

            db = DatabaseManager()
            settings = db.get_server_settings(interaction.guild.id)

            embed = EmbedHandler.settings_embed(settings, interaction)

            # Create buttons for editing settings
            class SettingsView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=180)  # 3 minute timeout

                @discord.ui.button(
                    label="Edit Prefix", style=discord.ButtonStyle.primary
                )
                async def edit_prefix(
                    self,
                    button_interaction: discord.Interaction,
                    button: discord.ui.Button,
                ):
                    # Create a modal for editing the prefix
                    class PrefixModal(discord.ui.Modal, title="Edit Prefix"):
                        prefix = discord.ui.TextInput(
                            label="New Command Prefix",
                            placeholder="Enter a prefix (max 5 characters)",
                            default=settings["command_prefix"],
                            max_length=5,
                            required=True,
                        )

                        async def on_submit(
                            self, modal_interaction: discord.Interaction
                        ):
                            db.update_server_setting(
                                interaction.guild.id,
                                "command_prefix",
                                self.prefix.value,
                            )
                            await modal_interaction.response.send_message(
                                f"Prefix updated to: `{self.prefix.value}`",
                                ephemeral=True,
                            )

                    await button_interaction.response.send_modal(PrefixModal())

                @discord.ui.button(
                    label="Edit Channel", style=discord.ButtonStyle.primary
                )
                async def edit_channel(
                    self,
                    button_interaction: discord.Interaction,
                    button: discord.ui.Button,
                ):
                    # Create a view with a channel select menu
                    class ChannelSelectView(discord.ui.View):
                        def __init__(self):
                            super().__init__(timeout=60)  # 1 minute timeout

                        @discord.ui.select(
                            cls=discord.ui.ChannelSelect,
                            channel_types=[discord.ChannelType.text],
                            placeholder="Select announcement channel",
                            min_values=1,
                            max_values=1,
                        )
                        async def channel_select(
                            self, select_interaction: discord.Interaction, select
                        ):
                            selected_channel = select.values[0]
                            db.update_server_setting(
                                interaction.guild.id,
                                "announcement_channel_id",
                                selected_channel.id,
                            )
                            await select_interaction.response.send_message(
                                f"Announcement channel updated to: {selected_channel.mention}",
                                ephemeral=True,
                            )

                    await button_interaction.response.send_message(
                        "Select the new announcement channel:",
                        view=ChannelSelectView(),
                        ephemeral=True,
                    )

                @discord.ui.button(
                    label="Edit Grace Period", style=discord.ButtonStyle.primary
                )
                async def edit_grace(
                    self,
                    button_interaction: discord.Interaction,
                    button: discord.ui.Button,
                ):
                    # Create a modal for editing the grace period
                    class GraceModal(discord.ui.Modal, title="Edit Grace Period"):
                        grace_period = discord.ui.TextInput(
                            label="New Grace Period (minutes)",
                            placeholder="Enter a value between 0-60",
                            default=str(settings["grace_period_minutes"]),
                            required=True,
                        )

                        async def on_submit(
                            self, modal_interaction: discord.Interaction
                        ):
                            try:
                                grace_minutes = int(self.grace_period.value)
                                if 0 <= grace_minutes <= 60:
                                    db.update_server_setting(
                                        interaction.guild.id,
                                        "grace_period_minutes",
                                        grace_minutes,
                                    )
                                    await modal_interaction.response.send_message(
                                        f"Grace period updated to: {grace_minutes} minutes",
                                        ephemeral=True,
                                    )
                                else:
                                    await modal_interaction.response.send_message(
                                        "Grace period must be between 0 and 60 minutes.",
                                        ephemeral=True,
                                    )
                            except ValueError:
                                await modal_interaction.response.send_message(
                                    "Invalid grace period value.", ephemeral=True
                                )

                    await button_interaction.response.send_modal(GraceModal())

            await interaction.response.send_message(
                embed=embed, view=SettingsView(), ephemeral=True
            )

    def _register_utility_commands(self):
        # Server Info Command
        @self.bot.tree.command(
            name="serverinfo", description="Shows information about the server"
        )
        async def serverinfo(interaction: discord.Interaction):
            guild = interaction.guild

            embed = EmbedHandler.server_info_embed(guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        # User Info Command
        @self.bot.tree.command(
            name="userinfo", description="Shows information about a user"
        )
        @app_commands.describe(
            user="The user to get information about (leave empty for yourself)"
        )
        async def userinfo(
            interaction: discord.Interaction, user: discord.Member = None
        ):
            target_user = user or interaction.user

            embed = EmbedHandler.user_info_embed(target_user)

            await interaction.response.send_message(embed=embed, ephemeral=True)

    def _register_moderation_commands(self):
        # Kick Command
        @self.bot.tree.command(name="kick", description="Kicks a user from the server")
        @app_commands.describe(
            user="The user to kick", reason="The reason for kicking the user"
        )
        @app_commands.checks.has_permissions(kick_members=True)
        async def kick(
            interaction: discord.Interaction,
            user: discord.Member,
            reason: str = "No reason provided",
        ):
            if (
                user.top_role >= interaction.user.top_role
                and interaction.user.id != interaction.guild.owner_id
            ):
                await interaction.response.send_message(
                    "You cannot kick someone with a higher or equal role.",
                    ephemeral=True,
                )
                return

            try:
                await user.kick(reason=f"Kicked by {interaction.user}: {reason}")
                await interaction.response.send_message(
                    f"✅ Kicked {user.mention} | Reason: {reason}"
                )
                logger.info(
                    f"User {user} was kicked by {interaction.user} for reason: {reason}"
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "I don't have permission to kick that user.", ephemeral=True
                )
            except Exception as e:
                logger.error(f"Error kicking user: {e}")
                await interaction.response.send_message(
                    f"An error occurred: {str(e)}", ephemeral=True
                )

        # Ban Command
        @self.bot.tree.command(name="ban", description="Bans a user from the server")
        @app_commands.describe(
            user="The user to ban",
            reason="The reason for banning the user",
            delete_days="Number of days of messages to delete (0-7)",
        )
        @app_commands.checks.has_permissions(ban_members=True)
        async def ban(
            interaction: discord.Interaction,
            user: discord.Member,
            reason: str = "No reason provided",
            delete_days: int = 1,
        ):
            if (
                user.top_role >= interaction.user.top_role
                and interaction.user.id != interaction.guild.owner_id
            ):
                await interaction.response.send_message(
                    "You cannot ban someone with a higher or equal role.",
                    ephemeral=True,
                )
                return

            try:
                delete_days = max(
                    0, min(7, delete_days)
                )  # Ensure delete_days is between 0 and 7
                await user.ban(
                    reason=f"Banned by {interaction.user}: {reason}",
                    delete_message_days=delete_days,
                )
                await interaction.response.send_message(
                    f"✅ Banned {user.mention} | Reason: {reason}"
                )
                logger.info(
                    f"User {user} was banned by {interaction.user} for reason: {reason}"
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "I don't have permission to ban that user.", ephemeral=True
                )
            except Exception as e:
                logger.error(f"Error banning user: {e}")
                await interaction.response.send_message(
                    f"An error occurred: {str(e)}", ephemeral=True
                )
