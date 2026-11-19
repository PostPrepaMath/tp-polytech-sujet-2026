"""
À compléter : ingestion de l'entité `bookings`, découpée en 3 fonctions bronze/silver/gold
(même structure que `ingest_airports.py`, à utiliser comme modèle).
"""
from datetime import date

from common import fetch_csv, get_connection

# à vérifier
def _snapshot_file(day: date = None, init: bool = False):
    if init:
        return "init", "bookings.csv"
    assert day is not None
    return "2025-09", f"bookings_{day.isoformat()}.csv"

# à vérifier
def ingest_bronze(day: date = None, init: bool = False):
    # TODO : télécharger le fichier bookings du jour (ou de init/) vers bronze/.
    if init:
        subdir, filename =_snapshot_file(day,init)
        fetch_csv(subdir, filename)
    else:
        daydir = day.strftime("%Y-%m")
        dayfile = f"bookings_{day.isoformat()}.csv"
        fetch_csv(daydir, dayfile)

# à vérifier
def create_silver_table(con):
    # TODO : créer silver_bookings (colonnes du CSV source + insert_timestamp/update_timestamp, cf. ingest_airports.py).
    con.execute("""
        CREATE TABLE IF NOT EXISTS silver_bookings (
            booking_id VARCHAR PRIMARY KEY,
            passenger_id VARCHAR,
            CONSTRAINT fk_passenger_booking 
                FOREIGN KEY (passenger_id) 
                REFERENCES silver_passengers(passenger_id),
            flight_id VARCHAR,
            CONSTRAINT fk_flight_booking 
                FOREIGN KEY (flight_id) 
                REFERENCES silver_flights(flight_id),
            airport_id VARCHAR,
            CONSTRAINT fk_airport_booking 
                FOREIGN KEY (airport_id) 
                REFERENCES silver_airports(airport_id),
            seat_class VARCHAR,
            amount DOUBLE,
            currency VARCHAR,
            CONSTRAINT fk_currency_booking 
                FOREIGN KEY (currency) 
                REFERENCES dim_currency(currency),
            booking_date DATE,
            booking_channel DATE,
            insert_timestamp TIMESTAMP,
            update_timestamp TIMESTAMP
        )
    """)


def ingest_silver(day: date = None, init: bool = False):
    # TODO : relire le fichier du jour depuis bronze/ et charger les lignes dans silver_bookings.
    raise NotImplementedError


def ingest_gold():
    # TODO : reconstruire la/les table(s) de gold avec les données booking à partir de silver_bookings. 
    raise NotImplementedError


def init():
    ingest_bronze(init=True)
    ingest_silver(init=True)
    ingest_gold()
    print("Réservations (init) ingérés.")


if __name__ == "__main__":
    init()
