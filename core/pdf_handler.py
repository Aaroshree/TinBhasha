"""
core/pdf_handler.py
TinBhasha — PDF Translation Handler
Reads a .pdf file page by page, translates all text AND table content,
writes a new translated .pdf preserving basic layout.
"""

import os
import re

import pdfplumber
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from core.tmt_client import get_client


# ---------------------------------------------------------------------------
# Page content model
# ---------------------------------------------------------------------------

PageBlocks = list[dict]


# ---------------------------------------------------------------------------
# Protected terms — never translated
# ---------------------------------------------------------------------------

PROTECTED_TERMS = {"TinBhasha", "tinbhasha", "TINBHASHA"}


def _should_skip_translation(text: str) -> bool:
    """Skip translation for protected brand names/proper nouns."""
    return any(term in text for term in PROTECTED_TERMS)


# ---------------------------------------------------------------------------
# Font setup
# ---------------------------------------------------------------------------

_FONT_NAME      = "Helvetica"
_FONT_NAME_BOLD = "Helvetica-Bold"
_font_cache: dict[str, tuple[str, str]] = {}


def _register_unicode_font() -> tuple[str, str]:
    """Register best available Unicode font; return (regular, bold). Cached."""
    if "result" in _font_cache:
        return _font_cache["result"]

    project_dir = os.path.dirname(os.path.abspath(__file__))
    r_path = os.path.join(project_dir, "NotoSansDevanagari_Condensed-Regular.ttf")
    b_path = os.path.join(project_dir, "NotoSansDevanagari_Condensed-Bold.ttf")

    if os.path.isfile(r_path):
        try:
            pdfmetrics.registerFont(TTFont("NotoDevanagari", r_path))
            if os.path.isfile(b_path):
                pdfmetrics.registerFont(TTFont("NotoDevanagari-Bold", b_path))
                _font_cache["result"] = ("NotoDevanagari", "NotoDevanagari-Bold")
            else:
                _font_cache["result"] = ("NotoDevanagari", "NotoDevanagari")
            return _font_cache["result"]
        except Exception:
            pass

    _font_cache["result"] = (_FONT_NAME, _FONT_NAME_BOLD)
    return _font_cache["result"]


# ---------------------------------------------------------------------------
# Extraction — structured blocks per page
# ---------------------------------------------------------------------------

def _extract_pages(input_path: str) -> list[PageBlocks]:
    all_pages: list[PageBlocks] = []

    with pdfplumber.open(input_path) as pdf:
        for page in pdf.pages:
            blocks: PageBlocks = []

            tables_found = page.find_tables()
            table_bboxes = [t.bbox for t in tables_found]

            def _in_table_bbox(word: dict) -> bool:
                y_mid = (word["top"] + word["bottom"]) / 2
                x_mid = (word["x0"]  + word["x1"])    / 2
                for (x0, y0, x1, y1) in table_bboxes:
                    if x0 <= x_mid <= x1 and y0 <= y_mid <= y1:
                        return True
                return False

            words_by_line: dict[int, list[str]] = {}
            for word in page.extract_words(x_tolerance=3, y_tolerance=3):
                if not _in_table_bbox(word):
                    key = round(word["top"])
                    words_by_line.setdefault(key, []).append(word["text"])

            text_blocks: list[tuple[float, dict]] = [
                (y, {"type": "text", "line": " ".join(words)})
                for y, words in sorted(words_by_line.items())
                if words
            ]

            table_blocks: list[tuple[float, dict]] = []
            for tbl_obj in tables_found:
                raw_rows = tbl_obj.extract()
                if not raw_rows:
                    continue
                clean_rows = [
                    [str(cell).strip() if cell is not None else "" for cell in row]
                    for row in raw_rows
                ]
                y_top = tbl_obj.bbox[1]
                table_blocks.append((y_top, {"type": "table", "rows": clean_rows}))

            all_blocks = text_blocks + table_blocks
            all_blocks.sort(key=lambda x: x[0])
            blocks = [b for _, b in all_blocks]

            all_pages.append(blocks)

    return all_pages


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _collect_unique_texts(pages: list[PageBlocks]) -> set[str]:
    unique: set[str] = set()
    for blocks in pages:
        for block in blocks:
            if block["type"] == "text":
                t = block["line"].strip()
                if t:
                    unique.add(t)
            else:
                for row in block["rows"]:
                    for cell in row:
                        t = cell.strip()
                        if t:
                            unique.add(t)
    return unique


def _build_translation_cache(
    unique_texts: set[str],
    source_lang: str,
    target_lang: str,
) -> dict[str, str]:
    client = get_client()
    result = {}
    for text in unique_texts:
        if _should_skip_translation(text):
            result[text] = text  # keep original
        else:
            result[text] = client.translate(text, source_lang, target_lang)
    return result


# ---------------------------------------------------------------------------
# Story builder
# ---------------------------------------------------------------------------

def _safe(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _is_heading(line: str) -> bool:
    return (line.isupper() and len(line) > 2) or (
        len(line) <= 60 and line.istitle() and not re.search(r"[.,:;?!]", line)
    )


def _build_table_flowable(
    rows: list[list[str]],
    cache: dict[str, str],
    font_name: str,
    font_bold: str,
    page_width_pts: float,
    h_margin_pts: float,
) -> Table:
    cell_style = ParagraphStyle(
        "TBCell", fontName=font_name, fontSize=9, leading=13, wordWrap="CJK",
    )
    header_style = ParagraphStyle(
        "TBCellHdr", fontName=font_bold, fontSize=9, leading=13,
        textColor=colors.white, wordWrap="CJK",
    )

    translated_rows = []
    for row_idx, row in enumerate(rows):
        style = header_style if row_idx == 0 else cell_style
        translated_rows.append([
            Paragraph(_safe(cache.get(cell.strip(), cell.strip()) if cell.strip() else ""), style)
            for cell in row
        ])

    usable_width = page_width_pts - 2 * h_margin_pts
    num_cols     = max(len(r) for r in rows) if rows else 1
    col_width    = usable_width / num_cols

    tbl = Table(translated_rows, colWidths=[col_width] * num_cols, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  colors.HexColor("#c61e3a")),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff5f7")]),
        ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#e8cfa0")),
        ("BOX",            (0, 0), (-1, -1), 0.8, colors.HexColor("#c61e3a")),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return tbl


def _build_pdf_story(
    pages: list[PageBlocks],
    cache: dict[str, str],
    font_name: str,
    font_bold: str,
) -> list:
    PAGE_W, _ = A4
    H_MARGIN  = 20 * mm

    normal_style = ParagraphStyle(
        "TBNormal", fontName=font_name, fontSize=10, leading=14, spaceAfter=2,
    )
    heading_style = ParagraphStyle(
        "TBHeading", fontName=font_bold, fontSize=12, leading=16,
        spaceBefore=6, spaceAfter=4,
    )

    story = []

    for page_idx, blocks in enumerate(pages):
        if page_idx > 0:
            story.append(PageBreak())

        if not blocks:
            story.append(Spacer(1, 20 * mm))
            continue

        for block in blocks:
            if block["type"] == "text":
                line       = block["line"]
                translated = cache.get(line.strip(), line)
                style      = heading_style if _is_heading(line) else normal_style
                story.append(Paragraph(_safe(translated), style))

            else:
                story.append(Spacer(1, 3 * mm))
                story.append(_build_table_flowable(
                    block["rows"], cache, font_name, font_bold, PAGE_W, H_MARGIN
                ))
                story.append(Spacer(1, 3 * mm))

    return story


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def translate_pdf(
    input_path: str,
    output_path: str,
    source_lang: str,
    target_lang: str,
) -> str:
    # Step 1 — register best available Unicode font
    font_name, font_bold = _register_unicode_font()

    # Step 2 — extract structured blocks (text + table grids) per page
    pages = _extract_pages(input_path)

    # Step 3 — collect unique strings for deduplication
    unique_texts = _collect_unique_texts(pages)

    # Step 4 — translate each unique string exactly once
    cache = _build_translation_cache(unique_texts, source_lang, target_lang)

    # Step 5 — build Platypus story
    story = _build_pdf_story(pages, cache, font_name, font_bold)

    # Step 6 — render to PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    doc.build(story)

    return output_path