"""
Entry point of the application.
Connects to the actual DB, retrieves real distances for JFK/EWR/LGA,
calculates geodesic distances from CSV (filtrando le rotte effettive),
e poi produce 6 subplots:
(1) JFK DB, (2) JFK CSV, (3) EWR DB, (4) EWR CSV, (5) LGA DB, (6) LGA CSV.
"""

import sqlite3
import pandas as pd
from constants import *
from distance_calculations import file_opener, geodesic_distance_calculator
from plots import multi_distance_distribution_gen
from helper_funcs import create_planes_copy_with_speed








def main():

    conn = sqlite3.connect(DATABASE_PATH)

    df_csv = file_opener("../Data/airports.csv")

    # dist_plots_args = []  

    # for code in NYC_AIRPORTS:
    #     query = f"""
    #         SELECT DISTINCT origin, dest, (distance * {MILES_TO_KM}) AS distance
    #         FROM flights
    #         WHERE origin='{code}' OR dest='{code}'
    #     """
    #     df_db_dist = pd.read_sql_query(query, conn)

    #     df_csv_geo = geodesic_distance_calculator(code, df_csv)

    #     route_airports = set(df_db_dist["origin"]) | set(df_db_dist["dest"])
    #     if code in route_airports:
    #         route_airports.remove(code)

    #     df_csv_geo_filtered = df_csv_geo[df_csv_geo["faa"].isin(route_airports)]

    #     dist_plots_args.append((df_db_dist, f"{code} - DB Distances", "distance"))
    #     dist_plots_args.append((df_csv_geo_filtered, f"{code} - CSV Distances", "geodesic_distance"))

    # multi_distance_distribution_gen(*dist_plots_args)


    create_planes_copy_with_speed(conn, recalc_speed=True)





    conn.close()

if __name__ == "__main__":
    main()
