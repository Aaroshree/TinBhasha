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
    st.session_state.src_lang = "English"
if "tgt_lang" not in st.session_state:
    st.session_state.tgt_lang = "Nepali"

LANG_CODES = {
    "English": "en",
    "Nepali":  "ne",
    "Tamang":  "tmg",

}

LANG_SCRIPTS = {
    "English": "En",
    "Nepali":  "ने",
    "Tamang":  "ता",
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
.block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 680px; }

/* ── HOME ── */
.home-wrap { text-align: center; padding: 20px 0 10px; }

.lang-pills { display: flex; justify-content: center; gap: 10px; margin-bottom: 28px; }
.lp { padding: 5px 18px; border-radius: 999px; font-size: 13px; font-weight: 600; border: 1.5px solid; display: inline-block; }
.lp-en { background: #fff8f0; color: #b05a00; border-color: #f0b87a; }
.lp-ne { background: #fff0f3; color: #a0002a; border-color: #f0a0b0; }
.lp-tmg { background: #f0f6ff; color: #003a8f; border-color: #90b8f0; }

.brand {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 64px;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 10px;
}
.brand .dark { color: #2e1a0f; }
.brand .red  { color: #c61e3a; }

.tagline { color: #7f674d; font-size: 18px; font-style: italic; margin-bottom: 6px; }
.script-row { font-size: 13px; color: #b09070; letter-spacing: 2px; margin-bottom: 28px; }

.live-box {
    background: rgba(255,255,255,0.75);
    border: 1px solid #f0d8b0;
    border-radius: 16px;
    padding: 18px 22px;
    margin: 0 auto 28px;
    max-width: 460px;
    text-align: left;
    backdrop-filter: blur(4px);
}
.live-box-label { font-size: 12px; color: #a08060; margin-bottom: 6px; font-weight: 500; letter-spacing: 0.5px; }
.live-result-text { font-size: 15px; color: #c61e3a; font-style: italic; min-height: 26px; margin-top: 8px; padding-top: 8px; border-top: 1px solid #f0d8b0; }

.stats-row { display: flex; justify-content: center; gap: 40px; margin-top: 24px; margin-bottom: 8px; }
.stat-item { text-align: center; }
.stat-num { font-size: 28px; font-weight: 700; color: #c61e3a; font-family: 'Playfair Display', serif; }
.stat-label { font-size: 10px; color: #a08060; letter-spacing: 2px; font-weight: 600; }

.tiny-footer { color: #c0a97e; font-size: 11px; letter-spacing: 3px; margin-top: 20px; text-align: center; }

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
    border-radius: 14px;
    padding: 12px 8px;
    text-align: center;
    cursor: pointer;
    background: white;
    transition: all 0.15s;
}
.lc:hover { border-color: #e09060; }
.lc.sel { border-color: #c61e3a; background: #fff5f7; }
.lc-script { font-size: 22px; font-weight: 700; color: #c61e3a; line-height: 1.2; }
.lc-name { font-size: 11px; color: #7f674d; font-weight: 500; letter-spacing: 0.5px; }
.swap-icon { font-size: 20px; color: #c61e3a; cursor: pointer; padding: 0 4px; }

/* Upload area */
.upload-styled {
    border: 2px dashed #e0c898;
    border-radius: 16px;
    padding: 32px 24px;
    text-align: center;
    background: rgba(255,255,255,0.5);
    margin-bottom: 12px;
}
.upload-icon-big { font-size: 32px; margin-bottom: 8px; }
.upload-main-text { font-size: 15px; color: #5a4a38; font-weight: 500; margin-bottom: 4px; }
.upload-sub-text { font-size: 12px; color: #a08060; }

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
    margin-bottom: 14px;
}

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
    border-radius: 999px !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
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
</style>
""", unsafe_allow_html=True)


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

    # CTA button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Translate a file →", use_container_width=True, type="primary"):
            st.session_state.page = "translate"
            st.rerun()

    # Stats
    st.markdown("""
    <div class="stats-row">
        <div class="stat-item"><div class="stat-num">3</div><div class="stat-label">LANGUAGES</div></div>
        <div class="stat-item"><div class="stat-num">6</div><div class="stat-label">DIRECTIONS</div></div>
        <div class="stat-item"><div class="stat-num">3</div><div class="stat-label">FILE TYPES</div></div>
    </div>
    <div class="tiny-footer">नेपाल &nbsp;•&nbsp; FILE TRANSLATION TOOL &nbsp;•&nbsp; KU ILPRL</div>
    """, unsafe_allow_html=True)


# ─── TRANSLATE PAGE ─────────────────────────────────────────────────────────────

else:

    # ── Header row: back button + brand ──
    h1, h2 = st.columns([1, 3])
    with h1:
        if st.button("← Home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
    with h2:
        st.markdown('<div class="t-brand" style="padding-top:6px">Tin<span class="red">Bhasha</span> Translator</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Language selector ──
    langs = ["English", "Nepali", "Tamang"]
    c = st.columns([1, 1, 1, 0.4, 1, 1, 1])

    for i, lang in enumerate(langs):
        with c[i]:
            sel = st.session_state.src_lang == lang
            script = LANG_SCRIPTS[lang]
            btn_label = f"{script}\n{lang}"
            if st.button(btn_label, key=f"src_{lang}", use_container_width=True,
                         type="primary" if sel else "secondary"):
                if lang != st.session_state.tgt_lang:
                    st.session_state.src_lang = lang
                    st.rerun()

    with c[3]:
        st.markdown("<div style='text-align:center;font-size:18px;color:#c61e3a;padding-top:10px'>⇄</div>", unsafe_allow_html=True)

    for i, lang in enumerate(langs):
        with c[i + 4]:
            sel = st.session_state.tgt_lang == lang
            script = LANG_SCRIPTS[lang]
            btn_label = f"{script}\n{lang}"
            if st.button(btn_label, key=f"tgt_{lang}", use_container_width=True,
                         type="primary" if sel else "secondary"):
                if lang != st.session_state.src_lang:
                    st.session_state.tgt_lang = lang
                    st.rerun()

    if st.session_state.src_lang == st.session_state.tgt_lang:
        st.markdown('<div class="warn-box">⚠️ Source and target languages must be different!</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── DOCX / PDF info ──
    st.markdown('<div class="info-box"> Complete DOCX support: Paragraphs + Tables + Formatting preserved! PDF support: Text extraction with layout preserved! </div>', unsafe_allow_html=True)

    # ── Upload box ──
    st.markdown("""
    <div class="upload-styled">
        <div class="upload-icon-big">☁️</div>
        <div class="upload-main-text">Drag and drop your file here</div>
        <div class="upload-sub-text">CSV, DOCX or PDF • max 1MB</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("", type=["csv", "docx", "pdf"], label_visibility="collapsed")

    # ── Inject sample file if one was requested ──
    import pathlib, io

    # ── Sample file button ──
    SAMPLE_FILES = {
        ".csv":  "samples/sample_english.csv",
        ".docx": "samples/sample_english.docx",
        ".pdf":  "samples/sample_english.pdf",
    }

    if uploaded_file is None and "sample_bytes" in st.session_state:
        uploaded_file = io.BytesIO(st.session_state.sample_bytes)
        uploaded_file.name = st.session_state.sample_name
        uploaded_file.size = len(st.session_state.sample_bytes)

    if uploaded_file is not None:
        if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.error(f"❌ File too large! Maximum size is {MAX_FILE_SIZE_MB}MB.")
            st.stop()
        st.markdown(f'<div class="file-chip">📄 {uploaded_file.name} &nbsp;<span style="color:#c08060">{round(uploaded_file.size/1024,1)}KB</span></div>', unsafe_allow_html=True)

    # ── Sample file button ──
    if st.button("Use a sample file to try it out", use_container_width=True):
        sample_path = "samples/sample_english.csv"
        if pathlib.Path(sample_path).exists():
            with open(sample_path, "rb") as f:
                st.session_state.sample_bytes = f.read()
                st.session_state.sample_name = "sample_english.csv"
            st.rerun()

    # ── Translate button ──
    same_lang = st.session_state.src_lang == st.session_state.tgt_lang
    translate_clicked = st.button(
        "Translate File",
        disabled=same_lang,
        use_container_width=True,
        type="primary"
    )

    if translate_clicked:
        if uploaded_file is None:
            st.warning("Please upload a file first!")
        else:
            src_code = LANG_CODES[st.session_state.src_lang]
            tgt_code = LANG_CODES[st.session_state.tgt_lang]
            filename  = uploaded_file.name
            fn_lower  = filename.lower()
            if fn_lower.endswith(".csv"):
                suffix = ".csv"
            elif fn_lower.endswith(".pdf"):
                suffix = ".pdf"
            else:
                suffix = ".docx"
            input_path = None
            output_path = None

            prog_label = st.empty()
            prog_bar   = st.progress(0)
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

                # ── Actual translation ──
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
                out_name  = f"{base_name}_translated_{tgt_code}{suffix}"
                if suffix == ".csv":
                    mime = "text/csv"
                elif suffix == ".pdf":
                    mime = "application/pdf"
                else:
                    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

                # ── Build preview lines ──
                preview_html = ""
                try:
                    if suffix == ".docx":
                        from docx import Document as _Doc
                        _doc = _Doc(output_path)
                        lines = [p.text for p in _doc.paragraphs if p.text.strip()][:6]
                        preview_html = "".join(f"<div style='margin-bottom:3px'>{l}</div>" for l in lines)
                    elif suffix == ".pdf":
                        import pdfplumber
                        with pdfplumber.open(output_path) as _pdf:
                            lines = []
                            for _page in _pdf.pages:
                                _text = _page.extract_text() or ""
                                lines.extend([l for l in _text.splitlines() if l.strip()])
                                if len(lines) >= 6:
                                    break
                        preview_html = "".join(f"<div style='margin-bottom:3px'>{l[:120]}</div>" for l in lines[:6])
                    else:
                        import pandas as pd
                        _df = pd.read_csv(io.BytesIO(result_bytes))
                        rows = _df.head(4).to_dict("records")
                        for row in rows:
                            preview_html += "<div style='margin-bottom:3px'>" + " &nbsp;|&nbsp; ".join(str(v) for v in row.values()) + "</div>"
                except Exception:
                    preview_html = "<div style='color:#a08060'>Preview not available</div>"

                # ── Result card ──
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

    st.markdown('<div class="powered">POWERED BY TMT API &nbsp;•&nbsp; ILPRL KATHMANDU UNIVERSITY</div>', unsafe_allow_html=True)