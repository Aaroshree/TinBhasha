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