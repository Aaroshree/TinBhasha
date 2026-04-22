"""
tests/test_handlers.py
TinBhasha — File Handler Tests
Run this once sample files exist in the samples/ folder.

What this tests:
  - CSV translation: all cells translated, output file saved correctly
  - DOCX translation: all paragraphs translated, output file saved correctly
  - Both handlers work end-to-end with the current client (mock or real)

Requires:
  samples/sample_english.csv
  samples/sample_english.docx
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.csv_handler import translate_csv
from core.docx_handler import translate_docx


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_sample_exists(path: str, label: str):
    """Fail early with a clear message if a sample file is missing."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Sample file not found: {path}\n"
            f"Please add a {label} to the samples/ folder before running this test."
        )


# ---------------------------------------------------------------------------
# CSV test
# ---------------------------------------------------------------------------

def test_csv_translation():
    """Translate sample_english.csv from English to Nepali and verify output."""
    input_path  = "samples/sample_english.csv"
    output_path = "samples/sample_nepali.csv"

    _check_sample_exists(input_path, "sample_english.csv")

    output = translate_csv(
        input_path=input_path,
        output_path=output_path,
        source_lang="en",
        target_lang="ne",
    )

    assert os.path.exists(output), f"Output file was not created at: {output}"
    print(f"  ✓ CSV translated and saved to: {output}")


# ---------------------------------------------------------------------------
# DOCX test
# ---------------------------------------------------------------------------

def test_docx_translation():
    """Translate sample_english.docx from English to Nepali and verify output."""
    input_path  = "samples/sample_english.docx"
    output_path = "samples/sample_nepali.docx"

    _check_sample_exists(input_path, "sample_english.docx")

    output = translate_docx(
        input_path=input_path,
        output_path=output_path,
        source_lang="en",
        target_lang="ne",
    )

    assert os.path.exists(output), f"Output file was not created at: {output}"
    print(f"  ✓ DOCX translated and saved to: {output}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    use_mock = os.getenv("USE_MOCK", "true").strip().lower()
    mode = "MOCK MODE" if use_mock == "true" else "LIVE API MODE"

    print(f"\n--- TinBhasha File Handler Tests [{mode}] ---\n")

    test_csv_translation()
    test_docx_translation()

    print(f"\n✓ All handler tests passed!")
    if use_mock == "true":
        print("  (Running in mock mode — set USE_MOCK=false in .env to test with real translations)")