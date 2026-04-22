"""
tests/test_connection.py
TinBhasha — Day 1 connection test
Run this once you have the real API key to confirm everything works.
"""

import sys
import os

# This lets Python find the core/ folder
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.tmt_client import TMTClient

def test_english_to_nepali():
    """Test: translate a simple English word to Nepali."""
    client = TMTClient()
    result = client.translate("Hello", source_lang="en", target_lang="ne")
    print(f"English → Nepali: 'Hello' = '{result}'")
    assert result, "Translation came back empty!"
    print("✓ English to Nepali works!")

def test_nepali_to_english():
    """Test: translate a Nepali word back to English."""
    client = TMTClient()
    result = client.translate("नमस्ते", source_lang="ne", target_lang="en")
    print(f"Nepali → English: 'नमस्ते' = '{result}'")
    assert result, "Translation came back empty!"
    print("✓ Nepali to English works!")

if __name__ == "__main__":
    print("--- TinBhasha API Connection Test ---")
    test_english_to_nepali()
    test_nepali_to_english()
    print("\n✓ All tests passed! API is connected and working.")

def test_csv_translation():
    """Test: translate sample_english.csv from English to Nepali."""
    from core.csv_handler import translate_csv

    output = translate_csv(
        input_path="samples/sample_english.csv",
        output_path="samples/sample_nepali.csv",
        source_lang="en",
        target_lang="ne",
    )
    print(f"✓ Translated CSV saved to: {output}")

if __name__ == "__main__":
    print("--- TinBhasha CSV Translation Test ---")
    test_csv_translation()

def test_docx_translation():
    """Test: translate sample_english.docx from English to Nepali."""
    from core.docx_handler import translate_docx

    output = translate_docx(
        input_path="samples/sample_english.docx",
        output_path="samples/sample_nepali.docx",
        source_lang="en",
        target_lang="ne",
    )
    print(f"✓ Translated DOCX saved to: {output}")

if __name__ == "__main__":
    print("--- TinBhasha DOCX Translation Test ---")
    test_docx_translation()