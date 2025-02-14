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
    target_lat, target_lon = target["lat"], target["lon"]
    
    df.loc[:, "geodesic_distance"] = R*np.sqrt(
        ((2*(np.sin((df["lat"] - target_lat)/2))*
         (np.cos((df["lat"] - target_lat)/2)))**2)+
        ((2*np.cos((df["lat"] + target_lat)/2)*
          np.sin(df["lon"] - target_lon/(2)))**2)
    )
    
    return df[["faa", "geodesic_distance"]].sort_values(by="euclidean_distance")





def distances_distribution_gen():
    print()
    

df=file_opener(r"data/airports.csv")

target_airport_code="JFK"
print(euclidean_distance_calculator(target_airport_code,df))
print(geodesic_distance_calculator(target_airport_code,df))


