# Habit class
import datetime

class Habit:
    def __init__(self, name, description, schedule, created_on=None):
        # Make sure schedule is valid
        if schedule != "daily" and schedule != "weekly":
            raise ValueError("Schedule must be 'daily' or 'weekly'")
            
        self.name = name
        self.description = description 
        self.schedule = schedule
        
        # Default to now if no time provided
        if created_on == None:
            self.created_on = datetime.datetime.now()
        else:
            self.created_on = created_on
    
    # Show habit as string
    def __str__(self):
        if self.description:
            return f"{self.name} ({self.schedule}) - {self.description}"
        else:
            return f"{self.name} ({self.schedule})"
    
    # For debugging
    def __repr__(self):
        return f"Habit('{self.name}', '{self.description}', '{self.schedule}', {self.created_on})"