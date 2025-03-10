import sqlite3
import logging
from datetime import datetime

from config import Config


class DatabaseManager:
    def __init__(self, db_path="loyalty_bot.db"):
        self.db_path = db_path
        self.logger = logging.getLogger("discord_bot")
        self.MAX_DAILY_AWAY_MINUTES = Config.MAX_DAILY_AWAY_MINUTES
        self.FEE_PER_MINUTE = Config.FEE_PER_MINUTE

    def initialize(self):
        """Initialize database tables for loyalty tracking"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

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

    def is_work_hours(self):
        """Check if current time is within work hours (9 AM - 5 PM on weekdays)"""
        now = datetime.now()
        current_time = now.time()

        # Check if it's a weekday (0 = Monday, 4 = Friday)
        is_weekday = now.weekday() < 5

        # Check if current time is between work hours
        is_work_time = self.WORK_START_TIME <= current_time <= self.WORK_END_TIME

        return is_weekday and is_work_time
        # return True

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
                fee_amount = over_limit * self.FEE_PER_MINUTE

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
                fee_amount = over_limit * self.FEE_PER_MINUTE

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
