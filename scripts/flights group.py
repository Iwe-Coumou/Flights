import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from timezonefinder import TimezoneFinder

# Earth radius in km
R = 6371



def file_opener(path):
    return pd.read_csv(path)


def euclidean_distance_calculator(target_code, df):
    
    target = df[df["faa"] == target_code].iloc[0]
    df = df[df["faa"] != target_code].copy() 
    
    target_lat, target_lon = target["lat"], target["lon"]
    
    df.loc[:, "euclidean_distance"] = np.sqrt(
        (df["lat"] - target_lat) ** 2 + (df["lon"] - target_lon) ** 2
    )
    
    return df[["faa", "euclidean_distance"]].sort_values(by="euclidean_distance")
    

def geodesic_distance_calculator(target_code, df):
    target = df[df["faa"] == target_code].iloc[0]
    df = df[df["faa"] != target_code].copy()

    target_lat, target_lon = np.radians(target["lat"]), np.radians(target["lon"])
    df["lat_rad"], df["lon_rad"] = np.radians(df["lat"]), np.radians(df["lon"])


    dphi = df["lat_rad"] - target_lat
    dlambda = df["lon_rad"] - target_lon
    phi_m = (df["lat_rad"] + target_lat) / 2

    # Applichiamo la formula dell'immagine
    df["geodesic_distance"] = R * np.sqrt(
        (2 * np.sin(dphi / 2) * np.cos(dlambda / 2)) ** 2 +
        (2 * np.cos(phi_m) * np.sin(dlambda / 2)) ** 2
    )

    return df[["faa", "geodesic_distance"]].sort_values(by="geodesic_distance")






def distances_distribution_gen(df_euclidean, df_geodesic):

    x0 = df_euclidean["euclidean_distance"]
    x1 = df_geodesic["geodesic_distance"]

    fig = make_subplots(rows=1, cols=2, subplot_titles=("Euclidean Distance", "Geodesic Distance"))

    fig.add_trace(go.Histogram(x=x0, name="Euclidean Distance", opacity=0.75, marker_color='blue'), row=1, col=1)

    fig.add_trace(go.Histogram(x=x1, name="Geodesic Distance", opacity=0.75, marker_color='green'), row=1, col=2)

    fig.update_layout(
        title="Comparison of Euclidean and Geodesic Distance Distributions",
        xaxis_title="Euclidean Distance",
        yaxis_title="Count",
        xaxis2_title="Geodesic Distance",
        bargap=0.2,
        showlegend=False,  
        width=1000, 
        height=500
    )

    fig.show()

    
def main():

    df=file_opener(r"Data\airports.csv")

    target_airport_code="JFK"
    euclidian=(euclidean_distance_calculator(target_airport_code,df))
    geodesic=(geodesic_distance_calculator(target_airport_code,df))

    distances_distribution_gen(euclidian,geodesic)


if __name__ == "__main__":
    main()