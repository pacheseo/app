# Functions for analyzing habits
# This was the hardest part of the assignment!
from habit import Habit
import datetime

# Helper function for calculating streaks
def calculate_streak(dates, schedule):
    """
    Counts how many days/weeks in a row a habit was done
    dates - list of datetime objects when habit was completed
    schedule - 'daily' or 'weekly'
    """
    if not dates or len(dates) == 0:
        return 0
    
    # First convert all datetimes to just dates and remove duplicates
    just_dates = []
    for d in dates:
        just_dates.append(d.date())
    
    # Remove duplicates by converting to set and back to list
    unique_dates = list(set(just_dates))
    
    # Sort newest to oldest
    unique_dates.sort(reverse=True)
    
    # For daily habits
    if schedule == "daily":
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        
        # Check if the streak is still going (completed today or yesterday)
        if unique_dates[0] < yesterday:
            return 0
            
        # Count consecutive days
        streak = 1  # Start with 1 for the most recent day
        
        # This part gave me trouble! Had to look up how to compare dates
        for i in range(len(unique_dates) - 1):
            date1 = unique_dates[i]
            date2 = unique_dates[i+1]
            
            # If the dates are consecutive, increment streak
            # I know there's probably a cleaner way to do this
            if (date1 - date2).days == 1:
                streak += 1
            else:
                # Break in the streak
                break
                
        return streak
        
    # For weekly habits - this is simpler than the original
    # I couldn't figure out all the edge cases with week numbers
    else:
        # Just check if the newest completion is within the last 7 days
        today = datetime.date.today()
        if (today - unique_dates[0]).days > 7:
            return 0
            
        # Just count weeks where there's at least one completion
        # Group dates by week - I asked my friend for help with this part
        weeks = {}
        for date in unique_dates:
            # Get year and week number
            year_week = date.strftime("%Y-%W")  # Format as year-weeknumber
            weeks[year_week] = True
        
        # Sort the weeks
        week_list = list(weeks.keys())
        week_list.sort(reverse=True)
        
        # Count consecutive weeks - this isn't perfect but works for most cases
        streak = 1
        for i in range(len(week_list) - 1):
            # Just check if the next entry is the previous week
            # This doesn't handle year boundaries perfectly
            # But prof said that's an edge case we can ignore
            week1 = week_list[i]
            week2 = week_list[i+1]
            
            # Super basic check - are they consecutive
            # This will break at year boundaries but it's ok for this assignment
            year1, weeknum1 = week1.split("-")
            year2, weeknum2 = week2.split("-")
            
            if year1 == year2 and int(weeknum1) - int(weeknum2) == 1:
                streak += 1
            else:
                break
                
        return streak

def get_current_streak_for_habit(habit, completions):
    """
    Gets the current streak for a habit
    """
    return calculate_streak(completions, habit.schedule)

def get_longest_streak_for_habit(habit, completions):
    """
    Gets the longest streak a habit has had
    This is a simplified version that doesn't handle all edge cases
    but good enough for the assignment
    """
    if not completions or len(completions) == 0:
        return 0
    
    # Convert to dates and remove duplicates
    just_dates = []
    for d in completions:
        just_dates.append(d.date())
    
    unique_dates = list(set(just_dates))
    unique_dates.sort()  # Oldest to newest
    
    if len(unique_dates) == 1:
        return 1
    
    # For daily habits
    if habit.schedule == "daily":
        longest = 1
        current = 1
        
        # Go through dates and count consecutive ones
        for i in range(1, len(unique_dates)):
            if (unique_dates[i] - unique_dates[i-1]).days == 1:
                current += 1
                if current > longest:
                    longest = current
            else:
                current = 1
                
        return longest
        
    # For weekly habits - simplified version
    else:
        # Group by week
        weeks = {}
        for date in unique_dates:
            year_week = date.strftime("%Y-%W")
            weeks[year_week] = True
            
        # Sort the weeks
        week_list = list(weeks.keys())
        week_list.sort()
        
        if len(week_list) == 1:
            return 1
            
        longest = 1
        current = 1
        
        # Count consecutive weeks
        for i in range(1, len(week_list)):
            year1, week1 = week_list[i-1].split("-")
            year2, week2 = week_list[i].split("-")
            
            # Basic check for consecutive weeks
            # Not perfect but good enough
            if year1 == year2 and int(week2) - int(week1) == 1:
                current += 1
                if current > longest:
                    longest = current
            else:
                current = 1
                
        return longest

# Filter habits by daily or weekly
def get_habits_by_periodicity(habits, schedule):
    """Returns habits that match the schedule (daily/weekly)"""
    if schedule != "daily" and schedule != "weekly":
        print(f"Warning: Invalid schedule {schedule}")
        return []
    
    matching = []
    for h in habits:
        if h.schedule == schedule:
            matching.append(h)
    return matching

def find_struggling_habits(habits, all_completions, period_start=None, period_end=None):
    """Finds habits that are being neglected"""
    if len(habits) == 0:
        return []
        
    # Default to last 30 days if no dates provided
    if period_end is None:
        period_end = datetime.date.today()
    if period_start is None:
        period_start = period_end - datetime.timedelta(days=30)
    
    results = []
    
    # Go through each habit
    for habit in habits:
        # Get completions for this habit
        comp_list = all_completions.get(habit.name, [])
        
        # Count completions in the date range
        completions_in_range = 0
        for c in comp_list:
            c_date = c.date()
            if c_date >= period_start and c_date <= period_end:
                completions_in_range += 1
        
        # Figure out expected number of completions
        days_in_period = (period_end - period_start).days + 1
        
        expected = 0
        if habit.schedule == "daily":
            expected = days_in_period
        else:  # weekly
            expected = days_in_period // 7 + 1
        
        # Calculate missed completions
        missed = expected - completions_in_range
        if missed < 0:
            missed = 0
            
        results.append((habit.name, missed))
    
    # Sort by most missed
    results.sort(key=lambda x: x[1], reverse=True)
    return results