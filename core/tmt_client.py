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
import time
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
    "tamang":  "tmg",
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
# REAL CLIENT
# ===========================================================================

class RealTMTClient(BaseTMTClient):

    BASE_URL    = "https://tmt.ilprl.ku.edu.np/lang-translate"
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(self):
        self.api_key = os.getenv("TMT_API_KEY")
        if not self.api_key:
            raise ValueError(
                "TMT_API_KEY not found. Please set it in your .env file."
            )

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text.strip():
            return text

        last_error = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = requests.post(
                    self.BASE_URL,
                    **self._build_request(text, source_lang, target_lang),
                    timeout=10,
                )

                if response.status_code in (429, 503):
                    time.sleep(self.RETRY_DELAY * attempt)
                    continue

                response.raise_for_status()
                return self._parse_response(response.json())

            except requests.exceptions.Timeout:
                last_error = f"Request timed out on attempt {attempt}"
                time.sleep(self.RETRY_DELAY * attempt)

            except requests.exceptions.ConnectionError:
                last_error = f"Connection error on attempt {attempt}"
                time.sleep(self.RETRY_DELAY * attempt)

            except requests.exceptions.RequestException as e:
                last_error = str(e)
                time.sleep(self.RETRY_DELAY * attempt)

        raise ValueError(
            f"TMT API failed after {self.MAX_RETRIES} attempts. Last error: {last_error}"
        )

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