import numpy as np

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

def compute_flight_direction(lat1, lon1, lat2, lon2):
    """
    Computes the flight bearing (direction) from an origin to a destination.
    Converts NumPy float64 values to standard Python float.

    Parameters:
    lat1, lon1: float - Latitude and longitude of the departure airport.
    lat2, lon2: float - Latitude and longitude of the destination airport.

    Returns:
    float - Bearing in degrees (0° = North, 90° = East, etc.), as a standard Python float.
    """
    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

    delta_lon = lon2 - lon1

    x = np.sin(delta_lon) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - (np.sin(lat1) * np.cos(lat2) * np.cos(delta_lon))

    initial_bearing = np.arctan2(x, y)

    # Convert from radians to degrees and normalize, then ensure it's a standard Python float
    bearing = float((np.degrees(initial_bearing) + 360) % 360)  # Convert np.float64 to float
    return bearing

def compute_inner_product(flight_direction, wind_direction, wind_speed):
    """
    Computes the inner product between the flight direction and wind vector.

    Parameters:
    flight_direction (float): Direction of the flight (in degrees).
    wind_direction (float): Direction of the wind (in degrees).
    wind_speed (float): Wind speed (scalar).

    Returns:
    float: The inner product (positive if wind helps the flight, negative if it opposes).
    """
    angle_difference = np.radians(flight_direction - wind_direction)
    inner_product = wind_speed * np.cos(angle_difference)
    return inner_product

def compute_flight_directions(airport_from, destinations):
    """
    Computes flight directions from a single origin airport to multiple destinations.

    Parameters:
    airport_from (tuple): A tuple containing:
        - origin_name (str): Name or IATA code of the origin airport.
        - origin_lat (float): Latitude of the origin airport.
        - origin_lon (float): Longitude of the origin airport.

    destinations (list of tuples): A list where each tuple contains:
        - dest_name (str): Name or IATA code of the destination airport.
        - dest_lat (float): Latitude of the destination airport.
        - dest_lon (float): Longitude of the destination airport.

    Returns:
    dict: A dictionary structured as:
        {
            "LAX": 270.5,
            "ORD": 285.2,
            "ATL": 245.8,
            ...
        }
    """
    origin_name, lat1, lon1 = airport_from  # Unpack single origin airport
    flight_directions = {}

    for dest_name, dest_lat, dest_lon in destinations:
        direction = compute_flight_direction(lat1, lon1, dest_lat, dest_lon)
        flight_directions[dest_name] = direction  # Store in dictionary

    return flight_directions

def get_airports_locations(conn, airport_list=None):
    """
    Fetches airport locations from an SQLite database.

    Parameters:
    conn (sqlite3.Connection): SQLite database connection.
    airport_list (list of str, optional): List of airport IATA codes to fetch.
                                           If None, fetches all airports.

    Returns:
    list of tuples: Each tuple contains (airport_name, latitude, longitude).
    """
    # Base query
    query = """
        SELECT faa, lat, lon
        FROM airports
    """

    # If a specific list of airports is given, add WHERE clause
    if airport_list:
        placeholders = ",".join(["?"] * len(airport_list))  # Create ?,?,? for parameterized query
        query += f" WHERE faa IN ({placeholders})"

    # Execute query and fetch results
    cursor = conn.cursor()
    if airport_list:
        cursor.execute(query, airport_list)  # Pass airport list as parameters
    else:
        cursor.execute(query)  # Fetch all airports

    results = cursor.fetchall()  # Get results as list of tuples
    return results