import plotly.graph_objects as go
import pandas as pd

import part1 as p1

def main():
    df_airports = pd.read_csv(r"./data/airports.csv")

    # Example with domestic & international airports
    airports_world = ["BSF", "BAF", "ANP", "TZR"]
    airports_us = ["BAF", "ANP"]
    home_base = "TUS"
    p1.plot_FAA(df_airports=df_airports, FAA_codes=airports_world)

if __name__ == "__main__":
    main()