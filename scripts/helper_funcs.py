import numpy as np
import pandas as pd

from pandas import read_sql_query

def get_flight_destinations_from_airport_on_day(conn, month: int, day: int, airport: str) -> set:
    """
    Retrieves all unique flight destinations leaving from a given NYC airport on a specified month and day.
    
    Parameters:
        conn (sqlite3.Connection): SQLite database connection.
        month (int): Month of the flight (1-12).
        day (int): Day of the flight (1-31).
        airport (str): The Origin airport FAA code (e.g., 'JFK', 'LGA', 'EWR').
    
    Returns:
        set: A set of unique destination FAA codes.
    """
    cursor = conn.cursor()
    query = """
        SELECT DISTINCT dest FROM flights 
        WHERE month = ? AND day = ? AND origin = ?;
    """
    cursor.execute(query, (month, day, airport))
    return {row[0] for row in cursor.fetchall()}

def top_5_manufacturers(conn, destination_airport: str) -> list:
    """
    Returns the top 5 airplane manufacturers for planes flying to the given destination airport.

    Parameters:
    conn (sqlite3.Connection or other DB connection): Database connection object.
    destination (str): The IATA airport code of the destination.

    Returns:
    pandas.DataFrame: A DataFrame with 'manufacturer' and 'num_flights' columns.
    """
    query = """
        SELECT planes.manufacturer, COUNT(*) as num_flights FROM flights 
        JOIN planes ON flights.tailnum = planes.tailnum
        WHERE flights.dest = ?
        GROUP BY planes.manufacturer
        ORDER BY num_flights DESC
        LIMIT 5;
    """

    return read_sql_query(query, conn, params=(destination_airport,))

def get_distance_vs_arr_delay(conn):
    """
    Retrieves flight distance and arrival delay data.

    Parameters:
    conn (sqlite3.Connection or other DB connection): Database connection object.

    Returns:
    pandas.DataFrame: DataFrame with 'distance' and 'arr_delay' columns.
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

def create_flight_dataframe(conn):
    """
    Fetches flight data, merges with airport coordinates, computes flight direction, 
    and automatically adds the wind impact column.
    """
    
    query = """
        SELECT f.flight, f.origin, f.dest, f.time_hour, f.air_time, 
               w.wind_dir, w.wind_speed
        FROM flights f
        LEFT JOIN weather w 
        ON f.origin = w.origin AND f.time_hour = w.time_hour;
    """
    df = pd.read_sql_query(query, conn)

    # Fetch airport coordinates
    airport_df = fetch_airport_coordinates_df(conn)

    # Compute flight direction
    unique_pairs = df[['origin', 'dest']].drop_duplicates()
    unique_pairs = unique_pairs.merge(airport_df, left_on="origin", right_on="faa", how="left")\
                               .rename(columns={"lat": "origin_lat", "lon": "origin_lon"})\
                               .drop(columns=["faa"])
    unique_pairs = unique_pairs.merge(airport_df, left_on="dest", right_on="faa", how="left")\
                               .rename(columns={"lat": "dest_lat", "lon": "dest_lon"})\
                               .drop(columns=["faa"])
    
    unique_pairs["direction"] = compute_flight_direction_vectorized(
        unique_pairs["origin_lat"], unique_pairs["origin_lon"], 
        unique_pairs["dest_lat"], unique_pairs["dest_lon"]
    )

    df = df.merge(unique_pairs[['origin', 'dest', 'direction']], on=['origin', 'dest'], how='left')

    # **Compute Wind Impact Automatically**
    df["wind_impact"] = df.apply(
        lambda row: compute_wind_impact(row["direction"], row["wind_dir"], row["wind_speed"]),
        axis=1
    )

    return df

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