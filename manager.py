# Data manager for habits
import database
from habit import Habit
import datetime

# Error for when a habit isn't found
class HabitNotFoundError(Exception):
    pass

# Main data manager class
class DataManager:
    def __init__(self, skip_predefined=False):
        """Set up the data manager"""
        # Create database tables if needed
        database.initialize_database()
        
        # Add example habits unless we're in test mode
        if not skip_predefined:
            self.load_predefined_habits()
        
        print("Data manager ready!")

    def load_predefined_habits(self):
        """Add some example habits to get started"""
        example_habits = [
            {"name": "Drink Water", "description": "Drink 8 glasses daily", "schedule": "daily"},
            {"name": "Exercise", "description": "30 minutes workout", "schedule": "daily"},
            {"name": "Read", "description": "Read for 20 minutes", "schedule": "daily"},
            {"name": "Meditate", "description": "10 minutes mindfulness", "schedule": "daily"},
            {"name": "Weekly Review", "description": "Review goals and progress", "schedule": "weekly"}
        ]
        
        # Create some completion data for examples
        example_completions = {}
        now = datetime.datetime.now()
        
        # For daily habits: add completions for most days in the past month
        for habit in example_habits:
            if habit["schedule"] == "daily":
                dates = []
                for x in range(28):  # 4 weeks back
                    # Skip some random days to make it realistic
                    if x % 7 != 3 and x % 11 != 5:  # Skip some days 
                        dates.append(now - datetime.timedelta(days=x))
                example_completions[habit["name"]] = dates
            else:  # weekly habits
                # Add completions for past 4 weeks
                dates = []
                for x in range(4):
                    # Get most recent Monday, then go back x weeks
                    last_monday = now - datetime.timedelta(days=now.weekday())
                    completion_date = last_monday - datetime.timedelta(weeks=x)
                    dates.append(completion_date)
                example_completions[habit["name"]] = dates

        # Add each example habit if it doesn't exist
        for habit in example_habits:
            try:
                # Check if habit exists first
                if not self.get_habit(habit["name"]):
                    # Add the habit
                    self.add_habit(habit["name"], habit["description"], habit["schedule"])
                    
                    # Add example completions
                    if habit["name"] in example_completions:
                        for date in example_completions[habit["name"]]:
                            self.log_completion(habit["name"], date)
            except Exception as e:
                print(f"Couldn't add example habit {habit['name']}: {e}")

    def add_habit(self, name, description, schedule):
        """Add a new habit"""
        # Check inputs
        if not name or name.strip() == "":
            raise ValueError("Habit name can't be empty")
        if schedule != "daily" and schedule != "weekly":
            raise ValueError(f"Schedule must be 'daily' or 'weekly'")
            
        # Add to database
        created = datetime.datetime.now()
        database.add_habit_db(name, description, schedule, created)
        return True

    def get_habit(self, name):
        """Get a habit by name"""
        data = database.get_habit_db(name)
        if data:
            return Habit(
                name=data["name"],
                description=data["description"],
                schedule=data["schedule"],
                created_on=datetime.datetime.fromisoformat(data["created_on"])
            )
        return None

    def get_all_habits(self):
        """Get all habits"""
        data = database.get_all_habits_db()
        habits = []
        for row in data:
            habit = Habit(
                name=row["name"],
                description=row["description"],
                schedule=row["schedule"],
                created_on=datetime.datetime.fromisoformat(row["created_on"])
            )
            habits.append(habit)
        return habits

    def delete_habit(self, name):
        """Delete a habit"""
        return database.delete_habit_db(name)

    def log_completion(self, habit_name, completion_time=None):
        """Log that a habit was completed"""
        # Check if habit exists
        habit = self.get_habit(habit_name)
        if not habit:
            raise HabitNotFoundError(f"Habit '{habit_name}' not found")
            
        # Use current time if none provided
        if completion_time is None:
            completion_time = datetime.datetime.now()
            
        # Log it
        database.log_completion_db(habit_name, completion_time)
        return True

    def get_completions(self, habit_name):
        """Get all times a habit was completed"""
        # Check if habit exists
        habit = self.get_habit(habit_name)
        if not habit:
            raise HabitNotFoundError(f"Habit '{habit_name}' not found")
            
        return database.get_completions_db(habit_name)

    def get_completions_in_range(self, habit_name, start_date, end_date):
        """Get completions between two dates"""
        # Make sure dates are in the right order
        if end_date < start_date:
            raise ValueError("End date must be after start date")
            
        # Check if habit exists
        habit = self.get_habit(habit_name)
        if not habit:
            raise HabitNotFoundError(f"Habit '{habit_name}' not found")
            
        return database.get_completions_in_range_db(habit_name, start_date, end_date)

    # Removed backup_data method - decided not to implement this feature