import sqlite3

# Connessione al database
conn = sqlite3.connect("C:/Users/fabio/OneDrive/Desktop/vu uni/data engeneering/group project flights/Flights/Data/flights_database.db")
cur = conn.cursor()

# Esegui la query
query = """
    UPDATE planes_copy
    SET speed = (
        SELECT AVG(distance / (air_time / 60.0))
        FROM flights
        WHERE flights.tailnum = planes_copy.tailnum
          AND air_time IS NOT NULL
          AND air_time > 0
          AND distance IS NOT NULL
          AND distance > 0
    )
    WHERE EXISTS (
        SELECT 1
        FROM flights
        WHERE flights.tailnum = planes_copy.tailnum
          AND air_time IS NOT NULL
          AND air_time > 0
          AND distance IS NOT NULL
          AND distance > 0
    );
"""

cur.execute(query)

# Commit delle modifiche per salvare nel DB
conn.commit()

# Verifica dei risultati
check_query = """
    SELECT tailnum, speed
    FROM planes_copy
    WHERE speed IS NOT NULL
    ORDER BY speed DESC
    LIMIT 10;
"""
cur.execute(check_query)
rows = cur.fetchall()

# Stampa i risultati
for row in rows:
    print(row)

# Chiude la connessione
conn.close()
