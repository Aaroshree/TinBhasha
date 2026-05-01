# TinBhasha

> A file translation tool for `.csv`, `.docx`, and `.pdf` files across **English**, **Nepali**, and **Tamang** — built for the Google Trilingual Machine Translation (TMT) Hackathon 2026.

**Institute:** Kathmandu University &nbsp;|&nbsp; **Track:** File Translation Tool (Track 2)  
**Live Demo:** https://tinbhasha-tzbyfthkos5r9h7semv4p2.streamlit.app/ 
 **GitHub Release:** 
**Demo Video:** _coming soon — will be added before submission_

---
## Why TinBhasha?
Tamang is a low-resource language spoken by over 1.5 million people in Nepal, yet digital tools for reading, writing, or translating Tamang are almost nonexistent. Nepali, while more resourced, still faces significant barriers in document-level translation for everyday users. TinBhasha was built to lower these barriers — allowing anyone to upload a real document and get a translated version in seconds, without any technical knowledge.TinBhasha is designed around the TMT API's sentence-level translation architecture — each handler segments documents into individual sentences before passing them through the API, ensuring compatibility with all three supported language pairs: English, Nepali, and Tamang. By building directly on the TMT system's trilingual capabilities, TinBhasha extends its reach beyond raw text input, making machine translation accessible through the everyday file formats people already use.

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
- **Drag and drop** — drag and drop files directly onto the upload area
- **Sample file picker** — built-in samples for all 3 languages × 3 formats
- **Language swap** — instantly swap source and target languages with one click
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
## Deployment

### Streamlit Cloud (one click)
1. Fork the repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set `TMT_API_KEY` in Streamlit secrets
5. Click Deploy

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "ui/app.py", "--server.port=8501"]
```
Build and run:
```bash
docker build -t tinbhasha .
docker run -p 8501:8501 --env TMT_API_KEY=your_key tinbhasha
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
**4. Mock Mode as a Design Feature**
-   Mock mode was used throughout development to build and test the entire pipeline before       the API key was available. This allowed parallel development and meant the real API    integration required zero code changes — only a `.env` update.

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
| `USE_MOCK` | Use mock translations when `true` | `false` |

---

## UI Guide

### Home Page
Click **"Translate a file →"** to go to the translate page.

### Translate Page
1. Select the **source language** from the language cards on the left
2. Select the **target language** from the language cards on the right
3. Use the **⇄ swap button** to instantly swap languages
4. Upload your **CSV, DOCX, or PDF** file — or click **"Use a sample file to try it out"**
5. Click **"Translate File"**
6. Wait for the progress bar to complete
7. Download your translated file using the **download button**

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
- **Mobile Friendly**- Optimize the layout so the app looks as good on a phone as it does on a computer.

## Track 2 Requirements

| Requirement | Status |
|-------------|--------|
| CSV file translation |  Complete |
| DOCX file translation |  Complete |
| PDF file translation | Complete |
| English ↔ Nepali |  Complete |
| English ↔ Tamang |  Complete |
| Nepali ↔ Tamang |  Complete |
| All 6 translation directions |  Complete |
| Formatting preservation |  Complete |
| Table translation (DOCX + PDF) |  Complete |
| Empty cell/paragraph handling |  Complete |
| File size limit (1MB) | Complete |

---

*Built for Google TMT Hackathon 2026 — Kathmandu University*