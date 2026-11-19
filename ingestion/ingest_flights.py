"""
À compléter : ingestion de l'entité `flights`, découpée en 3 fonctions bronze/silver/gold
(même structure que `ingest_airports.py`, à utiliser comme modèle).
"""
from datetime import date

from common import fetch_csv, get_connection

# à vérifier
def _snapshot_file(day: date = None, init: bool = False):
    if init:
        return "init", "flights.csv"
    assert day is not None
    return "2025-09", f"flights_{day.isoformat()}.csv"

# à vérifier
def ingest_bronze(day: date = None, init: bool = False):
    # TODO : télécharger le snapshot flights du jour (ou de init/) vers bronze/.
    if init:
        subdir, filename =_snapshot_file(day,init)
        fetch_csv(subdir, filename)
    else:
        daydir = day.strftime("%Y-%m")
        dayfile = f"flights_{day.isoformat()}.csv"
        fetch_csv(daydir, dayfile)

# à vérifier
def create_silver_table(con):
    # TODO : créer silver_flights (colonnes du CSV source + is_active + deleted_date
    # + insert_timestamp/update_timestamp, cf. ingest_airports.py).
    con.execute("""
        CREATE TABLE IF NOT EXISTS silver_flights(
            filght_id VARCHAR PRIMARY KEY,
            filght_num VARCHAR,
            airline VARCHAR,
            origin_airport_id VARCHAR,
            CONSTRAINT fk_origin_airport 
                FOREIGN KEY (origin_airport) 
                REFERENCES silver_airports(airport_id),
            destination_airport_id VARCHAR,
            CONSTRAINT fk_destination_airport 
                FOREIGN KEY (destination_airport) 
                REFERENCES silver_airports(airport_id),
            flight_date DATE,
            departure_time TIME,
            arrival_time TIME,
            aircraft_type VARCHAR,
            is_active BOOLEAN,
            deleted_date DATE,
            insert_timestamp TIMESTAMP,
            update_timestamp TIMESTAMP
        )
    """)


def ingest_silver(day: date = None, init: bool = False):
    # TODO : chargement de la données dans silver_flights par flight_id 
    raise NotImplementedError


def ingest_gold():
    # TODO : reconstruire la/les table(s) de gold avec les données flights à partir de silver_flights
    raise NotImplementedError


def init():
    ingest_bronze(init=True)
    ingest_silver(init=True)
    ingest_gold()
    print("Vols (init) ingérés.")


if __name__ == "__main__":
    init()
