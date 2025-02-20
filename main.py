import sqlite3 as sql

from scripts.plots import *
from scripts.no_category import *
from scripts.test import *
from scripts.constants import *

def main():
    conn = sql.connect("data/flights_database.db")
    month, day = 5, 23,
    
    for NYC_airport in NYC_AIRPORTS:
    # Plot flight destinations from a specific airport on a given date
        fig, missing_airports = plot_destinations_on_day_from_NYC_airport(conn, month, day, NYC_airport)
        if fig:
            fig.show()
        print(missing_airports)
    
    # Plot both airports with and without flights
    fig = plot_airports_with_and_without_flights(conn)
    if fig:
        fig.show()

    # Get flight statistics
    stats = get_flight_statistics(conn, month, day, NYC_airport)
    print(f"Flight Statistics for {NYC_airport} on {month}/{day}:")
    print(f"Total Flights: {stats['total_flights']}")
    print(f"Unique Destinations: {stats['unique_destinations']}")
    print(f"Most Visited Destination: {stats['most_visited_destination']} ({stats['most_visited_count']} times)")

    destination = "ATL"
    top_5 = top_5_manufacturers(conn, destination)
    print(top_5)

 
    distance_vs_arr_fig, correlation = plot_distance_vs_arr_delay(conn)   
    if distance_vs_arr_fig:
        distance_vs_arr_fig.show()

    print(f"Correlation coefficient: {correlation:.3f}")


    conn.close()

if __name__ == "__main__":
    main()