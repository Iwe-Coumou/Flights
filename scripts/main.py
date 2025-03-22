from data_cleaning import clean_database
from plots import *
from db_queries import *
from flight_stats import *
from geo_utils import *
import sqlite3 as sql

def main(conn):
    fig = plot_airports_with_and_without_flights(conn)
    if fig:
        fig.show()


if __name__ == "__main__":
    conn = sql.connect("data/flights_database.db")
    main(conn)