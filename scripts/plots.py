import plotly.graph_objects as go
import plotly.express as px
from helper_funcs import get_flight_destinations_from_airport_on_day, get_distance_vs_arr_delay
from constants import NYC_AIRPORTS
import numpy as np
import scipy.stats as stats

def plot_destinations_on_day_from_NYC_airport(conn, month: int, day: int, NYC_airport: str):
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

import plotly.graph_objects as go
import sqlite3

def plot_airports_with_and_without_flights(conn):
    """
    Generates a single plot with:
    - Red dots for airports that have no incoming and no outgoing flights.
    - Blue dots for airports that have either incoming or outgoing flights.
    
    Parameters:
        conn (sqlite3.Connection): SQLite database connection.
    
    Returns:
        go.Figure: A Plotly figure object containing the visualization.
    """
    cursor = conn.cursor()
    
    # Query for airports with neither incoming nor outgoing flights
    query_no_flights = """
        SELECT faa, name, lat, lon FROM airports
        WHERE faa NOT IN (SELECT DISTINCT dest FROM flights)
        AND faa NOT IN (SELECT DISTINCT origin FROM flights);
    """
    cursor.execute(query_no_flights)
    missing_airports = cursor.fetchall()
    
    # Query for airports that have at least one incoming or outgoing flight
    query_with_flights = """
        SELECT faa, name, lat, lon FROM airports
        WHERE faa IN (SELECT DISTINCT dest FROM flights)
        OR faa IN (SELECT DISTINCT origin FROM flights);
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
        print("All airports have at least one flight.")
    
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
        print("No airports have flights.")
    
    fig.update_layout(
        title_text='Airports With and Without Any Flights',
        geo=dict(
            scope="world",
            showland=True,
            landcolor="rgb(243, 243, 243)"
        )
    )
    
    return fig


def plot_distance_vs_arr_delay(conn):
    """
    Creates a scatterplot of flight distance vs. arrival delay and calculates the correlation.

    Parameters:
    distance_vs_arr_df (pandas.DataFrame): DataFrame with 'distance' and 'arr_delay' columns.

    Returns:
    tuple: (Plotly figure, correlation coefficient)
    """
    # Calculate correlation coefficient
    distance_vs_arr_df = get_distance_vs_arr_delay(conn)
    correlation = distance_vs_arr_df["distance"].corr(distance_vs_arr_df["arr_delay"])

    # Create scatter plot
    fig = px.scatter(
        distance_vs_arr_df,
        x="distance",
        y="arr_delay",
        title="Flight Distance vs Arrival Delay",
        labels={"distance": "Distance (miles)", "arr_delay": "Arrival Delay (minutes)"},
        opacity=0.5
    )

    # Add reference line at 0 delay
    fig.add_hline(y=0, line_dash="dash", line_color="red")

    return fig, correlation

def analyze_wind_impact_vs_air_time(df):
    """
    Analyzes the relationship between wind impact sign and air time using a violin plot,
    categorizing wind as Headwind, Tailwind, or Crosswind.
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing 'wind_impact' and 'air_time'.
    
    Returns:
    tuple: (violinplot_figure, correlation)
    """
    df = df.dropna(subset=["air_time", "wind_impact"])
    
    # Classify wind into Headwind, Tailwind, or Crosswind
    df["wind_type"] = np.where(df["wind_impact"] > 5, "Tailwind", 
                        np.where(df["wind_impact"] < -5, "Headwind", "Crosswind"))

    # Compute correlation (Pearson correlation coefficient)
    correlation = np.corrcoef(df["wind_impact"], df["air_time"])[0, 1]

    # Violin plot for a better distribution view
    fig2 = px.violin(df, x="wind_type", y="air_time", box=False, points=False,
                      title="Distribution of Air Time by Wind Type",
                      color="wind_type", 
                      color_discrete_map={"Headwind": "red", "Tailwind": "green", "Crosswind": "blue"})

    return fig2, correlation