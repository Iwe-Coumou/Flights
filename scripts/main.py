import sqlite3 as sql
from constants import *
from data_cleaning import clean_database
from helper_funcs import *
from plots import *
from part1 import *

def main():
    # Connessione al database
    #clean_database(conn)
    conn = sql.connect("Data/flights_database.db")
    fig, missing = plot_destinations_on_day_from_NYC_airport(conn,3,15,"JFK")
    fig.show()
    print("Missing values:",missing)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

if __name__ == "__main__":
    main()
