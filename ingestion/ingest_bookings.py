"""
À compléter : ingestion de l'entité `bookings`, découpée en 3 fonctions bronze/silver/gold
(même structure que `ingest_airports.py`, à utiliser comme modèle).
"""
from datetime import date

from common import fetch_csv, get_connection

BOOKING_COLS = [
    "passenger_id","flight_id","airport_id","seat_class",
    "amount","currency","booking_date"
]

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
            --CONSTRAINT fk_passenger_booking 
                --FOREIGN KEY (passenger_id) 
                --REFERENCES silver_passengers(passenger_id),
            flight_id VARCHAR,
            --CONSTRAINT fk_flight_booking 
                --FOREIGN KEY (flight_id) 
                --REFERENCES silver_flights(flight_id),
            airport_id VARCHAR,
            --CONSTRAINT fk_airport_booking 
                --FOREIGN KEY (airport_id) 
                --REFERENCES silver_airports(airport_id),
            seat_class VARCHAR,
            amount DOUBLE,
            currency VARCHAR,
            --CONSTRAINT fk_currency_booking 
                --FOREIGN KEY (currency) 
                --REFERENCES dim_currency(currency),
            booking_date DATE,
            booking_channel DATE,
            insert_timestamp TIMESTAMP,
            update_timestamp TIMESTAMP
        )
    """)


def ingest_silver(day: date = None, init: bool = False):
    # TODO : relire le fichier du jour depuis bronze/ et charger les lignes dans silver_bookings.
    """Relit le snapshot depuis bronze/ et l'upsert dans silver_airports."""
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
    update_cols = BOOKING_COLS
    set_clause = ", ".join(f"{c} = excluded.{c}" for c in update_cols)
    set_clause += ", update_timestamp = now()"

    con.execute(f"""
        INSERT INTO silver_bookings (
            booking_id, {", ".join(update_cols)}, insert_timestamp, update_timestamp
        )
        SELECT booking_id, {", ".join(update_cols)}, now(), now()
        FROM snapshot
        ON CONFLICT (booking_id) DO UPDATE SET {set_clause}
    """)

    # Les aéroports absents du snapshot du jour ont disparu de la source : on les désactive,
    # sans jamais les supprimer physiquement (des réservations passées peuvent déjà les référencer).
    # deleted_date prend la date du jour où la disparition est constatée, et ne bougera plus
    # ensuite (contrairement à update_timestamp, rafraîchi lui aussi ici, qui continuerait de
    # bouger si un jour ultérieur retouchait la ligne pour une autre raison).
    con.execute(
        """
        UPDATE silver_bookings SET update_timestamp = now()
        WHERE booking_id NOT IN (SELECT booking_id FROM snapshot)
        """
    )

    con.unregister("snapshot")
    con.close()


def ingest_gold():
    # TODO : à vérifier
    # - Ajouter les clés étrangères
    # - Ajouter amount_eur avec les calculs associés

    con = get_connection()

    # copie table des réservations
    con.execute("""
        CREATE OR REPLACE TABLE fact_booking AS
        SELECT
            sb.booking_id,
            sb.passenger_id,
            sb.flight_id,
            sb.airport_id,
            sb.seat_class,
            sb.amount,
            ROUND(sb.amount * dc.rate_to_eur, 2) AS amount_eur,
            sb.currency,
            sb.booking_date,
            sb.booking_channel,
            sb.insert_timestamp,
            sb.update_timestamp
        FROM silver_bookings AS sb
        LEFT JOIN dim_currency AS dc
            ON sb.currency = dc.currency
    """)

    con.close()


def init():
    ingest_bronze(init=True)
    ingest_silver(init=True)
    ingest_gold()
    print("Réservations (init) ingérés.")


if __name__ == "__main__":
    init()
