# TinBhasha 🌐
**Google TMT Hackathon 2026 — Track 2: File Translation Tool**

Translate `.csv` and `.docx` files between **English**, **Nepali**, and **Tamang** 
using the Google Trilingual Machine Translation (TMT) API.

---

## 👥 Team
| Name | Role |
|---|---|
| Aaroshree Gautam | Core code — API integration, CSV & DOCX translation |
| Niharika | UI (Streamlit), testing, README, demo video |

**Institute:** Kathmandu University
**Track:** File Translation Tool (Track 2)

---

## 📁 Project Structure
TinBhasha/
├── core/
│   ├── tmt_client.py       # TMT API wrapper
│   ├── csv_handler.py      # CSV translation logic
│   └── docx_handler.py     # DOCX translation logic (Day 3)
├── ui/
│   └── app.py              # Streamlit UI (Niharika)
├── tests/
│   └── test_connection.py  # API + CSV tests
├── samples/                # Sample input/output files
├── .env                    # API key (never committed)
├── requirements.txt
└── README.md

---

## ⚙️ Setup Instructions

**1. Clone the repo:**
```bash
git clone https://github.com/Aaroshree/TinBhasha.git
cd TinBhasha
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Add your API key:**

Create a `.env` file in the root folder:
TMT_API_KEY=your_api_key_here

---

## 🚀 How It Works

### CSV Translation
Reads every cell in a `.csv` file, translates it via the TMT API, 
and saves a new translated `.csv` file.

```python
from core.csv_handler import translate_csv

translate_csv(
    input_path="samples/sample_english.csv",
    output_path="samples/sample_nepali.csv",
    source_lang="en",
    target_lang="ne",
)
```

### Supported Languages
| Language | Code |
|---|---|
| English | `en` |
| Nepali | `ne` |
| Tamang | `taj` |

---

## 📅 Progress Log

| Day | Date | Task | Status |
|---|---|---|---|
| Day 1 | Apr 22 | Project scaffold, TMT client, GitHub setup | ✅ Done |
| Day 2 | Apr 22 | CSV handler + tests | ✅ Done |
| Day 3 | Apr 23 | DOCX handler | 🔜 Tomorrow |
| Day 4 | Apr 24 | Streamlit UI | 🔜 Niharika |
| Day 5 | Apr 25 | Connect UI to core | 🔜 Upcoming |
| Day 6 | Apr 26 | Full testing | 🔜 Upcoming |
| Day 7 | Apr 27 | Bug fixes + polish | 🔜 Upcoming |
| Day 8 | Apr 28 | Demo video + README final | 🔜 Niharika |
| Day 9 | Apr 29 | Final review + submission prep | 🔜 Upcoming |
| Day 10 | Apr 30 | **SUBMISSION** | 🎯 Deadline |

---

## 🧪 Running Tests
```bash
python tests/test_connection.py
```

---

*Built with ❤️ in Nepal for Google TMT Hackathon 2026*