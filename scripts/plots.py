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
import numpy as np
import scipy.stats as stats

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

def analyze_wind_impact_vs_air_time(df):
    """
    Analyzes the relationship between wind impact sign and air time using Plotly.
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing 'wind_impact' and 'air_time'.
    
    Returns:
    tuple: (boxplot_figure, scatterplot_figure, correlation)
    """
    df = df.dropna(subset=["air_time", "wind_impact"])
    df["wind_type"] = np.where(df["wind_impact"] < 0, "Headwind", "Tailwind")

    # Compute correlation (Pearson correlation coefficient)
    correlation = np.corrcoef(df["wind_impact"], df["air_time"])[0, 1]

    # Boxplot to compare air time for Headwind vs Tailwind
    fig1 = px.box(df, x="wind_type", y="air_time", color="wind_type",
                  title="Air Time vs. Wind Impact Type",
                  labels={"wind_type": "Wind Type", "air_time": "Air Time (minutes)"},
                  color_discrete_map={"Headwind": "red", "Tailwind": "green"})

    # Scatter plot (manually adding a trendline)
    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(
        x=df["wind_impact"], 
        y=df["air_time"], 
        mode='markers', 
        marker=dict(opacity=0.5), 
        name="Flights"
    ))

    # Compute trendline manually (simple linear regression)
    x_values = df["wind_impact"]
    y_values = df["air_time"]
    slope, intercept = np.polyfit(x_values, y_values, 1)  # Fit a linear model
    trend_x = np.linspace(min(x_values), max(x_values), 100)
    trend_y = slope * trend_x + intercept

    # Add the trendline
    fig2.add_trace(go.Scatter(
        x=trend_x, y=trend_y, mode='lines', name='Trendline', line=dict(color='blue')
    ))

    fig2.update_layout(
        title="Air Time vs. Wind Impact",
        xaxis_title="Wind Impact",
        yaxis_title="Air Time (minutes)"
    )

    return fig1, fig2, correlation

def analyze_weather_effects_plots(db_filename="flights_database.db"):
    """
    Generates a bar plot comparing average departure delays in different wind and precipitation
    conditions for each manufacturer, separating headwind and tailwind, and considering
    operational limits and gustiness.
    """
    conn = sqlite3.connect(db_filename)
    query = """
    SELECT f.dep_delay, p.manufacturer, w.wind_speed, w.wind_dir, w.wind_gust, w.precip
    FROM flights f
    JOIN planes p ON f.tailnum = p.tailnum
    JOIN weather w ON f.origin = w.origin AND f.time_hour = w.time_hour;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    # --- Data Cleaning and Filtering (already done) ---
    df = df[df['dep_delay'] < 300]  # Remove delay outliers
    df = df[df['dep_delay'] > -50]  # removing negative delay values (early departures)
    df = df.dropna(subset=['dep_delay', 'manufacturer', 'wind_speed', 'wind_dir', 'wind_gust', 'precip'])  # Handle missing values

    # --- Define Weather Conditions ---
    # Define thresholds (adjust as needed)
    strong_wind_threshold = 25  # Knots
    gustiness_threshold = 10  # Difference between wind_gust and wind_speed
    crosswind_threshold = 15  #Knots
    max_tailwind_component = 10 #Knots. Most aircraft have a maximum tailwind component for safe takeoff and landing—often around 10 knots for many commercial jets

    # Create a function to categorize wind conditions
    def categorize_wind(row):
        wind_speed = row['wind_speed']
        wind_dir = row['wind_dir']
        wind_gust = row['wind_gust']
        precip = row['precip']

        # Good Weather: Low wind speed, low gustiness, no precipitation
        if wind_speed <= 10 and wind_gust - wind_speed <= 5 and precip == 0:
            return 'Good'

        # Problematic Conditions:
        # Assuming runway heading is 0/360 degrees for simplicity - adjust as needed
        # 1a. Strong Headwind (within +/- 30 degrees of runway heading)
        if 330 <= wind_dir <= 360 or 0 <= wind_dir <= 30:
            if wind_speed > strong_wind_threshold:
                return 'Strong Headwind'

        # 1b. Strong Tailwind (within +/- 30 degrees of runway heading + 180 degrees)
        if 150 <= wind_dir <= 210:
            #Check if max tailwind is exceeded
            if wind_speed > max_tailwind_component:
                return 'Strong Tailwind'

        # 2. Strong Crosswind (wind direction is roughly perpendicular to runway - +/- 60 degrees)
        crosswind_component = wind_speed * abs(sin(radians(wind_dir)))#abs(sin(radians(wind_dir)))

        if crosswind_component > crosswind_threshold:
            return 'Strong Crosswind'

        # 3. High Gustiness
        if wind_gust - wind_speed > gustiness_threshold:
            return 'High Gustiness'

        # 4. Precipitation
        if precip > 0:
            return 'Precipitation'

        # If no specific condition is met, categorize as "Moderate"
        return 'Moderate'

    df['weather_condition'] = df.apply(categorize_wind, axis=1)

    # --- Calculate Average Delay per Manufacturer and Weather Condition ---
    manufacturer_delay = df.groupby(['manufacturer', 'weather_condition'])['dep_delay'].mean().reset_index()

    # --- Visualization: Grouped Bar Plot ---
    fig_manufacturer = px.bar(manufacturer_delay, x='manufacturer', y='dep_delay', color='weather_condition', barmode='group',
                              title='Average Departure Delay per Manufacturer (by Weather Condition)',
                              labels={'dep_delay': 'Average Delay (min)', 'manufacturer': 'Manufacturer', 'weather_condition': 'Weather Condition'})
    fig_manufacturer.show()
#remember to load you data correctly on your local machine, I´ve test this on colab so it should be good now.
analyze_weather_effects_plots()
