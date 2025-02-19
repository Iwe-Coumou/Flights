import sqlite3 as sql

from scripts.plots import *
from scripts.no_category import *
from scripts.test import *
from scripts.constants import *

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

    # # Get flight statistics
    # stats = get_flight_statistics(conn, month, day, NYC_airport)
    # print(f"Flight Statistics for {NYC_airport} on {month}/{day}:")
    # print(f"Total Flights: {stats['total_flights']}")
    # print(f"Unique Destinations: {stats['unique_destinations']}")
    # print(f"Most Visited Destination: {stats['most_visited_destination']} ({stats['most_visited_count']} times)")

    airline_delays_df = avg_departure_delay_per_airline(conn)
    print(airline_delays_df)
    fig = plot_avg_departure_delay(airline_delays_df)
    if fig:
        fig.show()
    
    conn.close()

if __name__ == "__main__":
    main()