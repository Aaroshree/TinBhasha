"""
tests/test_connection.py
TinBhasha — API Connection Test
Run this on Day 1 when you receive the real TMT API key.

What this tests:
  - API key is loaded correctly
  - English  → Nepali translation works
  - Nepali   → English translation works
  - English  → Tamang translation works  (confirms "taj" code is correct)
  - Empty string is handled without making an API call
  - Mock mode is clearly identified in output

No sample files required. Fast to run.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.tmt_client import get_client


def test_english_to_nepali():
    """Translate a simple English word to Nepali."""
    client = get_client()
    result = client.translate("Hello", source_lang="en", target_lang="ne")
    assert result, "Translation came back empty!"
    print(f"  ✓ English → Nepali:  'Hello' = '{result}'")


def test_nepali_to_english():
    """Translate a Nepali word to English."""
    client = get_client()
    result = client.translate("नमस्ते", source_lang="ne", target_lang="en")
    assert result, "Translation came back empty!"
    print(f"  ✓ Nepali  → English: 'नमस्ते' = '{result}'")


def test_english_to_tamang():
    """
    Translate a simple English word to Tamang.
    This will confirm whether the language code "taj" is correct.
    If this fails on the real API, update LANGUAGES["tamang"] in tmt_client.py.
    """
    client = get_client()
    result = client.translate("Hello", source_lang="en", target_lang="taj")
    assert result, "Translation came back empty!"
    print(f"  ✓ English → Tamang:  'Hello' = '{result}'")


def test_empty_string():
    """Empty strings should be returned as-is without an API call."""
    client = get_client()
    result = client.translate("   ", source_lang="en", target_lang="ne")
    assert result.strip() == "", f"Expected empty string back, got: '{result}'"
    print(f"  ✓ Empty string handled correctly")


if __name__ == "__main__":
    use_mock = os.getenv("USE_MOCK", "true").strip().lower()
    mode = "MOCK MODE" if use_mock == "true" else "LIVE API MODE"

    print(f"\n--- TinBhasha API Connection Test [{mode}] ---\n")

    test_english_to_nepali()
    test_nepali_to_english()
    test_english_to_tamang()
    test_empty_string()

    print(f"\n✓ All connection tests passed!")
    if use_mock == "true":
        print("  (Running in mock mode — set USE_MOCK=false in .env to test the real API)")