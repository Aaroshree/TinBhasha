# TinBhasha

> A file translation tool for `.csv`, `.docx`, and `.pdf` files across **English**, **Nepali**, and **Tamang** — built for the Google Trilingual Machine Translation (TMT) Hackathon 2026.

**Institute:** Kathmandu University &nbsp;|&nbsp; **Track:** File Translation Tool (Track 2)  
**Live Demo:** https://tinbhasha-tzbyfthkos5r9h7semv4p2.streamlit.app/  
**Demo Video:** _coming soon — will be added before submission_

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
- **File preview** — view original and translated content directly in the Streamlit UI before download
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

## Project Structure

```
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
```

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
USE_MOCK=false
```

**4. Run the app**

```bash
streamlit run ui/app.py
```

---

## Architecture

TinBhasha is built around three design principles:

**1. Adapter Pattern (TMT Client)**  
The `core/tmt_client.py` defines a `BaseTMTClient` interface with two interchangeable implementations:
- `MockTMTClient` — returns `[MOCK:<lang>] text` with no API key needed. Used for development and CI.
- `RealTMTClient` — calls the live TMT API at `https://tmt.ilprl.ku.edu.np/lang-translate` with bearer token auth, automatic retry (3 attempts, exponential backoff), and structured error surfacing.

A `get_client()` factory reads `USE_MOCK` from `.env` and returns the right client. No other file knows which client is active.

**2. Deduplication Cache (All Handlers)**  
Before making any API calls, each handler collects all unique text values across the entire file, translates each exactly once, then maps results back. This keeps API calls equal to unique value count — not total cell/paragraph count.

**3. Format-Specific Handlers**  
- `csv_handler.py` — reads with pandas, applies cache via `df.map()`, writes UTF-8-BOM CSV
- `docx_handler.py` — preserves paragraph-level formatting by writing into the first run only, clears remaining runs, translates table cells separately
- `pdf_handler.py` — extracts structured blocks (text + tables) with pdfplumber, rebuilds with reportlab Platypus, supports Devanagari via NotoSans font registration

---

## Usage

### Translate a CSV file

```python
from core.csv_handler import translate_csv

translate_csv(
    input_path="samples/sample_english.csv",
    output_path="output.csv",
    source_lang="en",
    target_lang="ne",
)
```

### Translate a DOCX file

```python
from core.docx_handler import translate_docx

translate_docx(
    input_path="samples/sample_english.docx",
    output_path="output.docx",
    source_lang="en",
    target_lang="ne",
)
```

### Translate a PDF file

```python
from core.pdf_handler import translate_pdf

translate_pdf(
    input_path="samples/sample_english.pdf",
    output_path="output.pdf",
    source_lang="en",
    target_lang="ne",
)
```

---

## Running Tests

```bash
python tests/test_connection.py
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

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `TMT_API_KEY` | Authentication key for the TMT API | Required in real mode |
| `USE_MOCK` | Use mock translations when `true` | `true` |

---

## UI Guide

### Home Page
Click **"Translate a file →"** to go to the translate page.

### Translate Page
1. Select the **source language** from the language cards
2. Select the **target language**
3. Upload your **CSV, DOCX, or PDF** file — or click **"Use a sample file to try it out"**
4. Click **"Translate File"**
5. Wait for the progress bar to complete
6. Download your translated file using the **download button**

### Notes
- Maximum file size is **1MB**
- Source and target languages must be different
- Translate button is disabled if the same language is selected on both sides

---

## Known Limitations

- **Mixed-run formatting:** Formatting is flattened to the style of the first run in multi-format paragraphs.
- **PDF layout:** Complex multi-column PDFs may not perfectly preserve their original layout.
- **Punctuation:** Some punctuation marks may not be preserved after translation.
- **Tamang accuracy:** Tamang translation accuracy could not be fully verified as it is a low-resource language.

---
## Future Plans

- **Auto-detect file type** — automatically identify CSV, DOCX, or PDF and the languages English, Nepali, Tamang without manual selection

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
| 9 | Apr 29 | Demo video | ⏳ Pending |
| 10 | Apr 30 | Final review + submission | ⏳ Pending |

---

*Built for Google TMT Hackathon 2026 — Kathmandu University*