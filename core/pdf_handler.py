"""
core/pdf_handler.py
TinBhasha — PDF Translation Handler
Reads a .pdf file page by page, translates all text AND table content,
writes a new translated .pdf preserving basic layout.
Uses pymupdf (fitz) for span-level font metadata extraction.
"""

import os

import fitz  # pymupdf
import pdfplumber
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
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
# Extraction — structured blocks per page using pymupdf + pdfplumber
# ---------------------------------------------------------------------------

def _extract_pages(input_path: str) -> list[PageBlocks]:
    all_pages: list[PageBlocks] = []

    # pdfplumber is kept solely for table extraction (more reliable)
    with pdfplumber.open(input_path) as plumber_pdf, fitz.open(input_path) as fitz_doc:

        for page_idx, fitz_page in enumerate(fitz_doc):
            blocks: PageBlocks = []
            page_width = fitz_page.rect.width

            # ── Table extraction via pdfplumber ───────────────────────────
            plumber_page = plumber_pdf.pages[page_idx]
            tables_found = plumber_page.find_tables()
            table_bboxes = [t.bbox for t in tables_found]  # (x0, y0, x1, y1)

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

            # ── Text extraction via pymupdf (span-level) ──────────────────
            captured_bboxes = table_bboxes  # capture per-iteration value

            def _in_table(x0, y0, x1, y1, _bboxes=captured_bboxes):
                cx = (x0 + x1) / 2
                cy = (y0 + y1) / 2
                for (tx0, ty0, tx1, ty1) in _bboxes:
                    if tx0 <= cx <= tx1 and ty0 <= cy <= ty1:
                        return True
                return False
            # Extract underline paths (horizontal drawn lines)
            underline_ys = set()
            for path in fitz_page.get_drawings():
                if path.get("type") == "s":  # stroke only
                    for item in path.get("items", []):
                        if item[0] == "l":  # line
                            p1, p2 = item[1], item[2]
                            if abs(p1.y - p2.y) < 2:  # horizontal line
                                underline_ys.add(round(p1.y))
            

            text_blocks: list[tuple[float, dict]] = []
            page_dict = fitz_page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

            for fitz_block in page_dict.get("blocks", []):
                if fitz_block.get("type") != 0:  # 0 = text block
                    continue

                for line in fitz_block.get("lines", []):
                    spans = line.get("spans", [])
                    if not spans:
                        continue

                    # Skip if inside a table
                    bbox = spans[0]["bbox"]
                    if _in_table(bbox[0], bbox[1], bbox[2], bbox[3]):
                        continue

                    # Collect span-level formatting
                    line_spans = []
                    full_text  = ""
                    for span in spans:
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        flags        = span.get("flags", 0)
                        font         = span.get("font", "")
                        is_bold      = bool(flags & 2**4) or "Bold" in font or "bold" in font
                        is_italic    = bool(flags & 2**1) or "Italic" in font or "italic" in font
                        span_y = round(span["bbox"][3])  # bottom of span
                        is_underline = any(abs(span_y - uy) < 6 for uy in underline_ys)
                        fontsize     = round(span.get("size", 10))

                        line_spans.append({
                            "text":        text,
                            "is_bold":     is_bold,
                            "is_italic":   is_italic,
                            "is_underline": is_underline,
                            "fontsize":    fontsize,
                        })
                        full_text += (" " if full_text else "") + text

                    if not full_text.strip():
                        continue

                    # Dominant span = longest span (drives line-level style)
                    dominant = max(line_spans, key=lambda s: len(s["text"]))

                    y_top = line["bbox"][1]
                    text_blocks.append((y_top, {
                        "type":        "text",
                        "line":        full_text,
                        "spans":       line_spans,
                        "fontsize":    dominant.get("fontsize", 10),
                        "is_bold":     dominant.get("is_bold", False),
                        "is_italic":   dominant.get("is_italic", False),
                        "is_underline": dominant.get("is_underline", False),
                        "x0":          fitz_block["bbox"][0],
                    }))

            # ── Merge and sort all blocks by y position ───────────────────
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
        try:
            result[text] = client.translate(text, source_lang, target_lang)
        except Exception:
            result[text] = text
    return result

# ---------------------------------------------------------------------------
# Story builder
# ---------------------------------------------------------------------------

def _safe(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _is_heading(line: str, fontsize: float = 10, is_bold: bool = False) -> bool:
    """Detect headings using font metadata; fall back to text pattern."""
    is_large = fontsize >= 14
    return is_large or (is_bold and fontsize >= 11) or (line.isupper() and len(line) > 2)


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


def _build_span_paragraph(
    spans: list[dict],
    cache: dict[str, str],
    full_line: str,
    font_name: str,
    font_bold: str,
    base_fontsize: float,
    is_heading: bool,
) -> Paragraph:
    """Build a Paragraph styled from dominant span's font metadata."""
    translated_line = cache.get(full_line.strip(), full_line)

    # Use dominant span (longest text) to drive the paragraph style
    dominant    = max(spans, key=lambda s: len(s["text"])) if spans else {}
    is_italic    = dominant.get("is_italic", False)
    is_underline = dominant.get("is_underline", False)
    is_bold      = (dominant.get("is_bold", False) or is_heading) and not is_italic
    fontsize    = min(max(dominant.get("fontsize", base_fontsize), 8), 18)
    leading     = fontsize + 4
    fn          = font_bold if is_bold else font_name

    style_kwargs = {
        "fontName":   fn,
        "fontSize":   fontsize,
        "leading":    leading,
        "spaceAfter": 2,
        "spaceBefore": 6 if is_heading else 0,
    }
    if is_underline:
        style_kwargs["underlineWidth"] = 1
        style_kwargs["underlineColor"] = "black"
        style_kwargs["underlineOffset"] = -2
        style_kwargs["underline"] = True

    style = ParagraphStyle("TBSpan", **style_kwargs)

    safe_text = _safe(translated_line)
    if is_underline:
        display_text = f'<u>{safe_text}</u>'
    else:
        display_text = safe_text

    return Paragraph(display_text, style)


def _build_pdf_story(
    pages: list[PageBlocks],
    cache: dict[str, str],
    font_name: str,
    font_bold: str,
) -> list:
    PAGE_W, _ = A4
    H_MARGIN  = 20 * mm

    story = []

    for page_idx, blocks in enumerate(pages):
        if page_idx > 0:
            story.append(PageBreak())

        if not blocks:
            story.append(Spacer(1, 20 * mm))
            continue

        for block in blocks:
            if block["type"] == "text":
                line     = block["line"]
                fontsize = block.get("fontsize", 10)
                is_bold  = block.get("is_bold", False)
                spans    = block.get("spans", [])
                heading  = _is_heading(line, fontsize, is_bold)

                story.append(_build_span_paragraph(
                    spans, cache, line, font_name, font_bold, fontsize, heading
                ))

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