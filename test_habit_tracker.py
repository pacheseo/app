from habit import Habit
from manager import DataManager, HabitNotFoundError
from habit_controller import HabitController, ValidationError
import analytics
import database
import datetime
import os
import logging
from typing import List, Dict

# Disable logging during tests
logging.disable(logging.CRITICAL)

# --- Test Setup Functions ---
def setup_test_db():
    """Sets up a temporary, clean database for testing."""
    TEST_DB_NAME = "test_habits.db"
    # Ensure any old test DB is removed
    if os.path.exists(TEST_DB_NAME):
        os.remove(TEST_DB_NAME)

    # Point the database module to the test DB
    original_db_name = database.DB_NAME
    database.DB_NAME = TEST_DB_NAME

    # Initialize the test database structure
    database.initialize_database()

    return TEST_DB_NAME

def create_data_manager():
    """Provides a DataManager instance using the test database."""
    setup_test_db()
    return DataManager(skip_predefined=True)  # Skip predefined habits for cleaner tests

def create_controller():
    """Provides a HabitController instance using the test database."""
    setup_test_db()
    return HabitController(test_mode=True)  # Test mode skips predefined habits

def create_sample_habits():
    """Creates sample habits for testing."""
    manager = create_data_manager()
    habits = [
        ("Morning Run", "30 minute jog", "daily"),
        ("Read Book", "Read 30 pages", "daily"),
        ("Weekly Review", "Review goals and progress", "weekly"),
        ("Meditation", "10 minute mindfulness", "daily")
    ]
    
    for name, desc, schedule in habits:
        manager.add_habit(name, desc, schedule)
    
    return habits, manager

def create_sample_completions():
    """Adds sample completions for the test habits."""
    habits, manager = create_sample_habits()
    today = datetime.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    
    # Morning Run: Perfect streak for 5 days
    for i in range(5):
        manager.log_completion("Morning Run", today - datetime.timedelta(days=i))
    
    # Read Book: missed yesterday
    manager.log_completion("Read Book", today)  # today
    for i in range(2, 5):  # skip yesterday
        manager.log_completion("Read Book", today - datetime.timedelta(days=i))
    
    # Weekly Review: consistent weekly streak
    for i in range(0, 28, 7):  # every 7 days for 4 weeks
        manager.log_completion("Weekly Review", today - datetime.timedelta(days=i))
    
    # Meditation: streak broken a while ago
    for i in range(10, 15):  # 5 day streak in the past
        manager.log_completion("Meditation", today - datetime.timedelta(days=i))
    
    streak_info = {
        "Morning Run": 5,       # current streak
        "Read Book": 1,         # streak broken yesterday
        "Weekly Review": 4,     # 4 week streak
        "Meditation": 0         # no current streak
    }
    
    return habits, manager, streak_info

# --- Habit Class Tests ---
def test_habit_creation():
    """Tests the Habit class initialization."""
    now = datetime.datetime.now()
    h = Habit("Test Habit", "A test", "daily", now)
    assert h.name == "Test Habit"
    assert h.description == "A test"
    assert h.schedule == "daily"
    assert h.created_on == now

def test_habit_validation():
    """Tests that Habit validates the schedule."""
    # Invalid schedule
    try:
        Habit("Invalid", "Test", "monthly")
        assert False, "Should have raised ValueError for invalid schedule"
    except ValueError:
        # This is expected
        pass
    
    # Empty schedule
    try:
        Habit("Invalid", "Test", "")
        assert False, "Should have raised ValueError for empty schedule"
    except ValueError:
        # This is expected
        pass
    
    # These should not raise
    Habit("Valid1", "Test", "daily")
    Habit("Valid2", "Test", "weekly")

def test_habit_string_representation():
    """Tests the string representation of a Habit."""
    h = Habit("Test", "Description", "daily")
    assert str(h) == f"Habit: Test (daily) - Created: {h.created_on.strftime('%Y-%m-%d')}"

# --- DataManager Tests ---
def test_add_get_habit():
    """Tests adding and retrieving a habit via DataManager."""
    manager = create_data_manager()
    manager.add_habit("Yoga", "Morning yoga", "daily")
    habit = manager.get_habit("Yoga")
    assert habit is not None
    assert habit.name == "Yoga"
    assert habit.description == "Morning yoga"
    assert habit.schedule == "daily"

def test_add_duplicate_habit():
    """Tests that adding a duplicate habit raises an error."""
    manager = create_data_manager()
    manager.add_habit("Unique", "Test", "daily")
    
    try:
        manager.add_habit("Unique", "Another desc", "weekly")
        assert False, "Should have raised QueryError for duplicate habit"
    except database.QueryError:
        # This is expected
        pass

def test_get_nonexistent_habit():
    """Tests that getting a non-existent habit returns None."""
    manager = create_data_manager()
    assert manager.get_habit("Nonexistent") is None

def test_get_all_habits():
    """Tests retrieving all habits."""
    habits, manager = create_sample_habits()
    all_habits = manager.get_all_habits()
    assert len(all_habits) == len(habits)
    
    # Check each habit is present
    habit_names = [h.name for h in all_habits]
    for name, _, _ in habits:
        assert name in habit_names

def test_delete_habit():
    """Tests deleting a habit."""
    manager = create_data_manager()
    manager.add_habit("ToDelete", "Will be deleted", "daily")
    assert manager.get_habit("ToDelete") is not None
    
    assert manager.delete_habit("ToDelete") is True
    assert manager.get_habit("ToDelete") is None

def test_delete_nonexistent_habit(data_manager):
    """Tests deleting a non-existent habit."""
    assert data_manager.delete_habit("Nonexistent") is False

def test_add_duplicate_habit(data_manager):
    """Tests that adding a duplicate habit raises an error."""
    data_manager.add_habit("Unique", "Test", "daily")
    
    with pytest.raises(database.QueryError):
        data_manager.add_habit("Unique", "Another desc", "weekly")

def test_get_nonexistent_habit(data_manager):
    """Tests that getting a non-existent habit returns None."""
    assert data_manager.get_habit("Nonexistent") is None

def test_get_all_habits(data_manager, sample_habits):
    """Tests retrieving all habits."""
    habits = data_manager.get_all_habits()
    assert len(habits) == len(sample_habits)
    
    # Check each habit is present
    habit_names = [h.name for h in habits]
    for name, _, _ in sample_habits:
        assert name in habit_names

def test_delete_habit(data_manager):
    """Tests deleting a habit."""
    data_manager.add_habit("ToDelete", "Will be deleted", "daily")
    assert data_manager.get_habit("ToDelete") is not None
    
    assert data_manager.delete_habit("ToDelete") is True
    assert data_manager.get_habit("ToDelete") is None

def test_delete_nonexistent_habit(data_manager):
    """Tests deleting a non-existent habit."""
    assert data_manager.delete_habit("Nonexistent") is False

def test_log_get_completion():
    """Tests logging and retrieving completions."""
    manager = create_data_manager()
    manager.add_habit("Read", "Read 30 mins", "daily")
    ts1 = datetime.datetime(2025, 4, 25, 10, 0, 0)
    ts2 = datetime.datetime(2025, 4, 26, 11, 0, 0)
    
    manager.log_completion("Read", ts1)
    manager.log_completion("Read", ts2)
    
    completions = manager.get_completions("Read")
    assert len(completions) == 2
    
    completion_dates = [c.date() for c in completions]
    assert ts1.date() in completion_dates
    assert ts2.date() in completion_dates

def test_log_completion_nonexistent_habit():
    """Tests that logging a completion for a non-existent habit raises an error."""
    manager = create_data_manager()
    try:
        manager.log_completion("Nonexistent", datetime.datetime.now())
        assert False, "Should have raised HabitNotFoundError"
    except HabitNotFoundError:
        # This is expected
        pass

def test_get_completions_nonexistent_habit():
    """Tests that getting completions for a non-existent habit raises an error."""
    manager = create_data_manager()
    try:
        manager.get_completions("Nonexistent")
        assert False, "Should have raised HabitNotFoundError"
    except HabitNotFoundError:
        # This is expected
        pass

def test_get_completions_in_range():
    """Tests retrieving completions within a date range."""
    _, manager, _ = create_sample_completions()
    today = datetime.datetime.now().date()
    
    # Get completions for Morning Run in the last 3 days
    completions = manager.get_completions_in_range(
        "Morning Run", 
        today - datetime.timedelta(days=3), 
        today
    )
    
    assert len(completions) == 3  # Should only include last 3 days

def test_get_completions_invalid_range(data_manager, sample_habits):
    """Tests that an invalid date range raises an error."""
    today = datetime.datetime.now().date()
    
    with pytest.raises(ValueError):
        data_manager.get_completions_in_range(
            "Morning Run",
            today,  # Start date
            today - datetime.timedelta(days=1)  # End date before start
        )

# --- Analytics Tests ---
def test_get_habits_by_periodicity():
    """Tests filtering habits by schedule."""
    habits = [
        Habit("Daily1", "", "daily"),
        Habit("Daily2", "", "daily"),
        Habit("Weekly1", "", "weekly")
    ]
    
    daily = analytics.get_habits_by_periodicity(habits, "daily")
    assert len(daily) == 2
    assert all(h.schedule == "daily" for h in daily)
    
    weekly = analytics.get_habits_by_periodicity(habits, "weekly")
    assert len(weekly) == 1
    assert weekly[0].name == "Weekly1"

def test_get_habits_by_invalid_periodicity():
    """Tests that filtering by an invalid schedule raises an error."""
    habits = [Habit("Test", "", "daily")]
    
    with pytest.raises(ValueError):
        analytics.get_habits_by_periodicity(habits, "monthly")

def test_daily_streak_calculation():
    """Tests the calculation of current daily streaks."""
    # Create date to simulate today
    today = datetime.date.today()
    
    # Perfect streak for the last 5 days
    dates = [
        datetime.datetime.combine(today, datetime.time(12, 0)),  # Today
        datetime.datetime.combine(today - datetime.timedelta(days=1), datetime.time(12, 0)),  # Yesterday
        datetime.datetime.combine(today - datetime.timedelta(days=2), datetime.time(12, 0)),
        datetime.datetime.combine(today - datetime.timedelta(days=3), datetime.time(12, 0)),
        datetime.datetime.combine(today - datetime.timedelta(days=4), datetime.time(12, 0))
    ]
    
    # Test current streak calculation
    streak = analytics._calculate_streak(dates, "daily")
    assert streak == 5
    
    # Test broken streak (missing yesterday)
    broken_dates = [
        datetime.datetime.combine(today, datetime.time(12, 0)),  # Today
        # Missing yesterday
        datetime.datetime.combine(today - datetime.timedelta(days=2), datetime.time(12, 0)),
        datetime.datetime.combine(today - datetime.timedelta(days=3), datetime.time(12, 0))
    ]
    
    streak = analytics._calculate_streak(broken_dates, "daily")
    assert streak == 1  # Only today counts

def test_longest_streak_calculation():
    """Tests the calculation of longest streaks."""
    # Create base date for testing
    base_date = datetime.date(2023, 1, 1)
    
    # Two separate streaks: 3 days and 5 days with a gap
    streak1 = [
        datetime.datetime.combine(base_date + datetime.timedelta(days=i), datetime.time(12, 0))
        for i in range(3)
    ]
    
    streak2 = [
        datetime.datetime.combine(base_date + datetime.timedelta(days=i+10), datetime.time(12, 0))
        for i in range(5)
    ]
    
    all_completions = streak1 + streak2
    
    # Test longest streak calculation
    longest = analytics._calculate_longest_streak(all_completions, "daily")
    assert longest == 5

def test_weekly_streak_calculation():
    """Tests the calculation of weekly streaks."""
    # Create base date for testing (a Monday)
    base_date = datetime.date(2023, 1, 2)  # A Monday
    
    # Create weekly completions for 4 consecutive weeks
    weekly_completions = [
        datetime.datetime.combine(base_date + datetime.timedelta(weeks=i), datetime.time(12, 0))
        for i in range(4)
    ]
    
    streak = analytics._calculate_streak(weekly_completions, "weekly")
    assert streak == 4
    
    # Test with a broken weekly streak (missing week 2)
    broken_weekly = weekly_completions.copy()
    broken_weekly.pop(2)  # Remove week 2
    
    streak = analytics._calculate_streak(broken_weekly, "weekly")
    assert streak == 2  # Only the last two weeks count

def test_get_longest_streak_for_habit():
    """Tests retrieving the longest streak for a habit."""
    habit = Habit("Test", "", "daily")
    
    # Create completions with two streaks
    today = datetime.date.today()
    streak1 = [  # 3-day streak this week
        datetime.datetime.combine(today - datetime.timedelta(days=i), datetime.time(12, 0))
        for i in range(3)
    ]
    
    streak2 = [  # 5-day streak last month
        datetime.datetime.combine(today - datetime.timedelta(days=i+30), datetime.time(12, 0))
        for i in range(5)
    ]
    
    completions = streak1 + streak2
    
    longest = analytics.get_longest_streak_for_habit(habit, completions)
    assert longest == 5

def test_get_current_streak_for_habit():
    """Tests retrieving the current streak for a habit."""
    habit = Habit("Test", "", "daily")
    
    # Create a current 3-day streak
    today = datetime.date.today()
    completions = [
        datetime.datetime.combine(today - datetime.timedelta(days=i), datetime.time(12, 0))
        for i in range(3)
    ]
    
    current = analytics.get_current_streak_for_habit(habit, completions)
    assert current == 3
    
    # Test with no current streak (last completion was 5 days ago)
    old_completions = [
        datetime.datetime.combine(today - datetime.timedelta(days=i+5), datetime.time(12, 0))
        for i in range(3)
    ]
    
    current = analytics.get_current_streak_for_habit(habit, old_completions)
    assert current == 0

def test_get_longest_streak_all():
    """Tests retrieving the longest streak across all habits."""
    habits = [
        Habit("Habit1", "", "daily"),
        Habit("Habit2", "", "daily"),
        Habit("Habit3", "", "weekly")
    ]
    
    today = datetime.date.today()
    
    # Habit1: 3-day streak
    habit1_completions = [
        datetime.datetime.combine(today - datetime.timedelta(days=i), datetime.time(12, 0))
        for i in range(3)
    ]
    
    # Habit2: 5-day streak
    habit2_completions = [
        datetime.datetime.combine(today - datetime.timedelta(days=i), datetime.time(12, 0))
        for i in range(5)
    ]
    
    # Habit3: 3-week streak
    habit3_completions = [
        datetime.datetime.combine(today - datetime.timedelta(weeks=i), datetime.time(12, 0))
        for i in range(3)
    ]
    
    all_completions = {
        "Habit1": habit1_completions,
        "Habit2": habit2_completions,
        "Habit3": habit3_completions
    }
    
    longest = analytics.get_longest_streak_all(habits, all_completions)
    assert longest == 5  # Habit2 has the longest streak

def test_find_struggling_habits():
    """Tests identifying struggling habits."""
    today = datetime.date.today()
    
    habits = [
        Habit("Daily1", "", "daily"),  # Missing most days
        Habit("Daily2", "", "daily"),  # Perfect record
        Habit("Weekly1", "", "weekly")  # Missing one week
    ]
    
    # Daily1: Only 3 completions in last 10 days (missing 7)
    daily1_completions = [
        datetime.datetime.combine(today - datetime.timedelta(days=1), datetime.time(12, 0)),
        datetime.datetime.combine(today - datetime.timedelta(days=5), datetime.time(12, 0)),
        datetime.datetime.combine(today - datetime.timedelta(days=9), datetime.time(12, 0))
    ]
    
    # Daily2: All 10 days completed
    daily2_completions = [
        datetime.datetime.combine(today - datetime.timedelta(days=i), datetime.time(12, 0))
        for i in range(10)
    ]
    
    # Weekly1: 1 completion in last 3 weeks (missing 2)
    weekly1_completions = [
        datetime.datetime.combine(today - datetime.timedelta(days=7), datetime.time(12, 0))
    ]
    
    all_completions = {
        "Daily1": daily1_completions,
        "Daily2": daily2_completions,
        "Weekly1": weekly1_completions
    }
    
    period_start = today - datetime.timedelta(days=10)
    period_end = today
    
    struggling = analytics.find_struggling_habits(habits, all_completions, period_start, period_end)
    
    # Verify the struggling habits are correctly identified (order is by missed count)
    assert struggling[0][0] == "Daily1"  # Most missed
    assert struggling[0][1] > 0
    
    assert struggling[1][0] == "Weekly1"  # Second most missed
    assert struggling[1][1] > 0
    
    assert struggling[2][0] == "Daily2"  # Not missing any
    assert struggling[2][1] == 0

# --- HabitController Tests ---
def test_controller_add_habit():
    """Tests adding a habit via the controller."""
    controller = create_controller()
    controller.add_habit("TestHabit", "Description", "daily")
    
    # Verify the habit was added
    habit = controller.manager.get_habit("TestHabit")
    assert habit is not None
    assert habit.name == "TestHabit"
    assert habit.description == "Description"
    assert habit.schedule == "daily"

def test_controller_add_invalid_habit():
    """Tests that adding an invalid habit raises appropriate errors."""
    controller = create_controller()
    
    # Invalid schedule
    try:
        controller.add_habit("Test", "Description", "monthly")
        assert False, "Should have raised ValidationError for invalid schedule"
    except ValidationError:
        # This is expected
        pass
    
    # Empty name
    try:
        controller.add_habit("", "Description", "daily")
        assert False, "Should have raised ValidationError for empty name"
    except ValidationError:
        # This is expected
        pass

def test_controller_mark_habit_done():
    """Tests marking a habit as done."""
    controller = create_controller()
    controller.add_habit("TestHabit", "Description", "daily")
    result = controller.mark_habit_done("TestHabit")
    assert result is True
    
    # Verify completion was recorded
    completions = controller.manager.get_completions("TestHabit")
    assert len(completions) == 1

def test_controller_mark_nonexistent_habit(controller):
    """Tests marking a non-existent habit raises an error."""
    with pytest.raises(HabitNotFoundError):
        controller.mark_habit_done("NonexistentHabit")

def test_controller_view_all_habits():
    """Tests viewing all habits."""
    controller = create_controller()
    # Create sample habits
    habits, _ = create_sample_habits()
    
    # Add sample habits via the controller
    for name, desc, schedule in habits:
        controller.add_habit(name, desc, schedule)
    
    result = controller.view_all_habits()
    
    # Check that the result includes all habit names
    for name, _, _ in habits:
        assert name in result

def test_controller_view_habits_by_schedule():
    """Tests viewing habits filtered by schedule."""
    controller = create_controller()
    # Create sample habits
    habits, _ = create_sample_habits()
    
    # Add sample habits via the controller
    for name, desc, schedule in habits:
        controller.add_habit(name, desc, schedule)
    
    # Test viewing daily habits
    result = controller.view_habits_by_schedule("daily")
    assert "Morning Run" in result
    assert "Read Book" in result
    assert "Weekly Review" not in result
    
    # Test viewing weekly habits
    result = controller.view_habits_by_schedule("weekly")
    assert "Weekly Review" in result
    assert "Morning Run" not in result

def test_controller_view_invalid_schedule():
    """Tests that viewing an invalid schedule raises an error."""
    controller = create_controller()
    try:
        controller.view_habits_by_schedule("monthly")
        assert False, "Should have raised ValidationError"
    except ValidationError:
        # This is expected
        pass

def test_controller_view_habit_streak():
    """Tests viewing a habit's streak information."""
    controller = create_controller()
    
    # Add a test habit
    controller.add_habit("Morning Run", "Daily exercise", "daily")
    
    # Add completions to create a streak
    today = datetime.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    
    # Morning Run: 5-day streak
    for i in range(5):
        controller.mark_habit_done("Morning Run", today - datetime.timedelta(days=i))
    
    result = controller.view_habit_streak("Morning Run")
    
    # Check that streak info is included
    assert "Morning Run" in result
    assert "Current Streak: 5" in result
    assert "Last completed" in result

def test_controller_view_nonexistent_habit_streak():
    """Tests viewing streak for a non-existent habit raises an error."""
    controller = create_controller()
    try:
        controller.view_habit_streak("NonexistentHabit")
        assert False, "Should have raised HabitNotFoundError"
    except HabitNotFoundError:
        # This is expected
        pass

def test_controller_view_longest_streak_all():
    """Tests viewing the longest streak across all habits."""
    controller = create_controller()
    
    # Add test habits
    controller.add_habit("Morning Run", "Daily exercise", "daily")
    controller.add_habit("Read Book", "Daily reading", "daily")
    
    # Add completions to create different streaks
    today = datetime.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    
    # Morning Run: 5-day streak
    for i in range(5):
        controller.mark_habit_done("Morning Run", today - datetime.timedelta(days=i))
    
    # Read Book: 3-day streak
    for i in range(3):
        controller.mark_habit_done("Read Book", today - datetime.timedelta(days=i))
    
    result = controller.view_longest_streak_all()
    
    # Check that the result includes the longest streak info
    assert "Morning Run" in result
    assert "5" in result  # The streak count

def test_controller_delete_habit():
    """Tests deleting a habit."""
    controller = create_controller()
    controller.add_habit("TestHabit", "Description", "daily")
    result = controller.delete_habit("TestHabit")
    assert result is True
    
    # Verify the habit was deleted
    habit = controller.manager.get_habit("TestHabit")
    assert habit is None

def test_controller_delete_nonexistent_habit():
    """Tests deleting a non-existent habit."""
    controller = create_controller()
    result = controller.delete_habit("NonexistentHabit")
    assert result is False

def test_controller_get_struggling_habits():
    """Tests getting struggling habits information."""
    controller = create_controller()
    
    # Add test habits
    controller.add_habit("Morning Run", "Daily exercise", "daily")
    controller.add_habit("Read Book", "Daily reading", "daily")
    
    # Add completions to create struggling habits
    today = datetime.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    
    # Morning Run: Perfect record (not struggling)
    for i in range(30):
        controller.mark_habit_done("Morning Run", today - datetime.timedelta(days=i))
    
    # Read Book: Missing most days (struggling)
    controller.mark_habit_done("Read Book", today)
    controller.mark_habit_done("Read Book", today - datetime.timedelta(days=10))
    controller.mark_habit_done("Read Book", today - datetime.timedelta(days=20))
    
    result = controller.get_struggling_habits(30)
    
    # Check that the struggling habit is identified
    assert "Read Book" in result
    assert "missed completions" in result
    assert "Morning Run" not in result or "Morning Run: 0 missed" in result

# Removed test_controller_backup_data - we decided not to implement this feature