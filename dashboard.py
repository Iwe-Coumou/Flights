import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from statistics import (
    get_delayed_flights_by_airline,
    get_delayed_flights_by_airport,
    get_delayed_flights_by_route,
    get_delay_statistics,
    get_delay_distribution,
    get_monthly_delays,
    get_airline_performance,
    get_airport_performance
)
from plots import (
    plot_destinations_on_day_from_NYC_airport,
    plot_airports_with_and_without_flights,
    plot_distance_vs_arr_delay,
    plot_wind_impact_vs_air_time,
    plot_avg_departure_delay,
    analyze_weather_effects_plots
)
import sqlite3

def main():
    st.set_page_config(page_title="Dashboard Voli", layout="wide")
    st.title("Dashboard Analisi Voli")

    # Connessione al database
    conn = sqlite3.connect("data/flights_database.db")

    # Sidebar per i filtri
    st.sidebar.title("Filtri")
    selected_month = st.sidebar.selectbox("Seleziona Mese", range(1, 13))
    selected_day = st.sidebar.selectbox("Seleziona Giorno", range(1, 32))
    selected_airport = st.sidebar.selectbox("Seleziona Aeroporto", ["JFK", "LGA", "EWR"])

    # Statistiche generali
    st.header("Statistiche Generali")
    stats = get_delay_statistics()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Totale Voli", f"{stats['total_flights']:,}")
    with col2:
        st.metric("Voli in Ritardo", f"{stats['delayed_flights']:,}")
    with col3:
        st.metric("Percentuale Ritardi", f"{stats['delay_percentage']:.1f}%")
    with col4:
        st.metric("Ritardo Medio", f"{stats['avg_delay']:.1f} min")

    # Distribuzione dei ritardi
    st.header("Distribuzione dei Ritardi")
    delay_dist = get_delay_distribution()
    fig_dist = px.bar(delay_dist, x='delay_category', y='delay',
                     title="Distribuzione dei Ritardi per Categoria")
    st.plotly_chart(fig_dist, use_container_width=True)

    # Performance per Compagnia Aerea
    st.header("Performance per Compagnia Aerea")
    airline_perf = get_airline_performance()
    fig_airline = px.bar(airline_perf, x='airline', y=['delay_percentage', 'avg_delay'],
                        barmode='group', title="Performance Compagnie Aeree")
    st.plotly_chart(fig_airline, use_container_width=True)

    # Performance per Aeroporto
    st.header("Performance per Aeroporto")
    airport_perf = get_airport_performance()
    fig_airport = px.bar(airport_perf, x='airport', y=['delay_percentage', 'avg_delay'],
                        barmode='group', title="Performance Aeroporti")
    st.plotly_chart(fig_airport, use_container_width=True)

    # Ritardi Mensili
    st.header("Ritardi Mensili")
    monthly_delays = get_monthly_delays()
    fig_monthly = px.line(monthly_delays, x='date', y='delay',
                         title="Andamento Ritardi Mensili")
    st.plotly_chart(fig_monthly, use_container_width=True)

    # Mappa delle Destinazioni
    st.header("Mappa delle Destinazioni")
    fig_map, missing = plot_destinations_on_day_from_NYC_airport(conn, selected_month, selected_day, selected_airport)
    if fig_map:
        st.plotly_chart(fig_map, use_container_width=True)

    # Impatto del Vento
    st.header("Impatto del Vento sui Voli")
    fig_wind, correlation = plot_wind_impact_vs_air_time(conn)
    st.plotly_chart(fig_wind, use_container_width=True)
    st.write(f"Correlazione tra impatto del vento e tempo di volo: {correlation:.3f}")

    # Effetti Meteo
    st.header("Effetti Meteo sui Ritardi")
    fig_weather = analyze_weather_effects_plots()
    st.plotly_chart(fig_weather, use_container_width=True)

    # Ritardi di Partenza per Compagnia
    st.header("Ritardi di Partenza per Compagnia")
    fig_dep = plot_avg_departure_delay(conn)
    st.plotly_chart(fig_dep, use_container_width=True)

    # Distanza vs Ritardo di Arrivo
    st.header("Distanza vs Ritardo di Arrivo")
    fig_dist_delay, correlation = plot_distance_vs_arr_delay(conn)
    st.plotly_chart(fig_dist_delay, use_container_width=True)
    st.write(f"Correlazione tra distanza e ritardo di arrivo: {correlation:.3f}")

    conn.close()

if __name__ == "__main__":
    main() 