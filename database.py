
# Database functions for Habit Tracker
import sqlite3
import datetime
import os
import shutil  # for backup

# Database filename
DB_NAME = "habits.db"

# Custom exceptions
class DatabaseError(Exception):
    pass

class ConnectionError(DatabaseError):
    pass

class QueryError(DatabaseError):
    pass

# Connect to the database
def connect_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # This makes results easier to work with
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise ConnectionError(f"Couldn't connect to database: {e}")

# Create database tables
def initialize_database():
    print(f"Creating database: {DB_NAME}")
    conn = None
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Create habits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                name TEXT PRIMARY KEY,
                description TEXT,
                schedule TEXT,
                created_on TIMESTAMP
            )
        ''')
        
        # Create completions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_name TEXT,
                completion_time TIMESTAMP,
                FOREIGN KEY (habit_name) REFERENCES habits (name) ON DELETE CASCADE
            )
        ''')
        
        # Create a simple index
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_completions_habit_name 
            ON completions(habit_name)
        ''')
        
        conn.commit()
        print("Database created successfully")
        return True
    except Exception as e:
        print(f"Error creating database: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# Add a new habit
def add_habit_db(name, description, schedule, created_on):
    conn = None
    try:
        # Check inputs
        if not name or name.strip() == "":
            raise ValueError("Name can't be empty")
        if schedule != "daily" and schedule != "weekly":
            raise ValueError("Schedule must be daily or weekly")
        
        conn = connect_db()
        conn.execute(
            "INSERT INTO habits VALUES (?, ?, ?, ?)",
            (name, description, schedule, created_on.isoformat())
        )
        conn.commit()
        print(f"Added habit: {name}")
        return True
    except sqlite3.IntegrityError:
        print(f"Error: Habit '{name}' already exists!")
        if conn:
            conn.rollback()
        raise QueryError(f"Habit '{name}' already exists")
    except Exception as e:
        print(f"Error adding habit: {e}")
        if conn:
            conn.rollback()
        raise QueryError(f"Failed to add habit: {e}")
    finally:
        if conn:
            conn.close()

# Get a habit by name
def get_habit_db(name):
    conn = None
    try:
        conn = connect_db()
        cursor = conn.execute("SELECT * FROM habits WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"Error getting habit: {e}")
        raise QueryError(f"Failed to get habit: {e}")
    finally:
        if conn:
            conn.close()

# Get all habits
def get_all_habits_db():
    conn = None
    try:
        conn = connect_db()
        cursor = conn.execute("SELECT * FROM habits ORDER BY created_on DESC")
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error getting habits: {e}")
        raise QueryError(f"Failed to get habits: {e}")
    finally:
        if conn:
            conn.close()

# Delete a habit
def delete_habit_db(name):
    conn = None
    try:
        conn = connect_db()
        cursor = conn.execute("DELETE FROM habits WHERE name = ?", (name,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"Deleted habit: {name}")
            return True
        else:
            print(f"Habit '{name}' not found")
            return False
    except Exception as e:
        print(f"Error deleting habit: {e}")
        if conn:
            conn.rollback()
        raise QueryError(f"Failed to delete habit: {e}")
    finally:
        if conn:
            conn.close()

# Log a habit completion
def log_completion_db(habit_name, completion_time):
    conn = None
    try:
        conn = connect_db()
        
        # Check if habit exists
        cursor = conn.execute("SELECT 1 FROM habits WHERE name = ?", (habit_name,))
        if not cursor.fetchone():
            raise ValueError(f"Habit '{habit_name}' doesn't exist")
        
        conn.execute(
            "INSERT INTO completions (habit_name, completion_time) VALUES (?, ?)",
            (habit_name, completion_time.isoformat())
        )
        conn.commit()
        print(f"Logged completion for: {habit_name}")
        return True
    except Exception as e:
        print(f"Error logging completion: {e}")
        if conn:
            conn.rollback()
        raise QueryError(f"Failed to log completion: {e}")
    finally:
        if conn:
            conn.close()

# Get all completions for a habit
def get_completions_db(habit_name):
    conn = None
    try:
        conn = connect_db()
        cursor = conn.execute(
            "SELECT completion_time FROM completions WHERE habit_name = ? ORDER BY completion_time DESC",
            (habit_name,)
        )
        return [datetime.datetime.fromisoformat(row['completion_time']) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error getting completions: {e}")
        raise QueryError(f"Failed to get completions: {e}")
    finally:
        if conn:
            conn.close()

# Get completions in a date range
def get_completions_in_range_db(habit_name, start_date, end_date):
    conn = None
    try:
        # Convert to datetime with time
        start_str = datetime.datetime.combine(start_date, datetime.time.min).isoformat()
        end_str = datetime.datetime.combine(end_date, datetime.time.max).isoformat()
        
        conn = connect_db()
        cursor = conn.execute(
            """
            SELECT completion_time FROM completions 
            WHERE habit_name = ? AND completion_time BETWEEN ? AND ?
            ORDER BY completion_time DESC
            """,
            (habit_name, start_str, end_str)
        )
        return [datetime.datetime.fromisoformat(row['completion_time']) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error getting completions in range: {e}")
        raise QueryError(f"Failed to get completions in range: {e}")
    finally:
        if conn:
            conn.close()

# Backup the database
def backup_database(backup_path=None):
    if not backup_path:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"habits_backup_{timestamp}.db"
    
    try:
        # Simple file copy
        shutil.copy2(DB_NAME, backup_path)
        print(f"Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Backup failed: {e}")
        raise ConnectionError(f"Failed to backup database: {e}")