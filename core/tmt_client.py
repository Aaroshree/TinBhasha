"""
core/tmt_client.py
TinBhasha — TMT API Client
Handles all communication with the TMT translation API.

ARCHITECTURE: Adapter pattern with mock mode.
- MockTMTClient  → used during development (USE_MOCK=true in .env)
- RealTMTClient  → used for actual hackathon evaluation (USE_MOCK=false)
- get_client()   → single factory; the ONLY thing you call from outside this file

When the real TMT API docs arrive, ONLY edit the RealTMTClient section below.
Everything else in your pipeline stays untouched.
"""

import os
from abc import ABC, abstractmethod

import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Language codes
# "en" and "ne" are standard BCP-47 codes.
# "taj" is a placeholder for Tamang — CONFIRM from TMT API docs when received.
# ---------------------------------------------------------------------------
LANGUAGES = {
    "english": "en",
    "nepali":  "ne",
    "tamang":  "taj",   # TODO: confirm exact code from TMT docs
}


# ===========================================================================
# BASE (interface) — defines the contract every client must follow
# ===========================================================================

class BaseTMTClient(ABC):
    """Abstract base class. All translation clients must implement translate()."""

    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate a single string.

        Args:
            text:        The text to translate.
            source_lang: Language code, e.g. "en"
            target_lang: Language code, e.g. "ne"

        Returns:
            Translated string.
        """
        ...


# ===========================================================================
# MOCK CLIENT — returns fake translations; lets you build everything else now
# ===========================================================================

class MockTMTClient(BaseTMTClient):
    """
    Development stand-in. Returns labelled fake output so you can:
      - Build and test CSV/DOCX processors end-to-end
      - Verify that empty strings, whitespace, and special characters are handled
      - Demonstrate the full UI flow before the real API is available

    Output format:  [MOCK:{target_lang}] <original text>
    Example:        [MOCK:ne] Hello World
    """

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text.strip():
            return text  # preserve empty / whitespace-only strings as-is
        return f"[MOCK:{target_lang}] {text}"


# ===========================================================================
# REAL CLIENT — fill this in when TMT API docs arrive
# ===========================================================================

class RealTMTClient(BaseTMTClient):
    """
    Talks to the actual TMT API provided by the hackathon.

    ┌─────────────────────────────────────────────────────────────┐
    │  TODO — fill in when you receive the TMT API documentation  │
    │                                                             │
    │  1. Replace BASE_URL with the real endpoint                 │
    │  2. Update _build_request() with the correct auth method    │
    │     (header token vs query-param key vs OAuth, etc.)        │
    │  3. Update _parse_response() to match the real JSON shape   │
    │  4. Confirm LANGUAGES["tamang"] code above                  │
    └─────────────────────────────────────────────────────────────┘
    """

    # ------------------------------------------------------------------
    # 1. BASE URL — replace with real TMT endpoint
    # ------------------------------------------------------------------
    BASE_URL = "https://TODO_TMT_ENDPOINT"   # ← replace this

    def __init__(self):
        self.api_key = os.getenv("TMT_API_KEY")
        if not self.api_key:
            raise ValueError(
                "TMT_API_KEY not found. Please set it in your .env file."
            )

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text.strip():
            return text

        response = requests.post(            # ← change to .get() if TMT uses GET
            self.BASE_URL,
            **self._build_request(text, source_lang, target_lang),
            timeout=10,
        )
        response.raise_for_status()
        return self._parse_response(response.json())

    # ------------------------------------------------------------------
    # 2. REQUEST BUILDER — update auth & payload shape to match TMT docs
    # ------------------------------------------------------------------
    def _build_request(
        self, text: str, source_lang: str, target_lang: str
    ) -> dict:
        """
        Returns kwargs for requests.post() / requests.get().

        Current shape is a GUESS — rewrite to match real TMT docs.
        Common patterns:
          - JSON body:   return {"json": {...}, "headers": {...}}
          - Form params: return {"data": {...}, "headers": {...}}
          - Query params (GET): return {"params": {...}}
        """
        return {
            "json": {                        # ← adjust field names / structure
                "text":        text,
                "source_lang": source_lang,
                "target_lang": target_lang,
            },
            "headers": {
                "Authorization": f"Bearer {self.api_key}",   # ← or "x-api-key", etc.
                "Content-Type":  "application/json",
            },
        }

    # ------------------------------------------------------------------
    # 3. RESPONSE PARSER — update to match the real TMT JSON structure
    # ------------------------------------------------------------------
    def _parse_response(self, data: dict) -> str:
        """
        Extracts the translated string from the API response.

        Current path is a GUESS — update to match real TMT docs.
        Example shapes you might see:
          data["translation"]
          data["result"]["text"]
          data["translations"][0]["output"]
        """
        return data["translation"]           # ← replace with real path


# ===========================================================================
# FACTORY — the ONLY function the rest of your app should import
# ===========================================================================

def get_client() -> BaseTMTClient:
    """
    Returns the right client based on the USE_MOCK env variable.

    .env for development:   USE_MOCK=true
    .env for hackathon eval: USE_MOCK=false

    Usage (from anywhere in your project):
        from core.tmt_client import get_client
        translator = get_client()
        result = translator.translate("Hello", "en", "ne")
    """
    use_mock = os.getenv("USE_MOCK", "true").strip().lower()
    if use_mock == "true":
        return MockTMTClient()
    return RealTMTClient()