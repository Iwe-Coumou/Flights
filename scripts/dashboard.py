import streamlit as st
import sqlite3
import os
from plots import *
from helper_funcs import *
from data_cleaning import clean_database
import datetime

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

#Establishes a connection to the SQLite database.
#If the connection is not already stored in the session state, it initializes it.
#The connection is stored in the session state to avoid reconnecting to the database on each interaction.

if "conn" not in st.session_state:
    db_path = os.path.abspath("C:/Users/fabio/vu uni/data engeneering/group project flights/Flights/Data/flights_database.db")
    st.session_state.conn = sqlite3.connect(db_path, check_same_thread=False)

conn = st.session_state.conn

# ----------------- SIDEBAR -----------------

# Sidebar Options
#Contains buttons for database maintenance and additional functionalities.

with st.sidebar:
    st.header("Options")

    if st.button("Clean Database"):
        clean_database(conn)
        st.success("Database cleaned successfully!")

# ----------------- DASHBOARD TITLE -----------------
st.title("✈️ NYC Flights Dashboard")

# ----------------- FETCHING AVAILABLE DATA -----------------

# Fetching Available Data
#Retrieves all available departure airports and dates from the database for dropdown selection.

available_airports = get_all_origin_airports(conn)  # Fetch all origin airports
available_dates = get_available_dates(conn)  # Fetch available flight dates

# ----------------- UPPER BLOCKS (Two side-by-side) -----------------
col1, col2 = st.columns(2)

with col1:
    
    # Flight Map
    #This section displays the flight map for departures from a selected NYC airport on a given date.
    
    selected_date = st.selectbox("Select a date", sorted(available_dates), index=0)
    selected_airport = st.selectbox("Select a departure airport", sorted(available_airports), index=0)

    # Fetch destinations dynamically based on selected airport and date
    month, day = selected_date.month, selected_date.day
    destination_airports = get_flight_destinations_from_airport_on_day(conn, month, day, selected_airport)

    # Generate Flight Map
    fig, missing = plot_destinations_on_day_from_NYC_airport(conn, month, day, selected_airport)

    if fig:
        with st.container():
            st.subheader("📍 Flight Map")
            st.plotly_chart(fig, use_container_width=True)

            if len(missing) > 0:
                st.warning(f"Missing airports in database: {missing}")

with col2:
    
    # Top 5 Airlines by Number of Flights   
    #Displays the top 5 airlines flying to a selected destination.
    
    if destination_airports:
        destination_airport = st.selectbox(
            "Select destination airport",
            sorted(destination_airports),  
            index=0
        )
    else:
        st.warning(f"No destinations found for {selected_airport}. Using default: LAX")
        destination_airport = "LAX"  

    df_top_carriers = top_5_carriers(conn, destination_airport)

    if not df_top_carriers.empty:
        with st.container():
            st.subheader("🏆 Top 5 Airlines by Number of Flights")

            fig_carriers = px.bar(df_top_carriers, x="carrier", y="num_flights",
                                  title=f"Top 5 Airlines for {destination_airport}",
                                  labels={"carrier": "Airline", "num_flights": "Flights"},
                                  color="carrier")
            st.plotly_chart(fig_carriers, use_container_width=True)

# ----------------- MIDDLE FULL-WIDTH BLOCK -----------------

# Average Departure Delay by Airline
#Analyzes the average departure delay per airline.

fig_delay = plot_avg_departure_delay(conn)
if fig_delay:
    with st.container():
        st.subheader("⏳ Average Departure Delay by Airline")
        st.plotly_chart(fig_delay, use_container_width=True)

# ----------------- LOWER BLOCKS (Two side-by-side) -----------------
col3, col4 = st.columns(2)

with col3:
    # Distance vs. Arrival Delay
    #Examines the correlation between flight distance and arrival delays.
    
    fig_distance_delay, correlation = plot_distance_vs_arr_delay(conn)

    if fig_distance_delay:
        with st.container():
            st.subheader("📊 Distance vs. Arrival Delay")
            st.plotly_chart(fig_distance_delay, use_container_width=True)
            st.write(f"Correlation between Distance and Arrival Delay: {correlation:.2f}")

with col4:

    ## Additional Metric (Future Expansion)    
    #This space can be used for extra analysis in the future.

    with st.container():
        st.subheader("✈️ Additional Metric (Future Expansion)")
        st.write("This space can be used for extra analysis in the future.")
