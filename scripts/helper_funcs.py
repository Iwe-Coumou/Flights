# helper_funcs.py
import sqlite3
import numpy as np
import pandas as pd
import datetime
"""
Module with additional utility functions for querying the DB 
and computing certain values (arrival delays, directions, etc.).
"""

import numpy as np
from pandas import read_sql_query

def get_flight_destinations_from_airport_on_day(conn, month: int, day: int, airport: str) -> set:
    """
    Retrieves all unique flight destinations leaving from a given airport 
    on a specific month/day. 
    """
    cursor = conn.cursor()
    query = """
        SELECT DISTINCT dest FROM flights 
        WHERE month = ? AND day = ? AND origin = ?;
    """
    cursor.execute(query, (month, day, airport))
    return {row[0] for row in cursor.fetchall()}

def top_5_manufacturers(conn, destination_airport: str):
    """
    Finds the top 5 airplane manufacturers for planes flying to a given airport code.
    """
    query = """
        SELECT planes.manufacturer, COUNT(*) as num_flights 
        FROM flights 
        JOIN planes ON flights.tailnum = planes.tailnum
        WHERE flights.dest = ?
        GROUP BY planes.manufacturer
        ORDER BY num_flights DESC
        LIMIT 5;
    """
    return read_sql_query(query, conn, params=(destination_airport,))

def top_5_carriers(conn, destination_airport: str):
    """
    Finds the top 5 airlines for planes flying to a given airport code.
    """
    query = """
        SELECT flights.carrier, COUNT(*) as num_flights 
        FROM flights 
        WHERE flights.dest = ?
        GROUP BY flights.carrier
        ORDER BY num_flights DESC
        LIMIT 5;
    """
    return read_sql_query(query, conn, params=(destination_airport,))


def get_all_origin_airports(conn):
    """
    Fetches all unique origin airports from the flights database.

    Parameters:
    conn (sqlite3.Connection): Active database connection.

    Returns:
    list: A sorted list of unique origin airport codes.
    """
    query = "SELECT DISTINCT origin FROM flights;"
    cursor = conn.cursor()
    cursor.execute(query)
    airports = [row[0] for row in cursor.fetchall()]
    return sorted(airports)  # Sorted for better usability

def get_available_dates(conn):
    """
    Fetches all unique flight dates from the database.

    Parameters:
    conn (sqlite3.Connection): Active database connection.

    Returns:
    list: A sorted list of available dates.
    """
    query = "SELECT DISTINCT month, day FROM flights;"
    cursor = conn.cursor()
    cursor.execute(query)
    dates = [datetime.date(2022, row[0], row[1]) for row in cursor.fetchall()]  # Assume year 2022
    return sorted(dates)

def get_distance_vs_arr_delay(conn):
    """
    Retrieves flight distance and arrival delay from the DB, returning them in a DataFrame.
    """
    query = """
        SELECT distance, arr_delay
        FROM flights
        WHERE arr_delay IS NOT NULL;
    """
    return read_sql_query(query, conn)

def fetch_airport_coordinates_df(conn):
    """Fetches airport coordinates as a Pandas DataFrame."""
    query = "SELECT faa, lat, lon FROM airports;"
    return pd.read_sql_query(query, conn)

def compute_flight_direction_vectorized(origin_lat, origin_lon, dest_lat, dest_lon):
    """
    Computes the flight direction (bearing) using vectorized NumPy operations.

    Parameters:
    origin_lat, origin_lon, dest_lat, dest_lon (Series): Latitude & Longitude values.

    Returns:
    Series: Bearing in degrees.
    """
    lat1, lon1, lat2, lon2 = map(np.radians, [origin_lat, origin_lon, dest_lat, dest_lon])
    delta_lon = lon2 - lon1

    x = np.sin(delta_lon) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(delta_lon)

    initial_bearing = np.arctan2(x, y)
    return (np.degrees(initial_bearing) + 360) % 360  # Normalize to [0, 360]

def compute_inner_product(flight_direction, wind_direction, wind_speed):
    """
    Computes the inner product between a flight direction and a wind vector 
    based on wind speed and wind direction.
    """
    angle_diff = np.radians(flight_direction - wind_direction)
    return wind_speed * np.cos(angle_diff)

def get_airports_locations(conn, airport_list=None):
    """
    Fetches airport locations from the 'airports' table.
    Optionally filters by a provided list of airport codes.
    """
    query = "SELECT faa, lat, lon FROM airports"
    cursor = conn.cursor()
    if airport_list:
        placeholders = ",".join(["?"] * len(airport_list))
        query += f" WHERE faa IN ({placeholders})"
        cursor.execute(query, airport_list)
    else:
        cursor.execute(query)
    return cursor.fetchall()




def create_flight_direction_mapping_table(conn):
    """
    Creates a new table 'flight_direction_map' in the database that stores each unique
    origin-destination pair and its computed flight direction (bearing).
    """
    # Step 1: Retrieve distinct origin-dest pairs
    unique_pairs_df = pd.read_sql_query("SELECT DISTINCT origin, dest FROM flights;", conn)
    
    # Step 2: Fetch airport coordinates
    airport_df = fetch_airport_coordinates_df(conn)
    
    # Merge to add origin coordinates
    unique_pairs_df = unique_pairs_df.merge(
        airport_df, left_on="origin", right_on="faa", how="left"
    ).rename(columns={"lat": "origin_lat", "lon": "origin_lon"}).drop(columns=["faa"])
    
    # Merge to add destination coordinates
    unique_pairs_df = unique_pairs_df.merge(
        airport_df, left_on="dest", right_on="faa", how="left"
    ).rename(columns={"lat": "dest_lat", "lon": "dest_lon"}).drop(columns=["faa"])
    
    # Step 3: Compute flight direction (bearing) using vectorized NumPy operations
    unique_pairs_df["direction"] = compute_flight_direction_vectorized(
        unique_pairs_df["origin_lat"], unique_pairs_df["origin_lon"],
        unique_pairs_df["dest_lat"], unique_pairs_df["dest_lon"]
    )
    
    # Keep only necessary columns: origin, dest, and direction
    mapping_df = unique_pairs_df[["origin", "dest", "direction"]]
    
    # Step 4: Create (or replace) the flight_direction_map table in the database.
    mapping_df.to_sql("flight_direction_map", conn, if_exists="replace", index=False)


def compute_wind_impact(flight_direction, wind_direction, wind_speed):
    """
    Computes the impact of wind on the flight by considering both wind direction and wind speed.

    Parameters:
    flight_direction (float): Flight direction in degrees.
    wind_direction (float): Wind direction in degrees.
    wind_speed (float): Wind speed in knots.

    Returns:
    float: Adjusted wind impact value.
    """
    if pd.isna(flight_direction) or pd.isna(wind_direction) or pd.isna(wind_speed):
        return None  # Handle missing values

    angle_difference = np.radians(flight_direction - wind_direction)
    return np.cos(angle_difference) * wind_speed  # Multiply by wind speed

def add_wind_and_inner_product(df):
    """
    Adds wind direction and inner product columns to the flight DataFrame.

    Parameters:
    df (pandas.DataFrame): DataFrame containing flights with flight direction.

    Returns:
    pandas.DataFrame: Updated DataFrame with wind direction and inner product.
    """
    df["inner_product"] = df.apply(
        lambda row: compute_wind_impact(row["direction"], row["wind_dir"]), axis=1
    )
    return df

def get_ny_origin_airports(conn):
    """
    Identifies all different airports in NYC and saves a dataframe.

    Parameters:
    df (pandas.DataFrame): DataFrame containing flights with flight direction.

    Returns:
    pandas.DataFrame: Updated DataFrame with information about distinct NYC airports.
    """
    cursor = conn.cursor()

    query = """
        SELECT DISTINCT airports.* 
        FROM airports 
        JOIN flights ON airports.faa = flights.origin 
        WHERE airports.tzone = 'America/New_York';
    """
    cursor.execute(query)

    rows = cursor.fetchall()
    df_origins = pd.DataFrame(rows, columns=[x[0] for x in cursor.description])

    return df_origins

def amount_of_delayed_flights(conn, start_month, end_month, destination):
    """
    Calculates the amount of delayed flights to the chosen destination.

    Parameters: 
    df (pandas.DataFrame): DataFrame containing flights with flight direction.
    start_month: beginning of the range months.
    end_month: ending of the range months.
    destination: the destination.

    Returns:
    pandas.DataFrame: Updated DataFrame with the amount of delayed flights.

    """
    cursor = conn.cursor()

    min_delay = 0

    query = f"SELECT COUNT(*) FROM flights WHERE month BETWEEN ? AND ? AND dest = ? AND dep_delay > ?;"
    cursor.execute(query, (start_month, end_month, destination, min_delay))

    amount_of_delayed_flights = cursor.fetchone()[0]

    return amount_of_delayed_flights



def create_col_with_speed(conn):
    c = conn.cursor()
    
    # Controlla se la colonna "speed" esiste
    cols = [x[1] for x in c.execute("PRAGMA table_info(planes)")]
    if "speed" not in cols:
        c.execute("ALTER TABLE planes ADD COLUMN speed REAL")

    # Aggiorna la velocità solo per gli aerei con voli validi
    c.execute("""
        UPDATE planes
        SET speed = (
            SELECT AVG(distance / (air_time / 60.0))
            FROM flights
            WHERE flights.tailnum = planes.tailnum
              AND air_time > 0
              AND distance > 0
        )
    """)
    
    conn.commit()
    
    
def create_col_local_arrival_time(conn, recalculate=False):
    """
    Updates the 'local_arrival_time' column in the flights table, 
    converting arrival time to the destination airport's local time.

    Parameters:
    recalculate (bool): If True, recalculates all local arrival times. 
                        If False, only calculates where 'local_arrival_time' is NULL.
    """
    c = conn.cursor()
    
    # Check if the column already exists
    cols = [x[1] for x in c.execute("PRAGMA table_info(flights)")]
    if "local_arrival_time" not in cols:
        c.execute("ALTER TABLE flights ADD COLUMN local_arrival_time TEXT")

    # Determine the condition for updating local arrival time
    condition = "WHERE arr_time IS NOT NULL"
    if not recalculate:
        condition += " AND (local_arrival_time IS NULL OR local_arrival_time = '')"

    # Update local arrival time based on origin and destination timezones
    c.execute(f"""
        UPDATE flights
        SET local_arrival_time = (
            SELECT strftime(
                '%Y-%m-%d %H:%M', 
                datetime(flights.arr_time, 
                    CASE 
                        WHEN CAST(a_dest.tz AS INTEGER) != CAST(a_origin.tz AS INTEGER) 
                        THEN (CAST(a_dest.tz AS INTEGER) - CAST(a_origin.tz AS INTEGER)) || ' hours' 
                        ELSE '0 hours'  -- Se il fuso è lo stesso, non modificare l'ora
                    END
                )
            )
            FROM airports a_origin
            JOIN airports a_dest ON flights.dest = a_dest.faa
            WHERE flights.origin = a_origin.faa
            AND flights.rowid = flights.rowid
        )
        {condition};
    """)

    conn.commit()
    print("Updated 'local_arrival_time' column in flights table.")



