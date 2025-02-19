def plot_FAA_from_db(conn, FAA_codes: list, home_base_faa: str, go=None):
    """
    Generates a flight path visualization from a specified NYC airport to multiple destinations using the database.
    
    Parameters:
        conn (sqlite3.Connection): SQLite database connection.
        FAA_codes (list): List of destination FAA codes.
        home_base_faa (str): The NYC airport FAA code (e.g., 'JFK', 'LGA', 'EWR').
        go (module): Plotly graph_objects module passed from main.py.
    
    Returns:
        go.Figure: A Plotly figure object containing the flight visualization.
        list: A list of missing airports that were not found in the database.
    """
    if go is None:
        raise ValueError("plotly.graph_objects must be passed as the 'go' parameter.")
    
    cursor = conn.cursor()
    
    # Fetch home base airport details
    cursor.execute("SELECT name, lat, lon FROM airports WHERE faa = ?", (home_base_faa,))
    home_base_data = cursor.fetchone()
    
    if not home_base_data:
        print(f"Error: Home base airport {home_base_faa} not found in the database.")
        return None, []
    
    home_base_name, home_base_lat, home_base_lon = home_base_data
    has_international = False
    lons, lats = [], []
    dest_lons, dest_lats, dest_names = [], [], []
    missing_airports = []
    
    fig = go.Figure()  # Initialize figure
    
    for FAA_code in FAA_codes:
        cursor.execute("SELECT name, lat, lon, tzone FROM airports WHERE faa = ?", (FAA_code,))
        airport_data = cursor.fetchone()
        if not airport_data:
            missing_airports.append(FAA_code)
            continue
        airport_name, airport_lat, airport_lon, tzone = airport_data
        
        is_international = not tzone.startswith("America")
        if is_international:
            has_international = True
        
        dest_lons.append(airport_lon)
        dest_lats.append(airport_lat)
        dest_names.append(f"{airport_name} ({FAA_code})")
        
        # Add paths using None separators to avoid excessive clutter
        lons.extend([home_base_lon, airport_lon, None])
        lats.extend([home_base_lat, airport_lat, None])
    
    # Add flight paths in a single trace for performance improvement
    fig.add_trace(go.Scattergeo(
        lon=lons,
        lat=lats,
        mode='lines',
        line=dict(width=1, color='black'),
        opacity=0.7,
        showlegend=False,
    ))
    
    # Add destination markers (red)
    fig.add_trace(go.Scattergeo(
        lon=dest_lons,
        lat=dest_lats,
        hoverinfo='text',
        text=dest_names,
        mode='markers',
        name='Destinations',
        marker=dict(size=6, color='rgb(255, 51, 51)', opacity=0.85)
    ))
    
    # Add home base marker (blue)
    fig.add_trace(go.Scattergeo(
        lon=[home_base_lon],
        lat=[home_base_lat],
        hoverinfo='text',
        text=[f"{home_base_name} ({home_base_faa})"],
        mode='markers',
        name=f"Home Base ({home_base_faa})",
        marker=dict(size=10, color='rgb(0, 102, 255)', opacity=0.9, symbol='circle')
    ))
    
    map_scope = "world" if has_international else "usa"
    
    fig.update_layout(
        title_text=f'Flights from {home_base_name}',
        geo=dict(
            scope=map_scope,
            projection_type="natural earth" if map_scope == "world" else None,
            showland=True,
            landcolor="rgb(243, 243, 243)"
        )
    )
    
    return fig, missing_airports

def get_flight_destinations_plot(conn, month, day, airport, go):
    """
    Retrieves all flight destinations leaving from a given NYC airport on a specified month and day
    and returns the figure.
    
    Parameters:
        conn (sqlite3.Connection): SQLite database connection.
        month (int): Month of the flight (1-12).
        day (int): Day of the flight (1-31).
        airport (str): The NYC airport FAA code (e.g., 'JFK', 'LGA', 'EWR').
        go (module): Plotly graph_objects module passed from main.py.
    
    Returns:
        go.Figure: A Plotly figure object containing the flight visualization.
        list: A list of missing airports that were not found in the database.
    """
    cursor = conn.cursor()
    
    query = """
        SELECT DISTINCT dest FROM flights 
        WHERE month = ? AND day = ? AND origin = ?;
    """
    cursor.execute(query, (month, day, airport))
    destinations = [row[0] for row in cursor.fetchall()]
    
    if destinations:
        return plot_FAA_from_db(conn, destinations, home_base_faa=airport, go=go)
    else:
        print(f"No flights found from {airport} on {month}/{day}.")
        return None, []


def plot_airports_without_flights(conn, go=None):
    """
    Generates a plot of all airports that have no flights to them.
    
    Parameters:
        conn (sqlite3.Connection): SQLite database connection.
        go (module): Plotly graph_objects module passed from main.py.
    
    Returns:
        go.Figure: A Plotly figure object containing the visualization.
    """
    if go is None:
        raise ValueError("plotly.graph_objects must be passed as the 'go' parameter.")
    
    cursor = conn.cursor()
    query = """
        SELECT faa, name, lat, lon FROM airports
        WHERE faa NOT IN (SELECT DISTINCT dest FROM flights);
    """
    cursor.execute(query)
    missing_airports = cursor.fetchall()
    
    if not missing_airports:
        print("All airports receive flights.")
        return None
    
    fig = go.Figure()
    
    lons, lats, names = [], [], []
    for faa, name, lat, lon in missing_airports:
        lons.append(lon)
        lats.append(lat)
        names.append(f"{name} ({faa})")
    
    fig.add_trace(go.Scattergeo(
        lon=lons,
        lat=lats,
        hoverinfo='text',
        text=names,
        mode='markers',
        name='Airports with No Flights',
        marker=dict(size=6, color='red', opacity=0.75)
    ))
    
    fig.update_layout(
        title_text='Airports Without Incoming Flights',
        geo=dict(
            scope="world",
            showland=True,
            landcolor="rgb(243, 243, 243)"
        )
    )
    
    return fig

def plot_airports_with_flights(conn, go=None):
    """
    Generates a plot of all airports that have at least one incoming flight.
    
    Parameters:
        conn (sqlite3.Connection): SQLite database connection.
        go (module): Plotly graph_objects module passed from main.py.
    
    Returns:
        go.Figure: A Plotly figure object containing the visualization.
    """
    if go is None:
        raise ValueError("plotly.graph_objects must be passed as the 'go' parameter.")
    
    cursor = conn.cursor()
    query = """
        SELECT faa, name, lat, lon FROM airports
        WHERE faa IN (SELECT DISTINCT dest FROM flights);
    """
    cursor.execute(query)
    active_airports = cursor.fetchall()
    
    if not active_airports:
        print("No airports have incoming flights.")
        return None
    
    fig = go.Figure()
    
    lons, lats, names = [], [], []
    for faa, name, lat, lon in active_airports:
        lons.append(lon)
        lats.append(lat)
        names.append(f"{name} ({faa})")
    
    fig.add_trace(go.Scattergeo(
        lon=lons,
        lat=lats,
        hoverinfo='text',
        text=names,
        mode='markers',
        name='Airports with Flights',
        marker=dict(size=6, color='blue', opacity=0.75)
    ))
    
    fig.update_layout(
        title_text='Airports With Incoming Flights',
        geo=dict(
            scope="world",
            showland=True,
            landcolor="rgb(243, 243, 243)"
        )
    )
    
    return fig

def plot_airports_with_and_without_flights(conn, go=None):
    """
    Generates a single plot with:
    - Red dots for airports that have no incoming flights.
    - Blue dots for airports that receive flights.
    
    Parameters:
        conn (sqlite3.Connection): SQLite database connection.
        go (module): Plotly graph_objects module passed from main.py.
    
    Returns:
        go.Figure: A Plotly figure object containing the visualization.
    """
    if go is None:
        raise ValueError("plotly.graph_objects must be passed as the 'go' parameter.")
    
    cursor = conn.cursor()
    
    # Query for airports with no incoming flights
    query_no_flights = """
        SELECT faa, name, lat, lon FROM airports
        WHERE faa NOT IN (SELECT DISTINCT dest FROM flights);
    """
    cursor.execute(query_no_flights)
    missing_airports = cursor.fetchall()
    
    # Query for airports that receive flights
    query_with_flights = """
        SELECT faa, name, lat, lon FROM airports
        WHERE faa IN (SELECT DISTINCT dest FROM flights);
    """
    cursor.execute(query_with_flights)
    active_airports = cursor.fetchall()
    
    fig = go.Figure()
    
    # Add airports with no flights (red)
    if missing_airports:
        no_flight_lons, no_flight_lats, no_flight_names = [], [], []
        for faa, name, lat, lon in missing_airports:
            no_flight_lons.append(lon)
            no_flight_lats.append(lat)
            no_flight_names.append(f"{name} ({faa})")
        
        fig.add_trace(go.Scattergeo(
            lon=no_flight_lons,
            lat=no_flight_lats,
            hoverinfo='text',
            text=no_flight_names,
            mode='markers',
            name='Airports with No Flights',
            marker=dict(size=6, color='red', opacity=0.75)
        ))
    else:
        print("All airports receive flights.")
    
    # Add airports with flights (blue)
    if active_airports:
        flight_lons, flight_lats, flight_names = [], [], []
        for faa, name, lat, lon in active_airports:
            flight_lons.append(lon)
            flight_lats.append(lat)
            flight_names.append(f"{name} ({faa})")
        
        fig.add_trace(go.Scattergeo(
            lon=flight_lons,
            lat=flight_lats,
            hoverinfo='text',
            text=flight_names,
            mode='markers',
            name='Airports with Flights',
            marker=dict(size=6, color='blue', opacity=0.75)
        ))
    else:
        print("No airports have incoming flights.")
    
    fig.update_layout(
        title_text='Airports With and Without Incoming Flights',
        geo=dict(
            scope="world",
            showland=True,
            landcolor="rgb(243, 243, 243)"
        )
    )
    
    return fig