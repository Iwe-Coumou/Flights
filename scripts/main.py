import sqlite3 as sql

from plots import *
from helper_funcs import *
from test import *
from constants import *

def main():
    conn = sql.connect("data/flights_database.db")
    month, day = 5, 23,
    
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

 
    # distance_vs_arr_fig, correlation = plot_distance_vs_arr_delay(conn)   
    # if distance_vs_arr_fig:
    #     distance_vs_arr_fig.show()

    # print(f"Correlation coefficient: {correlation:.3f}")

    airport_locations = get_airports_locations(conn)
    new_york_location = get_airports_locations(conn, ["JFK"])[0]
    flight_directions = compute_flight_directions(new_york_location, airport_locations)
    print(flight_directions)

    conn.close()

if __name__ == "__main__":
    main()