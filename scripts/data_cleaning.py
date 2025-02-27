import sqlite3
import timezonefinder
import plotly.express as px
import pandas as pd
from constants import MISSING_AIRPORTS

def delete_unused_airports(conn):
    """Deletes airports from the airports table that are not referenced as an origin or destination in the flights table."""
    try:
        cursor = conn.cursor()

        delete_query = """
        DELETE FROM airports
        WHERE faa NOT IN (
            SELECT DISTINCT origin FROM flights
            UNION
            SELECT DISTINCT dest FROM flights
        );
        """

        cursor.execute(delete_query)
        conn.commit()
        rows_deleted = cursor.rowcount

        print(f"Deleted {rows_deleted} unused airports from the airports table.")
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

def add_missing_airports(conn):
    """Adds manually defined missing airports to the airports table only if they do not already exist."""
    try:
        cursor = conn.cursor()
        for airport in MISSING_AIRPORTS:
            faa_code = airport[0]
            cursor.execute("SELECT COUNT(*) FROM airports WHERE faa = ?", (faa_code,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO airports (faa, name, lat, lon, alt, tz, dst, tzone) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, airport)
        conn.commit()
        print("Missing airports checked and added where necessary.")
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

def find_incorrect_timezones(conn):
    """Finds airports with incorrect timezones by comparing them against the actual timezone from latitude and longitude."""
    try:
        cursor = conn.cursor()
        tf = timezonefinder.TimezoneFinder()
        
        cursor.execute("SELECT faa, lat, lon, tzone, tz FROM airports")
        airports = cursor.fetchall()
        
        incorrect_airports = []
        
        for faa, lat, lon, tzone, tz in airports:
            estimated_tz = tf.timezone_at(lng=lon, lat=lat)
            if estimated_tz and estimated_tz != tzone:
                incorrect_airports.append((faa, lat, lon, tzone, estimated_tz, tz))
        
        return incorrect_airports
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return []

def correct_timezones(conn):
    """Corrects incorrect timezones and updates the hour difference column in the airports table."""
    incorrect_airports = find_incorrect_timezones(conn)
    if incorrect_airports:
        try:
            cursor = conn.cursor()
            updates = [(airport[4], airport[5], airport[0]) for airport in incorrect_airports]
            cursor.executemany("UPDATE airports SET tzone = ?, tz = ? WHERE faa = ?", updates)
            conn.commit()
            print(f"Updated {len(updates)} incorrect timezones and hour differences.")
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
    else:
        print("All timezones were already correct.")

def plot_timezones(conn):
    """Plots airport timezone hour differences before and after correction."""
    cursor = conn.cursor()
    cursor.execute("SELECT faa, lat, lon, tz FROM airports")
    airports = cursor.fetchall()
    
    df = pd.DataFrame(airports, columns=["FAA", "Latitude", "Longitude", "Hour Difference"])
    df["Hour Difference"] = df["Hour Difference"].astype(str)  # Convert to categorical
    
    fig = px.scatter_geo(
        df, lat="Latitude", lon="Longitude", color="Hour Difference",
        hover_name="FAA", title="Airport Timezone Hour Differences"
    )
    fig.show()

def remove_duplicate_flights(conn):
    """Removes duplicate flights while keeping the earliest record."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM flights
            WHERE ROWID NOT IN (
                SELECT MIN(ROWID)
                FROM flights
                GROUP BY year, month, day, flight, origin, dest, sched_dep_time
            );
        """
        )
        conn.commit()
        rows_deleted = cursor.rowcount
        print(f"Deleted {rows_deleted} duplicate flights.")
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

def add_canceled_column(conn):
    """Adds a 'canceled' column to the flights table to indicate flights that did not depart."""
    try:
        cursor = conn.cursor()
        # Add the canceled column if it doesn't exist
        cursor.execute("""
            ALTER TABLE flights ADD COLUMN canceled INTEGER DEFAULT 0
        """
        )
    except sqlite3.OperationalError:
        # The column already exists, so we can update it instead
        pass
    
    # Update the canceled column based on the simplified rule
    cursor.execute("""
        UPDATE flights 
        SET canceled = 1 
        WHERE dep_time IS NULL;
    """
    )
    conn.commit()
    print("Canceled flights identified and marked.")

def estimate_arr_delay_and_air_time(conn):
    """Estimates missing arr_delay and air_time for flights that have arr_time but missing these values,
    accounting for flights that cross midnight."""
    try:
        cursor = conn.cursor()
        
        # Update arr_delay using time conversion and handling midnight rollover
        cursor.execute("""
            UPDATE flights
            SET arr_delay = CASE
                WHEN (((arr_time / 100) * 60) + (arr_time % 100)) < (((sched_arr_time / 100) * 60) + (sched_arr_time % 100))
                    THEN (((arr_time / 100) * 60) + (arr_time % 100)) + 1440 - (((sched_arr_time / 100) * 60) + (sched_arr_time % 100))
                ELSE (((arr_time / 100) * 60) + (arr_time % 100)) - (((sched_arr_time / 100) * 60) + (sched_arr_time % 100))
            END
            WHERE arr_time IS NOT NULL 
              AND sched_arr_time IS NOT NULL 
              AND arr_delay IS NULL;
        """)
        
        # Update air_time using time conversion and handling midnight rollover
        cursor.execute("""
            UPDATE flights
            SET air_time = CASE
                WHEN (((arr_time / 100) * 60) + (arr_time % 100)) < (((dep_time / 100) * 60) + (dep_time % 100))
                    THEN (((arr_time / 100) * 60) + (arr_time % 100)) + 1440 - (((dep_time / 100) * 60) + (dep_time % 100))
                ELSE (((arr_time / 100) * 60) + (arr_time % 100)) - (((dep_time / 100) * 60) + (dep_time % 100))
            END
            WHERE arr_time IS NOT NULL 
              AND dep_time IS NOT NULL 
              AND air_time IS NULL;
        """)
        
        conn.commit()
        num_of_changes = cursor.rowcount
        print(f"Estimated missing arr_delay and air_time for {num_of_changes} flights using correct time conversion.")
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

def delete_flights_without_arrival(conn):
    """Deletes flights that have a departure time but no recorded arrival time."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM flights
            WHERE dep_time IS NOT NULL AND arr_time IS NULL;
        """
        )
        conn.commit()
        rows_deleted = cursor.rowcount
        print(f"Deleted {rows_deleted} flights with no recorded arrival time.")
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

def identify_unrealistic_air_times_dynamic(conn, min_speed=300, max_speed=600):
    """
    Identifies flights with unrealistic air_time values based on the flight's distance.
    
    The function assumes that:
        - A flight should not fly faster than max_speed (mph)
        - A flight should not fly slower than min_speed (mph)
    
    The expected flight time in minutes is calculated as:
        - Lower bound: (distance * 60) / max_speed
        - Upper bound: (distance * 60) / min_speed
        
    Flights with air_time below the lower bound or above the upper bound are flagged as unrealistic.
    
    Parameters:
        conn (sqlite3.Connection): A connection to the SQLite database.
        min_speed (int): The minimum expected average speed (mph). Defaults to 300.
        max_speed (int): The maximum expected average speed (mph). Defaults to 600.
        
    Returns:
        List of tuples: Each tuple is a row from the flights table with an unrealistic air_time.
    """
    try:
        cursor = conn.cursor()
        query = """
            SELECT *
            FROM flights
            WHERE air_time < (distance * 60.0 / ?)
               OR air_time > (distance * 60.0 / ?)
        """
        # The first parameter is used to compute the lower bound (fastest speed)
        # The second parameter is for the upper bound (slowest speed)
        cursor.execute(query, (max_speed, min_speed))
        rows = cursor.fetchall()
        print(f"Found {len(rows)} flights with unrealistic air_time values based on distance and speed assumptions.")
        return rows
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return []
    
def delete_unrealistic_air_times_dynamic(conn, min_speed=300, max_speed=600):
    """
    Deletes flights with unrealistic air_time values based on the flight's distance.
    
    The function assumes that flights should fly within a certain speed range:
      - They should not be faster than max_speed (mph) (i.e., air_time should not be shorter than distance * 60 / max_speed)
      - They should not be slower than min_speed (mph) (i.e., air_time should not be longer than distance * 60 / min_speed)
    
    Parameters:
        conn (sqlite3.Connection): A connection to the SQLite database.
        min_speed (int): The minimum expected average speed in mph (default is 300).
        max_speed (int): The maximum expected average speed in mph (default is 600).
        
    Returns:
        int: The number of flights deleted.
    """
    try:
        cursor = conn.cursor()
        delete_query = """
            DELETE FROM flights
            WHERE air_time < (distance * 60.0 / ?)
               OR air_time > (distance * 60.0 / ?)
        """
        cursor.execute(delete_query, (max_speed, min_speed))
        conn.commit()
        deleted_rows = cursor.rowcount
        print(f"Deleted {deleted_rows} unrealistic flight records based on dynamic air_time bounds.")
        return deleted_rows
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None

def validate_calculated_air_time_against_schedule(conn, tolerance=45):
    """
    Validates the calculated air_time (derived from dep_time and arr_time) against the scheduled flight duration 
    (sched_arr_time - sched_dep_time). Both times are converted from HHMM format to minutes, with an adjustment 
    for flights that cross midnight.
    
    A flight is flagged as unrealistic if the absolute difference between the calculated air_time and 
    the scheduled duration exceeds the given tolerance.
    
    The function prints:
      - The total number of flights compared.
      - The number of flights with a discrepancy greater than the tolerance.
    
    It returns nothing.
    """
    
    def convert_hhmm(time_val):
        """Converts a HHMM integer to minutes."""
        hours = int(time_val // 100)
        minutes = int(time_val % 100)
        return hours * 60 + minutes
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT flight, sched_dep_time, sched_arr_time, dep_time, arr_time, air_time
            FROM flights
            WHERE sched_dep_time IS NOT NULL 
              AND sched_arr_time IS NOT NULL
              AND dep_time IS NOT NULL
              AND arr_time IS NOT NULL
              AND air_time IS NOT NULL
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        total_flights = len(rows)
        unrealistic_count = 0
        
        for row in rows:
            flight_id, sched_dep_time, sched_arr_time, dep_time, arr_time, recorded_air_time = row
            
            # Convert scheduled times to minutes.
            sched_dep = convert_hhmm(sched_dep_time)
            sched_arr = convert_hhmm(sched_arr_time)
            if sched_arr < sched_dep:
                sched_arr += 1440  # Adjust for midnight rollover.
            scheduled_duration = sched_arr - sched_dep
            
            # Convert actual times to minutes.
            actual_dep = convert_hhmm(dep_time)
            actual_arr = convert_hhmm(arr_time)
            if actual_arr < actual_dep:
                actual_arr += 1440  # Adjust for midnight rollover.
            calculated_air_time = actual_arr - actual_dep
            
            # Check the absolute difference.
            if abs(calculated_air_time - scheduled_duration) > tolerance:
                unrealistic_count += 1
        
        print(f"Total flights compared: {total_flights}")
        print(f"Flights with air_time discrepancy > {tolerance} minutes: {unrealistic_count}")
    
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")


def clean_database(conn):
    """Calls all data cleaning functions."""
    print("Starting database cleaning...")

    # handle the aiport data
    add_missing_airports(conn)
    delete_unused_airports(conn)
    #plot_timezones(conn)
    correct_timezones(conn)
    #plot_timezones(conn)


    # handle the flights data
    remove_duplicate_flights(conn)
    add_canceled_column(conn)
    estimate_arr_delay_and_air_time(conn)
    delete_flights_without_arrival(conn)
    identify_unrealistic_air_times_dynamic(conn)
    validate_calculated_air_time_against_schedule(conn)
    #delete_unrealistic_air_times_dynamic(conn)

    print("Database cleaning completed.")

if __name__ == "__main__":
    db_path = "data/flights_database.db"  # Change this to the actual database path
    conn = sqlite3.connect(db_path)
    clean_database(conn)
    conn.close()