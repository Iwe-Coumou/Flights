import plotly.graph_objects as go
import plotly.express as px
from scripts.no_category import get_flight_destinations_from_airport_on_day
from scripts.constants import NYC_AIRPORTS

def plot_destinations_on_day_from_NYC_airport(conn, month: int, day: int, NYC_airport):
    """
    Generates a flight path visualization for all flights departing from a given airport on a specific day.
    
    Parameters:
        conn (sqlite3.Connection): SQLite database connection.
        month (int): Month of the flight (1-12).
        day (int): Day of the flight (1-31).
        NYC_airport (str): The NYC airport FAA code (e.g., 'JFK', 'LGA', 'EWR').

    Returns:
        go.Figure: A Plotly figure object containing the flight visualization.
        list: A list of missing airports that were not found in the database.
    """
    if NYC_airport not in NYC_AIRPORTS:
        print(f"Error: Home base airport {NYC_airport} not in New York City.")
        return None, []

    FAA_codes = get_flight_destinations_from_airport_on_day(conn, month, day, NYC_airport)
    
    cursor = conn.cursor()
    cursor.execute("SELECT name, lat, lon FROM airports WHERE faa = ?", (NYC_airport,))
    home_base_data = cursor.fetchone()
    if not home_base_data:
        print(f"Error: Home base airport {NYC_airport} not found in the database.")
        return None, []
    
    home_base_name, home_base_lat, home_base_lon = home_base_data
    lons, lats, dest_lons, dest_lats, dest_names = [], [], [], [], []
    missing_airports = []
    fig = go.Figure()
    
    for FAA_code in FAA_codes:
        cursor.execute("SELECT name, lat, lon FROM airports WHERE faa = ?", (FAA_code,))
        airport_data = cursor.fetchone()
        if not airport_data:
            missing_airports.append(FAA_code)
            continue
        
        airport_name, airport_lat, airport_lon = airport_data
        dest_lons.append(airport_lon)
        dest_lats.append(airport_lat)
        dest_names.append(f"{airport_name} ({FAA_code})")
        
        lons.extend([home_base_lon, airport_lon, None])
        lats.extend([home_base_lat, airport_lat, None])
    
    fig.add_trace(go.Scattergeo(
        lon=lons,
        lat=lats,
        mode='lines',
        line=dict(width=1, color='black'),
        opacity=0.7,
        showlegend=False
    ))
    
    fig.add_trace(go.Scattergeo(
        lon=dest_lons,
        lat=dest_lats,
        text=dest_names,
        hoverinfo='text',
        mode='markers',
        name='Destinations',
        marker=dict(size=6, color='red', opacity=0.85)
    ))

    fig.add_trace(go.Scattergeo(
        lon=[home_base_lon],
        lat=[home_base_lat],
        text=[home_base_name],
        hoverinfo='text',
        mode='markers',
        name='Home Base',
        marker=dict(size=10, color='blue')
    ))

    fig.update_layout(
        title_text=f'Flights from {home_base_name} on {month}/{day}',
        geo=dict(
            scope="world",
            showland=True,
            landcolor="rgb(243, 243, 243)",
        )
    )
    
    return fig, missing_airports


def plot_airports_without_flights(conn):
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

def plot_airports_with_flights(conn):
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

def plot_airports_with_and_without_flights(conn):
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

def plot_avg_departure_delay(df):
    """
    Creates and returns a Plotly vertical bar chart of the average departure delay per airline.

    Parameters:
    df (pandas.DataFrame): DataFrame with 'airline_name' and 'avg_dep_delay' columns.

    Returns:
    plotly.graph_objects.Figure: A vertical bar chart figure.
    """
    fig = px.bar(
        df,
        x="airline_name",  # X-axis: Airline name
        y="avg_dep_delay",  # Y-axis: Average delay
        title="Average Departure Delay per Airline",
        labels={"avg_dep_delay": "Average Departure Delay (minutes)", "airline_name": "Airline"},
        color="avg_dep_delay",  # Color bars based on delay size
        color_continuous_scale="Darkmint"
    )

    fig.update_layout(xaxis_tickangle=-45)  # Rotate x-axis labels for readability
    return fig


