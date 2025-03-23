"""
this file contains functions to get data on the number of flight,
number of delayed flights and avg departure delay into the dashboard
"""

def number_flights_origin(conn, origin: str, month: int = None, day: int = None):
    """
    Calculates the number of flights for a specified airport origin,
    optionally filtering by month and day if provided.

    Parameters:
        conn (sqlite3.Connection): Active database connection.
        origin (str): The airport origin (required).
        month (int, optional): Month to filter (1-12). Defaults to None.
        day (int, optional): Day to filter (1-31). Defaults to None.

    Returns:
        int: The number of flights matching the specified filters.
    """
    base_query = "SELECT COUNT(*) FROM flights WHERE origin = ?"
    params = [origin]

    if month is not None:
        base_query += " AND month = ?"
        params.append(month)

    if day is not None:
        base_query += " AND day = ?"
        params.append(day)

    cursor = conn.cursor()
    cursor.execute(base_query, params)
    result = cursor.fetchone()

    # Return the count if present, or None if no result is found
    return result[0] if result else None

def average_flights_for_origin(conn, origin: str) -> float:
    """
    Calculates the average (daily) number of flights from a specific origin airport
    across all days in the dataset (potentially multiple years).

    How it works:
      1) Groups flights by (year, month, day) to count flights for each calendar day.
      2) Averages those daily counts.

    Parameters:
        conn (sqlite3.Connection): Active database connection.
        origin (str): The origin airport code (e.g. "JFK").

    Returns:
        float: The average number of flights (per day) from the specified origin
               across all available days. Returns None if no flights match.
    """
    query = """
    SELECT AVG(daily_count) AS avg_flights
    FROM (
        SELECT year, month, day, COUNT(*) AS daily_count
        FROM flights
        WHERE origin = ?
        GROUP BY year, month, day
    ) sub
    """
    cursor = conn.cursor()
    cursor.execute(query, (origin,))
    row = cursor.fetchone()

    return row[0] if row and row[0] is not None else None

def avg_dep_delay_day(conn, month: int = None, day: int = None):
    """
    Calculates the average departure delay.
    
    If month and day are provided, it returns the average departure delay
    for that specific day. Otherwise, it returns the average departure delay
    for all flights.
    
    Parameters:
        conn (sqlite3.Connection): Database connection.
        month (int, optional): The specified month (1-12). Defaults to None.
        day (int, optional): The specified day (1-31). Defaults to None.
    
    Returns:
        float: The average departure delay (in minutes) for the specified filters,
               or overall if no filters are provided.
    """
    cursor = conn.cursor()
    
    if month is not None and day is not None:
        query = "SELECT AVG(dep_delay) FROM flights WHERE month = ? AND day = ?;"
        params = (month, day)
    else:
        query = "SELECT AVG(dep_delay) FROM flights;"
        params = ()
    
    cursor.execute(query, params)
    avg_dep_delay = cursor.fetchone()[0]
    
    return avg_dep_delay

def amount_of_delayed_flights(conn, origin: str, month: int = None, day: int = None):
    """
    Calculates the amount of delayed flights (with dep_delay > 0) for the chosen origin airport,
    optionally filtering by month and day if provided.

    Parameters:
        conn (sqlite3.Connection): Database connection.
        origin (str): The origin airport code.
        month (int, optional): The chosen month (1-12). Defaults to None.
        day (int, optional): The chosen day (1-31). Defaults to None.

    Returns:
        int: The number of delayed flights matching the specified filters.
    """
    cursor = conn.cursor()
    min_delay = 0

    # Build the query dynamically based on provided filters.
    if month is not None:
        if day is not None:
            query = """SELECT COUNT(*) FROM flights WHERE origin = ? AND month = ? AND day = ? AND dep_delay > ?;"""
            params = (origin, month, day, min_delay)
        else:
            query = """SELECT COUNT(*) FROM flights WHERE origin = ? AND month = ? AND dep_delay > ?;"""
            params = (origin, month, min_delay)
    else:
        query = """SELECT COUNT(*) FROM flights WHERE origin = ? AND dep_delay > ?;"""
        params = (origin, min_delay)
    
    cursor.execute(query, params)
    count = cursor.fetchone()[0]
    return count

def avg_delayed_flights_per_day(conn, origin: str) -> float:
    """
    Calculates the average number of delayed flights (dep_delay > 0) per day 
    for a specified origin airport, across all days in the dataset.

    Parameters:
        conn (sqlite3.Connection): Database connection.
        origin (str): The origin airport code (e.g. "JFK").

    Returns:
        float: The average number of delayed flights per day from the given origin.
               Returns None if no data is found.
    """
    query = """
    SELECT AVG(daily_count) AS avg_delayed
    FROM (
        SELECT COUNT(*) AS daily_count
        FROM flights
        WHERE origin = ? AND dep_delay > 0
        GROUP BY year, month, day
    ) sub;
    """
    cursor = conn.cursor()
    cursor.execute(query, (origin,))
    row = cursor.fetchone()
    return row[0] if row and row[0] is not None else None

def get_flight_data(conn, origin: str, month_and_day: tuple):
    """
    Retrieves flight statistics for a specified origin airport.
    
    If a (month, day) tuple is provided, it returns statistics for that specific day;
    otherwise, it returns overall statistics across all days.
    
    Parameters:
        conn (sqlite3.Connection): Active database connection.
        origin (str): The origin airport code.
        month_and_day (tuple or None): A tuple (month, day) to filter the flights,
                                       or None for overall statistics.
    
    Returns:
        tuple: A tuple containing:
            - total_flights (int): Total number of flights from the origin.
            - flights_on_day (int or None): Number of flights on the specified day (if applicable).
            - average_flights_per_day (float or None): Average daily flights from the origin.
    """

    total_flights = number_flights_origin(conn, origin)
    total_flights_on_day = number_flights_origin(conn, origin, month_and_day[0], month_and_day[1]) if month_and_day != None else None
    avg_flights_per_day = average_flights_for_origin(conn, origin)

    return (total_flights, total_flights_on_day, avg_flights_per_day)

def get_dep_delay_data(conn, origin: str, month_and_day: tuple):
    """
    Retrieves departure delay statistics for a specified origin airport.
    
    If a (month, day) tuple is provided, it returns statistics for that specific day;
    otherwise, it returns overall statistics across all days.
    
    Parameters:
        conn (sqlite3.Connection): Active database connection.
        origin (str): The origin airport code.
        month_and_day (tuple or None): A tuple (month, day) to filter the flights,
                                       or None for overall statistics.
    
    Returns:
        tuple: A tuple containing:
            - overall_avg_dep_delay (float): The overall average departure delay from the origin.
            - avg_dep_delay_on_day (float or None): The average departure delay on the specified day (if applicable).
    """

    total_avg_dep_delay = avg_dep_delay_day(conn)
    avg_dep_delay_on_day = avg_dep_delay_day(conn, month_and_day[0], month_and_day[1]) if month_and_day != None else None

    return (total_avg_dep_delay, avg_dep_delay_on_day)

def get_delayed_data(conn, origin: str, month_and_day: tuple):
    """
    Retrieves delayed flight statistics for a specified origin airport.
    
    If a (month, day) tuple is provided, it returns statistics for that specific day;
    otherwise, it returns overall statistics across all days.
    
    Parameters:
        conn (sqlite3.Connection): Active database connection.
        origin (str): The origin airport code.
        month_and_day (tuple or None): A tuple (month, day) to filter the flights,
                                       or None for overall statistics.
    
    Returns:
        tuple: A tuple containing:
            - total_delayed (int): Total number of delayed flights from the origin.
            - delayed_on_day (int or None): Number of delayed flights on the specified day (if applicable).
            - average_delayed_per_day (float or None): Average delayed flights per day from the origin.
    """

    total_delayed = amount_of_delayed_flights(conn, origin)
    total_delayed_on_day = amount_of_delayed_flights(conn, origin, month_and_day[0], month_and_day[1]) if month_and_day != None else None
    avg_delayed_per_day = avg_delayed_flights_per_day(conn, origin)

    return (total_delayed, total_delayed_on_day, avg_delayed_per_day)

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

def get_average_flight_stats_for_route(conn, origin: str, destination: str) -> dict:
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

def most_popular_destination(conn, origin: str, month: int = None, day: int = None) -> tuple:
    """
    Retrieves the most popular destination for flights departing from the specified origin,
    along with the airport's FAA code and number of flights.

    The function counts the number of flights to each destination from the given origin,
    optionally filtering by month and day. It joins the flights table with the airports table 
    (which is assumed to have columns "faa" and "name") so it can return the airport name.

    It then returns a tuple containing:
        - The FAA code of the destination airport
        - The name of the destination airport
        - The number of flights going to that destination
    
    Parameters:
        conn (sqlite3.Connection): Active database connection.
        origin (str): The origin airport code.
        month (int, optional): Month to filter (1-12). Defaults to None.
        day (int, optional): Day to filter (1-31). Defaults to None.
    
    Returns:
        tuple: (faa_code, airport_name, flight_count) 
               or (None, None, 0) if no flights match the criteria.
    """
    query = """
        SELECT a.faa, a.name, COUNT(*) AS flight_count
        FROM flights f
        JOIN airports a ON f.dest = a.faa
        WHERE f.origin = ?
    """
    params = [origin]

    if month is not None:
        query += " AND f.month = ?"
        params.append(month)

    if day is not None:
        query += " AND f.day = ?"
        params.append(day)

    query += " GROUP BY a.faa, a.name ORDER BY flight_count DESC LIMIT 1"

    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()

    if result:
        faa_code, airport_name, flight_count = result
        return faa_code, airport_name, flight_count
    else:
        return None, None, 0
    
def most_popular_carrier(conn, origin: str, month: int = None, day: int = None) -> tuple:
    """
    Retrieves the carrier with the most flights from a specified origin,
    optionally filtered by month and day. Joins the flights table with
    the airlines table to return both the carrier code and the airline name.

    Parameters:
        conn (sqlite3.Connection): Active database connection.
        origin (str): The origin airport code (e.g. "JFK").
        month (int, optional): Month to filter (1-12). Defaults to None.
        day (int, optional): Day to filter (1-31). Defaults to None.

    Returns:
        tuple: (carrier_code, airline_name, flight_count)
               e.g. ("AA", "American Airlines", 12345)
               If no flights match, returns (None, None, 0).
    """
    query = """
        SELECT a.carrier, a.name, COUNT(*) AS flight_count
        FROM flights f
        JOIN airlines a ON f.carrier = a.carrier
        WHERE f.origin = ?
    """
    params = [origin]

    if month is not None:
        query += " AND f.month = ?"
        params.append(month)

    if day is not None:
        query += " AND f.day = ?"
        params.append(day)

    query += " GROUP BY a.carrier, a.name ORDER BY flight_count DESC LIMIT 1"

    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()

    if result:
        carrier_code, airline_name, flight_count = result
        return carrier_code, airline_name, flight_count
    else:
        return None, None, 0
