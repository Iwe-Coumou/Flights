#dashboard.py

import streamlit as st
import sqlite3
import os
from plots import *
from helper_funcs import *
from data_cleaning import clean_database
from datetime import datetime, date
selected_flight=None
def normalize_date(selected_date):
    """Converts selected_date to datetime.date if necessary."""
    if isinstance(selected_date, str):
        return datetime.strptime(selected_date, "%Y-%m-%d").date()
    elif isinstance(selected_date, date):
        return selected_date
    else:
        st.error(f"Unrecognized date format: {selected_date} ({type(selected_date)})")
        return None

       
# ----------------- PAGE STYLING -----------------
st.set_page_config(layout="wide")  # Wide layout for better spacing

st.markdown("""
    <style>
        /* Background color */
        .stApp { background-color: #f5f5f5; }

        /* Block style */
        .st-container {
            background-color: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)





# ----------------- DATABASE CONNECTION -----------------

# Database Connection

# Establishes a connection to the SQLite database.
# If the connection is not already stored in the session state, it initializes it.
# The connection is stored in the session state to avoid reconnecting to the database on each interaction.

if "conn" not in st.session_state:
    db_path = os.path.abspath("C:/Users/fabio/vu uni/data engeneering/group project flights/Flights/Data/flights_database.db")
    st.session_state.conn = sqlite3.connect(db_path, check_same_thread=False)

conn = st.session_state.conn
# ----------------- SIDEBAR STYLING -----------------
with st.sidebar:
    st.header("Options")
    
#reset button 
    if st.button("Reset"):
        selected_destination = "None"
        selected_date = "None"
        selected_flight = "None"
        

    if st.button("Clean Database"):
        clean_database(conn)
        st.success("Database cleaned successfully!")

    # Select departure airport
    selected_airport = st.selectbox("Select departure airport", sorted(get_all_origin_airports(conn)), index=0, key="sidebar_airport")

    # Select destination
    destination_airports = get_available_destination_airports(conn, selected_airport)
    if destination_airports:
        selected_destination = st.selectbox("Select destination airport (optional)", ["None"] + sorted(destination_airports), index=0)
    else:
        selected_destination = "None"

    # Filter available dates based on airport and destination selection
    available_dates = get_available_dates(conn, selected_airport, None if selected_destination == "None" else selected_destination)

    # If no dates are available, show a warning
    if not available_dates:
        st.warning(f"No available dates for flights from {selected_airport} to {selected_destination}.")
        selected_date = None
    else:
        available_dates = ["None"] + available_dates  # Add "None" option
        selected_date = st.selectbox("Here you can see all of the dates that have at least one flight and you can select one for a finer search", available_dates, index=0, key="sidebar_date")
        if selected_date == "None":
            selected_date = None
        else:
            selected_date = normalize_date(selected_date)  # Normalize the date

    df_flights = pd.DataFrame()

    if selected_destination != "None":
        show_only_non_cancelled = st.checkbox("Show only non-cancelled flights", value=True, key="show_non_cancelled_checkbox")
        selected_flight = None

        df_flights = get_flights_on_date_and_route(conn, str(selected_date), selected_airport, selected_destination, show_only_non_cancelled)
        if not df_flights.empty and {"flight", "carrier"}.issubset(df_flights.columns):
            # Create a column that combines carrier and flight number
            df_flights["flight_display"] = df_flights["carrier"] + df_flights["flight"].astype(str)

            # Visual selection with carrier and flight number
            selected_flight_display = st.selectbox(
                "Select a specific flight",
                ["None"] + df_flights["flight_display"].tolist(),
                index=0,
                key="sidebar_flight_selector"
            )

            # Extract only the flight number (removing the carrier)
            selected_flight_row = df_flights[df_flights["flight_display"] == selected_flight_display]

            if not selected_flight_row.empty:
                selected_flight = str(selected_flight_row["flight"].values[0])  # Ensure it is a string
            else:
                selected_flight = None
                st.success("no flight selected, you are in route analysis mode")

    elif selected_destination != "None":
        st.warning("No flights available for this route on the selected date.")
        selected_flight = None

# ----------------- DASHBOARD TITLE -----------------
st.title("✈️ NYC Flights Dashboard")

# ----------------- FETCHING AVAILABLE DATA -----------------

# Fetching Available Data
# Retrieves all available departure airports and dates from the database for dropdown selection.

available_airports = get_all_origin_airports(conn)  # Fetch all origin airports
available_dates = get_available_dates(conn, selected_airport, None if selected_destination == "None" else selected_destination)
 # Fetch available flight dates

# ----------------- UPPER BLOCKS (Two side-by-side) -----------------
col1, col2 = st.columns(2)

if selected_destination == "None":

    with col1:
        
        # Flight Map
        # This section displays the flight map for departures from a selected NYC airport on a given date.
        
        if selected_date:
            # Fetch destinations dynamically based on selected airport and date
            month, day = selected_date.month, selected_date.day
            destination_airports = get_flight_destinations_from_airport_on_day(conn, month, day, selected_airport)
            # Generate Flight Map
            fig, missing = plot_destinations_on_day_from_NYC_airport(conn, month, day, selected_airport)
        else:
            # Generate Flight Map for all destinations
            fig, missing = plot_all_destinations_from_NYC_airport(conn, selected_airport)

        if fig:
            with st.container():
                st.subheader("📍 Flight Map")
                st.plotly_chart(fig, use_container_width=True)

                if len(missing) > 0:
                    st.warning(f"Missing airports in database: {missing}")
    with col2:

        ## Additional Metric (Future Expansion)    
        # This space can be used for extra analysis in the future.

        with st.container():
            st.subheader("✈️ Additional Metric (Future Expansion)")
            st.write("This space can be used for extra analysis in the future.")

    # ----------------- MIDDLE FULL-WIDTH BLOCK -----------------

    # Average Departure Delay by Airline
    # Analyzes the average departure delay per airline.

    fig_delay = plot_avg_departure_delay(conn)
    if fig_delay:
        with st.container():
            st.subheader("⏳ Average Departure Delay by Airline")
            st.plotly_chart(fig_delay, use_container_width=True)

    # ----------------- LOWER BLOCKS (Two side-by-side) -----------------
    col3, col4 = st.columns(2)

    with col3:
        # Distance vs. Arrival Delay
        # Examines the correlation between flight distance and arrival delays.
        
        if "fig_distance_delay" not in st.session_state or "correlation" not in st.session_state:
            fig_distance_delay, correlation = plot_distance_vs_arr_delay(conn,"histogram")
            st.session_state.fig_distance_delay = fig_distance_delay
            st.session_state.correlation = correlation
        else:
            fig_distance_delay = st.session_state.fig_distance_delay
            correlation = st.session_state.correlation

        if fig_distance_delay:
            with st.container():
                st.subheader("📊 Distance vs. Arrival Delay")
                st.plotly_chart(fig_distance_delay, use_container_width=True)
                st.write(f"Correlation between Distance and Arrival Delay: {correlation:.2f}")

    with col4:
        
        # Top 5 Airlines by Number of Flights   
        # Displays the top 5 airlines flying from the selected airport.
        

        df_top_carriers = top_5_carriers_from_specified_airport(conn, selected_airport)

        if not df_top_carriers.empty:
            with st.container():
                st.subheader(f"🏆 Top 5 Airlines from {selected_airport}")

                fig_carriers = px.bar(df_top_carriers, x="carrier", y="num_flights",
                                    title=f"Top 5 Airlines from {selected_airport}",
                                    labels={"carrier": "Airline", "num_flights": "Flights"},
                                    color="carrier")
                st.plotly_chart(fig_carriers, use_container_width=True)
else:

    fig_route = plot_route_map(conn, selected_airport, selected_destination)
    if fig_route:
        st.plotly_chart(fig_route, use_container_width=True)
    if selected_flight=="None":
        flight_data = df_flights[df_flights["flight"].astype(str) == selected_flight].iloc[0]
        origin, destination = flight_data["origin"], flight_data["dest"]
        average_flight_data = get_average_flight_stats_for_route(conn, origin, destination)

        st.subheader(f"🛫 Flight Details for {selected_flight}")
        with st.expander("Show Flight Details"):
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Flight data")
                st.metric("Flight time", f"{flight_data['air_time']} min")
                st.metric("Departure delay", f"{flight_data['dep_delay']} min")
                st.metric("Arrival delay", f"{flight_data['arr_delay']} min")
                st.metric("Distance", f"{flight_data['distance']} miles")
                st.metric("Carrier", f"{flight_data['carrier']}")
                st.metric("Scheduled Departure Time", f"{flight_data['sched_dep_time']}")
            with col2:
                st.subheader("Average flight data")
                st.metric("Flight time", f"{round(average_flight_data['avg_flight_time'],2)} min")
                st.metric("Departure delay", f"{round(average_flight_data['avg_dep_delay'], 2)} min")
                st.metric("Arrival delay", f"{round(average_flight_data['avg_arr_delay'], 2)} min")

        tailnum = flight_data["tailnum"]
        aircraft_info = get_aircraft_info(conn, tailnum)
        if aircraft_info:
            with st.expander("Show Aircraft Details"):
                st.metric("Manufacturer", f"{aircraft_info['manufacturer']}")
                st.metric("Model", f"{aircraft_info['model']}")
                st.metric("Tail number", f"{flight_data['tailnum']}")
                st.metric("Origin", f"{flight_data['origin']}")
                st.metric("Destination", f"{flight_data['dest']}")
        else:
            st.warning("No aircraft information available.")
    

        # ---- WEATHER CONDITIONS ----
        weather_data = get_weather_for_flight(conn, selected_airport, selected_destination, str(selected_date))
        if weather_data:
            st.subheader("🌬️ Wind Conditions")

            wind_speed = weather_data.get("wind_speed", None)
            wind_gust = weather_data.get("wind_gust", None)
            wind_dir = weather_data.get("wind_dir", None)
            temp = weather_data.get("temp", None)
            vis = weather_data.get("vis", None)

            def safe_write(label, value, unit=""):
                if value is not None and not (isinstance(value, float) and np.isnan(value)):
                    st.write(f"{label}: {value}{unit}")

            safe_write("Wind speed", wind_speed, " knots")
            safe_write("Wind gust", wind_gust, " knots")
            safe_write("Wind direction", wind_dir, "°")
            safe_write("Temperature", temp, "°C")
            safe_write("Visibility", vis, " miles")

            if all(v is None or (isinstance(v, float) and np.isnan(v)) for v in [wind_speed, wind_gust, wind_dir, temp, vis]):
                st.warning("⚠️ No weather data available for this flight.")

            if wind_dir is not None and not (isinstance(wind_dir, float) and np.isnan(wind_dir)):
                fig_wind = plot_wind_direction(wind_dir)
                st.plotly_chart(fig_wind, use_container_width=True)
            else:
                st.warning("⚠️ No wind direction data available.")

    
    else:
        st.subheader(f"🔗 Route Analysis: {selected_airport} → {selected_destination}")
        
        df_top_carriers = get_top_5_carriers_for_route(conn, selected_airport, selected_destination)
        if not df_top_carriers.empty:
            st.subheader("🏆 Top 5 Airlines on This Route")
            fig_carriers = px.bar(df_top_carriers, x="name", y="num_flights", title=f"Top 5 Airlines for {selected_airport} → {selected_destination}", labels={"name": "Airline", "num_flights": "Flights"}, color="name")
            fig_carriers.update_layout(showlegend=False)
            st.plotly_chart(fig_carriers, use_container_width=True)
        
        weather_stats = get_weather_stats_for_route(conn, selected_airport, selected_destination)
        if weather_stats["avg_wind_speed"] is not None:
            st.subheader("🌦️ Weather Stats on This Route")
            st.write(f"Average Wind Speed: {weather_stats['avg_wind_speed']:.2f} knots")
            if weather_stats["avg_temp"] is not None:
                st.write(f"Average Temperature: {weather_stats['avg_temp']:.2f}°C")
            else:
                st.write("Average Temperature: No data available")

        else:
            st.warning("No weather data available for this route.")
        
        avg_daily_flights, df_monthly_flights = get_flight_counts_for_route(conn, selected_airport, selected_destination)
        st.subheader("📈 Flight Volume Analysis")
        st.metric(label="Average Flights Per Day", value=f"{avg_daily_flights:.1f}")
        fig_flights = px.bar(df_monthly_flights, x="month", y="num_flights", title="Total Flights Per Month", labels={"month": "Month", "num_flights": "Flights"})
        st.plotly_chart(fig_flights, use_container_width=True)
        
        df_by_month, df_by_carrier, df_by_manufacturer = get_delay_stats_for_route(conn, selected_airport, selected_destination)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("⏳ Average Delay Per Month")
            fig_delay_month = px.line(df_by_month, x="month", y="avg_delay", title="Average Delay by Month", labels={"month": "Month", "avg_delay": "Average Delay (min)"})
            st.plotly_chart(fig_delay_month, use_container_width=True)
        with col2:
            st.subheader("✈️ Average Delay by Airline")
            fig_delay_carrier = px.bar(df_by_carrier, x="name", y="avg_delay", title="Average Delay by Carrier", labels={"name": "Airline", "avg_delay": "Average Delay (min)"}, color="name")
            fig_delay_carrier.update_layout(showlegend=False)
            st.plotly_chart(fig_delay_carrier, use_container_width=True)
        st.subheader("🏭 Average Delay by Aircraft Manufacturer")
        fig_delay_manufacturer = px.bar(df_by_manufacturer, x="manufacturer", y="avg_delay", title="Average Delay by Manufacturer", labels={"manufacturer": "Aircraft Manufacturer", "avg_delay": "Average Delay (min)"}, color="manufacturer")
        fig_delay_manufacturer.update_layout(showlegend=False)
        st.plotly_chart(fig_delay_manufacturer, use_container_width=True)