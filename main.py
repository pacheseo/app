# Main program file for Habit Tracker
import cli
import database
import sys
import os

# Basic setup function
def setup():
    # Check if database exists
    if not os.path.exists("habits.db"):
        print("First time running - setting up database...")
        database.initialize_database()
        return True
    return True

# Main function
def main():
    print("Starting Habit Tracker")
    
    # Setup and run
    if setup():
        try:
            cli.run_cli()
        except KeyboardInterrupt:
            print("\nGoodbye and see you soon!")
        except Exception as e:
            print(f"\nError: {e}")
            sys.exit(1)
    else:
        print("Couldn't set up the database!")
        sys.exit(1)

# Run the program
if __name__ == "__main__":
    main()