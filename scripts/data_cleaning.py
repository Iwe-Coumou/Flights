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

    print("Database cleaning completed.")

if __name__ == "__main__":
    db_path = "data/flights_database.db"  # Change this to the actual database path
    conn = sqlite3.connect(db_path)
    clean_database(conn)
    conn.close()