"""
this file contains functions to get data on the number of flight,
number of delayed flights and avg departure delay into the dashboard
"""

def avg_departure_delay_month(conn, month: int, day: int, origin:None):
    """
    Calculates the average departure delay for all flights in the specified months.

    Parameters: 
    conn (sqlite3.Connection): Database connection.
    start_month: beginning of the range months.
    end_month: ending of the range months.
    origin (str, optional): The airport for which to calculate the average delay. If none, calculates for all airports.

    Returns:
    float: The average departure delay for the flights at the chosen month and day for (optional) chosen origin.
    """
    cursor = conn.cursor()

    if origin:
        query = """SELECT AVG(dep_delay) FROM flights WHERE origin = ? AND month = ? AND day = ?;"""  
        cursor.execute(query, (month, day, origin))
    else:
        query = """SELECT AVG(dep_delay) FROM flights WHERE month = ? AND day = ?;""" 
        cursor.execute(query, (month, day))
    
    avg_delay = cursor.fetchone()[0]

    return round(avg_delay, 3) if avg_delay is not None else None

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

def amount_of_delayed_flights_origin(conn, origin: str, month: int = None, day: int = None):
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

    total_flights = number_flights_origin(conn, origin)
    total_flights_on_day = number_flights_origin(conn, origin, month_and_day[0], month_and_day[1]) if month_and_day != None else None
    avg_flights_per_day = average_flights_for_origin(conn, origin)

    return (total_flights, total_flights_on_day, avg_flights_per_day)

def get_dep_delay_data(conn, origin: str, month_and_day: tuple):
    total_avg_dep_delay = avg_dep_delay_day(conn)
    avg_dep_delay_on_day = avg_dep_delay_day(conn, month_and_day[0], month_and_day[1]) if month_and_day != None else None

    return (total_avg_dep_delay, avg_dep_delay_on_day)

def get_delayed_data(conn, origin: str, month_and_day: tuple):
    total_delayed = amount_of_delayed_flights_origin(conn, origin)
    total_delayed_on_day = amount_of_delayed_flights_origin(conn, origin, month_and_day[0], month_and_day[1]) if month_and_day != None else None
    avg_delayed_per_day = avg_delayed_flights_per_day(conn, origin)

    return (total_delayed, total_delayed_on_day, avg_delayed_per_day)

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
