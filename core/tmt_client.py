"""
core/tmt_client.py
TinBhasha — TMT API Client
Handles all communication with the TMT translation API.

ARCHITECTURE: Adapter pattern with mock mode.
- MockTMTClient  → used during development (USE_MOCK=true in .env)
- RealTMTClient  → used for actual hackathon evaluation (USE_MOCK=false)
- get_client()   → single factory; the ONLY thing you call from outside this file
"""

import os
from abc import ABC, abstractmethod

import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Language codes — confirmed from TMT API documentation
# ---------------------------------------------------------------------------
LANGUAGES = {
    "english": "en",
    "nepali":  "ne",
    "tamang":  "tmg",   # confirmed from API docs (was "taj" before)
}


# ===========================================================================
# BASE (interface)
# ===========================================================================

class BaseTMTClient(ABC):
    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        ...


# ===========================================================================
# MOCK CLIENT
# ===========================================================================

class MockTMTClient(BaseTMTClient):
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text.strip():
            return text
        return f"[MOCK:{target_lang}] {text}"


# ===========================================================================
# REAL CLIENT — fully filled in from TMT API docs
# ===========================================================================

class RealTMTClient(BaseTMTClient):

    BASE_URL = "https://tmt.ilprl.ku.edu.np/lang-translate"

    def __init__(self):
        self.api_key = os.getenv("TMT_API_KEY")
        if not self.api_key:
            raise ValueError(
                "TMT_API_KEY not found. Please set it in your .env file."
            )

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text.strip():
            return text

        response = requests.post(
            self.BASE_URL,
            **self._build_request(text, source_lang, target_lang),
            timeout=10,
        )
        response.raise_for_status()
        return self._parse_response(response.json())

    def _build_request(self, text: str, source_lang: str, target_lang: str) -> dict:
        return {
            "json": {
                "text":     text,
                "src_lang": source_lang,
                "tgt_lang": target_lang,
            },
            "headers": {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type":  "application/json",
            },
        }

    def _parse_response(self, data: dict) -> str:
        if data.get("message_type") == "SUCCESS":
            return data["output"]
        raise ValueError(f"TMT API error: {data.get('message', 'Unknown error')}")


# ===========================================================================
# FACTORY
# ===========================================================================

def get_client() -> BaseTMTClient:
    use_mock = os.getenv("USE_MOCK", "true").strip().lower()
    if use_mock == "true":
        return MockTMTClient()
    return RealTMTClient()