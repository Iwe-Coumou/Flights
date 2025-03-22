import numpy as np
import pandas as pd
from db_queries import fetch_airport_coordinates_df

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


def create_flight_direction_mapping_table(conn):
    """
    Creates a new table 'flight_direction_map' in the database that stores each unique
    origin-destination pair and its computed flight direction (bearing).
    """
    # Retrieve distinct origin-dest pairs
    unique_pairs_df = pd.read_sql_query("SELECT DISTINCT origin, dest FROM flights;", conn)
    
    # Fetch airport coordinates
    airport_df = fetch_airport_coordinates_df(conn)
    
    # Merge to add origin coordinates
    unique_pairs_df = unique_pairs_df.merge(
        airport_df, left_on="origin", right_on="faa", how="left"
    ).rename(columns={"lat": "origin_lat", "lon": "origin_lon"}).drop(columns=["faa"])
    
    # Merge to add destination coordinates
    unique_pairs_df = unique_pairs_df.merge(
        airport_df, left_on="dest", right_on="faa", how="left"
    ).rename(columns={"lat": "dest_lat", "lon": "dest_lon"}).drop(columns=["faa"])
    
    # Compute flight direction (bearing) using vectorized NumPy operations
    unique_pairs_df["direction"] = compute_flight_direction_vectorized(
        unique_pairs_df["origin_lat"], unique_pairs_df["origin_lon"],
        unique_pairs_df["dest_lat"], unique_pairs_df["dest_lon"]
    )
    
    # Keep only necessary columns: origin, dest, and direction
    mapping_df = unique_pairs_df[["origin", "dest", "direction"]]
    
    # Create (or replace) the flight_direction_map table in the database.
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
