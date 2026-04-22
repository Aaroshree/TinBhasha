"""
core/docx_handler.py
TinBhasha — DOCX Translation Handler
Reads a .docx file, translates every paragraph, writes a new translated .docx file.

Fixes applied:
  1. Uses get_client() instead of removed TMTClient()
  2. Guards against paragraphs with no runs (prevents IndexError crash)
  3. Preserves first run's formatting (bold, italic, font size, colour, etc.)
     and clears only the remaining runs, not all of them
"""

from docx import Document
from core.tmt_client import get_client


def translate_docx(
    input_path: str,
    output_path: str,
    source_lang: str,
    target_lang: str,
) -> str:
    """
    Translate all paragraphs in a .docx file while preserving formatting.

    Args:
        input_path:  Path to the original .docx file.
        output_path: Path where the translated .docx will be saved.
        source_lang: e.g. "en"
        target_lang: e.g. "ne"

    Returns:
        output_path — the path of the saved translated file.
    """
    # Step 1 — open the original docx
    doc = Document(input_path)

    # Step 2 — get the right client (mock or real, depending on .env)
    client = get_client()

    # Step 3 — translate every paragraph
    for paragraph in doc.paragraphs:

        # Skip paragraphs that are empty or whitespace-only
        if not paragraph.text.strip():
            continue

        # Skip paragraphs that have no runs — nothing to write into
        # (can happen with certain Word-generated styles or section markers)
        if not paragraph.runs:
            continue

        # Translate the full paragraph text
        translated = client.translate(paragraph.text, source_lang, target_lang)

        # Write translated text into the FIRST run — this preserves its
        # formatting (bold, italic, font size, colour, underline, etc.)
        paragraph.runs[0].text = translated

        # Clear all remaining runs so the original text doesn't bleed through
        for run in paragraph.runs[1:]:
            run.text = ""

    # Step 4 — save the translated docx
    doc.save(output_path)

    return output_path