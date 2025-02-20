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

def get_flight_statistics(conn, month: int, day: int, airport: str) -> dict:
    """
    Returns flight statistics for a given airport on a specific day.
    
    Parameters:
        conn (sqlite3.Connection): SQLite database connection.
        month (int): Month of the flight (1-12).
        day (int): Day of the flight (1-31).
        airport (str): The Origin airport FAA code (e.g., 'JFK', 'LGA', 'EWR').
    
    Returns:
        dict:   total_flights,
                unique_destinations,
                most_visited_destination,
                most_visited_count

    """
    cursor = conn.cursor()
    
    # Total number of flights
    cursor.execute(
        "SELECT COUNT(*) FROM flights WHERE month = ? AND day = ? AND origin = ?;",
        (month, day, airport),
    )
    total_flights = cursor.fetchone()[0]

    # Number of unique destinations
    cursor.execute(
        "SELECT COUNT(DISTINCT dest) FROM flights WHERE month = ? AND day = ? AND origin = ?;",
        (month, day, airport),
    )
    unique_destinations = cursor.fetchone()[0]

    # Most visited destination
    cursor.execute(
        """
        SELECT dest, COUNT(*) as flight_count 
        FROM flights 
        WHERE month = ? AND day = ? AND origin = ?
        GROUP BY dest 
        ORDER BY flight_count DESC 
        LIMIT 1;
        """,
        (month, day, airport),
    )
    most_visited = cursor.fetchone()
    most_visited_dest = most_visited[0] if most_visited else "None"
    most_visited_count = most_visited[1] if most_visited else 0

    return {
        "total_flights": total_flights,
        "unique_destinations": unique_destinations,
        "most_visited_destination": most_visited_dest,
        "most_visited_count": most_visited_count,
    }

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