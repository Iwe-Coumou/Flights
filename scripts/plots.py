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
from scripts.db_queries import get_flight_destinations_from_airport_on_day, get_distance_vs_arr_delay
from scripts.geo_utils import create_flight_direction_mapping_table, compute_wind_impact
from scripts.constants import NYC_AIRPORTS
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import sqlite3 as sql
from math import sin, radians

def plot_route_map(conn, origin, destination):
    """
    Generates a flight path visualization between two airports.

    Parameters:
    conn (sqlite3.Connection): Active database connection.
    origin (str): Origin airport code.
    destination (str): Destination airport code.

    Returns:
    plotly Figure: Map with flight route.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT lat, lon, faa FROM airports WHERE faa = ?", (origin,))
    origin_data = cursor.fetchone()
    
    cursor.execute("SELECT lat, lon, faa FROM airports WHERE faa = ?", (destination,))
    destination_data = cursor.fetchone()

    if not origin_data or not destination_data:
        return None  # One of the airports is missing

    fig = go.Figure()
    fig.add_trace(go.Scattergeo(lon=[origin_data[1], destination_data[1]],
                                lat=[origin_data[0], destination_data[0]],
                                mode="lines",
                                line=dict(width=2, color="red"),
                                hovertext=[f"Origin: {origin_data[2]}", f"Destination: {destination_data[2]}"]))

    return fig

def plot_all_destinations_from_NYC_airport(conn, NYC_airport: str):
    """
    Generates a flight path visualization for all flights departing 
    from a given NYC airport (no month/day filter).

    Parameters:
        conn (sqlite3.Connection): Active database connection.
        NYC_airport (str): The NYC airport code (e.g., 'JFK', 'LGA', 'EWR').

    Returns:
        (fig, missing_airports): 
            fig (go.Figure): Plotly figure of the flight routes.
            missing_airports (list): List of airport codes not found in the database.
    """
    # Check if the airport is recognized
    if NYC_airport not in NYC_AIRPORTS:
        print(f"Error: '{NYC_airport}' is not recognized as a NYC airport.")
        return None, []

    # Retrieve all unique destinations for this airport (no date filter)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT dest FROM flights WHERE origin = ?", (NYC_airport,))
    results = cursor.fetchall()
    FAA_codes = [row[0] for row in results]

    # Get info for the home base airport
    cursor.execute("SELECT name, lat, lon FROM airports WHERE faa = ?", (NYC_airport,))
    home_base_data = cursor.fetchone()

    if not home_base_data:
        print(f"Error: Home base '{NYC_airport}' not found in the database.")
        return None, []

    home_base_name, home_base_lat, home_base_lon = home_base_data

    # Prepare lists for plotting
    lons, lats = [], []
    dest_lons, dest_lats, dest_names = [], [], []
    missing_airports = []

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

        # Build the line path (home base -> destination -> None for break)
        lons.extend([home_base_lon, airport_lon, None])
        lats.extend([home_base_lat, airport_lat, None])

    # Create the figure
    fig = go.Figure()

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

    # Layout settings
    fig.update_layout(
        title_text=f'All Flights Departing from {home_base_name} ({NYC_airport})',
        geo=dict(
            scope="world",
            showland=True,
            landcolor="rgb(243, 243, 243)"
        )
    )

    return fig, missing_airports

def plot_destinations_on_day_from_NYC_airport(conn,month: int, day: int, NYC_airport: str):
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

def plot_distance_vs_arr_delay(conn, plot_type="scatter", month=None, day=None):
    """
    Creates a plot of flight distance vs. arrival delay, and calculates the correlation 
    between these two variables.
    
    If both month and day are provided, the function filters the flights to only that day.
    
    Parameters:
        conn (sqlite3.Connection): Active database connection.
        plot_type (str): Type of plot to generate ("scatter" or "histogram").
        month (int, optional): Month number to filter flights.
        day (int, optional): Day number to filter flights.
        
    Returns:
        tuple: (figure, correlation)
    """
    # Use the updated function to get the data (filtered if month and day are provided)
    distance_vs_arr_df = get_distance_vs_arr_delay(conn, month, day)
    
    # Calculate correlation between distance and arrival delay
    correlation = distance_vs_arr_df["distance"].corr(distance_vs_arr_df["arr_delay"])
    
    if plot_type == "scatter":
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
    elif plot_type == "histogram":
        fig = px.histogram(
            distance_vs_arr_df,
            x="distance",
            y="arr_delay",
            title="Flight Distance vs Arrival Delay",
            labels={"distance": "Distance (miles)", "arr_delay": "Arrival Delay (minutes)"},
            nbins=50,
            opacity=0.75,
            histfunc="avg"
        )
    else:
        raise ValueError("Invalid plot_type. Choose either 'scatter' or 'histogram'.")
    
    return fig, correlation

def multi_distance_distribution_gen(conn,*args):
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

def plot_wind_impact_vs_air_time(conn,impact_threshold=5):
    """
    Creates a violin plot to analyze the relationship between wind impact and air_time.
    
    Parameters:
      conn (sqlite3.Connection): Connection to the SQLite database.
      impact_threshold (float): Threshold (in knots) to classify wind as headwind/tailwind.
    
    Returns:
      tuple: (violin plot figure, correlation value)
    """
    cursor = conn.cursor()
    # Check if the flight_direction_map table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='flight_direction_map';")
    if cursor.fetchone() is None:
        print("flight_direction_map table not found. Creating it...")
        create_flight_direction_mapping_table(conn)
    
    # Query flights joined with weather and flight_direction_map
    query = """
        SELECT f.flight, f.origin, f.dest, f.time_hour, f.air_time,
               w.wind_dir, w.wind_speed, fdm.direction
        FROM flights f
        LEFT JOIN weather w 
            ON f.origin = w.origin AND f.time_hour = w.time_hour
        LEFT JOIN flight_direction_map fdm 
            ON f.origin = fdm.origin AND f.dest = fdm.dest;
    """
    df = pd.read_sql_query(query, conn)
    
    # Compute wind impact
    df["wind_impact"] = df.apply(
        lambda row: compute_wind_impact(row["direction"], row["wind_dir"], row["wind_speed"]),
        axis=1
    )
    
    # Remove rows with missing air_time or wind_impact
    df = df.dropna(subset=["air_time", "wind_impact"])
    
    # Classify wind type based on the wind impact
    df["wind_type"] = np.where(df["wind_impact"] > impact_threshold, "Tailwind",
                         np.where(df["wind_impact"] < -impact_threshold, "Headwind", "Crosswind"))
    

    correlation = np.corrcoef(df["wind_impact"], df["air_time"])[0, 1]
    
    # Create a violin plot of air_time by wind type
    fig = px.violin(df, x="wind_type", y="air_time", box=False, points=False,
                    title="Distribution of Air Time by Wind Type",
                    color="wind_type", 
                    color_discrete_map={"Headwind": "red", "Tailwind": "green", "Crosswind": "blue"})
    
    return fig, correlation  

def plot_avg_departure_delay(conn, month=None, day=None):
    """
    Fetches and visualizes the average departure delay per airline.
    If month and day are provided, it filters the flights to only that day.
    
    Parameters:
        conn (sqlite3.Connection): Database connection object.
        month (int, optional): Month number to filter flights (1-12).
        day (int, optional): Day number to filter flights (1-31).
    
    Returns:
        plotly.graph_objects.Figure: A bar plot showing average delays by airline.
        
    Raises:
        sqlite3.Error: If there's an error executing the SQL query.
        ValueError: If no data is found for any airline.
        
    Example:
        >>> conn = sqlite3.connect('flights.db')
        >>> fig = plot_avg_departure_delay(conn, month=3, day=15)
        >>> fig.show()
    """
    try:
        cursor = conn.cursor()

        # Base query and parameters list
        query = """
            SELECT airlines.name AS airline_name, 
                   AVG(flights.dep_delay) AS avg_dep_delay 
            FROM flights 
            JOIN airlines ON flights.carrier = airlines.carrier 
        """
        params = []

        # If both month and day are provided, add filtering condition
        if month is not None and day is not None:
            query += "WHERE flights.month = ? AND flights.day = ? "
            params.extend([month, day])

        query += "GROUP BY airlines.name"

        # Execute the query
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        if not rows:
            raise ValueError("No flight delay data found for any airline")

        df_delays = pd.DataFrame(rows, columns=["Airline", "Average departure delay"])

        fig = go.Figure(data=[go.Bar(
            x=df_delays["Airline"],
            y=df_delays["Average departure delay"],
            marker_color='skyblue'
        )])

        fig.update_layout(
            title="Average Departure Delay per Airline",
            xaxis_title="Airline",
            yaxis_title="Average Departure Delay (minutes)",
            xaxis_tickangle=-45,
            template="plotly_white",
            showlegend=False
        )

        return fig

    except sql.Error as e:
        raise sql.Error(f"Database error occurred: {str(e)}")
    except Exception as e:
        raise Exception(f"An error occurred while creating the plot: {str(e)}")

def analyze_weather_effects_plots(conn):
    """
    Analyzes and visualizes the relationship between weather conditions and flight delays
    for different aircraft manufacturers.

    Parameters:
        db_filename (str): Path to the SQLite database file. Defaults to 'flights_database.db'.

    Returns:
        plotly.graph_objects.Figure: A grouped bar plot showing average delays by manufacturer
                                   and weather condition.

    Raises:
        sqlite3.Error: If there's an error connecting to or querying the database.
        ValueError: If no valid data is found after filtering.
        
    Example:
        >>> fig = analyze_weather_effects_plots('my_flights.db')
        >>> fig.show()
    """
    try:
        query = """
        SELECT f.dep_delay, p.manufacturer, 
               w.wind_speed, w.wind_dir, w.wind_gust, w.precip
        FROM flights f
        JOIN planes p ON f.tailnum = p.tailnum
        JOIN weather w ON f.origin = w.origin 
                     AND f.time_hour = w.time_hour
        WHERE p.manufacturer IS NOT NULL
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            raise ValueError("No valid data found in the database")

        # Data Cleaning and Filtering
        df = df[df['dep_delay'] < 300]  # Remove delay outliers
        df = df[df['dep_delay'] > -50]  # Remove early departures
        df = df.dropna(subset=['dep_delay', 'manufacturer', 'wind_speed', 
                              'wind_dir', 'wind_gust', 'precip'])

        if df.empty:
            raise ValueError("No valid data remains after filtering")

        # --- Define Weather Conditions ---
        # Define thresholds (adjust as needed)
        strong_wind_threshold = 25
        gustiness_threshold = 10
        crosswind_threshold = 15
        max_tailwind_component = 10

        # Create a function to categorize wind conditions
        def categorize_wind(row):
            """
            Categorizes weather conditions based on wind and precipitation data.

            Parameters:
                row (pd.Series): A pandas Series containing the following fields:
                    - wind_speed: Wind speed in knots
                    - wind_dir: Wind direction in degrees
                    - wind_gust: Wind gust speed in knots
                    - precip: Precipitation amount

            Returns:
                str: Weather condition category ('Good', 'Strong Headwind', 'Strong Tailwind',
                     'Strong Crosswind', 'High Gustiness', 'Precipitation', or 'Moderate')

            Raises:
                KeyError: If any required field is missing from the input row
                ValueError: If wind direction is not in valid range [0-360]
            """
            try:
                wind_speed = row['wind_speed']
                wind_dir = row['wind_dir']
                wind_gust = row['wind_gust']
                precip = row['precip']

                # Validate wind direction
                if not (0 <= wind_dir <= 360):
                    raise ValueError(f"Wind direction must be between 0 and 360 degrees, got {wind_dir}")

                # Good Weather: Low wind speed, low gustiness, no precipitation
                if wind_speed <= 10 and wind_gust - wind_speed <= 5 and precip == 0:
                    return 'Good'

                # Problematic Conditions:
                # Strong Headwind (within +/- 30 degrees of runway heading)
                if (330 <= wind_dir <= 360 or 0 <= wind_dir <= 30) and wind_speed > strong_wind_threshold:
                    return 'Strong Headwind'

                # Strong Tailwind (within +/- 30 degrees of runway heading + 180 degrees)
                if 150 <= wind_dir <= 210 and wind_speed > max_tailwind_component:
                    return 'Strong Tailwind'

                # Strong Crosswind
                crosswind_component = wind_speed * abs(sin(radians(wind_dir)))
                if crosswind_component > crosswind_threshold:
                    return 'Strong Crosswind'

                # High Gustiness
                if wind_gust - wind_speed > gustiness_threshold:
                    return 'High Gustiness'

                # Precipitation
                if precip > 0:
                    return 'Precipitation'

                return 'Moderate'

            except KeyError as e:
                raise KeyError(f"Missing required field in input row: {str(e)}")
            except Exception as e:
                raise Exception(f"Error categorizing wind conditions: {str(e)}")

        df['weather_condition'] = df.apply(categorize_wind, axis=1)

        # --- Calculate Average Delay per Manufacturer and Weather Condition ---
        manufacturer_delay = df.groupby(['manufacturer', 'weather_condition'])['dep_delay'].mean().reset_index()

        # --- Visualization: Grouped Bar Plot ---
        fig = px.bar(manufacturer_delay, x='manufacturer', y='dep_delay', color='weather_condition', barmode='group',
                     title='Average Departure Delay per Manufacturer (by Weather Condition)',
                     labels={'dep_delay': 'Average Delay (min)', 'manufacturer': 'Manufacturer', 'weather_condition': 'Weather Condition'})

        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

        return fig
    
    except sql.Error as e:
        raise sql.Error(f"Database error occurred: {str(e)}")
    except Exception as e:
        raise Exception(f"An error occurred while creating the plot: {str(e)}")

def plot_avg_delay_by_hour(conn, month: int, day: int):
    """
    Plots the average departure delay grouped by hour for a specific day.

    Parameters:
    conn (sqlite3.Connection): Database connection.
    month (int): The specified month.
    day (int): The specified day.

    Returns:
    plotly.graph_objects.Figure: A bar plot showing the average departure delay by hour.
    """
    cursor = conn.cursor()

    query = """
    SELECT strftime('%H', sched_dep_time ) AS hour, AVG(dep_delay) AS avg_delay
    FROM flights
    WHERE month = ? AND day = ? AND sched_dep_time  IS NOT NULL
    GROUP BY hour
    ORDER BY hour;
    """
    cursor.execute(query, (month, day))
    result = cursor.fetchall()

    if not result:
        print("No data available for the specified day.")
        return

    df = pd.DataFrame(result, columns=['hour', 'avg_delay'])
    df['hour'] = df['hour'].astype(int)

    all_hours = pd.DataFrame({'hour': range(24)})
    df = pd.merge(all_hours, df, on='hour', how='left').fillna(0)

    fig = px.bar(
        df,
        x='hour',
        y='avg_delay',
        title=f"Average Departure Delay by Hour on {month}/{day}",
        labels={'hour': 'Hour of the Day (24-Hour Format)', 'avg_delay': 'Average Delay (Minutes)'},
        color='avg_delay',
        color_continuous_scale='Blues'
    )
    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        yaxis=dict(title='Average Delay (Minutes)'),
        bargap=0.2
    )

    return fig

def plot_avg_visibility_by_hour(conn, month: int, day: int):
    """
    Plots the average visibility (visib) grouped by hour for a specific day.

    Parameters:
    conn (sqlite3.Connection): Database connection.
    month (int): The specified month.
    day (int): The specified day.

    Returns:
    plotly.graph_objects.Figure: A bar plot showing the average visibility by hour.
    """
    cursor = conn.cursor()

    query = """
    SELECT hour, AVG(visib) AS avg_visib
    FROM weather
    WHERE month = ? AND day = ? AND visib IS NOT NULL
    GROUP BY hour
    ORDER BY hour;
    """
    cursor.execute(query, (month, day))
    result = cursor.fetchall()

    if not result:
        print("No data available for the specified day.")
        return

    df = pd.DataFrame(result, columns=['hour', 'avg_visib'])
    df['hour'] = df['hour'].astype(int)

    all_hours = pd.DataFrame({'hour': range(24)})
    df = pd.merge(all_hours, df, on='hour', how='left').fillna(0)

    fig = px.bar(
        df,
        x='hour',
        y='avg_visib',
        title=f"Average Visibility by Hour on {month}/{day}",
        labels={'hour': 'Hour of the Day (24-Hour Format)', 'avg_visib': 'Average Visibility (Miles)'},
        color='avg_visib',
        color_continuous_scale='Blues'
    )
    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        yaxis=dict(title='Average Visibility (Miles)'),
        bargap=0.2
    )

    return fig

def plot_avg_wind_speed_by_hour(conn, month: int, day: int):
    """
    Plots the average wind speed grouped by hour for a specific day.

    Parameters:
    conn (sqlite3.Connection): Database connection.
    month (int): The specified month.
    day (int): The specified day.

    Returns:
    plotly.graph_objects.Figure: A bar plot showing the average wind speed by hour.
    """
    cursor = conn.cursor()

    query = """
    SELECT hour, AVG(wind_speed) AS avg_wind_speed
    FROM weather
    WHERE month = ? AND day = ? AND wind_speed IS NOT NULL
    GROUP BY hour
    ORDER BY hour;
    """
    cursor.execute(query, (month, day))
    result = cursor.fetchall()

    if not result:
        print("No data available for the specified day.")
        return

    df = pd.DataFrame(result, columns=['hour', 'avg_wind_speed'])
    df['hour'] = df['hour'].astype(int)

    all_hours = pd.DataFrame({'hour': range(24)})
    df = pd.merge(all_hours, df, on='hour', how='left').fillna(0)

    fig = px.bar(
        df,
        x='hour',
        y='avg_wind_speed',
        title=f"Average Wind Speed by Hour on {month}/{day}",
        labels={'hour': 'Hour of the Day (24-Hour Format)', 'avg_wind_speed': 'Average Wind Speed (Knots)'},
        color='avg_wind_speed',
        color_continuous_scale='Blues'
    )
    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        yaxis=dict(title='Average Wind Speed (Knots)'),
        bargap=0.2
    )

    return fig

def plot_avg_wind_gust_by_hour(conn, month: int, day: int):
    """
    Plots the average wind gust grouped by hour for a specific day.

    Parameters:
    conn (sqlite3.Connection): Database connection.
    month (int): The specified month.
    day (int): The specified day.

    Returns:
    plotly.graph_objects.Figure: A bar plot showing the average wind gust by hour.
    """
    cursor = conn.cursor()

    query = """
    SELECT hour, AVG(wind_gust) AS avg_wind_gust
    FROM weather
    WHERE month = ? AND day = ? AND wind_gust IS NOT NULL
    GROUP BY hour
    ORDER BY hour;
    """
    cursor.execute(query, (month, day))
    result = cursor.fetchall()

    if not result:
        print("No data available for the specified day.")
        return

    df = pd.DataFrame(result, columns=['hour', 'avg_wind_gust'])
    df['hour'] = df['hour'].astype(int)

    all_hours = pd.DataFrame({'hour': range(24)})
    df = pd.merge(all_hours, df, on='hour', how='left').fillna(0)

    fig = px.bar(
        df,
        x='hour',
        y='avg_wind_gust',
        title=f"Average Wind Gust by Hour on {month}/{day}",
        labels={'hour': 'Hour of the Day (24-Hour Format)', 'avg_wind_gust': 'Average Wind Gust (Knots)'},
        color='avg_wind_gust',
        color_continuous_scale='Blues'
    )
    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        yaxis=dict(title='Average Wind Gust (Knots)'),
        bargap=0.2
    )

    return fig

def plot_avg_precip_by_hour(conn, month: int, day: int):
    """
    Plots the average precipitation grouped by hour for a specific day.

    Parameters:
    conn (sqlite3.Connection): Database connection.
    month (int): The specified month.
    day (int): The specified day.

    Returns:
    plotly.graph_objects.Figure: A bar plot showing the average precipitation by hour.
    """
    cursor = conn.cursor()

    query = """
    SELECT hour, AVG(precip) AS avg_precip
    FROM weather
    WHERE month = ? AND day = ? AND precip IS NOT NULL
    GROUP BY hour
    ORDER BY hour;
    """
    cursor.execute(query, (month, day))
    result = cursor.fetchall()

    if not result:
        print("No data available for the specified day.")
        return

    df = pd.DataFrame(result, columns=['hour', 'avg_precip'])
    df['hour'] = df['hour'].astype(int)

    all_hours = pd.DataFrame({'hour': range(24)})
    df = pd.merge(all_hours, df, on='hour', how='left').fillna(0)

    fig = px.bar(
        df,
        x='hour',
        y='avg_precip',
        title=f"Average Precipitation by Hour on {month}/{day}",
        labels={'hour': 'Hour of the Day (24-Hour Format)', 'avg_precip': 'Average Precipitation (Inches)'},
        color='avg_precip',
        color_continuous_scale='Blues'
    )
    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        yaxis=dict(title='Average Precipitation (Inches)'),
        bargap=0.2
    )

    return fig

def plot_wind_direction(direction, wind_speed=1):
    """
    Creates a compass visualization for wind direction.

    Parameters:
    direction (float): Wind direction in degrees.
    wind_speed (float): Wind speed (optional, to scale the arrow length).

    Returns:
    plotly.graph_objects.Figure: A polar chart representing wind direction.
    """
    # Convert direction to radians
    angle_rad = np.radians(direction)

    # Define the starting point (center)
    x_start, y_start = 0, 0  # Start from the center of the graph

    # Define the endpoint based on the direction
    x_end = np.cos(angle_rad) * wind_speed  # Projection on X
    y_end = np.sin(angle_rad) * wind_speed  # Projection on Y

    fig = go.Figure()

    # Draw the circular axis
    fig.add_trace(go.Scatterpolar(
        r=[0, wind_speed],  # Start from the center
        theta=[direction, direction],
        mode="lines",
        line=dict(color="red", width=3)
    ))

    fig.update_layout(
        title="Wind Direction",
        polar=dict(
            radialaxis=dict(visible=False, range=[0, wind_speed]),
            angularaxis=dict(direction="clockwise", tickmode="array", 
                             tickvals=[0, 90, 180, 270], ticktext=["N", "E", "S", "W"])
        ),
        showlegend=False
    )

    return fig

def plot_avg_wind_speed_for_route(conn, origin, destination):
    """
    Plots the average daily wind speed for a given route (origin → destination)
    based on the wind conditions at the origin airport at departure times.

    Parameters:
        conn (sqlite3.Connection): SQLite database connection
        origin (str): Origin airport code
        destination (str): Destination airport code

    Returns:
        plotly.graph_objs._figure.Figure or None: A Plotly figure showing wind trends, or None if no data.
    """
    query = """
        SELECT strftime('%Y-%m', f.sched_dep_time) AS month, AVG(w.wind_speed) AS avg_wind_speed
        FROM flights f
        JOIN weather w ON f.origin = w.origin AND f.time_hour = w.time_hour
        WHERE f.origin = ? AND f.dest = ?
        GROUP BY strftime('%Y-%m', f.sched_dep_time)
        ORDER BY strftime('%Y-%m', f.sched_dep_time)
    """
    df = pd.read_sql_query(query, conn, params=(origin, destination))

    # Check if there is valid data
    if df.empty or df['avg_wind_speed'].isnull().all():
        return None

    # Convert to datetime if not already
    df['month'] = pd.to_datetime(df['month'])

    # Create the bar graph
    fig = px.bar(
        df,
        x="month",
        y="avg_wind_speed",
        title=f"Monthly Avg Wind Speed — {origin} → {destination}",
        labels={"month": "Month", "avg_wind_speed": "Wind Speed (knots)"}
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=50),
        xaxis=dict(tickformat="%Y-%m")
    )

    return fig
