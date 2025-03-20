"""
Entry point of the application.
Connects to the actual DB, retrieves real distances for JFK/EWR/LGA,
calculates geodesic distances from CSV (filtrando le rotte effettive),
e poi produce 6 subplots:
(1) JFK DB, (2) JFK CSV, (3) EWR DB, (4) EWR CSV, (5) LGA DB, (6) LGA CSV.
"""

import sqlite3 as sql
import pandas as pd
from constants import *
from distance_calculations import *
from plots import *
from helper_funcs import *
from test import *
from data_cleaning import clean_database


def main():
    conn = sql.connect("data/flights_database.db")

    clean_database(conn)

    # month, day = 5, 23
    
    # for NYC_airport in NYC_AIRPORTS:
    # # Plot flight destinations from a specific airport on a given date
    #     fig, missing_airports = plot_destinations_on_day_from_NYC_airport(conn, month, day, NYC_airport)
    #     if fig:
    #         fig.show()

    # # Plot both airports with and without flights
    # fig = plot_airports_with_and_without_flights(conn)
    # if fig:
    #     fig.show()

    # destination = "ATL"
    # top_5 = top_5_manufacturers(conn, destination)
    # print(top_5)
 
    distance_vs_arr_fig, correlation = plot_distance_vs_arr_delay(conn)   
    if distance_vs_arr_fig:
        distance_vs_arr_fig.show()

    print(f"Correlation coefficient between distance and arrival time delay: {correlation:.3f}")

    # fig, correlation = plot_wind_impact_vs_air_time(conn)

    # # Display figures
    # fig.show()
    # print(f"Correlation between wind impact and air time: {correlation:.3f}")
    #create_col_with_speed(conn)
    

    print("aaaaa")
    create_col_local_arrival_time(conn)
    conn.close()

    print("aaaaa")

    
if __name__ == "__main__":
    
    
    main()
