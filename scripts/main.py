import sqlite3 as sql

from plots import *
from helper_funcs import *
from test import *
from constants import *
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

    wind_df = create_flight_dataframe(conn)  # Get flights with precomputed directions

    wind_df_filtered = wind_df.dropna()  # Remove rows with missing values

    fig1, fig2, correlation = analyze_wind_impact_vs_air_time(wind_df_filtered)

    # Display figures
    fig1.show()
    fig2.show()
    print(f"Correlation between wind impact and air time: {correlation:.3f}")

    conn.close()

if __name__ == "__main__":
    main()