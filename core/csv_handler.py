"""
core/csv_handler.py
TinBhasha — CSV Translation Handler
Reads a .csv file, translates every cell, writes a new translated .csv file.

Fixes applied:
  1. Uses get_client() instead of removed TMTClient()
  2. df.applymap() → df.map() (pandas 2.1+ compatibility, no deprecation warning)
  3. Deduplication: collects all unique cell values first, translates each once,
     then maps results back — drastically reduces API calls on real-world CSVs
"""

import pandas as pd
from core.tmt_client import get_client


def translate_csv(
    input_path: str,
    output_path: str,
    source_lang: str,
    target_lang: str,
) -> str:
    """
    Translate all cells in a CSV file.

    Uses deduplication: each unique cell value is translated exactly once,
    regardless of how many times it appears in the file. This keeps API call
    count equal to the number of UNIQUE values, not total cells.

    Args:
        input_path:  Path to the original .csv file.
        output_path: Path where the translated .csv will be saved.
        source_lang: e.g. "en"
        target_lang: e.g. "ne"

    Returns:
        output_path — the path of the saved translated file.
    """
    # Step 1 — read the csv
    df = pd.read_csv(input_path)

    # Step 2 — get the right client (mock or real, depending on .env)
    client = get_client()

    # Step 3 — collect all unique, non-empty cell values across the entire df
    unique_values = set()
    for col in df.columns:
        for val in df[col]:
            if not pd.isna(val) and str(val).strip():
                unique_values.add(str(val))

    # Step 4 — translate each unique value exactly once, build a lookup dict
    # Example: {"Hello": "[MOCK:ne] Hello", "World": "[MOCK:ne] World"}
    translation_cache = {}
    for value in unique_values:
        translation_cache[value] = client.translate(value, source_lang, target_lang)
           

    # Step 5 — map translations back onto the dataframe (no extra API calls)
    def translate_cell(cell):
        if pd.isna(cell):
            return cell                         # preserve empty cells as-is
        return translation_cache.get(str(cell), str(cell))

    df = df.map(translate_cell)                 # pandas 2.1+ compatible

    # Step 6 — save the translated csv
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    return output_path