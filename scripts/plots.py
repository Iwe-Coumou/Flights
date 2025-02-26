# plots.py

"""
Module gathering all plotting functions for this project.
Includes:
- Plot of flights departing from NYC airports on a given day
- Plot of airports that do/do not receive flights
- Plot distance vs arrival delay
- Multi-distance distribution histogram plotting
"""

import plotly.graph_objects as go
import plotly.express as px
from helper_funcs import get_flight_destinations_from_airport_on_day, get_distance_vs_arr_delay
from constants import NYC_AIRPORTS
from plotly.subplots import make_subplots
import pandas as pd

def plot_destinations_on_day_from_NYC_airport(conn, month: int, day: int, NYC_airport: str):
    """
    Generates a flight path visualization for all flights departing from a given NYC airport 
    on a specific day (month/day). 
    Returns (fig, missing_airports).
    """
    if NYC_airport not in NYC_AIRPORTS:
        print(f"Error: '{NYC_airport}' is not recognized as a NYC airport.")
        return None, []

    # Retrieve destination codes from the DB
    FAA_codes = get_flight_destinations_from_airport_on_day(conn, month, day, NYC_airport)
    cursor = conn.cursor()
    cursor.execute("SELECT name, lat, lon FROM airports WHERE faa = ?", (NYC_airport,))
    home_base_data = cursor.fetchone()

    if not home_base_data:
        print(f"Error: Home base '{NYC_airport}' not found in the database.")
        return None, []

    home_base_name, home_base_lat, home_base_lon = home_base_data
    lons, lats, dest_lons, dest_lats, dest_names = [], [], [], [], []
    missing_airports = []
    fig = go.Figure()

    # For each destination, gather data and plot lines
    for code in FAA_codes:
        cursor.execute("SELECT name, lat, lon FROM airports WHERE faa = ?", (code,))
        airport_data = cursor.fetchone()
        if not airport_data:
            missing_airports.append(code)
            continue
        airport_name, airport_lat, airport_lon = airport_data
        dest_lons.append(airport_lon)
        dest_lats.append(airport_lat)
        dest_names.append(f"{airport_name} ({code})")

        lons.extend([home_base_lon, airport_lon, None])
        lats.extend([home_base_lat, airport_lat, None])

    # Flight paths
    fig.add_trace(go.Scattergeo(
        lon=lons,
        lat=lats,
        mode='lines',
        line=dict(width=1, color='black'),
        opacity=0.7,
        showlegend=False
    ))

    # Destination markers
    fig.add_trace(go.Scattergeo(
        lon=dest_lons,
        lat=dest_lats,
        text=dest_names,
        hoverinfo='text',
        mode='markers',
        name='Destinations',
        marker=dict(size=6, color='red', opacity=0.85)
    ))

    # Home base marker
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
            landcolor="rgb(243, 243, 243)"
        )
    )
    return fig, missing_airports

def plot_airports_with_and_without_flights(conn):
    """
    Creates a single plot with:
      - Red dots for airports that have no incoming flights
      - Blue dots for airports that do receive flights
    Returns a Plotly figure object.
    """
    cursor = conn.cursor()
    query_no_flights = """
        SELECT faa, name, lat, lon FROM airports
        WHERE faa NOT IN (SELECT DISTINCT dest FROM flights);
    """
    cursor.execute(query_no_flights)
    missing_airports = cursor.fetchall()

    query_with_flights = """
        SELECT faa, name, lat, lon FROM airports
        WHERE faa IN (SELECT DISTINCT dest FROM flights);
    """
    cursor.execute(query_with_flights)
    active_airports = cursor.fetchall()

    fig = go.Figure()

    # Airports with no flights (red)
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

    # Airports with flights (blue)
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

    fig.update_layout(
        title_text='Airports With and Without Incoming Flights',
        geo=dict(
            scope="world",
            showland=True,
            landcolor="rgb(243, 243, 243)"
        )
    )
    return fig

def plot_distance_vs_arr_delay(conn):
    """
    Creates a scatter plot of flight distance vs. arrival delay, 
    and calculates the correlation between these two variables.
    Returns (figure, correlation).
    """
    distance_vs_arr_df = get_distance_vs_arr_delay(conn)
    correlation = distance_vs_arr_df["distance"].corr(distance_vs_arr_df["arr_delay"])

    fig = px.scatter(
        distance_vs_arr_df,
        x="distance",
        y="arr_delay",
        title="Flight Distance vs Arrival Delay",
        labels={"distance": "Distance (miles)", "arr_delay": "Arrival Delay (minutes)"},
        opacity=0.5
    )

    # Add a reference line at 0 delay
    fig.add_hline(y=0, line_dash="dash", line_color="red")

    return fig, correlation

def multi_distance_distribution_gen(*args):
    """
    Creates multiple histogram subplots in a single figure.
    Each item in *args should be a tuple: (df, title, column_name).

    Example usage:
    multi_distance_distribution_gen(
        (df_1, "Title 1", "distance"),
        (df_2, "Title 2", "distance"),
        ...
    )
    """
    num_graphs = len(args)
    if num_graphs == 0:
        raise ValueError("No dataframes provided to plot.")

    rows = (num_graphs + 1) // 2  # 2 subplots per row
    cols = 2

    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[title for _, title, _ in args],
        shared_xaxes=True,
        shared_yaxes=True
    )

    colors = ["blue", "green", "red", "purple", "orange", "cyan", "magenta", "yellow"]
    color_index = 0

    for i, (df, title, column) in enumerate(args):
        if column not in df.columns:
            raise ValueError(f"The column '{column}' does not exist in '{title}' DataFrame")

        r = (i // 2) + 1
        c = (i % 2) + 1

        fig.add_trace(
            go.Histogram(
                x=df[column],
                name=title,
                opacity=0.75,
                marker_color=colors[color_index % len(colors)],
                nbinsx=30
            ),
            row=r,
            col=c
        )

        color_index += 1

    fig.update_layout(
        title="Comparison of Distance Distributions",
        bargap=0.1,
        showlegend=False,
        width=900,
        height=rows * 400
    )

    fig.show()
