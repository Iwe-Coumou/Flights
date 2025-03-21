import sqlite3 as sql
from constants import *
from data_cleaning import clean_database
from helper_funcs import *
from plots import *
from part1 import *

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
