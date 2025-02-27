
"""
Module containing functions to calculate Euclidean and Geodesic distances 
between airports, based on latitude/longitude data.
"""

import numpy as np
import pandas as pd

R = 6371  # Earth radius in kilometers

def file_opener(path: str) -> pd.DataFrame:
    """
    Opens a CSV file and returns a pandas DataFrame.

    Parameters:
    - path (str): The file path to the CSV.

    Returns:
    - pd.DataFrame: The loaded DataFrame.
    """
    return pd.read_csv(path)

def euclidean_distance_calculator(target_code: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the Euclidean distance (in 3D, approximate) between a target airport 
    and all other airports in the DataFrame.

    Parameters:
    - target_code (str): The FAA code of the target airport (e.g., 'JFK').
    - df (pd.DataFrame): Must contain 'faa', 'lat', 'lon' columns.

    Returns:
    - pd.DataFrame: Columns = ['faa', 'euclidean_distance'], sorted by distance ascending.
    """
    # Select the target airport
    target = df[df["faa"] == target_code].iloc[0]
    # Filter out the target from the main DataFrame
    df = df[df["faa"] != target_code].copy()

    # Convert lat/lon to radians
    target_lat, target_lon = np.radians(target["lat"]), np.radians(target["lon"])
    df["lat_rad"], df["lon_rad"] = np.radians(df["lat"]), np.radians(df["lon"])

    # Convert to 3D cartesian coordinates
    target_x = R * np.cos(target_lat) * np.cos(target_lon)
    target_y = R * np.cos(target_lat) * np.sin(target_lon)

    df["x"] = R * np.cos(df["lat_rad"]) * np.cos(df["lon_rad"])
    df["y"] = R * np.cos(df["lat_rad"]) * np.sin(df["lon_rad"])

    # Calculate Euclidean distance
    df["euclidean_distance"] = np.sqrt(
        (df["x"] - target_x) ** 2 + (df["y"] - target_y) ** 2
    )

    return df[["faa", "euclidean_distance"]].sort_values(by="euclidean_distance")

def geodesic_distance_calculator(target_code: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the geodesic distance (on Earth's surface) between a target airport
    and all other airports in the DataFrame, using a spherical approximation.

    Parameters:
    - target_code (str): The FAA code of the target airport (e.g., 'JFK').
    - df (pd.DataFrame): Must contain 'faa', 'lat', 'lon' columns.

    Returns:
    - pd.DataFrame: Columns = ['faa', 'geodesic_distance'], sorted by distance ascending.
    """
    # Select the target airport
    target = df[df["faa"] == target_code].iloc[0]
    # Filter out the target
    df = df[df["faa"] != target_code].copy()

    # Convert lat/lon to radians
    target_lat, target_lon = np.radians(target["lat"]), np.radians(target["lon"])
    df["lat_rad"], df["lon_rad"] = np.radians(df["lat"]), np.radians(df["lon"])

    # Perform spherical distance calculation
    dphi = df["lat_rad"] - target_lat
    dlambda = df["lon_rad"] - target_lon
    phi_m = (df["lat_rad"] + target_lat) / 2

    df["geodesic_distance"] = R * np.sqrt(
        (2 * np.sin(dphi / 2) * np.cos(dlambda / 2)) ** 2 +
        (2 * np.cos(phi_m) * np.sin(dlambda / 2)) ** 2
    )

    return df[["faa", "geodesic_distance"]].sort_values(by="geodesic_distance")
