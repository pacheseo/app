# Command line interface for the habit tracker
import datetime
import os
import sys
from habit_controller import HabitController, ValidationError
from manager import HabitNotFoundError
import database

def clear_screen():
    """Clears the terminal screen."""
    # This works different on Windows vs Mac/Linux
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """Prints a formatted header."""
    print("\n" + "=" * 50)
    print(f"{title:^50}")
    print("=" * 50)

def display_menu():
    """Prints the main menu options."""
    print_header("Habit Tracker Menu")
    print("\n1. Add New Habit")
    print("2. Mark Habit as Complete")
    print("3. View All Habits")
    print("4. View Habits by Schedule (Daily/Weekly)")
    print("5. View Habit Streak")
    print("6. View Longest Overall Streak")
    print("7. View Struggling Habits")
    print("8. Delete Habit")
    print("0. Exit")
    print("\n" + "-" * 50)

def get_valid_input(prompt, validator=None, error_msg=None):
    """
    Gets user input with validation.
    
    Args:
        prompt: The input prompt
        validator: Function that returns True if input is valid
        error_msg: Message to display if validation fails
        
    Returns:
        Validated user input
    """
    while True:
        user_input = input(prompt).strip()
        if validator is None or validator(user_input):
            return user_input
        print(error_msg or "Invalid input. Please try again.")

def add_habit_menu(controller):
    """Handles the add habit menu."""
    print_header("Add New Habit")
    
    try:
        name = get_valid_input(
            "Enter habit name: ", 
            lambda x: len(x) > 0, 
            "Habit name cannot be empty."
        )
        
        desc = input("Enter habit description: ")
        
        sched = get_valid_input(
            "Enter schedule (daily/weekly): ",
            lambda x: x.lower() in ["daily", "weekly"],
            "Invalid schedule. Please enter 'daily' or 'weekly'."
        ).lower()
        
        controller.add_habit(name, desc, sched)
        print(f"\nSuccess! Habit '{name}' added.")
        input("\nPress Enter to continue...")
    except ValidationError as e:
        print(f"\nError: {e}")
        input("\nPress Enter to continue...")
    except database.QueryError as e:
        print(f"\nDatabase Error: {e}")
        input("\nPress Enter to continue...")

def mark_habit_done_menu(controller):
    """Handles the mark habit as done menu."""
    print_header("Mark Habit as Complete")
    
    # Show available habits to help user
    habits = controller.manager.get_all_habits()
    if not habits:
        print("\nNo habits available to mark as complete.")
        input("\nPress Enter to continue...")
        return
        
    print("\nAvailable habits:")
    for i, habit in enumerate(habits, 1):
        print(f"{i}. {habit.name} ({habit.schedule})")
    
    try:
        # Allow selection by number or name
        selection = input("\nEnter habit number or name: ")
        
        # Check if selection is a number
        if selection.isdigit() and 1 <= int(selection) <= len(habits):
            habit_name = habits[int(selection) - 1].name
        else:
            habit_name = selection
            
        # Optionally allow selecting a different completion date
        use_custom_date = get_valid_input(
            "Mark complete for today? (yes/no): ",
            lambda x: x.lower() in ["yes", "no", "y", "n"],
            "Please enter 'yes' or 'no'."
        ).lower()
        
        completion_time = datetime.datetime.now()
        
        if use_custom_date in ["no", "n"]:
            date_str = get_valid_input(
                "Enter date (YYYY-MM-DD): ",
                lambda x: is_valid_date(x),
                "Invalid date format. Please use YYYY-MM-DD."
            )
            completion_time = datetime.datetime.fromisoformat(date_str)
            
        controller.mark_habit_done(habit_name, completion_time)
        print(f"\nSuccess! Habit '{habit_name}' marked as complete.")
        input("\nPress Enter to continue...")
    except HabitNotFoundError as e:
        print(f"\nError: {e}")
        input("\nPress Enter to continue...")
    except database.QueryError as e:
        print(f"\nDatabase Error: {e}")
        input("\nPress Enter to continue...")

def view_all_habits_menu(controller):
    """Handles the view all habits menu."""
    print_header("All Habits")
    result = controller.view_all_habits()
    print("\n" + result)
    input("\nPress Enter to continue...")

def view_habits_by_schedule_menu(controller):
    """Handles the view habits by schedule menu."""
    print_header("View Habits by Schedule")
    
    try:
        sched = get_valid_input(
            "Enter schedule to view (daily/weekly): ",
            lambda x: x.lower() in ["daily", "weekly"],
            "Invalid schedule. Please enter 'daily' or 'weekly'."
        ).lower()
        
        result = controller.view_habits_by_schedule(sched)
        print("\n" + result)
        input("\nPress Enter to continue...")
    except ValidationError as e:
        print(f"\nError: {e}")
        input("\nPress Enter to continue...")

def view_habit_streak_menu(controller):
    """Handles the view habit streak menu."""
    print_header("View Habit Streak")
    
    # Show available habits to help user
    habits = controller.manager.get_all_habits()
    if not habits:
        print("\nNo habits available.")
        input("\nPress Enter to continue...")
        return
        
    print("\nAvailable habits:")
    for i, habit in enumerate(habits, 1):
        print(f"{i}. {habit.name} ({habit.schedule})")
    
    try:
        # Allow selection by number or name
        selection = input("\nEnter habit number or name: ")
        
        # Check if selection is a number
        if selection.isdigit() and 1 <= int(selection) <= len(habits):
            habit_name = habits[int(selection) - 1].name
        else:
            habit_name = selection
            
        result = controller.view_habit_streak(habit_name)
        print("\n" + result)
        input("\nPress Enter to continue...")
    except HabitNotFoundError as e:
        print(f"\nError: {e}")
        input("\nPress Enter to continue...")

def view_longest_streak_menu(controller):
    """Handles the view longest streak menu."""
    print_header("Longest Overall Streak")
    result = controller.view_longest_streak_all()
    print("\n" + result)
    input("\nPress Enter to continue...")

def view_struggling_habits_menu(controller):
    """Handles the view struggling habits menu."""
    print_header("Struggling Habits")
    
    days_options = ["7", "14", "30", "60", "90"]
    print("\nAnalysis period options:")
    for i, days in enumerate(days_options, 1):
        print(f"{i}. Last {days} days")
    
    selection = get_valid_input(
        "\nSelect analysis period (1-5): ",
        lambda x: x.isdigit() and 1 <= int(x) <= len(days_options),
        "Please enter a number between 1 and 5."
    )
    
    days = int(days_options[int(selection) - 1])
    result = controller.get_struggling_habits(days)
    print("\n" + result)
    input("\nPress Enter to continue...")

def delete_habit_menu(controller):
    """Handles the delete habit menu."""
    print_header("Delete Habit")
    
    # Show available habits to help user
    habits = controller.manager.get_all_habits()
    if not habits:
        print("\nNo habits available to delete.")
        input("\nPress Enter to continue...")
        return
        
    print("\nAvailable habits:")
    for i, habit in enumerate(habits, 1):
        print(f"{i}. {habit.name} ({habit.schedule})")
    
    try:
        # Allow selection by number or name
        selection = input("\nEnter habit number or name to delete: ")
        
        # Check if selection is a number
        if selection.isdigit() and 1 <= int(selection) <= len(habits):
            habit_name = habits[int(selection) - 1].name
        else:
            habit_name = selection
            
        # Confirmation with habit name
        confirm = get_valid_input(
            f"\nAre you sure you want to delete '{habit_name}'? This cannot be undone. (yes/no): ",
            lambda x: x.lower() in ["yes", "no", "y", "n"],
            "Please enter 'yes' or 'no'."
        ).lower()
        
        if confirm in ["yes", "y"]:
            result = controller.delete_habit(habit_name)
            if result:
                print(f"\nHabit '{habit_name}' deleted successfully.")
            else:
                print(f"\nHabit '{habit_name}' not found.")
        else:
            print("\nDeletion cancelled.")
            
        input("\nPress Enter to continue...")
    except database.QueryError as e:
        print(f"\nDatabase Error: {e}")
        input("\nPress Enter to continue...")

# Removed backup_data_menu function

def is_valid_date(date_str):
    """Validates a date string in YYYY-MM-DD format."""
    try:
        datetime.date.fromisoformat(date_str)
        return True
    except ValueError:
        return False

def run_cli():
    """Runs the main command-line interface loop."""
    controller = HabitController()
    clear_screen()
    print_header("Welcome to Habit Tracker")
    print("\nTrack your habits and build consistency!")
    input("\nPress Enter to continue...")

    while True:
        clear_screen()
        display_menu()
        choice = input("\nEnter your choice (0-8): ")

        try:
            if choice == '1':
                add_habit_menu(controller)
            elif choice == '2':
                mark_habit_done_menu(controller)
            elif choice == '3':
                view_all_habits_menu(controller)
            elif choice == '4':
                view_habits_by_schedule_menu(controller)
            elif choice == '5':
                view_habit_streak_menu(controller)
            elif choice == '6':
                view_longest_streak_menu(controller)
            elif choice == '7':
                view_struggling_habits_menu(controller)
            elif choice == '8':
                delete_habit_menu(controller)
            elif choice == '0':
                clear_screen()
                print_header("Thank You for Using Habit Tracker")
                print("\nGoodbye!")
                break
            else:
                print("\nInvalid choice. Please enter a number between 0 and 8.")
                input("\nPress Enter to continue...")
        except Exception as e:
            print(f"\nError: {e}")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    run_cli()