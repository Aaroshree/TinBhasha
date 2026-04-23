import streamlit as st
import tempfile
import os
import sys
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================
# MOCK MODE — Set to False when API key is ready
# That is the ONLY change you need to make when API arrives!
# ============================================================
MOCK_MODE = True

if not MOCK_MODE:
    from core.tmt_client import get_client
    from core.csv_handler import translate_csv
    from core.docx_handler import translate_docx

st.set_page_config(page_title="TinBhasha", page_icon="🌐", layout="centered")

if "page" not in st.session_state:
    st.session_state.page = "home"

def go_to_translate():
    st.session_state.page = "translate"

def go_to_home():
    st.session_state.page = "home"

LANG_CODES = {
    "English": "en",
    "Nepali": "ne",
    "Tamang": "taj"
}

MAX_FILE_SIZE_MB = 5  # Maximum allowed file size in MB

st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at top left, #fff6e6 0%, #f5e2b8 45%, #f0d9a6 100%);
        font-family: Georgia, serif;
    }
    .main-card {
        max-width: 760px;
        margin: 40px auto;
        background: rgba(255, 248, 230, 0.92);
        border-radius: 32px;
        padding: 42px 36px 34px 36px;
        box-shadow: 0 18px 50px rgba(140, 100, 40, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.45);
        text-align: center;
    }
    .small-top { color: #9b6f2d; font-size: 20px; font-weight: 600; margin-bottom: 18px; }
    .welcome-text { color: #b08a56; letter-spacing: 6px; font-size: 16px; margin-bottom: 18px; }
    .brand { font-size: 58px; font-weight: 700; line-height: 1; margin-bottom: 14px; font-family: Georgia, serif; }
    .brand .dark { color: #2e1a0f; }
    .brand .red { color: #c61e3a; }
    .subtitle { color: #7f674d; font-size: 24px; font-style: italic; line-height: 1.5; margin-bottom: 28px; }
    div.stButton > button {
        font-size: 22px !important;
        font-weight: 600 !important;
        padding: 18px 42px !important;
        border-radius: 999px !important;
        border: none !important;
        background: linear-gradient(90deg, #d81f4d 0%, #e67e17 100%) !important;
        color: white !important;
        box-shadow: 0 12px 30px rgba(214, 57, 40, 0.28) !important;
        width: 360px !important;
        max-width: 100% !important;
        margin: 0 auto !important;
        display: block !important;
    }
    .footer-text { color: #c0a97e; margin-top: 16px; font-size: 16px; }
    .tiny-footer { color: #c9b58a; text-align: center; margin-top: 18px; letter-spacing: 4px; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HOME PAGE
# ============================================================
if st.session_state.page == "home":
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<div class="small-top">नमस्ते 🙏</div>', unsafe_allow_html=True)
    st.markdown('<div class="welcome-text">WELCOME TO</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand"><span class="dark">Tin</span><span class="red">Bhasha</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Translate your CSV and DOCX files into<br>beautiful Nepali, English, or Tamang — instantly.</div>', unsafe_allow_html=True)
    st.button("Tap here to open →", on_click=go_to_translate)
    st.markdown('<div class="footer-text">Upload any CSV or DOCX • Translate to Nepali, English, or Tamang •</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="tiny-footer">नेपाल • FILE TRANSLATION TOOL</div>', unsafe_allow_html=True)

# ============================================================
# TRANSLATE PAGE
# ============================================================
else:
    st.title(" TinBhasha Translator")
    st.markdown("Upload your CSV or DOCX file and translate it between English, Nepali, and Tamang.")

    # Show mock mode banner
    if MOCK_MODE:
        st.info("🔧 Running in Mock Mode — file will be returned as-is. Real translation will work once API key is added.")

    # DOCX tables warning — always visible so judges are aware
    st.warning(" Note: Tables inside DOCX files are not translated in this version. Only paragraphs are translated.")

    uploaded_file = st.file_uploader("Upload your file", type=["csv", "docx"])

    # FIX 1 — File size check immediately after upload
    if uploaded_file is not None:
        if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.error(f"File too large! Please upload a file smaller than {MAX_FILE_SIZE_MB}MB.")
            st.stop()

    col1, col2 = st.columns(2)
    with col1:
        source_lang = st.selectbox("From", ["English", "Nepali", "Tamang"])
    with col2:
        target_lang = st.selectbox("To", ["English", "Nepali", "Tamang"])

    # FIX 2 — Disable translate button if same language selected
    same_lang = source_lang == target_lang
    if same_lang:
        st.warning("Source and target languages must be different!")

    if st.button(" Translate File", disabled=same_lang):
        if uploaded_file is None:
            st.warning("Please upload a file first!")
        else:
            src_code = LANG_CODES[source_lang]
            tgt_code = LANG_CODES[target_lang]
            filename = uploaded_file.name

            # FIX 3 — Case-insensitive file extension check
            suffix = ".csv" if filename.lower().endswith(".csv") else ".docx"

            # FIX 4 — Initialize paths to None so finally block is always safe
            input_path = None
            output_path = None

            with st.spinner("Translating... please wait"):
                try:
                    # Save uploaded file to a temp location
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
                        tmp_in.write(uploaded_file.read())
                        input_path = tmp_in.name

                    # Create a temp output file path
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_out:
                        output_path = tmp_out.name

                    # ============================================================
                    # TRANSLATION LOGIC
                    # MOCK_MODE = True  → copies file as-is (no API needed)
                    # MOCK_MODE = False → calls real translation API
                    # Only change MOCK_MODE at the top of this file!
                    # ============================================================
                    if MOCK_MODE:
                        shutil.copy(input_path, output_path)
                    else:
                        if suffix == ".csv":
                            translate_csv(input_path, output_path, src_code, tgt_code)
                        else:
                            translate_docx(input_path, output_path, src_code, tgt_code)

                    # Read the result and offer download
                    with open(output_path, "rb") as f:
                        result_bytes = f.read()

                    # FIX 5 — Safe output filename using rsplit
                    base_name = filename.rsplit(suffix, 1)[0]
                    out_name = f"{base_name}_translated_{tgt_code}{suffix}"
                    mime = "text/csv" if suffix == ".csv" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

                    st.success("Translation complete! ")
                    st.download_button(
                        label="⬇️ Download Translated File",
                        data=result_bytes,
                        file_name=out_name,
                        mime=mime
                    )

                except Exception as e:
                    st.error(f" Something went wrong: {e}")

                finally:
                    # FIX 6 — Safe cleanup: only delete if variables exist and files exist
                    if input_path and os.path.exists(input_path):
                        os.unlink(input_path)
                    if output_path and os.path.exists(output_path):
                        os.unlink(output_path)

    st.button("⬅ Back to Home", on_click=go_to_home)