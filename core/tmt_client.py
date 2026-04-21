"""
core/tmt_client.py
TinBhasha — TMT API Client
Handles all communication with the TMT translation API.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Language codes for our 3 supported languages
LANGUAGES = {
    "english": "en",
    "nepali":  "ne",
    "tamang":  "taj",  # we will confirm this code when API docs arrive
}

BASE_URL = "https://translation.googleapis.com/language/translate/v2"


class TMTClient:
    """Wrapper around the TMT API."""

    def __init__(self):
        self.api_key = os.getenv("TMT_API_KEY")
        if not self.api_key:
            raise ValueError("TMT_API_KEY not found. Please set it in your .env file.")

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate a single string.

        Args:
            text:        The text to translate.
            source_lang: e.g. "en"
            target_lang: e.g. "ne"

        Returns:
            Translated string.
        """
        if not text.strip():
            return text  # don't waste API calls on empty strings

        params = {
            "q": text,
            "source": source_lang,
            "target": target_lang,
            "key": self.api_key,
            "format": "text",
        }

        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        return data["data"]["translations"][0]["translatedText"]