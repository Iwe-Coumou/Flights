import plotly.graph_objects as go
import pandas as pd

def plot_FAA(df_airports: pd.DataFrame,FAA_codes: list, home_base_faa: str = "JFK") -> None:
    fig = go.Figure()
    
    home_base_data = df_airports[df_airports["faa"] == home_base_faa]
    home_base_name, home_base_lat, home_base_lon = map(str, home_base_data.iloc[0][["name", "lat", "lon"]])

    has_international = False

    for FAA_code in FAA_codes:
        airport_data = df_airports[df_airports["faa"] == FAA_code]    
        airport_name, airport_lat, airport_lon = map(str, airport_data.iloc[0][["name", "lat", "lon"]])

        tzone = airport_data["tzone"].iloc[0]
        is_international = not tzone.startswith("America")
        if is_international:
            has_international = True

        location_mode = "ISO-3"  

         # Add flight path (line) to home_base (hidden from legend)
        fig.add_trace(go.Scattergeo(
            locationmode=location_mode,
            lon=[airport_lon, home_base_lon],
            lat=[airport_lat, home_base_lat],
            mode='lines',
            showlegend=False,  # **Hide from legend**
            line=dict(width=2.5, color='rgb(0, 0, 0)'), 
            opacity=0.6
        ))

        # Add marker for the selected airport (shown in legend)
        fig.add_trace(go.Scattergeo(
            locationmode=location_mode,
            lon=[airport_lon],
            lat=[airport_lat],
            hoverinfo='text',
            text=[f"{airport_name} ({FAA_code})"],
            mode='markers',
            name=f"{airport_name} ({FAA_code})",  
            marker=dict(size=8, color='rgb(255, 51, 51)', opacity=0.85, line=dict(width=1.5, color='rgb(255, 51, 51)'))
        ))

    # Add marker for home_base (shown in legend)
    fig.add_trace(go.Scattergeo(
        locationmode="ISO-3",
        lon=[home_base_lon],
        lat=[home_base_lat],
        hoverinfo='text',
        text= [f"{home_base_name} ({home_base_faa})"],
        mode='markers',
        name=f"{home_base_name} ({home_base_faa})",  
        marker=dict(size=10, color='rgb(0, 102, 255)', opacity=0.9, symbol='circle', line=dict(width=2, color='rgb(0, 102, 255)'))
    ))

    map_scope = "world" if has_international else "usa"

    fig.update_layout(
        title_text = f'Flights from airports to {home_base_name}',
        geo=dict(
            scope=map_scope,
            projection_type = "natural earth" if map_scope == "world" else None,  
            showland=True,
            landcolor="rgb(243, 243, 243)"
        )
    )

    fig.show()


def main():
    df_airports = pd.read_csv(r"data/airports.csv")

     # Example with domestic & international airports
    airports_world = ["BSF", "BAF", "ANP", "TZR"]
    airports_us = ["BAF", "ANP"]
    home_base = "TUS"
    plot_FAA(df_airports=df_airports, FAA_codes=airports_world)

if __name__ == "__main__":
    main()