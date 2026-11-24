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