"""
core/csv_handler.py
TinBhasha — CSV Translation Handler
Reads a .csv file, translates every cell, writes a new translated .csv file.
"""

import pandas as pd
from core.tmt_client import TMTClient


def translate_csv(input_path: str, output_path: str, source_lang: str, target_lang: str) -> str:
    """
    Translate all cells in a CSV file.

    Args:
        input_path:  Path to the original .csv file
        output_path: Path where translated .csv will be saved
        source_lang: e.g. "en"
        target_lang: e.g. "ne"

    Returns:
        output_path — the path of the saved translated file
    """
    # Step 1 — read the csv
    df = pd.read_csv(input_path)

    # Step 2 — create the TMT client
    client = TMTClient()

    # Step 3 — translate every cell
    def translate_cell(cell):
        if pd.isna(cell):
            return cell                        # skip empty cells
        return client.translate(str(cell), source_lang, target_lang)

    df = df.applymap(translate_cell)

    # Step 4 — save the translated csv
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    return output_path