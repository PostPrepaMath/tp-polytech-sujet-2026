"""
À compléter : ingestion de l'entité `flights`, découpée en 3 fonctions bronze/silver/gold
(même structure que `ingest_airports.py`, à utiliser comme modèle).
"""
from datetime import date

from common import fetch_csv, get_connection

FLIGHT_COLS = [
    "flight_number", "airline", "origin_airport_id","destination_airport_id",
    "flight_date", "departure_time", "arrival_time", "aircraft_type"
]

def _snapshot_file(day: date = None, init: bool = False):
    if init:
        return "init", "flights.csv"
    assert day is not None
    return "2025-09", f"flights_{day.isoformat()}.csv"

def ingest_bronze(day: date = None, init: bool = False):
    # TODO : télécharger le snapshot flights du jour (ou de init/) vers bronze/.
    if init:
        subdir, filename =_snapshot_file(day,init)
        fetch_csv(subdir, filename)
    else:
        daydir = day.strftime("%Y-%m")
        dayfile = f"flights_{day.isoformat()}.csv"
        fetch_csv(daydir, dayfile)

def create_silver_table(con):
    # TODO : créer silver_flights (colonnes du CSV source + is_active + deleted_date
    # + insert_timestamp/update_timestamp, cf. ingest_airports.py).
    con.execute("""
        CREATE TABLE IF NOT EXISTS silver_flights(
            flight_id VARCHAR PRIMARY KEY,
            flight_number VARCHAR,
            airline VARCHAR,
            origin_airport_id VARCHAR,
            --CONSTRAINT fk_origin_airport 
                --FOREIGN KEY (origin_airport_id) 
                --REFERENCES silver_airports(airport_id),
            destination_airport_id VARCHAR,
            --CONSTRAINT fk_destination_airport 
                --FOREIGN KEY (destination_airport_id) 
                --REFERENCES silver_airports(airport_id),
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
    subdir, filename = _snapshot_file(day, init)
    df = fetch_csv(subdir, filename)  # déjà en cache local : pas de nouveau téléchargement
    snapshot_date = date(2025, 8, 31) if init else day

    df = df.copy()
    df["is_active"] = True

    con = get_connection()
    create_silver_table(con)
    con.register("snapshot", df)

    # Upsert : on insère les nouvelles lignes, on met à jour celles dont la clé existe déjà.
    # insert_timestamp n'apparaît PAS dans le SET du conflit : sur un conflit (ligne déjà
    # connue), on veut garder sa valeur d'origine, pas l'écraser. update_timestamp, lui, est
    # rafraîchi à chaque passage, qu'il y ait eu un vrai changement de valeur ou non.
    # deleted_date est remis à NULL sur un conflit : la ligne est présente dans le snapshot du
    # jour, donc active — si elle avait été désactivée puis réapparaissait (pas le cas dans ce
    # jeu de données, mais une vraie source pourrait le faire), elle redevient active proprement.
    update_cols = FLIGHT_COLS + ["is_active"]
    set_clause = ", ".join(f"{c} = excluded.{c}" for c in update_cols)
    set_clause += ", deleted_date = NULL, update_timestamp = now()"

    con.execute(f"""
        INSERT INTO silver_flights (
            flight_id, {", ".join(update_cols)}, deleted_date, insert_timestamp, update_timestamp
        )
        SELECT flight_id, {", ".join(update_cols)}, NULL, now(), now()
        FROM snapshot
        ON CONFLICT (flight_id) DO UPDATE SET {set_clause}
    """)

    # Les aéroports absents du snapshot du jour ont disparu de la source : on les désactive,
    # sans jamais les supprimer physiquement (des réservations passées peuvent déjà les référencer).
    # deleted_date prend la date du jour où la disparition est constatée, et ne bougera plus
    # ensuite (contrairement à update_timestamp, rafraîchi lui aussi ici, qui continuerait de
    # bouger si un jour ultérieur retouchait la ligne pour une autre raison).
    con.execute(
        """
        UPDATE silver_flights SET is_active = false, deleted_date = ?, update_timestamp = now()
        WHERE is_active = true AND flight_id NOT IN (SELECT flight_id FROM snapshot)
        """,
        [snapshot_date],
    )

    con.unregister("snapshot")
    con.close()


def ingest_gold():
    # TODO : à tester

    con = get_connection()

    # remarque : séparer la création et le copiage des données
    # puisque les commandes alter table + FK ne fonctionnent pas
    # sur duckdb

    # copie table des vols

    con.execute("""
        CREATE OR REPLACE TABLE dim_flight AS
        SELECT * FROM silver_flights
        WHERE is_active = TRUE
    """)

    con.close()


def init():
    ingest_bronze(init=True)
    ingest_silver(init=True)
    ingest_gold()
    print("Vols (init) ingérés.")


if __name__ == "__main__":
    init()
