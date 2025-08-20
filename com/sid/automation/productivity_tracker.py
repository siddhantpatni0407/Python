import time
import psutil
import csv
from datetime import datetime
import os

# Define productive apps (you can customize this)
PRODUCTIVE_APPS = ["code.exe", "pycharm64.exe", "idea64.exe", "chrome.exe", "excel.exe", "word.exe"]

LOG_FILE = "productivity_log.csv"

# Initialize CSV file if not exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header row to the CSV file
        writer.writerow(["Timestamp", "Application", "Status"])

def get_active_applications():
    """
    Retrieves a list of currently running applications.

    Returns:
        list: A list of application names (strings) currently running on the system.
    """
    active_apps = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # Append the name of the process to the active apps list
            active_apps.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Ignore processes that cannot be accessed or no longer exist
            pass
    return active_apps

def log_activity(app, status):
    """
    Logs the activity of an application to a CSV file.

    Args:
        app (str): The name of the application.
        status (str): The status of the application (e.g., "Productive" or "Unproductive").
    """
    with open(LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        # Write the timestamp, application name, and status to the CSV file
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), app, status])

def track_productivity():
    """
    Tracks productivity by monitoring active applications and logging their status.

    - Applications listed in PRODUCTIVE_APPS are logged as "Productive".
    - All other applications are logged as "Unproductive".
    - Logs are written to the CSV file every 10 seconds.

    Press CTRL+C to stop the tracking.
    """
    print("Tracking productivity... Press CTRL+C to stop.")
    try:
        while True:
            # Get the list of currently active applications
            active_apps = get_active_applications()
            for app in active_apps:
                if app.lower() in PRODUCTIVE_APPS:
                    # Log the application as productive
                    log_activity(app, "Productive")
                else:
                    # Log the application as unproductive
                    log_activity(app, "Unproductive")
            # Wait for 10 seconds before the next log
            time.sleep(10)
    except KeyboardInterrupt:
        # Handle the user interrupt (CTRL+C) gracefully
        print("\nTracking stopped.")

if __name__ == "__main__":
    # Start tracking productivity when the script is executed
    track_productivity()