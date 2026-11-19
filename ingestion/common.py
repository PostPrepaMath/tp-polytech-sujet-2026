"""
Utilitaires partagés par les scripts d'ingestion. `get_connection` est fourni tel quel ;
`fetch_csv` est à vous d'implémenter (cf. TODO)
"""
import os

import duckdb
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRONZE_DIR = os.path.join(BASE_DIR, "bronze")
DB_PATH = os.path.join(BASE_DIR, "warehouse.duckdb")
RAW_BASE = "https://raw.githubusercontent.com/kevinl75/tp-polytech-dataset/main"

def fetch_csv(subdir: str, filename: str) -> pd.DataFrame:
    """Doit renvoyer le contenu de <subdir>/<filename> sous forme de DataFrame pandas."""
    # TODO : le fichier CSV source est disponible à l'URL f"{RAW_BASE}/{subdir}/{filename}".
    # - S'il n'existe pas déjà en local dans BRONZE_DIR/<subdir>/<filename>, téléchargez-le et
    #   écrivez-le tel quel sur disque à cet emplacement (créez les dossiers nécessaires).
    # - Eviter si possible de le retéléchargez s'il est déjà présent.

    # création du dossier bronze s'il n'existe pas
    if not os.path.isdir(BRONZE_DIR):
        os.mkdir(BRONZE_DIR)

    local_path = os.path.join(BRONZE_DIR, subdir)

    # création du dossier s'il n'existe pas
    if not os.path.isdir(local_path):
        os.mkdir(local_path)

    local_file = os.path.join(local_path, filename)

    # télechargement du fichier s'il n'existe pas
    if not os.path.isfile(local_file):
        url = os.path.join(RAW_BASE, subdir, filename)
        df = pd.read_csv(url)
        df.to_csv(local_file, index=False)

    return pd.read_csv(local_file)


def get_connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(DB_PATH)

# fetch_csv("2025-09","airports_2025-09-01.csv")
# fetch_csv("2025-09","bookings_2025-09-01.csv")
# fetch_csv("2025-09","flights_2025-09-01.csv")
# fetch_csv("2025-09","passengers_en_2025-09-01.csv")
# fetch_csv("2025-09","passengers_fr_2025-09-01.csv")