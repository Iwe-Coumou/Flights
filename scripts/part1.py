import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sqlite3 as sql

#Shows figure of all airports (including na)
def map_of_all_airports(df_airports: pd.DataFrame) -> None:
    fig = px.scatter_geo(df_airports, 
                        lat="lat", 
                        lon="lon", 
                        hover_name="name",  
                        projection="natural earth",
                        color="alt",
                        title="World Map of Airports")
    fig.show()

#Shows figure of airports inside US (na values excluded)
def map_of_US_airports(df_airports: pd.DataFrame) -> None:
    df_us = df_airports[df_airports["tzone"].notna() & df_airports["tzone"].str.startswith("America")]
    fig_us = px.scatter_geo(df_us, 
                                lat="lat", 
                                lon="lon", 
                                hover_name="name", 
                                projection="albers usa",
                                color="alt",
                                title="Airports Inside the US")
    fig_us.show()

#Shows figure of airports outside US (na values excluded)
def map_of_outside_US_airports(df_airports: pd.DataFrame) -> None:
    df_outside_us = df_airports[df_airports["tzone"].notna() & (df_airports["tzone"].str.startswith("America")==False)]
    fig_outside_us = px.scatter_geo(df_outside_us, 
                                lat="lat", 
                                lon="lon", 
                                hover_name="name", 
                                color="alt",
                                projection="natural earth",
                                title="Airports Outside the US")
    fig_outside_us.show()

#This is an extra figure showing the airports inside/outside US in one figure
def map_of_inside_vs_outside_US(df_airports: pd.DataFrame) -> None:
    df_us = df_airports[df_airports["tzone"].notna() & df_airports["tzone"].str.startswith("America")]
    df_outside_us = df_airports[df_airports["tzone"].notna() & (df_airports["tzone"].str.startswith("America")==False)]

    df_us["Location"] = "Inside US"
    df_outside_us["Location"] = "Outside US"

    df_difference = pd.concat([df_us, df_outside_us])

    fig_difference = px.scatter_geo(df_difference, 
                        lat="lat", 
                        lon="lon", 
                        hover_name="name", 
                        color="Location", 
                        projection="natural earth", 
                        title="Airports Inside and Outside the US",
                        color_discrete_map={"Inside US": "purple", "Outside US": "blue"})
    fig_difference.show()

#This takes a list of FAA codes and plots lines from them to the home base, default=JFK.
def plot_FAA(df_airports: pd.DataFrame, FAA_codes: list, home_base_faa: str = "JFK") -> None:
    fig = go.Figure()
    
    home_base_data = df_airports[df_airports["faa"] == home_base_faa]
    home_base_name, home_base_lat, home_base_lon = map(str, home_base_data.iloc[0][["name", "lat", "lon"]])

    has_international = False
    destination_lats, destination_lons, destination_names = [], [], []

    for FAA_code in FAA_codes:
        airport_data = df_airports[df_airports["faa"] == FAA_code]    
        airport_name, airport_lat, airport_lon = map(str, airport_data.iloc[0][["name", "lat", "lon"]])

        tzone = airport_data["tzone"].iloc[0]
        is_international = not tzone.startswith("America")
        if is_international:
            has_international = True

        # Store destination markers in a list to plot them together
        destination_lats.append(airport_lat)
        destination_lons.append(airport_lon)
        destination_names.append(f"{airport_name} ({FAA_code})")

        # Add flight path (lines) from home base to destinations
        fig.add_trace(go.Scattergeo(
            lon=[airport_lon, home_base_lon],
            lat=[airport_lat, home_base_lat],
            mode='lines',
            showlegend=False,  # Hide flight paths from legend
            line=dict(width=2.5, color='rgb(0, 0, 0)'), 
            opacity=0.6
        ))

    # Format FAA codes for the legend
    destination_faa_list = ", ".join(FAA_codes)
    home_base_faa_legend = f"Home Base ({home_base_faa})"
    destination_faa_legend = f"Destinations ({destination_faa_list})"

    # Add a single trace for all destination markers (red)
    fig.add_trace(go.Scattergeo(
        lon=destination_lons,
        lat=destination_lats,
        hoverinfo='text',
        text=destination_names,
        mode='markers',
        name=destination_faa_legend,  # Legend entry with FAA codes
        marker=dict(size=8, color='rgb(255, 51, 51)', opacity=0.85)
    ))

    # Add home base marker (blue)
    fig.add_trace(go.Scattergeo(
        lon=[home_base_lon],
        lat=[home_base_lat],
        hoverinfo='text',
        text=[f"{home_base_name} ({home_base_faa})"],
        mode='markers',
        name=home_base_faa_legend,  # Legend entry with FAA code
        marker=dict(size=10, color='rgb(0, 102, 255)', opacity=0.9, symbol='circle')
    ))

    map_scope = "world" if has_international else "usa"

    fig.update_layout(
        title_text=f'Flights from airports to {home_base_name}',
        geo=dict(
            scope=map_scope,
            projection_type="natural earth" if map_scope == "world" else None,  
            showland=True,
            landcolor="rgb(243, 243, 243)"
        )
    )

    fig.show()

def plot_time_zones(df):
    
    
    df["tz"] = df["tz"].astype(str)

    fig = px.scatter_geo(
        df,
        lat="lat",
        lon="lon",
        color="tz",
        projection="natural earth",
        title="Distribution of Airports Across Time Zones",
        hover_name="tz",
        category_orders={"tz": sorted(df["tz"].unique())},
    )

    fig.show()
    
def get_plane_type_counts(departing_airport: str, arriving_airport: str) -> dict:
    """
    Returns a dictionary describing how many times each plane type was used
    for a given flight trajectory (departing_airport -> arriving_airport).
    
    :param departing_airport: IATA code of the origin airport (e.g., "JFK")
    :param arriving_airport: IATA code of the destination airport (e.g., "LAX")
    :return: Dictionary {plane_type: count}
    """

    conn = sql.connect("flights database.db")
    cursor = conn.cursor()
    
    query = """
    SELECT p.type, COUNT(*) as count
    FROM flights f
    JOIN planes p ON f.tailnum = p.tailnum
    WHERE f.origin = ? AND f.dest = ?
    GROUP BY p.type
    ORDER BY count DESC;
    """

    # Execute query with the provided airports
    cursor.execute(query, (departing_airport, arriving_airport))
    
    # Fetch results and convert to a dictionary
    results = dict(cursor.fetchall())

    # Close the database connection
    conn.close()

    return results




def main():
    df_airports = pd.read_csv(r"data/airports.csv")

    map_of_all_airports(df_airports)
    map_of_US_airports(df_airports)
    map_of_outside_US_airports(df_airports)
    map_of_inside_vs_outside_US(df_airports)
    plot_time_zones(df_airports)

    # Example with domestic & international airports
    airports_world = ["BSF", "BAF", "ANP", "TZR"]
    airports_us = ["BAF", "ANP"]
    home_base = "TUS"
    plot_FAA(df_airports=df_airports, FAA_codes=airports_world)

if __name__ == "__main__":
    main()