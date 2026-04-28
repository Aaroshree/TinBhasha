# TinBhasha

> A file translation tool for `.csv`, `.docx`, and `.pdf` files across **English**, **Nepali**, and **Tamang** — built for the Google Trilingual Machine Translation (TMT) Hackathon 2026.

**Institute:** Kathmandu University &nbsp;|&nbsp; **Track:** File Translation Tool (Track 2)

---

## Team

| Name | Role | Contributions |
|------|------|---------------|
| Aaroshree Gautam | Backend Lead | TMT API client (adapter pattern + mock mode + retry logic), CSV handler with deduplication cache, DOCX handler with formatting preservation, PDF handler, test suite, sample files |
| Niharika | UI Lead | Streamlit UI, testing, README, demo video |

---

## Features

- Translate `.csv`, `.docx`, and `.pdf` files across 3 languages and 6 directions
- **Deduplication cache** — each unique value is translated only once, minimizing API calls
- **Formatting preservation** — paragraph-level bold, italic, font size, and color survive translation
- **Table translation** — tables inside DOCX and PDF files are fully translated
- **Retry logic** — automatically retries up to 3 times on API timeouts or rate limits
- **Mock mode** — develop and test without an API key
- Graceful handling of empty cells and blank paragraphs

---

## Supported Languages

| Language | Code |
|----------|------|
| English  | `en` |
| Nepali   | `ne` |
| Tamang   | `tmg` |

All 6 translation directions are supported: EN↔NE, EN↔TMG, NE↔TMG.

---

TinBhasha/
├── core/
│   ├── tmt_client.py        # TMT API wrapper (adapter pattern: mock + real)
│   ├── csv_handler.py       # CSV translation with deduplication cache
│   ├── docx_handler.py      # DOCX translation with formatting & table preservation
│   └── pdf_handler.py       # PDF translation with layout preservation
├── ui/
│   └── app.py               # Streamlit UI
├── tests/
│   ├── test_connection.py   # API client tests (no sample files required)
│   └── test_handlers.py     # CSV + DOCX + PDF end-to-end tests
├── samples/
│   ├── sample_english.csv / .docx / .pdf
│   ├── sample_nepali.csv / .docx / .pdf
│   └── sample_tamang.csv / .docx / .pdf
├── .env
├── requirements.txt
└── README.md

---

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/Aaroshree/TinBhasha.git
cd TinBhasha
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure environment**

Create a `.env` file in the project root:

```env
TMT_API_KEY=your_api_key_here
USE_MOCK=true
```

Set `USE_MOCK=false` once you have a real API key.

---

## Obtaining a TMT API Key

When the hackathon organizers provide TMT API documentation:

1. Update `BASE_URL` in `core/tmt_client.py` with the real endpoint
2. Update `_build_request()` and `_parse_response()` to match the API contract
3. Set `USE_MOCK=false` in `.env`
4. Run `python tests/test_connection.py` to verify

---

## Usage

### Translate a CSV file

```python
from core.csv_handler import translate_csv

translate_csv(
    input_path="samples/sample_english.csv",
    output_path="samples/sample_nepali.csv",
    source_lang="en",
    target_lang="ne",
)
```

Every cell in the file is translated. Repeated values are translated once and reused from cache.

### Translate a DOCX file

```python
from core.docx_handler import translate_docx

translate_docx(
    input_path="samples/sample_english.docx",
    output_path="samples/sample_nepali.docx",
    source_lang="en",
    target_lang="ne",
)
```

All paragraphs and tables are translated. Paragraph-level formatting (bold, italic, font size, color) is preserved.

### Translate a PDF file

```python
from core.pdf_handler import translate_pdf

translate_pdf(
    input_path="samples/sample_english.pdf",
    output_path="samples/sample_nepali.pdf",
    source_lang="en",
    target_lang="ne",
)
```

All text and tables are extracted, translated, and written to a new PDF with layout preserved.

---

## Running Tests

**Test the API client** (no sample files needed):

```bash
python tests/test_connection.py
```

Covers: EN→NE, NE→EN, EN→TMG, and empty string handling.

**Test file handlers end-to-end:**

```bash
python tests/test_handlers.py
```

**Expected output in mock mode:**
--- TinBhasha API Connection Test [MOCK MODE] ---
✓ English → Nepali:  'Hello'    = '[MOCK:ne] Hello'
✓ Nepali → English:  'नमस्ते'    = '[MOCK:en] नमस्ते'
✓ English → Tamang:  'Hello'    = '[MOCK:tmg] Hello'
✓ Empty string handled correctly
✓ All connection tests passed!

---

## Architecture

The TMT client uses the **adapter pattern** with two interchangeable implementations:

- **`MockTMTClient`** — returns simulated translations prefixed with `[MOCK:<lang>]`. No API key required. Useful for development and CI.
- **`RealTMTClient`** — calls the actual TMT API with automatic retry logic (up to 3 attempts with exponential backoff on timeouts and rate limits).

A `get_client()` factory reads the `USE_MOCK` environment variable and returns the appropriate client. The rest of the application only ever calls `get_client()`, so swapping between mock and real requires no code changes.

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `TMT_API_KEY` | Authentication key for the TMT API | Required in real mode |
| `USE_MOCK` | Use mock translations when `true` | `true` |

---

## Known Limitations

**Mixed-run formatting:** If a single paragraph contains multiple formatting runs (e.g., one bold word within normal text), formatting is flattened to the style of the first run. Paragraph-level formatting is fully preserved.

**PDF layout:** Complex multi-column PDFs may not perfectly preserve their original layout, as text is re-flowed into a single-column output.

---

## Track 2 Requirements

| Requirement | Status |
|-------------|--------|
| CSV file translation | ✅ Complete |
| DOCX file translation | ✅ Complete |
| PDF file translation | ✅ Complete |
| English ↔ Nepali | ✅ Complete |
| English ↔ Tamang | ✅ Complete |
| Nepali ↔ Tamang | ✅ Complete |
| All 6 translation directions | ✅ Complete |
| Formatting preservation | ✅ Complete |
| Table translation (DOCX + PDF) | ✅ Complete |
| Empty cell/paragraph handling | ✅ Complete |
| File size limit (1MB) | ✅ Complete |

## UI Guide

### Home Page
When you open TinBhasha you will see a welcome screen in English and Nepali. 
Click the **"Translate a file →"** button to go to the translate page.

### Translate Page
1. Select the **source language** (the language your file is in)
2. Select the **target language** (the language you want to translate to)
3. Upload your **CSV or DOCX** file
4. Click **"Translate File"**
5. Download your translated file using the **download button**

### Supported Files
- `.csv` — all cells are translated
- `.docx` — all paragraphs are translated (tables are not translated)

### How to Run
```bash
streamlit run ui/app.py
```

### Notes
- Maximum file size is 200MB
- Make sure source and target languages are different
---

## UI Guide

### Home Page
When you open TinBhasha you will see a welcome screen with the brand name, language pills, and a button to go to the translate page.

Click **"Translate a file →"** to go to the translate page.

### Translate Page
1. Select the **source language** (the language your file is in) from the language cards
2. Select the **target language** (the language you want to translate to)
3. Upload your **CSV, DOCX, or PDF** file — or click **"Use a sample file to try it out"**
4. Click **"Translate File"**
5. Wait for the progress bar to complete
6. Download your translated file using the **download button**

### How Each File Type is Translated

**CSV files:**
- Every cell in the file is translated
- Repeated values are translated only once and reused from cache

**DOCX files:**
- Every paragraph and table cell is translated
- Paragraph-level formatting is preserved

**PDF files:**
- All text and table content is extracted and translated
- Devanagari font support included for Nepali and Tamang output

### How to Run
```bash
streamlit run ui/app.py
```

### Notes
- Maximum file size is **1MB**
- Source and target languages must be different
- Translate button is disabled if the same language is selected on both sides

---

## How Mock Mode Was Used

Since the real TMT API key was not available at the start, we built the entire app using **Mock Mode** first.

- `USE_MOCK=true` → uses `MockTMTClient` which returns `[MOCK:ne] Hello` style output. No API key needed.
- `USE_MOCK=false` → uses `RealTMTClient` which calls the actual TMT API.

This allowed us to build and test the full UI, file handlers, and tests before receiving the API key. When the key arrived, only one line needed to change in the `.env` file.

---

## Day by Day Progress

| Day | Date | Task | Status |
|-----|------|------|--------|
| 1 | Apr 21 | Project scaffold, GitHub setup | ✅ Complete |
| 2 | Apr 22 | TMT client, CSV handler | ✅ Complete |
| 3 | Apr 22 | DOCX handler, test suite | ✅ Complete |
| 4 | Apr 22 | Sample files (3 languages × 3 formats) | ✅ Complete |
| 5 | Apr 23 | Streamlit UI with mock mode | ✅ Complete |
| 6 | Apr 24 | Connect UI to core, PDF support | ✅ Complete |
| 7 | Apr 26 | Bug fixes (Tamang code, sample button, retry logic) | ✅ Complete |
| 8 | Apr 28 | Final testing + README update | ✅ Complete |
| 9 | Apr 29 | Demo video | Pending |
| 10 | Apr 30 | Final review + submission | Pending |

---

*Built for Google TMT Hackathon 2026 — Kathmandu University*
