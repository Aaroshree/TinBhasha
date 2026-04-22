"""
core/docx_handler.py
TinBhasha — DOCX Translation Handler
Reads a .docx file, translates every paragraph, writes a new translated .docx file.
"""

from docx import Document
from core.tmt_client import TMTClient


def translate_docx(input_path: str, output_path: str, source_lang: str, target_lang: str) -> str:
    """
    Translate all paragraphs in a .docx file.

    Args:
        input_path:  Path to the original .docx file
        output_path: Path where translated .docx will be saved
        source_lang: e.g. "en"
        target_lang: e.g. "ne"

    Returns:
        output_path — the path of the saved translated file
    """
    # Step 1 — open the original docx
    doc = Document(input_path)

    # Step 2 — create the TMT client
    client = TMTClient()

    # Step 3 — translate every paragraph
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():              # skip empty paragraphs
            translated = client.translate(
                paragraph.text,
                source_lang,
                target_lang
            )
            # clear existing runs and write translated text
            for run in paragraph.runs:
                run.text = ""
            paragraph.runs[0].text = translated

    # Step 4 — save the translated docx
    doc.save(output_path)

    return output_path