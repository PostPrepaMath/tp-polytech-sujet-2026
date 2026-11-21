"""
À compléter : ingestion de l'entité `passengers`, découpée en 3 fonctions bronze/silver/gold
(même structure que `ingest_airports.py`, à utiliser comme modèle).
"""
import pandas as pd
from datetime import date


from common import fetch_csv, get_connection

DICO_EN_FR = {
    "id_passager": "passenger_id",
    "prenom": "first_name",
    "nom": "last_name",
    "genre": "gender",
    "nationalite": "nationality",
    "email": "email",
    "date_naissance": "birth_date",
    "date_inscription": "signup_date"
}

PASSENGER_COLS = ["first_name","last_name","gender","nationality","email","birth_date","signup_date"]

# à vérifier
def _snapshot_file_fr(day: date = None, init: bool = False):
    if init:
        return "init", "passengers_fr.csv"
    assert day is not None
    return "2025-09", f"passengers_fr_{day.isoformat()}.csv"

# à vérifier
def _snapshot_file_en(day: date = None, init: bool = False):
    if init:
        return "init", "passengers_en.csv"
    assert day is not None
    return "2025-09", f"passengers_en_{day.isoformat()}.csv"

# à vérifier
def ingest_bronze(day: date = None, init: bool = False):
    # TODO : télécharger les deux snapshots (EN et FR) du jour (ou de init/) vers bronze/.
    if init:
        subdir_fr, filename_fr =_snapshot_file_fr(day,init)
        subdir_en, filename_en =_snapshot_file_en(day,init)
        fetch_csv(subdir_fr, filename_fr)
        fetch_csv(subdir_en, filename_en)
    else:
        daydir = day.strftime("%Y-%m")
        dayfile_fr = f"passengers_fr_{day.isoformat()}.csv"
        dayfile_en = f"passengers_en_{day.isoformat()}.csv"
        fetch_csv(daydir, dayfile_fr)
        fetch_csv(daydir, dayfile_en)

# à vérifier
def create_silver_table(con):
    # TODO : créer silver_passengers avec un schéma de table UNIQUE
    # + is_active + deleted_date + insert_timestamp/update_timestamp (cf. ingest_airports.py).
    con.execute("""
        CREATE TABLE IF NOT EXISTS silver_passengers(
            passenger_id VARCHAR PRIMARY KEY,
            first_name VARCHAR,
            last_name VARCHAR,
            gender VARCHAR,
            nationality VARCHAR,
            email VARCHAR,
            birth_date DATE,
            signup_date DATE,
            is_active BOOLEAN,
            deleted_date DATE,
            insert_timestamp TIMESTAMP,
            update_timestamp TIMESTAMP
        )
    """)


def ingest_silver(day: date = None, init: bool = False):
    # TODO : chargement de la données dans dans silver_passengers par passenger_id
    """Relit le snapshot depuis bronze/ et l'upsert dans silver_airports."""
    subdir_fr, filename_fr = _snapshot_file_fr(day, init)
    subdir_en, filename_en = _snapshot_file_en(day, init)
    df_fr = fetch_csv(subdir_fr, filename_fr)  # déjà en cache local : pas de nouveau téléchargement
    df_en = fetch_csv(subdir_en, filename_en)

    # Concaténation des tableaux français-anglais en anglais
    df_fr.rename(columns=DICO_EN_FR, inplace=True)

    df_fr["birth_date"] = pd.to_datetime(
        df_fr["birth_date"],
        format="%d/%m/%Y"
    ).dt.strftime("%Y-%m-%d")

    df_fr["signup_date"] = pd.to_datetime(
            df_fr["signup_date"],
            format="%d/%m/%Y"
    ).dt.strftime("%Y-%m-%d")

    df = pd.concat([df_fr, df_en], ignore_index=True)

    snapshot_date = date(2025, 8, 31) if init else day

    df = df.copy()
    df["is_active"] = True

    con = get_connection()
    create_silver_table(con)
    con.register("snapshot", df)
    print(con.execute("SELECT * FROM snapshot").fetchdf())

    # Upsert : on insère les nouvelles lignes, on met à jour celles dont la clé existe déjà.
    # insert_timestamp n'apparaît PAS dans le SET du conflit : sur un conflit (ligne déjà
    # connue), on veut garder sa valeur d'origine, pas l'écraser. update_timestamp, lui, est
    # rafraîchi à chaque passage, qu'il y ait eu un vrai changement de valeur ou non.
    # deleted_date est remis à NULL sur un conflit : la ligne est présente dans le snapshot du
    # jour, donc active — si elle avait été désactivée puis réapparaissait (pas le cas dans ce
    # jeu de données, mais une vraie source pourrait le faire), elle redevient active proprement.
    update_cols = PASSENGER_COLS + ["is_active"]
    set_clause = ", ".join(f"{c} = excluded.{c}" for c in update_cols)
    set_clause += ", deleted_date = NULL, update_timestamp = now()"

    con.execute(f"""
        INSERT INTO silver_passengers (
            passenger_id, {", ".join(update_cols)}, deleted_date, insert_timestamp, update_timestamp
        )
        SELECT passenger_id, {", ".join(update_cols)}, NULL, now(), now()
        FROM snapshot
        ON CONFLICT (passenger_id) DO UPDATE SET {set_clause}
    """)
    print("Insertion de passager réussie")

    # Les aéroports absents du snapshot du jour ont disparu de la source : on les désactive,
    # sans jamais les supprimer physiquement (des réservations passées peuvent déjà les référencer).
    # deleted_date prend la date du jour où la disparition est constatée, et ne bougera plus
    # ensuite (contrairement à update_timestamp, rafraîchi lui aussi ici, qui continuerait de
    # bouger si un jour ultérieur retouchait la ligne pour une autre raison).
    con.execute(
        """
        UPDATE silver_passengers SET is_active = false, deleted_date = ?, update_timestamp = now()
        WHERE is_active = true AND passenger_id NOT IN (SELECT passenger_id FROM snapshot)
        """,
        [snapshot_date],
    )
    print("Update des passagers réussie")

    con.unregister("snapshot")
    con.close()


def ingest_gold():
    # TODO : reconstruire la/les table(s) de gold avec les données passengers à partir de silver_passengers
    raise NotImplementedError


def init():
    ingest_bronze(init=True)
    ingest_silver(init=True)
    ingest_gold()
    print("Passagers (init) ingérés.")


if __name__ == "__main__":
    init()
