# helper_funcs.py
import sqlite3
import numpy as np
import pandas as pd
import datetime
import plotly.graph_objects as go
from pandas import read_sql_query

"""
Module with additional utility functions for querying the DB 
and computing certain values (arrival delays, directions, etc.).
"""

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

def get_aircraft_info(conn, tailnum):
    """
    Retrieves the manufacturer and model of an aircraft given its tail number (tailnum).
    
    Parameters:
    conn (sqlite3.Connection): Database connection.
    tailnum (str): Tail number of the aircraft.

    Returns:
    dict: Dictionary with 'manufacturer' and 'model' or None if not found.
    """
    query = """
        SELECT manufacturer, model 
        FROM planes 
        WHERE tailnum = ?;
    """
    cursor = conn.cursor()
    cursor.execute(query, (tailnum,))
    result = cursor.fetchone()

    if result:
        return {"manufacturer": result[0], "model": result[1]}
    return None

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

def top_5_carriers_from_specified_airport(conn, destination_airport: str):
    """
    Finds the top 5 airlines for planes flying to a given airport code.
    """
    query = """
        SELECT flights.carrier, COUNT(*) as num_flights 
        FROM flights 
        WHERE flights.origin = ?
        GROUP BY flights.carrier
        ORDER BY num_flights DESC
        LIMIT 5;
    """
    return read_sql_query(query, conn, params=(destination_airport,))


def get_available_destination_airports(conn, origin_airport):
    """
    Fetches all unique destination airports for a given origin airport.

    Parameters:
    conn (sqlite3.Connection): Active database connection.
    origin_airport (str): Selected departure airport.

    Returns:
    list: Sorted list of unique destination airports.
    """
    query = "SELECT DISTINCT dest FROM flights WHERE origin = ?;"
    cursor = conn.cursor()
    cursor.execute(query, (origin_airport,))
    airports = [row[0] for row in cursor.fetchall()]
    return sorted(airports)

def get_available_dates(conn, origin, destination=None):
    """
    Fetches all unique flight dates from the database.
    If an origin is specified, it filters the dates for that airport.
    If both origin and destination are specified, it filters dates for that specific route.

    Parameters:
    conn (sqlite3.Connection): Active database connection.
    origin (str): Origin airport code.
    destination (str, optional): Destination airport code (default is None).

    Returns:
    list: A sorted list of available dates.
    """
    query = """
        SELECT DISTINCT substr(sched_dep_time, 1, 10) AS flight_date
        FROM flights
        WHERE origin = ?
    """
    params = [origin]

    if destination:
        query += " AND dest = ?"
        params.append(destination)

    query += " ORDER BY flight_date"

    cursor = conn.cursor()
    cursor.execute(query, params)
    dates = [row[0] for row in cursor.fetchall()]
    
    return sorted(dates)

def get_top_5_carriers_for_route(conn, origin, destination):
    
    """
    Fetches the top 5 airlines operating the most flights on a given route.

    Parameters:
    conn (sqlite3.Connection): Active database connection.
    origin (str): Origin airport code.
    destination (str): Destination airport code.

    Returns:
    pandas.DataFrame: DataFrame with carrier and number of flights.
    """
    query = """
        SELECT airlines.name, COUNT(*) as num_flights 
        FROM flights
        JOIN airlines ON flights.carrier = airlines.carrier 
        WHERE origin = ? AND dest = ?
        GROUP BY airlines.name
        ORDER BY num_flights DESC
        LIMIT 5;
    """
    return read_sql_query(query, conn, params=(origin, destination))

def get_weather_stats_for_route(conn, origin, destination):
    
    """
    Fetches average weather statistics (wind speed, temperature) for a flight route.

    Parameters:
    conn (sqlite3.Connection): Active database connection.
    origin (str): Origin airport code.
    destination (str): Destination airport code.

    Returns:
    dict: Dictionary with average temperature, wind speed, and other stats.
    """
    query = """
        SELECT AVG(wind_speed) AS avg_wind_speed, AVG(temp) AS avg_temp
        FROM weather
        WHERE origin = ? 
        AND time_hour IN (
            SELECT time_hour FROM flights WHERE origin = ? AND dest = ?
        );
    """
    cursor = conn.cursor()
    cursor.execute(query, (origin, origin, destination))
    result = cursor.fetchone()
    
    return {
        "avg_wind_speed": result[0] if result else None,
        "avg_temp": result[1] if result else None,
    }

def get_flight_counts_for_route(conn, origin, destination):
    """
    Fetches average daily flights and total flights per month for a given route.
    """
    cursor = conn.cursor()

    # Query per calcolare il numero medio di voli giornalieri
    query_daily = """
        SELECT COUNT(*) * 1.0 / (SELECT COUNT(DISTINCT month || '-' || day) 
                                 FROM flights 
                                 WHERE origin = ? AND dest = ?) 
        FROM flights 
        WHERE origin = ? AND dest = ?;
    """

    # Query per il numero di voli mensili
    query_monthly = """
        SELECT month, COUNT(*) AS num_flights
        FROM flights 
        WHERE origin = ? AND dest = ?
        GROUP BY month
        ORDER BY month;
    """

    # Esegui la query per il numero medio di voli giornalieri
    cursor.execute(query_daily, (origin, destination, origin, destination))
    avg_daily_flights = cursor.fetchone()[0] or 0  # Evita None se la query non restituisce nulla

    # Esegui la query per il numero di voli mensili
    df_monthly_flights = read_sql_query(query_monthly, conn, params=(origin, destination))

    return avg_daily_flights, df_monthly_flights

def get_delay_stats_for_route(conn, origin, destination):
    """
    Fetches average arrival delay statistics for a given route.

    Parameters:
    conn (sqlite3.Connection): Active database connection.
    origin (str): Origin airport code.
    destination (str): Destination airport code.

    Returns:
    tuple: (df_by_month, df_by_carrier, df_by_manufacturer)
    """
    query_by_month = """
        SELECT month, AVG(arr_delay) AS avg_delay
        FROM flights 
        WHERE origin = ? AND dest = ?
        GROUP BY month
        ORDER BY month;
    """

    query_by_carrier = """
        SELECT airlines.name, AVG(arr_delay) AS avg_delay
        FROM flights 
        JOIN airlines ON flights.carrier = airlines.carrier
        WHERE origin = ? AND dest = ?
        GROUP BY airlines.name
        ORDER BY avg_delay DESC;
    """

    query_by_manufacturer = """
        SELECT planes.manufacturer, AVG(flights.arr_delay) AS avg_delay
        FROM flights 
        JOIN planes ON flights.tailnum = planes.tailnum
        WHERE flights.origin = ? AND flights.dest = ?
        GROUP BY planes.manufacturer
        ORDER BY avg_delay DESC;
    """

    df_by_month = read_sql_query(query_by_month, conn, params=(origin, destination))
    df_by_carrier = read_sql_query(query_by_carrier, conn, params=(origin, destination))
    df_by_manufacturer = read_sql_query(query_by_manufacturer, conn, params=(origin, destination))

    return df_by_month, df_by_carrier, df_by_manufacturer

def get_flights_on_date_and_route(conn, date, airport_departure, airport_arrival, only_non_cancelled=False):
    """
    Fetches all flights that occurred on a specific date and route.

    Parameters:
    conn (sqlite3.Connection): Active database connection.
    date (datetime.date or str): Date object.
    airport_departure (str): Departure airport code.
    airport_arrival (str): Arrival airport code.
    only_non_cancelled (bool): If True, filters out cancelled flights.

    Returns:
    pandas.DataFrame: DataFrame containing the flights.
    """
    query = """
        SELECT * FROM flights
        WHERE substr(sched_dep_time, 1, 10) = ?
        AND origin = ? AND dest = ?
    """

    
    # Assicuriamoci che il valore della data sia in formato stringa "YYYY-MM-DD"
    params = [str(date), airport_departure, airport_arrival]
    print(f"Type of date: {type(date)}, Value: {date}")


    if only_non_cancelled:
        query += " AND canceled = 0"

    print(f"Executing SQL Query: {query} with params {params}")  # Debugging

    df = pd.read_sql_query(query, conn, params=params)

    print(df)  # Debugging: Controlliamo se il DataFrame ha dati

    return df

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

def get_weather_for_flight(conn, origin, destination, date):
    """
    Retrieves wind speed and direction for a given flight based on its departure time.

    Parameters:
    conn (sqlite3.Connection): Active database connection.
    origin (str): Departure airport code.
    destination (str): Arrival airport code.
    date (str): Date in 'YYYY-MM-DD'.

    Returns:
    dict: Dictionary containing wind speed and direction.
    """
    query = """
        SELECT w.wind_speed, w.wind_dir
        FROM weather w
        JOIN flights f ON w.origin = f.origin AND w.time_hour = f.time_hour
       WHERE DATE(f.sched_dep_time) = ? AND f.origin = ? AND f.dest = ?
        LIMIT 1;
    """
    cursor = conn.cursor()
    cursor.execute(query, (date, origin, destination))
    result = cursor.fetchone()

    if result:
        return {"wind_speed": result[0], "wind_dir": result[1]}
    return None

def get_average_flight_stats_for_route(conn: sqlite3.Connection, origin: str, destination: str) -> dict:
    """
    Retrieves the average flight time, average departure delay, and average arrival delay
    for flights between a given origin and destination.

    Parameters:
        conn (sqlite3.Connection): SQLite database connection
        origin (str): Origin airport code
        destination (str): Destination airport code

    Returns:
        dict: {
            "avg_flight_time": float or None,
            "avg_dep_delay": float or None,
            "avg_arr_delay": float or None
        }
        If no flights exist for the route, the dictionary values may be None.
    """
    cursor = conn.cursor()
    query = """
        SELECT 
            AVG(air_time)          AS avg_flight_time,
            AVG(dep_delay)         AS avg_dep_delay,
            AVG(arr_delay)         AS avg_arr_delay
        FROM flights
        WHERE origin = ? 
          AND dest = ?
          AND canceled = 0
    """
    cursor.execute(query, (origin, destination))
    row = cursor.fetchone()

    if row:
        return {
            "avg_flight_time": row[0],
            "avg_dep_delay": row[1],
            "avg_arr_delay": row[2]
        }
    else:
        return {
            "avg_flight_time": None,
            "avg_dep_delay": None,
            "avg_arr_delay": None
        }

def plot_wind_direction(direction, wind_speed=1):
    """
    Creates a compass visualization for wind direction.

    Parameters:
    direction (float): Wind direction in degrees.
    wind_speed (float): Wind speed (optional, to scale the arrow length).

    Returns:
    plotly.graph_objects.Figure: A polar chart representing wind direction.
    """
    # Convert direction to radians
    angle_rad = np.radians(direction)

    # Define the starting point (center)
    x_start, y_start = 0, 0  # Start from the center of the graph

    # Define the endpoint based on the direction
    x_end = np.cos(angle_rad) * wind_speed  # Projection on X
    y_end = np.sin(angle_rad) * wind_speed  # Projection on Y

    fig = go.Figure()

    # Draw the circular axis
    fig.add_trace(go.Scatterpolar(
        r=[0, wind_speed],  # Start from the center
        theta=[direction, direction],
        mode="lines",
        line=dict(color="red", width=3)
    ))

    fig.update_layout(
        title="Wind Direction",
        polar=dict(
            radialaxis=dict(visible=False, range=[0, wind_speed]),
            angularaxis=dict(direction="clockwise", tickmode="array", 
                             tickvals=[0, 90, 180, 270], ticktext=["N", "E", "S", "W"])
        ),
        showlegend=False
    )

    return fig
