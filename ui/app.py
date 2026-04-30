"""
ui/app.py
TinBhasha — Streamlit UI (Redesigned)
Beautiful two-page app with language cards, progress bar, result preview, and stats.
"""

import streamlit as st
import tempfile
import os
import sys
import shutil
import time
import io
import pathlib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tmt_client import get_client
from core.csv_handler import translate_csv
from core.docx_handler import translate_docx
from core.pdf_handler import translate_pdf

st.set_page_config(page_title="TinBhasha", page_icon="🌏", layout="centered")

# ─── Session state ────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "home"
if "src_lang" not in st.session_state:
    st.session_state.src_lang = "Eng"
if "tgt_lang" not in st.session_state:
    st.session_state.tgt_lang = "Nep"
if "do_swap" not in st.session_state:
    st.session_state.do_swap = False
# ─── Swap resolution (BEFORE anything renders) ────────────────────────────────
if st.session_state.do_swap:
    cycle = [
        ("Eng", "Nep"),
        ("Nep",  "Tmg"),
        ("Tmg",  "Eng"),
    ]

    current = (st.session_state.src_lang, st.session_state.tgt_lang)
    if current in cycle:
        next_pair = cycle[(cycle.index(current) + 1) % len(cycle)]
    else:
        next_pair = ("English", "Nepali")
    st.session_state.src_lang, st.session_state.tgt_lang = next_pair
    st.session_state.do_swap = False
    st.session_state.page = "translate"
LANG_CODES = {
    "Eng": "en",
    "Nep":  "ne",
    "Tmg":  "tmg",
}

LANG_SCRIPTS = {
    "Eng": "En",
    "Nep":  "ने",
    "Tmg":  "ता",
}

MAX_FILE_SIZE_MB = 1

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: radial-gradient(ellipse at top left, #fff9f0 0%, #fdf0d8 50%, #fae8c0 100%);
}

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 48px 36px 32px !important;
    max-width: 680px;
    background: rgba(253, 243, 210, 0.88);
    border: 1.5px solid #e8cfa0;
    border-radius: 24px;
    backdrop-filter: blur(6px);
    box-shadow: 0 4px 24px rgba(180, 120, 40, 0.10);
    margin-top: 40px !important;
}

/* ── HOME ── */
/* ── HOME ── */
.home-wrap { 
    text-align: center; 
    padding: 40px 20px 30px;
    position: relative;
    overflow: hidden;
    background: rgba(253, 243, 224, 0.92);
    border-radius: 24px;
    border: 1.5px solid #e8d5a0;
    margin: 10px 0;
}
.lang-pills { display: flex; justify-content: center; gap: 10px; margin-bottom: 28px; position: relative; z-index: 1; }
.lp { padding: 5px 18px; border-radius: 999px; font-size: 13px; font-weight: 600; border: 1.5px solid; display: inline-block; }
.lp-en { background: #fff8f0; color: #b05a00; border-color: #f0b87a; }
.lp-ne { background: #fff0f3; color: #a0002a; border-color: #f0a0b0; }
.lp-tmg { background: #f0f6ff; color: #003a8f; border-color: #90b8f0; }
.brand { font-family: 'Playfair Display', Georgia, serif; font-size: 64px; font-weight: 700; line-height: 1; margin-bottom: 10px; position: relative; z-index: 1; }
.brand .dark { color: #2e1a0f; }
.brand .red  { color: #c61e3a; }
.tagline { color: #7f674d; font-size: 18px; font-style: italic; margin-bottom: 6px; position: relative; z-index: 1; }
.script-row { font-size: 13px; color: #b09070; letter-spacing: 2px; margin-bottom: 28px; position: relative; z-index: 1; }
.stats-row { display: flex; justify-content: center; gap: 16px; margin-top: 24px; margin-bottom: 16px; }
.stat-item { text-align: center; background: rgba(255,255,255,0.65); border: 1px solid #e8d5a0; border-radius: 14px; padding: 16px 24px; min-width: 100px; }
.stat-num { font-size: 28px; font-weight: 700; color: #c61e3a; font-family: 'Playfair Display', serif; }
.stat-label { font-size: 10px; color: #a08060; letter-spacing: 2px; font-weight: 600; }
.tiny-footer { color: #c0a97e; font-size: 11px; letter-spacing: 3px; margin-top: 16px; text-align: center; }
.diya-row { display: flex; justify-content: space-between; margin-top: 16px; font-size: 22px; }
/* ── TRANSLATE PAGE ── */
.t-header { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
.t-brand {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 26px;
    font-weight: 700;
}
.t-brand .red { color: #c61e3a; }

/* Language cards */
.lang-grid { display: flex; gap: 8px; align-items: center; margin-bottom: 20px; }
.lc {
    
    flex: 1;
    border: 2px solid #e8cfa0;
    border-radius: 999px;
    padding: 10px 0px;
    text-align: center;
    cursor: pointer;
    background: white;
    transition: all 0.15s;
    display: block;             
    min-width: 72px;
    flex-shrink: 0;        
}
.lc:hover { border-color: #e09060; }
.lc.sel { border-color: #c61e3a; background: #fff5f7; box-sizing:border-box; }
.lc-script { font-size: 18px; font-weight: 700; color: #c61e3a; line-height: 1.1; }
.lc-name { font-size: 11px; color: #7f674d; font-weight: 600; display: block; white-space: nowrap; display: block; width: 100%; position:static; }
.swap-icon { font-size: 20px; color: #c61e3a; cursor: pointer; padding: 0 4px; }


/* File chip */
.file-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #fff5ee;
    border: 1px solid #f0c0a0;
    border-radius: 999px;
    padding: 6px 16px;
    font-size: 13px;
    color: #a04020;
    margin-bottom: 10px;
}

/* ── File preview box ── */
.preview-box {
    background: rgba(255,255,255,0.78);
    border: 1px solid #e8d0a8;
    border-radius: 14px;
    padding: 14px 18px;
    margin-bottom: 16px;
}
.preview-label {
    font-size: 10px;
    font-weight: 700;
    color: #b09070;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.preview-text-line {
    font-size: 13px;
    color: #3a2a1a;
    line-height: 1.8;
    padding: 3px 0;
    border-bottom: 1px solid #f0e4cc;
}
.preview-text-line:last-child { border-bottom: none; }

/* Progress bar */
.prog-wrap { margin: 12px 0; }
.prog-label { font-size: 12px; color: #a08060; margin-bottom: 6px; font-weight: 500; }
.prog-bar {
    height: 7px;
    background: #f0d8b0;
    border-radius: 999px;
    overflow: hidden;
}
.prog-fill {
    height: 100%;
    background: linear-gradient(90deg, #d81f4d, #e67e17);
    border-radius: 999px;
    transition: width 0.3s ease;
}

/* Result card */
.result-wrap {
    background: white;
    border: 1.5px solid #b8e0b0;
    border-radius: 16px;
    padding: 18px 22px;
    margin-top: 16px;
}
.result-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.result-title { font-size: 15px; font-weight: 600; color: #2a6020; }
.result-badges { display: flex; gap: 10px; }
.badge { font-size: 11px; color: #50903a; background: #edf8e8; padding: 3px 10px; border-radius: 999px; font-weight: 500; }
.result-preview-lines { border-top: 1px solid #e0f0d8; padding-top: 12px; font-size: 13px; color: #404040; line-height: 1.9; margin-bottom: 14px; }

/* Sample link */
.sample-hint { text-align: center; font-size: 12px; color: #b09070; margin-bottom: 14px; }

/* Warning / info */
.warn-box {
    background: #fffbf0;
    border: 1px solid #f0d890;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    color: #806000;
    margin-bottom: 14px;
}
.info-box {
    background: #f0f8ff;
    border: 1px solid #b0d8f8;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    color: #004080;
    margin-bottom: 14px;
}

.powered { text-align: center; font-size: 11px; color: #c0a97e; letter-spacing: 2px; margin-top: 20px; }

/* Override streamlit button */
div.stButton > button {
    border-radius: 20px !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    white-space: pre-line !important; 
    line-height: 1.2 !important;
    padding: 10px 5px !important;
    min-height: 55px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
}
div.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #d81f4d 0%, #e67e17 100%) !important;
    border: none !important;
    color: white !important;
}
div.stDownloadButton > button {
    background: #2a6020 !important;
    color: white !important;
    border: none !important;
    border-radius: 999px !important;
    font-weight: 600 !important;
    padding: 10px 28px !important;
}
/* ── Swap button specific styling ── */
div[data-testid="column"]:nth-child(4) div.stButton > button {
    background: white !important;
    border: 1.5px solid #e8cfa0 !important;
    color: #c61e3a !important;
    font-size: 18px !important;
    border-radius: 999px !important;
    height: 44px !important;
    width: 44px !important;
    min-width: unset !important;
    padding: 0 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}
div[data-testid="column"]:nth-child(4) div.stButton > button:hover {
    border-color: #c61e3a !important;
    box-shadow: 0 2px 8px rgba(198,30,58,0.15) !important;
    background: #fff0f0 !important;
}
/* ── Swap button: invisible shell, just the icon ── */
div[data-testid="column"]:nth-child(4) div.stButton > button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #c61e3a !important;
    font-size: 22px !important;
    padding: 0 !important;
    height: 60px !important;
    width: 60px !important;
    min-width: unset !important;
    cursor: pointer !important;
}
div[data-testid="column"]:nth-child(4) div.stButton > button:hover {
    background: transparent !important;
    color: #a01020 !important;
    transform: scale(1.2) !important;
    transition: all 0.15s !important;
}
div[data-testid="column"]:nth-child(4) div.stButton > button:focus {
    box-shadow: none !important;
    outline: none !important;
}
.home-card {
    background: rgba(255, 255, 255, 0.55);
    border: 1.5px solid #e8cfa0;
    border-radius: 24px;
    padding: 36px 40px;
    max-width: 560px;
    margin: 20px auto;
    backdrop-filter: blur(6px);
    box-shadow: 0 4px 24px rgba(180, 120, 40, 0.10);
}
</style>
""", unsafe_allow_html=True)
import base64
try:
    with open("ui/static/dhaka.jpg", "rb") as f:
        dhaka_b64 = base64.b64encode(f.read()).decode()
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{dhaka_b64}") !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
    }}
    .stApp::before {{
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(253, 243, 224, 0.82);
        z-index: 0;
        pointer-events: none;
    }}
    </style>
    """, unsafe_allow_html=True)
except:
    pass


# ─── HOME PAGE ─────────────────────────────────────────────────────────────────
# ─── HOME PAGE ─────────────────────────────────────────────────────────────────
# ─── HOME PAGE ─────────────────────────────────────────────────────────────────
if st.session_state.page == "home":

    st.markdown("""
    <div class="home-wrap">
        <div class="lang-pills">
            <span class="lp lp-en">English</span>
            <span class="lp lp-ne">नेपाली</span>
            <span class="lp lp-tmg">तामाङ</span>
        </div>
        <div class="brand"><span class="dark">Tin</span><span class="red">Bhasha</span></div>
        <div class="tagline">Translate CSV, DOCX and PDF files across three languages</div>
        <div class="script-row">ङाला मिन &nbsp;•&nbsp; मेरो नाम &nbsp;•&nbsp; My name</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Translate a file →", use_container_width=True, type="primary"):
            st.session_state.page = "translate"
            st.rerun()

    st.markdown("""
    <div class="stats-row">
        <div class="stat-item"><div class="stat-num">3</div><div class="stat-label">LANGUAGES</div></div>
        <div class="stat-item"><div class="stat-num">6</div><div class="stat-label">DIRECTIONS</div></div>
        <div class="stat-item"><div class="stat-num">3</div><div class="stat-label">FILE TYPES</div></div>
    </div>
    <div class="diya-row"><span>🪔</span><span>🪔</span></div>
    <div class="tiny-footer">नेपाल &nbsp;•&nbsp; FILE TRANSLATION TOOL &nbsp;•&nbsp; KU ILPRL</div>
    """, unsafe_allow_html=True)
# ─── TRANSLATE PAGE ─────────────────────────────────────────────────────────────

else:

    # ── Header ──
    h1, h2 = st.columns([1, 3])
    with h1:
        if st.button("← Home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
    with h2:
        st.markdown(
            '<div class="t-brand" style="padding-top:6px">Tin<span class="red">Bhasha</span> Translator</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Language selector ──
    langs = ["Eng", "Nep", "Tmg"]
    c = st.columns([1, 1, 1, 0.6, 1, 1, 1])

    # Source language buttons
    for i, lang in enumerate(langs):
        with c[i]:
            sel = st.session_state.src_lang == lang
            if st.button(
                f"{LANG_SCRIPTS[lang]}\n{lang}",
                key=f"src_{lang}",
                use_container_width=True,
                type="primary" if sel else "secondary",
            ):
                if lang != st.session_state.tgt_lang:
                    st.session_state.src_lang = lang
                    st.rerun()

    # ── Swap button ──
    with c[3]:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("⇄", key="swap_langs", use_container_width=True):
            st.session_state.do_swap = True
            st.session_state.page = "translate"
            st.rerun()

    # Target language buttons
    for i, lang in enumerate(langs):
        with c[i + 4]:
            sel = st.session_state.tgt_lang == lang
            if st.button(
                f"{LANG_SCRIPTS[lang]}\n{lang}",
                key=f"tgt_{lang}",
                use_container_width=True,
                type="primary" if sel else "secondary",
            ):
                if lang != st.session_state.src_lang:
                    st.session_state.tgt_lang = lang
                    st.rerun()

    if st.session_state.src_lang == st.session_state.tgt_lang:
        st.markdown(
            '<div class="warn-box">⚠️ Source and target languages must be different!</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── DOCX / PDF info ──
    st.markdown(
        '<div class="info-box">Complete DOCX support: Paragraphs + Tables + Formatting preserved! '
        'PDF support: Text extraction with layout preserved!</div>',
        unsafe_allow_html=True,
    )

    # ── Upload box ──
    uploaded_file = st.file_uploader("", type=["csv", "docx", "pdf"], label_visibility="collapsed")

    # ── Sample file map ──
    SAMPLE_FILES = {
        ("English", ".csv"):  "samples/sample_english.csv",
        ("English", ".docx"): "samples/sample_english.docx",
        ("English", ".pdf"):  "samples/sample_english.pdf",
        ("Nepali",  ".csv"):  "samples/sample_nepali.csv",
        ("Nepali",  ".docx"): "samples/sample_nepali.docx",
        ("Nepali",  ".pdf"):  "samples/sample_nepali.pdf",
        ("Tamang",  ".csv"):  "samples/sample_tamang.csv",
        ("Tamang",  ".docx"): "samples/sample_tamang.docx",
        ("Tamang",  ".pdf"):  "samples/sample_tamang.pdf",
    }

    # Inject sample file if requested
    if uploaded_file is None and "sample_bytes" in st.session_state:
        uploaded_file = io.BytesIO(st.session_state.sample_bytes)
        uploaded_file.name = st.session_state.sample_name
        uploaded_file.size = len(st.session_state.sample_bytes)

    # ── File chip + pre-upload preview — FEATURE 2 ──
    # Read the file into memory once so we can (a) show a preview and
    # (b) still pass the bytes to the translation handler later.
    if uploaded_file is not None:
        if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.error(f"❌ File too large! Maximum size is {MAX_FILE_SIZE_MB}MB.")
            st.stop()

        # File chip
        st.markdown(
            f'<div class="file-chip">📄 {uploaded_file.name}'
            f' &nbsp;<span style="color:#c08060">{round(uploaded_file.size / 1024, 1)}KB</span></div>',
            unsafe_allow_html=True,
        )

        # Read all bytes now; seek back so translate can read again
        raw_bytes = uploaded_file.read()
        uploaded_file.seek(0)

        fname_lower = uploaded_file.name.lower()

        # --- CSV preview: use st.dataframe for a proper table ---
        if fname_lower.endswith(".csv"):
            try:
                import pandas as pd
                _df = pd.read_csv(io.BytesIO(raw_bytes))
                st.markdown(
                    '<div class="preview-box">'
                    '<div class="preview-label"> File Preview </div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                st.dataframe(_df.head(5), use_container_width=True, hide_index=True)
            except Exception as e:
                st.markdown(
                    f'<div class="preview-box"><div class="preview-label"> File Preview</div>'
                    f'<div class="preview-text-line" style="color:#c08060">Could not read CSV: {e}</div></div>',
                    unsafe_allow_html=True,
                )

        elif fname_lower.endswith(".docx"):
            try:
                from docx import Document as _Doc
                _doc = _Doc(io.BytesIO(raw_bytes))
                inner = ""
                count = 0
                for p in _doc.paragraphs:
                    if not p.text.strip():
                        continue
                    spans = ""
                    for run in p.runs:
                        style = ""
                        if run.bold:
                            style += "font-weight:bold;"
                        if run.italic:
                            style += "font-style:italic;"
                        if run.underline:
                            style += "text-decoration:underline;"
                        if run.font.name:
                            style += f"font-family:'{run.font.name}', sans-serif;"
                        if run.font.size:
                            pt = run.font.size.pt
                            style += f"font-size:{min(pt, 18)}px;"
                        spans += f'<span style="{style}">{run.text}</span>'
                    inner += f'<div class="preview-text-line">{spans}</div>'
                    count += 1
                    if count >= 6:
                        break
                if not inner:
                    inner = '<div class="preview-text-line" style="color:#a08060">No text paragraphs found.</div>'
            except Exception as e:
                inner = f'<div class="preview-text-line" style="color:#c08060">Could not read DOCX: {e}</div>'
            st.markdown(
                f'<div class="preview-box">'
                f'<div class="preview-label"> File Preview — first paragraphs</div>'
                f'{inner}</div>',
                unsafe_allow_html=True,
            )


        # --- PDF preview: first 8 non-empty lines across pages ---
        elif fname_lower.endswith(".pdf"):
            try:
                import fitz
                inner = ""
                count = 0
                fitz_doc = fitz.open(stream=raw_bytes, filetype="pdf")
                for page in fitz_doc:
                    underline_ys = set()
                    for path in page.get_drawings():
                        if path.get("type") == "s":
                            for item in path.get("items", []):
                                if item[0] == "l":
                                    p1, p2 = item[1], item[2]
                                    if abs(p1.y - p2.y) < 2:
                                        underline_ys.add(round(p1.y))
                    page_dict = page.get_text("dict")
                    for block in page_dict.get("blocks", []):
                        if block.get("type") != 0:
                            continue
                        for line in block.get("lines", []):
                            spans = line.get("spans", [])
                            if not spans:
                                continue
                            line_html = ""
                            for span in spans:
                                text = span.get("text", "").strip()
                                if not text:
                                    continue
                                flags = span.get("flags", 0)
                                font  = span.get("font", "")
                                style = ""
                                if bool(flags & 2**4) or "Bold" in font:
                                    style += "font-weight:bold;"
                                if bool(flags & 2**1) or "Italic" in font:
                                    style += "font-style:italic;"
                                span_y = round(span.get("bbox", [0,0,0,0])[3])
                                if any(abs(span_y - uy) < 6 for uy in underline_ys):
                                    style += "text-decoration:underline;"
                                size = span.get("size", 10)
                                style += f"font-size:{min(int(size), 18)}px;"
                                line_html += f'<span style="{style}">{text} </span>'
                            if line_html.strip():
                                inner += f'<div class="preview-text-line">{line_html}</div>'
                                count += 1
                            if count >= 8:
                                break
                        if count >= 8:
                            break
                    if count >= 8:
                        break
                fitz_doc.close()
                if not inner:
                    inner = '<div class="preview-text-line" style="color:#a08060">No text extracted from PDF.</div>'
            except Exception as e:
                inner = f'<div class="preview-text-line" style="color:#c08060">Could not read PDF: {e}</div>'
            st.markdown(
                f'<div class="preview-box">'
                f'<div class="preview-label"> File Preview — first lines</div>'
                f'{inner}</div>',
                unsafe_allow_html=True,
            )

    # ── Sample file picker ──
    with st.expander(" Use a sample file to try it out"):
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            sample_lang = st.selectbox("Language", ["English", "Nepali", "Tamang"], key="sample_lang")
        with s_col2:
            sample_fmt = st.selectbox("Format", [".csv", ".docx", ".pdf"], key="sample_fmt")

        if st.button("Load sample", use_container_width=True):
            sample_path = SAMPLE_FILES.get((sample_lang, sample_fmt))
            if sample_path and pathlib.Path(sample_path).exists():
                with open(sample_path, "rb") as f:
                    st.session_state.sample_bytes = f.read()
                    st.session_state.sample_name = f"sample_{sample_lang.lower()}{sample_fmt}"
                st.rerun()
            else:
                st.warning(f"Sample file for {sample_lang} {sample_fmt} not found in samples/ folder.")

    # ── Translate button ──
    same_lang = st.session_state.src_lang == st.session_state.tgt_lang
    translate_clicked = st.button(
        "Translate File",
        disabled=same_lang,
        use_container_width=True,
        type="primary",
    )

    if translate_clicked:
        if uploaded_file is None:
            st.warning("Please upload a file first!")
        else:
            src_code = LANG_CODES[st.session_state.src_lang]
            tgt_code = LANG_CODES[st.session_state.tgt_lang]
            filename = uploaded_file.name
            fn_lower = filename.lower()
            if fn_lower.endswith(".csv"):
                suffix = ".csv"
            elif fn_lower.endswith(".pdf"):
                suffix = ".pdf"
            else:
                suffix = ".docx"

            input_path = None
            output_path = None
            prog_label = st.empty()
            prog_bar = st.progress(0)
            steps = [
                (0.15, "Reading file..."),
                (0.35, "Connecting to TMT API..."),
                (0.60, "Translating content..."),
                (0.85, "Preserving formatting..."),
                (1.00, "Finalising output..."),
            ]

            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
                    tmp_in.write(uploaded_file.read())
                    input_path = tmp_in.name

                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_out:
                    output_path = tmp_out.name

                start_time = time.time()

                for prog, label in steps[:-2]:
                    prog_label.markdown(f'<div class="prog-label">{label}</div>', unsafe_allow_html=True)
                    prog_bar.progress(prog)
                    time.sleep(0.3)

                # Actual translation
                if suffix == ".csv":
                    translate_csv(input_path, output_path, src_code, tgt_code)
                elif suffix == ".pdf":
                    translate_pdf(input_path, output_path, src_code, tgt_code)
                else:
                    translate_docx(input_path, output_path, src_code, tgt_code)

                elapsed = round(time.time() - start_time, 1)

                for prog, label in steps[-2:]:
                    prog_label.markdown(f'<div class="prog-label">{label}</div>', unsafe_allow_html=True)
                    prog_bar.progress(prog)
                    time.sleep(0.2)

                prog_label.empty()
                prog_bar.empty()

                with open(output_path, "rb") as f:
                    result_bytes = f.read()

                base_name = filename.rsplit(suffix, 1)[0]
                out_name = f"{base_name}_translated_{tgt_code}{suffix}"
                if suffix == ".csv":
                    mime = "text/csv"
                elif suffix == ".pdf":
                    mime = "application/pdf"
                else:
                    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

                # Build result preview
                preview_html = ""
                try:
                    if suffix == ".docx":
                        from docx import Document as _Doc
                        _doc = _Doc(output_path)
                        preview_html = ""
                        count = 0
                        for p in _doc.paragraphs:
                            if not p.text.strip():
                                continue
                            spans = ""
                            for run in p.runs:
                                style = ""
                                if run.bold:
                                    style += "font-weight:bold;"
                                if run.italic:
                                    style += "font-style:italic;"
                                if run.underline:
                                    style += "text-decoration:underline;"
                                if run.font.name:
                                    style += f"font-family:'{run.font.name}', sans-serif;"
                                if run.font.size:
                                    pt = run.font.size.pt
                                    style += f"font-size:{min(pt, 18)}px;"
                                spans += f'<span style="{style}">{run.text}</span>'
                            preview_html += f"<div style='margin-bottom:3px'>{spans}</div>"
                            count += 1
                            if count >= 6:
                                break
                    elif suffix == ".pdf":
                        import fitz
                        preview_html = ""
                        count = 0
                        fitz_doc = fitz.open(output_path)
                        for page in fitz_doc:
                            underline_ys = set()
                            for path in page.get_drawings():
                                if path.get("type") == "s":
                                    for item in path.get("items", []):
                                        if item[0] == "l":
                                            p1, p2 = item[1], item[2]
                                            if abs(p1.y - p2.y) < 2:
                                                underline_ys.add(round(p1.y))
                            page_dict = page.get_text("dict")
                            for block in page_dict.get("blocks", []):
                                if block.get("type") != 0:
                                    continue
                                for line in block.get("lines", []):
                                    spans = line.get("spans", [])
                                    if not spans:
                                        continue
                                    line_html = ""
                                    for span in spans:
                                        text = span.get("text", "").strip()
                                        if not text:
                                            continue
                                        flags = span.get("flags", 0)
                                        font  = span.get("font", "")
                                        style = ""
                                        if bool(flags & 2**4) or "Bold" in font:
                                            style += "font-weight:bold;"
                                        if bool(flags & 2**1) or "Italic" in font:
                                            style += "font-style:italic;"
                                        span_y = round(span.get("bbox", [0,0,0,0])[3])
                                        if any(abs(span_y - uy) < 6 for uy in underline_ys):
                                            style += "text-decoration:underline;"
                                        size = span.get("size", 10)
                                        style += f"font-size:{min(int(size), 18)}px;"
                                        line_html += f'<span style="{style}">{text} </span>'
                                    if line_html.strip():
                                        preview_html += f"<div style='margin-bottom:3px'>{line_html}</div>"
                                        count += 1
                                    if count >= 6:
                                        break
                                if count >= 6:
                                    break
                            if count >= 6:
                                break
                        fitz_doc.close()
                    else:
                        import pandas as pd
                        _df = pd.read_csv(io.BytesIO(result_bytes))
                        rows = _df.head(4).to_dict("records")
                        for row in rows:
                            preview_html += (
                                "<div style='margin-bottom:3px'>"
                                + " &nbsp;|&nbsp; ".join(str(v) for v in row.values())
                                + "</div>"
                            )
                except Exception:
                    preview_html = "<div style='color:#a08060'>Preview not available</div>"

                st.markdown(f"""
                <div class="result-wrap">
                    <div class="result-top">
                        <div class="result-title">✓ Translation complete</div>
                        <div class="result-badges">
                            <span class="badge">{st.session_state.src_lang} → {st.session_state.tgt_lang}</span>
                            <span class="badge">{elapsed}s</span>
                        </div>
                    </div>
                    <div class="result-preview-lines">{preview_html}</div>
                </div>
                """, unsafe_allow_html=True)

                st.download_button(
                    label="⬇ Download Translated File",
                    data=result_bytes,
                    file_name=out_name,
                    mime=mime,
                    use_container_width=True,
                )

            except Exception as e:
                prog_label.empty()
                prog_bar.empty()
                st.error(f"❌ Something went wrong: {e}")

            finally:
                if input_path and os.path.exists(input_path):
                    os.unlink(input_path)
                if output_path and os.path.exists(output_path):
                    os.unlink(output_path)

    st.markdown(
        '<div class="powered">POWERED BY TMT API &nbsp;•&nbsp; ILPRL KATHMANDU UNIVERSITY</div>',
        unsafe_allow_html=True,
    )