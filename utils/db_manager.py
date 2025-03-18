import sqlite3
import logging
from datetime import datetime
from config import Config


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
                """CREATE TABLE IF NOT EXISTS server_settings (
                guild_id INTEGER PRIMARY KEY,
                command_prefix TEXT DEFAULT '!',
                channel_id INTEGER,
                grace_period_minutes INTEGER DEFAULT 1,
                fee_percentage_per_minute REAL DEFAULT 0.0007,
                max_single_away_minutes INTEGER DEFAULT 40,
                max_daily_away_minutes INTEGER DEFAULT 90,
                work_start_hour INTEGER DEFAULT 9,
                work_end_hour INTEGER DEFAULT 17
            )"""
            )

            # Table to track user away time
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS away_time (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
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
                date TEXT NOT NULL,
                total_minutes INTEGER DEFAULT 0,
                over_limit_minutes INTEGER DEFAULT 0,
                fee_amount REAL DEFAULT 0,
                UNIQUE(user_id, date)
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
            """INSERT OR REPLACE INTO guild_settings 
                        (guild_id, command_prefix, log_path, channel_id, 
                        grace_period_minutes, fee_percentage_per_minute, 
                        max_single_away_minutes, max_daily_away_minutes,
                        work_start_hour, work_start_minute, 
                        work_end_hour, work_end_minute)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                guild_id,
                config_data.get("command_prefix", "!"),
                config_data.get("log_path", "logs"),
                config_data.get("channel_id"),
                config_data.get("grace_period_minutes", 1),
                config_data.get("fee_percentage_per_minute", 0.0007),
                config_data.get("max_single_away_minutes", 40),
                config_data.get("max_daily_away_minutes", 90),
                config_data["work_start_time"].hour,
                config_data["work_start_time"].minute,
                config_data["work_end_time"].hour,
                config_data["work_end_time"].minute,
            ),
        )
        conn.commit()

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
                # Ensure Config.CHANNEL_ID is valid, else set to None
                channel_id = (
                    Config.CHANNEL_ID if hasattr(Config, "CHANNEL_ID") else None
                )

                work_start_time = Config.WORK_START_TIME.strftime("%H:%M:%S")
                work_end_time = Config.WORK_END_TIME.strftime("%H:%M:%S")

                # Insert default settings for the server
                cursor.execute(
                    """
                    INSERT INTO server_settings (
                        guild_id, 
                        command_prefix, 
                        channel_id, 
                        grace_period_minutes, 
                        fee_percentage_per_minute, 
                        max_single_away_minutes, 
                        max_daily_away_minutes, 
                        work_start_hour, 
                        work_end_hour
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        guild_id,
                        Config.PREFIX,
                        channel_id,
                        Config.GRACE_PERIOD_MINUTES,
                        Config.FEE_PERCENTAGE_PER_MINUTE,
                        Config.MAX_SINGLE_AWAY_MINUTES,
                        Config.MAX_DAILY_AWAY_MINUTES,
                        work_start_time,
                        work_end_time,
                    ),
                )
                connection.commit()
                # Fetch the newly created settings
                cursor.execute(
                    "SELECT * FROM server_settings WHERE guild_id = ?",
                    (guild_id,),
                )
                server = cursor.fetchone()

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

    def is_work_hours(self):
        """Check if current time is within work hours (9 AM - 5 PM on weekdays)"""
        # now = datetime.now()
        # current_time = now.time()

        # # Check if it's a weekday (0 = Monday, 4 = Friday)
        # is_weekday = now.weekday() < 5

        # # Check if current time is between work hours
        # is_work_time = self.WORK_START_TIME <= current_time <= self.WORK_END_TIME

        # return is_weekday and is_work_time
        return True

    def get_today_away_time(self, user_id):
        """Get total away time for user today"""
        today = datetime.now().strftime("%Y-%m-%d")

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Get from daily tracking
            cursor.execute(
                """
            SELECT total_minutes FROM away_daily
            WHERE user_id = ? AND date = ?
            """,
                (user_id, today),
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                return result[0]
            return 0
        except Exception as e:
            self.logger.error(f"Error getting daily away time: {e}")
            return 0

    def update_daily_totals(self, user_id, user_name, minutes_away):
        """Update daily totals for user away time"""
        today = datetime.now().strftime("%Y-%m-%d")

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Get current daily total
            cursor.execute(
                """
            SELECT total_minutes FROM away_daily
            WHERE user_id = ? AND date = ?
            """,
                (user_id, today),
            )

            result = cursor.fetchone()

            if result:
                # Update existing record
                new_total = result[0] + minutes_away
                over_limit = max(0, new_total - self.MAX_DAILY_AWAY_MINUTES)
                fee_amount = over_limit * self.FEE_PERCENTAGE_PER_MINUTE

                cursor.execute(
                    """
                UPDATE away_daily
                SET total_minutes = ?,
                    over_limit_minutes = ?,
                    fee_amount = ?
                WHERE user_id = ? AND date = ?
                """,
                    (new_total, over_limit, fee_amount, user_id, today),
                )
            else:
                # Create new record
                over_limit = max(0, minutes_away - self.MAX_DAILY_AWAY_MINUTES)
                fee_amount = over_limit * self.FEE_PERCENTAGE_PER_MINUTE

                cursor.execute(
                    """
                INSERT INTO away_daily
                (user_id, user_name, date, total_minutes, over_limit_minutes, fee_amount)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (user_id, user_name, today, minutes_away, over_limit, fee_amount),
                )

            conn.commit()
            conn.close()

            return over_limit, fee_amount
        except Exception as e:
            self.logger.error(f"Error updating daily totals: {e}")
            return 0, 0

    def record_away_session(
        self,
        user_id,
        user_name,
        start_time,
        end_time,
        expected_minutes,
        actual_minutes,
        fee_amount,
    ):
        """Record a complete away session in the database"""
        today = start_time.strftime("%Y-%m-%d")

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
            INSERT INTO away_time
            (user_id, user_name, date, start_time, end_time, expected_minutes, actual_minutes, fee_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    user_name,
                    today,
                    start_time.strftime("%H:%M:%S"),
                    end_time.strftime("%H:%M:%S"),
                    expected_minutes,
                    actual_minutes,
                    fee_amount,
                ),
            )

            conn.commit()
            conn.close()
            self.logger.info(
                f"Recorded away session for {user_name}: {actual_minutes} minutes"
            )
        except Exception as e:
            self.logger.error(f"Error recording away session: {e}")

    def _fetch_away_data(self, date, user_id=None):
        """Fetch away data from the database."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # If user_id is provided, fetch data for a specific user, else for all users (admin view)
        if user_id:
            cursor.execute(
                """
                SELECT user_name, total_minutes, over_limit_minutes, fee_amount
                FROM away_daily
                WHERE user_id = ? AND date = ?
                """,
                (user_id, date),
            )
            user_record = cursor.fetchone()

            cursor.execute(
                """
                SELECT start_time, end_time, expected_minutes, actual_minutes, fee_amount
                FROM away_time
                WHERE user_id = ? AND date = ?
                ORDER BY start_time
                """,
                (user_id, date),
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
                WHERE date = ?
                ORDER BY total_minutes DESC
                """,
                (date,),
            )
            daily_records = cursor.fetchall()

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
