# Controller for the habit tracker app
import analytics
from manager import DataManager, HabitNotFoundError
import datetime
import database

# Error for bad inputs
class ValidationError(Exception):
    pass

# Main controller class that coordinates everything
class HabitController:
    def __init__(self, test_mode=False):
        """Create the controller"""
        # Get a data manager (without examples if in test mode)
        self.manager = DataManager(skip_predefined=test_mode)

    def add_habit(self, name, description, schedule):
        """Add a new habit"""
        try:
            # Clean inputs
            name = name.strip()
            description = description.strip()
            schedule = schedule.strip().lower()
            
            # Validation
            if name == "":
                raise ValidationError("Habit name can't be empty")
            if schedule != "daily" and schedule != "weekly":
                raise ValidationError(f"Schedule must be 'daily' or 'weekly'")
                
            # Add it
            return self.manager.add_habit(name, description, schedule)
        except ValueError as e:
            # Convert errors to ValidationError
            raise ValidationError(str(e))

    def mark_habit_done(self, name, timestamp=None):
        """Mark a habit as completed"""
        name = name.strip()
        return self.manager.log_completion(name, timestamp)

    def view_all_habits(self):
        """Get a list of all habits"""
        habits = self.manager.get_all_habits()
        if not habits:
            return "No habits defined yet."
            
        # Group by schedule
        daily = []
        weekly = []
        
        for h in habits:
            if h.schedule == "daily":
                daily.append(h)
            else:
                weekly.append(h)
        
        # Format output
        lines = []
        
        if daily:
            lines.append("Daily Habits:")
            for h in daily:
                lines.append(f"  {h}")
            
        if weekly:
            if lines:  # Add a blank line if we have daily habits
                lines.append("")
            lines.append("Weekly Habits:")
            for h in weekly:
                lines.append(f"  {h}")
            
        return "\n".join(lines)

    def view_habits_by_schedule(self, schedule):
        """Get habits filtered by schedule"""
        schedule = schedule.strip().lower()
        if schedule != "daily" and schedule != "weekly":
            raise ValidationError(f"Schedule must be 'daily' or 'weekly'")
            
        all_habits = self.manager.get_all_habits()
        filtered_habits = analytics.get_habits_by_periodicity(all_habits, schedule)
        
        if not filtered_habits:
            return f"No {schedule} habits found."
            
        # Format output
        lines = [f"{schedule.capitalize()} Habits:"]
        for habit in filtered_habits:
            lines.append(f"  {habit}")
            
        return "\n".join(lines)

    def view_habit_streak(self, name):
        """Calculate streak info for a habit"""
        name = name.strip()
        
        # Get the habit
        habit = self.manager.get_habit(name)
        if not habit:
            raise HabitNotFoundError(f"Habit '{name}' not found")

        # Get completions and calculate streaks
        completions = self.manager.get_completions(name)
        current_streak = analytics.get_current_streak_for_habit(habit, completions)
        longest_streak = analytics.get_longest_streak_for_habit(habit, completions)
        
        # Format the output
        lines = [f"Habit: {habit.name} ({habit.schedule})"]
        lines.append(f"Current Streak: {current_streak} {habit.schedule} completion(s)")
        lines.append(f"Longest Streak: {longest_streak} {habit.schedule} completion(s)")
        
        # Add last completion info
        if completions:
            last_completion = max(completions).strftime("%Y-%m-%d %H:%M")
            lines.append(f"Last completed: {last_completion}")
        else:
            lines.append("No completions recorded yet")
            
        return "\n".join(lines)

    def view_longest_streak_all(self):
        """Find the longest streak across all habits"""
        # First get all the habits
        all_habits = self.manager.get_all_habits()
        if not all_habits:
            return "No habits defined to calculate streaks."
            
        # Get all completions - originally I was calling this for each habit
        # inside the loop below but that's inefficient
        all_completions = {}
        for habit in all_habits:
            completions = self.manager.get_completions(habit.name)
            all_completions[habit.name] = completions
        
        # Calculate longest streak for each habit
        # This part took me a while to figure out
        habit_streaks = []
        for habit in all_habits:
            streak = analytics.get_longest_streak_for_habit(habit, all_completions[habit.name])
            
            # Store as tuples to keep track of everything
            habit_streaks.append((habit.name, streak, habit.schedule))
            
        # Find the best streak(s)
        if not habit_streaks:
            return "No streaks to report."
            
        # Find the maximum streak value
        # I first tried using the max() function directly but couldn't get it working right
        max_streak = 0
        for _, streak, _ in habit_streaks:
            if streak > max_streak:
                max_streak = streak
        
        # Find all habits with the maximum streak
        # This handles the case where multiple habits have the same streak
        best_habits = []
        for name, streak, schedule in habit_streaks:
            if streak == max_streak:
                best_habits.append((name, streak, schedule))
        
        # Format the output - this makes it nice to read
        if len(best_habits) == 1:
            # Just one winner
            name, streak, schedule = best_habits[0]
            return f"Longest streak: {name} ({schedule}) with {streak} consecutive completions"
        else:
            # Multiple habits tied for best streak
            # I used a list comprehension to format each habit - we learned this in week 5!
            habit_list = ", ".join([f"{name} ({schedule})" for name, _, schedule in best_habits])
            return f"Longest streak: {max_streak} completions, shared by: {habit_list}"

    def delete_habit(self, name):
        """Delete a habit"""
        name = name.strip()
        return self.manager.delete_habit(name)

    def get_struggling_habits(self, days=30):
        """Find habits that are being neglected"""
        all_habits = self.manager.get_all_habits()
        if not all_habits:
            return "No habits defined to analyze."
            
        # Set up date range
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Get completions for all habits in the date range
        all_completions = {}
        for habit in all_habits:
            completions = self.manager.get_completions_in_range(
                habit.name, start_date, end_date)
            all_completions[habit.name] = completions
            
        # Find struggling habits
        struggling = analytics.find_struggling_habits(
            all_habits, all_completions, start_date, end_date)
        
        if not struggling:
            return f"No struggling habits in the last {days} days."
            
        # Format output
        lines = [f"Struggling habits (last {days} days):"]
        
        for habit_name, missed_count in struggling:
            if missed_count > 0:
                # Find the habit object to get the schedule
                for habit in all_habits:
                    if habit.name == habit_name:
                        lines.append(f"  {habit_name} ({habit.schedule}): {missed_count} missed completions")
                        break
                        
        # If we only have the header, there are no struggling habits
        if len(lines) == 1:
            return f"No struggling habits in the last {days} days."
            
        return "\n".join(lines)

    # Removed backup_data method