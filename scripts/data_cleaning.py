import sqlite3
import timezonefinder
import plotly.express as px
import pandas as pd
from constants import MISSING_AIRPORTS
import pytz
from datetime import datetime, timezone

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

def get_utc_offset_in_hours(timezone_name):
    """
    Given a time zone name (e.g., 'Asia/Irkutsk'), compute the current UTC offset in hours
    using the built-in 'timezone.utc' instead of datetime.utcnow().
    """
    try:
        # Get the current time in UTC
        now_utc = datetime.now(timezone.utc)

        # Convert the UTC time to the local time for the given time zone
        local_tz = pytz.timezone(timezone_name)
        local_time = now_utc.astimezone(local_tz)

        # Compute the offset in hours
        offset_hours = local_time.utcoffset().total_seconds() / 3600
        return offset_hours
    except Exception as e:
        print(f"Error computing offset for {timezone_name}: {e}")
        return None

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
    """
    Corrects incorrect timezones and updates the UTC offset (tz column) in the airports table.
    For each airport with an incorrect time zone, it recalculates the offset based on the estimated time zone.
    """
    incorrect_airports = find_incorrect_timezones(conn)
    if incorrect_airports:
        try:
            cursor = conn.cursor()
            updates = []
            for airport in incorrect_airports:
                faa = airport[0]
                estimated_tz = airport[4]  # new timezone from TimezoneFinder
                new_offset = get_utc_offset_in_hours(estimated_tz)
                updates.append((estimated_tz, new_offset, faa))
            cursor.executemany("UPDATE airports SET tzone = ?, tz = ? WHERE faa = ?", updates)
            conn.commit()
            print(f"Updated {len(updates)} incorrect timezones and their UTC offsets.")
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
    rows = cursor.rowcount
    print(f"{rows} Canceled flights identified and marked.")

def convert_hhmm_to_full_datetime(conn: sqlite3.Connection):
    """
    Converts HHMM integer columns [sched_dep_time, dep_time, sched_arr_time, arr_time] 
    into proper 'YYYY-MM-DD HH:MM:SS' datetimes using the separate year, month, day columns.
    
    For example, if sched_dep_time = 700 (meaning 07:00) and the date columns 
    are year=2013, month=1, day=15, this sets sched_dep_time to '2013-01-15 07:00:00'.
    
    Assumes:
      - 'year', 'month', 'day' columns exist and contain valid integers.
      - The HHMM columns are stored as integers (e.g. 700, 1345, etc.) or as short strings.
      - If any of the HHMM columns is NULL, it is left unchanged.
      - The conversion is only applied if the value is not already in datetime format 
        (we assume that valid datetime strings have a length of 19 characters).
    
    Parameters:
        conn (sqlite3.Connection): A connection to the SQLite database.
    """
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN")
        
        # Convert sched_dep_time only if not already in datetime format.
        cursor.execute("""
            UPDATE flights
            SET sched_dep_time = datetime(
                year || '-' || printf('%02d', month) || '-' || printf('%02d', day) || ' ' ||
                substr(printf('%04d', sched_dep_time), 1, 2) || ':' ||
                substr(printf('%04d', sched_dep_time), 3, 2) || ':00'
            )
            WHERE sched_dep_time IS NOT NULL
              AND length(sched_dep_time) < 19;
        """)
        
        # Convert dep_time only if not already in datetime format.
        cursor.execute("""
            UPDATE flights
            SET dep_time = datetime(
                year || '-' || printf('%02d', month) || '-' || printf('%02d', day) || ' ' ||
                substr(printf('%04d', dep_time), 1, 2) || ':' ||
                substr(printf('%04d', dep_time), 3, 2) || ':00'
            )
            WHERE dep_time IS NOT NULL
              AND length(dep_time) < 19;
        """)
        
        # Convert sched_arr_time only if not already in datetime format.
        cursor.execute("""
            UPDATE flights
            SET sched_arr_time = datetime(
                year || '-' || printf('%02d', month) || '-' || printf('%02d', day) || ' ' ||
                substr(printf('%04d', sched_arr_time), 1, 2) || ':' ||
                substr(printf('%04d', sched_arr_time), 3, 2) || ':00'
            )
            WHERE sched_arr_time IS NOT NULL
              AND length(sched_arr_time) < 19;
        """)
        
        # Convert arr_time only if not already in datetime format.
        cursor.execute("""
            UPDATE flights
            SET arr_time = datetime(
                year || '-' || printf('%02d', month) || '-' || printf('%02d', day) || ' ' ||
                substr(printf('%04d', arr_time), 1, 2) || ':' ||
                substr(printf('%04d', arr_time), 3, 2) || ':00'
            )
            WHERE arr_time IS NOT NULL
              AND length(arr_time) < 19;
        """)

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

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

def fix_overnight_flights(conn: sqlite3.Connection):
    """
    Adjusts times for overnight flights in the 'flights' table.
    
    Functionality:
      1) Normalize any '24:00:00' timestamps in the following columns:
         - dep_time
         - sched_dep_time
         - arr_time
         - sched_arr_time
         For each, if the stored time ends with '24:00:00', it converts it to the next day's '00:00:00'.
      
      2) Apply overnight logic:
         (a) If dep_time is less than sched_dep_time and dep_delay is NULL or >= 0,
             add one day to dep_time.
         (b) If sched_arr_time is less than sched_dep_time, add one day to sched_arr_time.
         (c) If arr_time is less than sched_arr_time, add one day to arr_time.
    
    Assumptions:
      - Times are stored in a recognized datetime format (as text) except for the potential '24:00:00' issue.
      - The table 'flights' has the columns: dep_time, sched_dep_time, arr_time, sched_arr_time, and dep_delay.
      - There is no primary key; updates are applied directly.
    """
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN")
        
        # # ---------------------------------------------------------------------
        # # STEP 1: Normalize any '24:00:00' timestamps to the next day's '00:00:00'
        # # ---------------------------------------------------------------------
        # normalization_updates = {
        #     "dep_time": "fixed_dep_time",
        #     "sched_dep_time": "fixed_sched_dep_time",
        #     "arr_time": "fixed_arr_time",
        #     "sched_arr_time": "fixed_sched_arr_time"
        # }
        # norm_counts = {}
        # for col, label in normalization_updates.items():
        #     sql = f"""
        #         UPDATE flights
        #         SET {col} = datetime(
        #             strftime('%Y-%m-%d', {col}, '+1 day') || ' 00:00:00'
        #         )
        #         WHERE {col} LIKE '% 24:00:00';
        #     """
        #     cursor.execute(sql)
        #     norm_counts[label] = cursor.rowcount
        
        # ---------------------------------------------------------------------
        # STEP 2: Apply overnight adjustments
        # ---------------------------------------------------------------------
        
        # (a) Adjust dep_time: if dep_time < sched_dep_time and dep_delay is NULL or >= 0, add one day.
        cursor.execute("""
            UPDATE flights
            SET dep_time = datetime(dep_time, '+1 day')
            WHERE dep_time IS NOT NULL
              AND sched_dep_time IS NOT NULL
              AND strftime('%s', dep_time) < strftime('%s', sched_dep_time)
              AND (dep_delay IS NULL OR dep_delay >= 0);
        """)
        dep_shifted = cursor.rowcount
        
        # (b) Adjust sched_arr_time: if sched_arr_time < sched_dep_time, add one day.
        cursor.execute("""
            UPDATE flights
            SET sched_arr_time = datetime(sched_arr_time, '+1 day'),
            arr_time = datetime(arr_time, '+1 day')
            WHERE sched_arr_time IS NOT NULL
              AND sched_dep_time IS NOT NULL
              AND strftime('%s', sched_arr_time) < strftime('%s', sched_dep_time);
        """)
        sched_arr_shifted = cursor.rowcount
        
        # (c) Adjust arr_time: if arr_time < sched_arr_time, add one day.
        cursor.execute("""
            UPDATE flights
            SET arr_time = datetime(arr_time, '+1 day')
            WHERE arr_time IS NOT NULL
              AND sched_arr_time IS NOT NULL
              AND (arr_delay >= 0 OR arr_delay IS NULL)
              AND strftime('%s', arr_time) < strftime('%s', sched_arr_time);
        """)
        arr_shifted = cursor.rowcount
        
        conn.commit()
        
        print("Fix Overnight Flights Complete (New Version).")
        # print("Normalization of '24:00:00' -> next day '00:00:00':")
        # for label, count in norm_counts.items():
        #     print(f"  {label}: {count} rows updated")
        print("Overnight adjustments:")
        print(f"  dep_time shifted:       {dep_shifted} rows updated")
        print(f"  sched_arr_time shifted: {sched_arr_shifted} rows updated")
        print(f"  arr_time shifted:       {arr_shifted} rows updated")
    
    except Exception as e:
        conn.rollback()
        raise e

def update_missing_arr_delay_air_time(conn: sqlite3.Connection):
    """
    Updates rows that have an arr_time but are missing either arr_delay or air_time.
    The values are computed as follows:
      - arr_delay: difference in minutes between arr_time and sched_arr_time.
                   If the computed difference is negative (indicating an overnight flight),
                   add 86400 seconds (i.e. 24 hours) before dividing by 60.
      - air_time:  difference in minutes between arr_time and dep_time.
                   If the computed difference is negative, add 86400 seconds before dividing by 60.
    
    This function updates the values in-place and prints the number of rows updated.
    
    Assumptions:
      - Time columns (sched_arr_time, arr_time, dep_time) are stored in a standard datetime format
        ("YYYY-MM-DD HH:MM:SS").
      - A negative computed difference indicates that the flight crossed midnight.
    """
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN")
        update_query = """
            UPDATE flights
            SET arr_delay = CASE 
                              WHEN (strftime('%s', arr_time) - strftime('%s', sched_arr_time)) < 0
                                THEN CAST((strftime('%s', arr_time) - strftime('%s', sched_arr_time) + 86400) / 60 AS INTEGER)
                              ELSE CAST((strftime('%s', arr_time) - strftime('%s', sched_arr_time)) / 60 AS INTEGER)
                            END,
                air_time = CASE
                              WHEN (strftime('%s', arr_time) - strftime('%s', dep_time)) < 0
                                THEN CAST((strftime('%s', arr_time) - strftime('%s', dep_time) + 86400) / 60 AS INTEGER)
                              ELSE CAST((strftime('%s', arr_time) - strftime('%s', dep_time)) / 60 AS INTEGER)
                           END
            WHERE arr_time IS NOT NULL 
              AND (arr_delay IS NULL OR air_time IS NULL);
        """
        cursor.execute(update_query)
        rows_updated = cursor.rowcount
        
        conn.commit()
        print(f"Updated {rows_updated} rows for missing arr_delay/air_time with overnight correction.")
    except Exception as e:
        conn.rollback()
        raise e

def check_and_fix_flight_time_consistency(conn: sqlite3.Connection, fix_delays: bool = True):
    """
    For each flight in the 'flights' table:
      - If fix_delays=True:
          Corrects dep_delay to be the difference in minutes between dep_time and sched_dep_time.
          Corrects arr_delay to be the difference in minutes between arr_time and sched_arr_time.
        Otherwise, only checks the current values without modifying them.
      
      - Checks air_time vs (arr_time - dep_time) for consistency (without correcting air_time).
    
    After optionally making corrections for departure and arrival delays, prints a summary with:
      - Total flights with valid departure data and how many have incorrect dep_delay.
      - Total flights with valid arrival data and how many have incorrect arr_delay.
      - Total flights with valid airtime data and how many have incorrect air_time.
      - How many rows were corrected (if fix_delays=True).
    
    Parameters:
      - conn (sqlite3.Connection): SQLite database connection
      - fix_delays (bool): Whether to actually fix (update) the dep_delay and arr_delay columns.
                          If False, the function only checks the current values.
    
    Assumptions:
      - Time columns (sched_dep_time, dep_time, sched_arr_time, arr_time) are stored in a standard 
        datetime format ("YYYY-MM-DD HH:MM:SS").
      - Differences are computed in minutes.
    """
    cursor = conn.cursor()
    
    rows_dep_updated = 0
    rows_arr_updated = 0
    
    if fix_delays:
        try:
            cursor.execute("BEGIN")
            
            # Update dep_delay
            cursor.execute("""
                UPDATE flights
                SET dep_delay = CAST(
                    (strftime('%s', dep_time) - strftime('%s', sched_dep_time)) / 60 AS INTEGER
                )
                WHERE dep_time IS NOT NULL 
                  AND sched_dep_time IS NOT NULL
                  AND dep_delay != CAST(
                      (strftime('%s', dep_time) - strftime('%s', sched_dep_time)) / 60 AS INTEGER
                  );
            """)
            rows_dep_updated = cursor.rowcount
    
            # Update arr_delay
            cursor.execute("""
                UPDATE flights
                SET arr_delay = CAST(
                    (strftime('%s', arr_time) - strftime('%s', sched_arr_time)) / 60 AS INTEGER
                )
                WHERE arr_time IS NOT NULL 
                  AND sched_arr_time IS NOT NULL
                  AND arr_delay != CAST(
                      (strftime('%s', arr_time) - strftime('%s', sched_arr_time)) / 60 AS INTEGER
                  );
            """)
            rows_arr_updated = cursor.rowcount
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e

    # Now perform the checks (whether or not we fixed delays).
    
    # Departure delay check
    cursor.execute("""
        SELECT COUNT(*) FROM flights
        WHERE dep_time IS NOT NULL AND sched_dep_time IS NOT NULL;
    """)
    total_dep = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM flights
        WHERE dep_time IS NOT NULL AND sched_dep_time IS NOT NULL
          AND dep_delay != CAST(
              (strftime('%s', dep_time) - strftime('%s', sched_dep_time)) / 60 AS INTEGER
          );
    """)
    dep_incorrect = cursor.fetchone()[0]
    
    # Arrival delay check
    cursor.execute("""
        SELECT COUNT(*) FROM flights
        WHERE arr_time IS NOT NULL AND sched_arr_time IS NOT NULL;
    """)
    total_arr = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM flights
        WHERE arr_time IS NOT NULL AND sched_arr_time IS NOT NULL
          AND arr_delay != CAST(
              (strftime('%s', arr_time) - strftime('%s', sched_arr_time)) / 60 AS INTEGER
          );
    """)
    arr_incorrect = cursor.fetchone()[0]
    
    # Airtime check
    cursor.execute("""
        SELECT COUNT(*) FROM flights
        WHERE dep_time IS NOT NULL AND arr_time IS NOT NULL;
    """)
    total_air = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM flights
        WHERE dep_time IS NOT NULL AND arr_time IS NOT NULL
          AND air_time != CAST(
              (strftime('%s', arr_time) - strftime('%s', dep_time)) / 60 AS INTEGER
          );
    """)
    air_incorrect = cursor.fetchone()[0]
    
    # Print the summary
    print("Flight Time Consistency Summary:")
    print(f"  Total flights with valid dep data: {total_dep}")
    print(f"  Flights still incorrect for dep_delay: {dep_incorrect}")
    print(f"  Total flights with valid arr data: {total_arr}")
    print(f"  Flights still incorrect for arr_delay: {arr_incorrect}")
    print(f"  Total flights with valid airtime data: {total_air}")
    print(f"  Flights with incorrect air_time: {air_incorrect}")
    
    if fix_delays:
        print("\nCorrections Applied:")
        print(f"  Flights with corrected dep_delay: {rows_dep_updated}")
        print(f"  Flights with corrected arr_delay: {rows_arr_updated}")
    else:
        print("\nNo corrections applied (fix_delays=False).")

def count_large_airtime_discrepancies(conn: sqlite3.Connection, threshold=45):
    """
    Compares the scheduled flight duration with the stored airtime for each flight and
    counts how many flights have an absolute difference greater than the given threshold (in minutes).
    
    The scheduled duration is computed as:
      - If sched_arr_time is earlier than sched_dep_time (i.e. overnight flight),
        then scheduled duration = (strftime('%s', sched_arr_time) - strftime('%s', sched_dep_time) + 86400) / 60.
      - Otherwise, scheduled duration = (strftime('%s', sched_arr_time) - strftime('%s', sched_dep_time)) / 60.
    
    Only flights where sched_dep_time, sched_arr_time, and air_time are not NULL are considered.
    
    Parameters:
      conn (sqlite3.Connection): A connection to the SQLite database.
      threshold (int): The threshold (in minutes) for the absolute difference between
                       scheduled duration and stored airtime. Defaults to 45 minutes.
    
    Prints the count of flights that exceed this threshold.
    """
    cursor = conn.cursor()
    query = f"""
        SELECT COUNT(*) 
        FROM flights
        WHERE sched_dep_time IS NOT NULL 
          AND sched_arr_time IS NOT NULL
          AND air_time IS NOT NULL
          AND ABS(
              (CASE 
                  WHEN (strftime('%s', sched_arr_time) - strftime('%s', sched_dep_time)) < 0
                  THEN (strftime('%s', sched_arr_time) - strftime('%s', sched_dep_time) + 86400) / 60.0
                  ELSE (strftime('%s', sched_arr_time) - strftime('%s', sched_dep_time)) / 60.0
               END) - air_time
          ) > {threshold};
    """
    cursor.execute(query)
    count = cursor.fetchone()[0]
    print(f"Number of flights where the absolute difference between scheduled duration and airtime exceeds {threshold} minutes: {count}")

def check_and_update_flight_times(conn: sqlite3.Connection):
    """
    High-level function that:
      1) Fixes overnight flights by adding +1 day if:
         - dep_time < sched_dep_time (actual departure crosses midnight)
         - arr_time < dep_time (arrival crosses midnight)
         - sched_arr_time < sched_dep_time (scheduled arrival crosses midnight)
      2) Updates missing arr_delay/air_time values.
      3) Checks and prints a consistency summary.
    """
    fix_overnight_flights(conn)
    update_missing_arr_delay_air_time(conn)
    check_and_fix_flight_time_consistency(conn, True)

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
    convert_hhmm_to_full_datetime(conn)
    check_and_update_flight_times(conn)
    delete_flights_without_arrival(conn)
    count_large_airtime_discrepancies(conn)

    print("Database cleaning completed.")

if __name__ == "__main__":
    db_path = "data/flights_database.db"
    conn = sqlite3.connect(db_path)
    clean_database(conn)
    conn.close()