# constants.py
"""
Module that stores global constants used throughout the project.
"""

DATABASE_PATH = "../Data/flights_database.db"  # Path to your SQLite database
NYC_AIRPORTS = ["JFK", "LGA", "EWR"]   # NYC Airport codes

MISSING_AIRPORTS = [
    ("SJU", "Luis Muñoz Marín International", 18.4360, -66.0058, 9, -4, "N", "America/Puerto_Rico"),
    ("STT", "Cyril E. King Airport", 18.3373, -64.9734, 23, -4, "N", "America/St_Thomas"),
    ("BQN", "Rafael Hernández International", 18.4949, -67.1294, 237, -4, "N", "America/Puerto_Rico"),
    ("PSE", "Mercedita International", 18.0083, -66.5630, 10, -4, "N", "America/Puerto_Rico"),
]
# Distance-related constants
ERROR_MARGIN_KM = 2.0
MILES_TO_KM = 1.60934
R = 6371  # Earth radius in kilometers

