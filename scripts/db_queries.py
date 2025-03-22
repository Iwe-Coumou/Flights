import pandas as pd
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

def top_5_carriers_from_specified_airport(conn, destination_airport: str, month: int = None, day: int = None):
    """
    Finds the top 5 airlines for flights originating from a given airport code.
    
    If month and day are provided, it filters the flights to that specific day.
    Otherwise, it returns the top 5 carriers for all flights from that airport.
    
    Parameters:
        conn (sqlite3.Connection): Active database connection.
        destination_airport (str): Airport code to filter flights by (as origin).
        month (int, optional): Month to filter flights (1-12). Defaults to None.
        day (int, optional): Day to filter flights (1-31). Defaults to None.
        
    Returns:
        pd.DataFrame: DataFrame containing the carrier and the number of flights.
    """
    if month is not None and day is not None:
        query = """
            SELECT airlines.name, COUNT(*) as num_flights 
            FROM flights 
            JOIN airlines ON flights.carrier = airlines.carrier
            WHERE flights.origin = ?
              AND flights.month = ?
              AND flights.day = ?
            GROUP BY airlines.name
            ORDER BY num_flights DESC
            LIMIT 5;
        """
        params = (destination_airport, month, day)
    else:
        query = """
            SELECT airlines.name, COUNT(*) as num_flights 
            FROM flights 
            JOIN airlines ON flights.carrier = airlines.carrier
            WHERE flights.origin = ?
            GROUP BY airlines.name
            ORDER BY num_flights DESC
            LIMIT 5;
        """
        params = (destination_airport,)

    return read_sql_query(query, conn, params=params)

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

def get_top_5_carriers_for_route(conn, origin, destination, date=None):
    """
    Fetches the top 5 airlines operating the most flights on a given route.
    If a date is provided, it filters the results to that specific date.

    Parameters:
    conn (sqlite3.Connection): Active database connection.
    origin (str): Origin airport code.
    destination (str): Destination airport code.
    date (str, optional): Date in 'YYYY-MM-DD' format. Defaults to None.

    Returns:
    pandas.DataFrame: DataFrame with carrier and number of flights.
        """
    base_query = """
        SELECT airlines.name, COUNT(*) as num_flights 
        FROM flights
        JOIN airlines ON flights.carrier = airlines.carrier 
        WHERE origin = ? AND dest = ?
    """
    params = [origin, destination]

    if date:
        base_query += " AND substr(sched_dep_time, 1, 10) = ?"
        params.append(date)

    base_query += """
        GROUP BY airlines.name
        ORDER BY num_flights DESC
        LIMIT 5;
    """

    return read_sql_query(base_query, conn, params=params)

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

def get_distance_vs_arr_delay(conn, month=None, day=None):
    """
    Retrieves flight distance and arrival delay from the DB, returning them in a DataFrame.
    If both month and day are provided, filters the flights to only that specific day.
    
    Parameters:
        conn (sqlite3.Connection): Active database connection.
        month (int, optional): Month number to filter flights (1-12).
        day (int, optional): Day number to filter flights (1-31).
        
    Returns:
        pd.DataFrame: DataFrame with columns 'distance' and 'arr_delay'.
    """
    query = """
        SELECT distance, arr_delay
        FROM flights
        WHERE arr_delay IS NOT NULL
    """
    params = []
    if month is not None and day is not None:
        query += " AND month = ? AND day = ?"
        params.extend([month, day])
    query += ";"
    
    return pd.read_sql_query(query, conn, params=tuple(params))

def fetch_airport_coordinates_df(conn):
    """Fetches airport coordinates as a Pandas DataFrame."""
    query = "SELECT faa, lat, lon FROM airports;"
    return pd.read_sql_query(query, conn)

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
