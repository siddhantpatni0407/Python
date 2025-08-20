import os
import sqlite3
import pandas as pd
import shutil
from datetime import datetime, timedelta


def fetch_history(time_range):
    """
    Fetch Chrome browsing history based on the selected time range.

    Args:
        time_range (int): The time range for fetching history.
            1 - Last 1 hour
            2 - Last 24 hours
            3 - Last 1 month
            4 - All history (since system is on)

    Returns:
        pd.DataFrame: A DataFrame containing the browsing history with columns:
            - URL: The visited URL.
            - Title: The title of the webpage.
            - Last Visit Time: The timestamp of the last visit.
    """
    # Chrome history database location
    history_db = os.path.expanduser(
        r"~\AppData\Local\Google\Chrome\User Data\Default\History"
    )

    # Copy the database to a temporary location to avoid file lock issues
    temp_db = "temp_history.db"
    shutil.copy2(history_db, temp_db)

    # Connect to the copied database
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Chrome stores time in microseconds since 1601-01-01
    base_time = datetime(1601, 1, 1)

    # Determine the start time based on the selected time range
    if time_range == 1:  # Last 1 hour
        start_time = (datetime.utcnow() - timedelta(hours=1))
    elif time_range == 2:  # Last 24 hours
        start_time = (datetime.utcnow() - timedelta(days=1))
    elif time_range == 3:  # Last 1 month
        start_time = (datetime.utcnow() - timedelta(days=30))
    else:  # Since system is on (all history)
        start_time = None

    # SQL query to fetch browsing history
    query = "SELECT url, title, last_visit_time FROM urls"

    # Add a condition to the query if a start time is specified
    if start_time:
        start_timestamp = int((start_time - base_time).total_seconds() * 1000000)
        query += f" WHERE last_visit_time >= {start_timestamp}"

    # Execute the query and fetch all rows
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    # Clean up the temporary database file
    os.remove(temp_db)

    # Convert the results to a DataFrame
    df = pd.DataFrame(rows, columns=["URL", "Title", "Last Visit Time"])
    df["Last Visit Time"] = df["Last Visit Time"].apply(
        lambda x: base_time + timedelta(microseconds=x)
    )

    return df


if __name__ == "__main__":
    """
    Main script execution:
    - Prompts the user to select a time range for fetching browsing history.
    - Fetches the browsing history using the `fetch_history` function.
    - Saves the history to an Excel file if data is found.
    """
    print("Select Time Range to Fetch Browsing History:")
    print("1. Last 1 Hour")
    print("2. Last 24 Hours")
    print("3. Last 1 Month")
    print("4. Since System is On")

    # Get the user's choice for the time range
    choice = int(input("Enter option (1-4): "))

    # Fetch the browsing history for the selected time range
    df = fetch_history(choice)

    if not df.empty:
        # Save the browsing history to an Excel file
        filename = f"chrome_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        sheet_name = {
            1: "Last_1_Hour",
            2: "Last_24_Hours",
            3: "Last_1_Month",
            4: "All_History"
        }[choice]

        df.to_excel(filename, sheet_name=sheet_name, index=False)
        print(f"✅ Browsing history saved to {filename} (Sheet: {sheet_name})")
    else:
        print("⚠️ No browsing history found for the selected range.")