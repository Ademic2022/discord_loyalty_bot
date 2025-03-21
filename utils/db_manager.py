import sqlite3
import logging
from datetime import datetime
from config import Config
import traceback


class DatabaseManager:
    def __init__(self, db_path="loyalty_bot.db"):
        self.db_path = db_path
        self.logger = logging.getLogger("discord_bot")
        self.MAX_DAILY_AWAY_MINUTES = Config.MAX_DAILY_AWAY_MINUTES
        self.FEE_PERCENTAGE_PER_MINUTE = Config.FEE_PERCENTAGE_PER_MINUTE
        self.WORK_START_TIME = Config.WORK_START_TIME
        self.WORK_END_TIME = Config.WORK_END_TIME

    def initialize(self):
        """Initialize database tables for loyalty tracking"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS server_settings (
                    guild_id INTEGER PRIMARY KEY,
                    command_prefix TEXT DEFAULT '!',
                    channel_id INTEGER,
                    grace_period_minutes INTEGER DEFAULT 1,
                    fee_percentage_per_minute REAL DEFAULT 0.0007,
                    max_single_away_minutes INTEGER DEFAULT 40,
                    max_daily_away_minutes INTEGER DEFAULT 90,
                    work_start_hour INTEGER DEFAULT 9,
                    work_end_hour INTEGER DEFAULT 17
                )
                """
            )

            # Table to track user away time
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS away_time (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    user_name TEXT NOT NULL,
                    guild_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    expected_minutes INTEGER NOT NULL,
                    actual_minutes INTEGER,
                    fee_amount REAL DEFAULT 0
                )
                """
            )

            # Table to track daily totals
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS away_daily (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    user_name TEXT NOT NULL,
                    guild_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    total_minutes INTEGER DEFAULT 0,
                    over_limit_minutes INTEGER DEFAULT 0,
                    fee_amount REAL DEFAULT 0,
                    UNIQUE(user_id, date, guild_id)
                );
                """
            )

            # Table to track active away sessions
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS active_away_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    user_name TEXT NOT NULL,
                    guild_id INTEGER NOT NULL,
                    start_time TEXT NOT NULL,
                    expected_minutes INTEGER NOT NULL,
                    UNIQUE(user_id, guild_id)
                )
                """
            )

            conn.commit()
            conn.close()
            self.logger.info("Loyalty tracking database tables initialized")
        except Exception as e:
            self.logger.error(f"Error initializing loyalty tracking database: {e}")

    def get_connection(self):
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            self.logger.error(f"Error connecting to database: {e}")
            return None

    def save_guild_config(self, guild_id, config_data):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """INSERT OR REPLACE INTO server_settings 
                        (guild_id, command_prefix, channel_id, 
                        grace_period_minutes, fee_percentage_per_minute, 
                        max_single_away_minutes, max_daily_away_minutes,
                        work_start_hour, work_end_hour)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                guild_id,
                config_data.get("command_prefix", Config.PREFIX),
                config_data.get("channel_id", Config.CHANNEL_ID),
                config_data.get("grace_period_minutes", Config.GRACE_PERIOD_MINUTES),
                config_data.get(
                    "fee_percentage_per_minute", Config.FEE_PERCENTAGE_PER_MINUTE
                ),
                config_data.get(
                    "max_single_away_minutes", Config.MAX_SINGLE_AWAY_MINUTES
                ),
                config_data.get(
                    "max_daily_away_minutes", Config.MAX_DAILY_AWAY_MINUTES
                ),
                config_data.get("work_start_hour", 9),
                config_data.get("work_end_hour", 17),
            ),
        )
        conn.commit()
        conn.close()

    def get_server_settings(self, guild_id, conn=None):
        """Get settings for a specific server, or create with defaults if not exists"""
        connection = conn or sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        try:
            # Try to fetch the server settings
            cursor.execute(
                "SELECT * FROM server_settings WHERE guild_id = ?",
                (guild_id,),
            )
            server = cursor.fetchone()

            if not server:
                return {
                    "command_prefix": Config.PREFIX,
                    "channel_id": Config.CHANNEL_ID,
                    "grace_period_minutes": Config.GRACE_PERIOD_MINUTES,
                    "fee_percentage_per_minute": Config.FEE_PERCENTAGE_PER_MINUTE,
                    "max_single_away_minutes": Config.MAX_SINGLE_AWAY_MINUTES,
                    "max_daily_away_minutes": Config.MAX_DAILY_AWAY_MINUTES,
                    "work_start_hour": Config.WORK_START_TIME,
                    "work_end_hour": Config.WORK_END_TIME,
                }

            # Convert to dictionary
            columns = [description[0] for description in cursor.description]
            server_dict = dict(zip(columns, server))

        except Exception as e:
            print(f"Error while fetching or inserting server settings: {e}")
            server_dict = None

        finally:
            if not conn:
                connection.close()
        return server_dict

    def get_server_setting(self, guild_id, setting_name, conn=None):

        connection = conn or sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        try:
            # Fetch the specific setting from the database
            cursor.execute(
                f"SELECT {setting_name} FROM server_settings WHERE guild_id = ?",
                (guild_id,),
            )
            result = cursor.fetchone()

            if result:
                # Return the value of the setting
                return result[0]
            else:
                return Config.__dict__.get(setting_name.upper())

        except Exception as e:
            print(f"Error while fetching server setting '{setting_name}': {e}")
            return None

        finally:
            if not conn:
                connection.close()

    def update_server_setting(self, guild_id, setting, value):
        """Update a specific setting for a server"""
        print(f"Updating setting: {setting} to {value}")
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        try:
            # Ensure the server exists in our database, reuse the same connection
            self.get_server_settings(guild_id, conn=self.conn)

            # Update the setting
            cursor.execute(
                f"""
                UPDATE server_settings SET {setting} = ? WHERE guild_id = ?
                """,
                (value, guild_id),
            )

            self.conn.commit()

        except Exception as e:
            print(f"Error updating server setting: {e}")
            return False

        finally:
            if self.conn:
                self.conn.close()
                print("Connection closed after updating")

        return True

    def is_work_hours(self, settings):
        """Check if current time is within work hours (e.g., 08:00 - 16:00 on weekdays)."""
        now = datetime.now()
        current_time = now.time()

        # Check if it's a weekday (0 = Monday, 4 = Friday)
        is_weekday = now.weekday() < 5

        # Convert work_start_hour and work_end_hour from strings to datetime.time objects
        try:
            work_start_hour = datetime.strptime(
                settings["work_start_hour"], "%H:%M"
            ).time()
            work_end_hour = datetime.strptime(settings["work_end_hour"], "%H:%M").time()

            print("work_start_hour", work_start_hour)
            print("work_end_hour", work_end_hour)
        except ValueError as e:
            self.logger.error(f"Error parsing work hours: {e}")
            return False

        # Check if current time is between work hours
        is_work_time = work_start_hour <= current_time <= work_end_hour

        return is_weekday and is_work_time

    def get_today_away_time(self, user_id, guild_id):
        """Get total away time for user today in a specific guild"""
        today = datetime.now().strftime("%Y-%m-%d")

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Get from daily tracking
            cursor.execute(
                """
                SELECT total_minutes FROM away_daily
                WHERE user_id = ? AND date = ? AND guild_id = ?
                """,
                (user_id, today, guild_id),
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                return result[0]
            return 0
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"Error getting daily away time: {e}")
            return 0

    def update_daily_totals(
        self,
        user_id,
        user_name,
        guild_id,
        minutes_away,
        max_daily_minutes,
        fee_percentage,
    ):
        """Update daily totals for user away time in a specific guild"""
        today = datetime.now().strftime("%Y-%m-%d")

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Get current daily total
            cursor.execute(
                """
                SELECT total_minutes FROM away_daily
                WHERE user_id = ? AND date = ? AND guild_id = ?
                """,
                (user_id, today, guild_id),
            )

            result = cursor.fetchone()

            if result:
                # Update existing record
                new_total = result[0] + minutes_away
                over_limit = max(0, new_total - max_daily_minutes)
                fee_amount = over_limit * fee_percentage

                cursor.execute(
                    """
                    UPDATE away_daily
                    SET total_minutes = ?,
                        over_limit_minutes = ?,
                        fee_amount = ?
                    WHERE user_id = ? AND date = ? AND guild_id = ?
                    """,
                    (new_total, over_limit, fee_amount, user_id, today, guild_id),
                )
            else:
                # Create new record
                over_limit = max(0, minutes_away - max_daily_minutes)
                fee_amount = over_limit * fee_percentage

                cursor.execute(
                    """
                    INSERT INTO away_daily
                    (user_id, user_name, guild_id, date, total_minutes, over_limit_minutes, fee_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        user_name,
                        guild_id,
                        today,
                        minutes_away,
                        over_limit,
                        fee_amount,
                    ),
                )

            conn.commit()
            conn.close()

            return over_limit, fee_amount
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"Error updating daily totals: {e}")
            return 0, 0

    def record_away_session(
        self,
        user_id,
        user_name,
        guild_id,
        start_time,
        end_time,
        expected_minutes,
        actual_minutes,
        fee_amount,
    ):
        """Record a complete away session in the database for a specific guild"""
        today = datetime.now().strftime("%Y-%m-%d")
        print("Today:", today)
        print("Start time:", start_time)
        print("start_time type:", type(start_time))

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO away_time
                (user_id, user_name, guild_id, date, start_time, end_time, expected_minutes, actual_minutes, fee_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    user_name,
                    guild_id,
                    today,
                    start_time,
                    end_time,
                    expected_minutes,
                    actual_minutes,
                    fee_amount,
                ),
            )

            conn.commit()
            conn.close()
            self.logger.info(
                f"Recorded away session for {user_name} in guild {guild_id}: {actual_minutes} minutes"
            )
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"Error recording away session: {e}")

    def _fetch_away_data(self, date, guild_id, user_id=None):
        """Fetch away data from the database for a specific guild."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # If user_id is provided, fetch data for a specific user, else for all users (admin view)
        if user_id:
            cursor.execute(
                """
                SELECT user_name, total_minutes, over_limit_minutes, fee_amount
                FROM away_daily
                WHERE user_id = ? AND date = ? AND guild_id = ?
                """,
                (user_id, date, guild_id),
            )
            user_record = cursor.fetchone()

            cursor.execute(
                """
                SELECT start_time, end_time, expected_minutes, actual_minutes, fee_amount
                FROM away_time
                WHERE user_id = ? AND date = ? AND guild_id = ?
                ORDER BY start_time
                """,
                (user_id, date, guild_id),
            )
            session_records = cursor.fetchall()

            # Calculate accumulated fee from session records
            accumulated_fee = sum(
                record[4] for record in session_records
            )  # record[4] is fee_amount

            # Add accumulated fee to the user's daily record
            user_record = (*user_record[:3], accumulated_fee)

            return user_record, session_records
        else:
            cursor.execute(
                """
                SELECT user_name, total_minutes, over_limit_minutes, fee_amount
                FROM away_daily
                WHERE date = ? AND guild_id = ?
                ORDER BY total_minutes DESC
                """,
                (date, guild_id),
            )
            daily_records = cursor.fetchall()

            cursor.execute(
                """
                SELECT user_name, start_time, end_time, expected_minutes, actual_minutes, fee_amount
                FROM away_time
                WHERE date = ? AND guild_id = ?
                ORDER BY start_time
                """,
                (date, guild_id),
            )
            session_records = cursor.fetchall()

            # Create a dictionary to accumulate fees for each user
            fee_totals = {}

            for session in session_records:
                user_name = session[0]  # record[0] is user_name
                fee_amount = session[5]  # record[5] is fee_amount

                if user_name not in fee_totals:
                    fee_totals[user_name] = 0.0
                fee_totals[user_name] += fee_amount

            # Update the daily records with accumulated fee amounts
            updated_daily_records = []

            for record in daily_records:
                user_name = record[0]
                accumulated_fee = fee_totals.get(user_name, 0.0)
                updated_daily_record = (*record[:3], accumulated_fee)
                updated_daily_records.append(updated_daily_record)

            return updated_daily_records, session_records

    def add_active_away_session(self, user_id, user_name, guild_id, expected_minutes):
        """
        Add an active away session to the database.

        Args:
            user_id (int): The ID of the user.
            user_name (str): The name of the user.
            guild_id (int): The ID of the guild.
            start_time (str): The start time of the away session.
            expected_minutes (int): The expected duration of the away session in minutes.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            now = datetime.now()
            start_time = now.strftime("%H:%M:%S")

            cursor.execute(
                """
                INSERT INTO active_away_sessions
                (user_id, user_name, guild_id, start_time, expected_minutes)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, guild_id) DO UPDATE SET
                    start_time = excluded.start_time,
                    expected_minutes = excluded.expected_minutes
                """,
                (user_id, user_name, guild_id, start_time, expected_minutes),
            )

            conn.commit()
            conn.close()
            self.logger.info(
                f"Active away session added for user {user_name} (ID: {user_id}) in guild {guild_id}"
            )
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"Error adding active away session: {e}")

    def remove_active_away_session(self, user_id, guild_id):
        """
        Remove an active away session from the database.

        Args:
            user_id (int): The ID of the user.
            guild_id (int): The ID of the guild.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM active_away_sessions
                WHERE user_id = ? AND guild_id = ?
                """,
                (user_id, guild_id),
            )

            conn.commit()
            conn.close()
            self.logger.info(
                f"Active away session removed for user {user_id} in guild {guild_id}"
            )
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"Error removing active away session: {e}")

    def get_active_away_session(self, user_id, guild_id):
        """
        Get an active away session for a user in a specific guild.

        Args:
            user_id (int): The ID of the user.
            guild_id (int): The ID of the guild.

        Returns:
            dict: The active away session, or None if not found.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM active_away_sessions
                WHERE user_id = ? AND guild_id = ?
                """,
                (user_id, guild_id),
            )

            result = cursor.fetchone()
            conn.close()

            print("Active away session result:", result)

            if result:
                columns = [description[0] for description in cursor.description]
                session = dict(zip(columns, result))
                session["start_time"] = datetime.strptime(
                    session["start_time"], "%H:%M:%S"
                ).time()
                return session
            return None
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"Error fetching active away session: {e}")
            return None
