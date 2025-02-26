#THIS CAN BE CHANGED TO BE MORE SPECIFIC RIGHT NOW IT WORKS FOR THE THREE AIRPORTS OF NYC AND PROBABLY THE ONLY ONES WE HAVE DEPARTURE FROM

"""
Module to compare distances retrieved from the database (in miles, converted to km)
with geodesic distances computed from a CSV file.
"""

import sqlite3
import pandas as pd
from constants import NYC_AIRPORTS, ERROR_MARGIN_KM, MILES_TO_KM
from distance_calculations import file_opener, geodesic_distance_calculator

def check_distances_for_code(
    conn: sqlite3.Connection,
    csv_df: pd.DataFrame,
    code: str,
    error_margin_km: float = ERROR_MARGIN_KM
) -> pd.DataFrame:
    """
    Compare DB distances (miles->km) with geodesic distances computed from the CSV 
    for a single airport code. Returns a DataFrame with routes that exceed the error margin.

    Parameters:
    - conn (sqlite3.Connection): Open connection to the flights DB.
    - csv_df (pd.DataFrame): DataFrame of airport lat/lon (from CSV).
    - code (str): Airport code to compare (e.g. 'JFK').
    - error_margin_km (float): Maximum distance difference allowed.

    Returns:
    - pd.DataFrame: Routes that exceed the allowed error margin.
    """
    query = f"""
        SELECT DISTINCT origin, dest, distance
        FROM flights
        WHERE dest='{code}' OR origin='{code}'
        ORDER BY distance;
    """
    df_db = pd.read_sql_query(query, conn)
    # Convert distance from miles to km
    df_db["distance"] *= MILES_TO_KM

    # Compute geodesic distances from CSV
    df_geo = geodesic_distance_calculator(code, csv_df)

    # Merge on dest airport code = df_geo.faa
    merged_df = pd.merge(
        df_db,
        df_geo,
        left_on="dest",
        right_on="faa",
        how="inner"
    )
    merged_df["difference"] = abs(merged_df["distance"] - merged_df["geodesic_distance"])

    # Filter out the routes that exceed the error margin
    incorrect_distances = merged_df[merged_df["difference"] > error_margin_km]
    return incorrect_distances

def compare_nyc_airports(
    conn: sqlite3.Connection,
    csv_path: str,
    error_margin_km: float = ERROR_MARGIN_KM
) -> dict:
    """
    Runs the comparison on all airports in NYC_AIRPORTS. Prints any routes that exceed
    the error margin, and returns a dictionary of DataFrames.

    Parameters:
    - conn (sqlite3.Connection): DB connection.
    - csv_path (str): Path to the CSV file with airport info.
    - error_margin_km (float): Threshold for distance difference.

    Returns:
    - dict: Example structure { "JFK": DataFrame, "EWR": DataFrame, "LGA": DataFrame }
    """
    csv_df = file_opener(csv_path)
    results = {}

    for code in NYC_AIRPORTS:
        df_bad = check_distances_for_code(conn, csv_df, code, error_margin_km)
        if df_bad.empty:
            print(f"All distances for {code} are within the error margin.")
        else:
            print(f"\n=== Incorrect distances for {code} ===")
            print(df_bad[["origin", "dest", "distance", "geodesic_distance", "difference"]])
        results[code] = df_bad

    return results
