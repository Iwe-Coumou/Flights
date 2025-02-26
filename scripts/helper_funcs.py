# helper_funcs.py

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

def compute_flight_direction(lat1, lon1, lat2, lon2):
    """
    Computes the bearing (direction) of a flight between two lat/lon points. 
    Returns it in degrees (0°=North, 90°=East, etc.).
    """
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    delta_lon = lon2 - lon1
    x = np.sin(delta_lon) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1)*np.cos(lat2)*np.cos(delta_lon)
    bearing = (np.degrees(np.arctan2(x, y)) + 360) % 360
    return float(bearing)

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



def create_planes_copy_with_speed(conn, recalc_speed=False):
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS planes_copy")
    c.execute("CREATE TABLE planes_copy AS SELECT * FROM planes")
    cols = [x[1] for x in c.execute("PRAGMA table_info(planes_copy)")]
    if "speed" not in cols:
        c.execute("ALTER TABLE planes_copy ADD COLUMN speed REAL")
    elif recalc_speed:
        c.execute("UPDATE planes_copy SET speed = NULL")
    c.execute("""
        UPDATE planes_copy
        SET speed = (
            SELECT AVG(distance / (air_time / 60.0))
            FROM flights
            WHERE flights.tailnum = planes_copy.tailnum
              AND air_time IS NOT NULL
              AND air_time > 0
              AND distance IS NOT NULL
              AND distance > 0
        )
        WHERE EXISTS (
            SELECT 1
            FROM flights
            WHERE flights.tailnum = planes_copy.tailnum
              AND air_time IS NOT NULL
              AND air_time > 0
              AND distance IS NOT NULL
              AND distance > 0
        );
    """)
    conn.commit()

    
def update_planes_speed(conn):
    c = conn.cursor()
    cols = [x[1] for x in c.execute("PRAGMA table_info(planes)")]
    if "speed" not in cols:
        c.execute("ALTER TABLE planes ADD COLUMN speed REAL")
    else:
        c.execute("UPDATE planes SET speed = NULL")
    c.execute("""
        UPDATE planes
        SET speed = (
            SELECT AVG(distance / (air_time / 60.0))
            FROM flights
            WHERE flights.tailnum = planes.tailnum
              AND air_time IS NOT NULL
              AND air_time > 0
        )
    """)
    conn.commit()
    
# one create a new table and modify that the other one modify the original

