"""Layout-aware extraction of the two assignment PDFs.

PDF 2 (51st Shodhyatra, two Honey Bee newsletter articles)
    Text blocks are classified by font/size/position into title, running header,
    standfirst, heading, body, caption, footer and pull-quote. Body text is put in
    reading order (3-column layout), paragraphs that continue across columns/pages are
    re-joined, and every paragraph keeps its PDF page and printed page number.
    Footers, running headers and the newsletter's footer questions are excluded from
    the content but used as provenance (issue, printed page).

PDF 1 (53rd Shodhyatra presentation, Hindi)
    Per-slide text is extracted, the broken Devanagari is repaired
    (gian_kb.devanagari) and text hidden behind images (drawn earlier, then covered)
    is detected from the drawing order (``page.get_bboxlog``).

Outputs: data/interim/sy51_paragraphs.json, data/interim/sy53_slides_extracted.json
"""
from __future__ import annotations

import json
import re
from collections import Counter

import pymupdf

from . import devanagari
from .config import DOCUMENTS, INTERIM, PDF_SY51, PDF_SY53

FOOTER_Y = 725          # footer band of the newsletter pages (points)
COLUMN_LEFT_EDGES = (57, 226, 396)   # 3-column grid; a column spans [edge, next edge)


def _column(x0: float) -> int:
    col = 0
    for i, edge in enumerate(COLUMN_LEFT_EDGES):
        if x0 >= edge - 6:
            col = i
    return col


def _join_lines(lines: list[str]) -> str:
    out = ""
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if out.endswith("-") and ln[:1].islower():
            out += ln                       # keep real compound hyphen: millet-based
        else:
            out = f"{out} {ln}" if out else ln
    return re.sub(r"\s+", " ", out).strip()


def _fix_urls(text: str) -> str:
    """Re-join URLs that the layout broke across lines/columns."""
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"(https?://\S*[/\-_])\s+([\w\-./]+)", r"\1\2", text)
    return text


def _classify(font: str, size: float, y0: float, text: str) -> str:
    if y0 >= FOOTER_Y and size >= 11.5:
        return "footer"
    if font.startswith("Cambria-Bold"):
        return "running_header"
    if font.startswith("BirchStd"):
        return "title"
    if size > 30:
        return "drop_cap"
    if font.startswith("MinionPro-BoldIt"):
        return "caption"
    if font.startswith("MinionPro-Bold"):
        return "heading"
    if font.startswith("MinionPro-It"):
        # sidebar standfirst paragraphs are full sentences; photo captions carry no final period
        return "standfirst" if re.search(r"[.!?]\s*$", text) else "caption"
    return "body"


def extract_sy51() -> list[dict]:
    doc = pymupdf.open(PDF_SY51)
    page_to_doc = {}
    for did in ("SY51-HB-P1", "SY51-HB-P2"):
        for p, printed in DOCUMENTS[did]["pdf_to_printed_page"].items():
            page_to_doc[p] = (did, printed)

    items: list[dict] = []          # ordered content items across the whole file
    footers: list[dict] = []
    for pno, page in enumerate(doc, start=1):
        did, printed = page_to_doc[pno]
        page_items, drop_cap = [], ""
        for b in page.get_text("dict")["blocks"]:
            if b["type"] != 0:
                continue
            spans = [s for l in b["lines"] for s in l["spans"] if s["text"].strip()]
            if not spans:
                continue
            font, size = Counter((s["font"], round(s["size"], 1)) for s in spans).most_common(1)[0][0]
            x0, y0, x1, y1 = b["bbox"]
            lines = ["".join(s["text"] for s in l["spans"]) for l in b["lines"]]
            text = _join_lines(lines)
            role = _classify(font, size, y0, text)
            if role == "drop_cap":
                drop_cap = text
                continue
            if role == "footer":
                footers.append({"pdf_page": pno, "text": text})
                continue
            if role == "caption":
                # a caption block can hold two captions placed side by side: split the
                # spans by column, then rebuild each caption in (line, x) order
                by_col: dict[int, list[tuple]] = {}
                for s in spans:
                    by_col.setdefault(_column(s["bbox"][0]), []).append((round(s["bbox"][1]), s["bbox"][0], s["text"]))
                for col, ss in sorted(by_col.items()):
                    ss.sort()
                    page_items.append({"role": "caption", "col": col, "y": y0,
                                       "text": re.sub(r"\s+", " ", " ".join(t for _, _, t in ss)).strip()})
                continue
            page_items.append({"role": role, "col": _column(x0), "y": y0, "text": text})
        # reading order: title/header first, then columns left->right, top->bottom
        rank = {"running_header": 0, "title": 1}
        page_items.sort(key=lambda it: (rank.get(it["role"], 2), it["col"], it["y"]))
        if drop_cap:
            for it in page_items:
                if it["role"] == "body":
                    it["text"] = drop_cap + it["text"]
                    break
        for it in page_items:
            it.update({"document_id": did, "pdf_page": pno, "printed_page": printed})
            items.append(it)

    # merge body blocks that continue across columns / pages into paragraphs. A body block
    # continues the previous body paragraph when that paragraph has no sentence-final
    # punctuation; photo captions placed in between (layout) do not break the paragraph.
    paragraphs: list[dict] = []
    for it in items:
        if it["role"] in ("running_header",):
            continue
        last_body = None
        for j in range(len(paragraphs) - 1, -1, -1):
            if paragraphs[j]["role"] == "caption":
                continue
            last_body = paragraphs[j] if paragraphs[j]["role"] == "body" else None
            break
        continues = (
            last_body is not None and it["role"] == "body"
            and last_body["document_id"] == it["document_id"]
            and not re.search(r"[.!?:\"”)]\s*$", last_body["text"])
        )
        if continues:
            sep = "" if last_body["text"].endswith("-") and it["text"][:1].islower() else " "
            last_body["text"] = last_body["text"] + sep + it["text"]
            if it["pdf_page"] not in last_body["pdf_pages"]:
                last_body["pdf_pages"].append(it["pdf_page"])
                last_body["printed_pages"].append(it["printed_page"])
            continue
        paragraphs.append({"document_id": it["document_id"], "role": it["role"], "text": it["text"],
                           "pdf_pages": [it["pdf_page"]], "printed_pages": [it["printed_page"]]})
    for p in paragraphs:
        p["text"] = _fix_urls(p["text"])
    out = {"paragraphs": paragraphs, "excluded_footers": footers}
    INTERIM.mkdir(parents=True, exist_ok=True)
    (INTERIM / "sy51_paragraphs.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return paragraphs


def _hidden_text(page) -> str:
    """Text whose bounding box is (>=90 %) covered by an image/fill drawn *after* it."""
    log = page.get_bboxlog()
    hidden = []
    for i, (typ, bb) in enumerate(log):
        if "text" not in typ:
            continue
        r = pymupdf.Rect(bb)
        if r.is_empty or r.get_area() == 0:
            continue
        for t2, b2 in log[i + 1:]:
            if "image" in t2 or t2 == "fill-path":
                inter = r & pymupdf.Rect(b2)
                if not inter.is_empty and inter.get_area() / r.get_area() > 0.9:
                    hidden.append(r)
                    break
    if not hidden:
        return ""
    union = hidden[0]
    for r in hidden[1:]:
        union |= r
    return page.get_textbox(union)


def extract_sy53() -> list[dict]:
    doc = pymupdf.open(PDF_SY53)
    slides = []
    for sno, page in enumerate(doc, start=1):
        raw = page.get_text()
        hidden_raw = _hidden_text(page)
        fixed = devanagari.repair(raw)
        hidden_fixed = devanagari.repair(hidden_raw) if hidden_raw else ""
        slides.append({
            "slide": sno,
            "raw_text": raw,
            "repaired_text": fixed,
            "hidden_text_repaired": hidden_fixed,
            "has_visible_text": bool(raw.strip()) and (not hidden_raw or len(raw.strip()) > len(hidden_raw.strip()) + 20),
            "image_count": len(page.get_images()),
            "residual_problems": devanagari.residual_problems(fixed),
        })
    meta = doc.metadata
    out = {"pdf_metadata": meta, "slide_count": doc.page_count, "slides": slides}
    (INTERIM / "sy53_slides_extracted.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return slides


if __name__ == "__main__":
    paras = extract_sy51()
    print("SY51 paragraphs:", len(paras), Counter(p["role"] for p in paras))
    slides = extract_sy53()
    print("SY53 slides:", len(slides), "with residual problems:",
          [s["slide"] for s in slides if s["residual_problems"]],
          "hidden text on slides:", [s["slide"] for s in slides if s["hidden_text_repaired"]])
