"""Repair Devanagari text extracted from the 53rd Shodhyatra presentation PDF.

The PDF was produced with PScript5/Acrobat Distiller. Its embedded Hindi font has an
incomplete ToUnicode map, so text extraction returns three kinds of corruption:

1. Conjunct / ligature glyphs are emitted as unrelated Latin code points
   (e.g. ``è`` for ``स्``, ``Ú`` for ``ध्``, ``Ʌ`` for ``ें``).
2. The short-i matra (ि) is emitted in *visual* order, i.e. before the consonant
   cluster it belongs to (``िकया`` instead of ``किया``).
3. The reph (र् written above the next letter) is emitted after the syllable it sits on
   (``कायर्`` instead of ``कार्य``).

The repair is deterministic: a glyph map (built by aligning extracted text with the
rendered slides), then i-matra reordering, then reph reordering. Every slide was checked
against its rendered image afterwards; residual problems (missing spaces in one line)
are fixed through documented overrides in ``data/curated/sy53_slides.json``.
"""
from __future__ import annotations

import re

# Latin code point emitted by the broken font  ->  intended Devanagari sequence
GLYPH_MAP: dict[str, str] = {
    "Ʌ": "ें",              # Ʌ -> ें
    "ɉ": "ों",              # ɉ -> ों
    "ɇ": "ैं",              # ɇ -> ैं
    "ɋ": "ौं",              # ɋ -> ौं
    "è": "स्",              # è -> स्
    "Û": "न्",              # Û -> न्
    "ã": "ल्",              # ã -> ल्
    "×": "त्",              # × -> त्
    "Ú": "ध्",              # Ú -> ध्
    "Í": "च्",              # Í -> च्
    "å": "व्",              # å -> व्
    "ɮ": "द्",              # ɮ -> द्
    "à": "म्",              # à -> म्
    "ç": "ष्",              # ç -> ष्
    "æ": "श्",              # æ -> श्
    "Þ": "ब्",              # Þ -> ब्
    "Ü": "प्",              # Ü -> प्
    "Ï": "ज्",              # Ï -> ज्
    "ɬ": "ड्",              # ɬ -> ड्
    "ɪ": "ट्",              # ɪ -> ट्
    "Ö": "ण्",              # Ö -> ण्
    "Ø": "थ्",              # Ø -> थ्
    "é": "ह्",              # é -> ह्
    "ó": "ज़्",        # ó -> ज़्
    "ê": "क्ष्",  # ê -> क्ष्
    "Į": "श्र",        # Į -> श्र
    "İ": "स्र",        # İ -> स्र
    "Ƨ": "द्द",        # Ƨ -> द्द
    "Ǻ": "दृ",              # Ǻ -> दृ
    "Ǿ": "रू",              # Ǿ -> रू
    "ǽ": "रु",              # ǽ -> रु
    # glyphs that combine a vowel sign with a (visually trailing) reph; the reph is
    # emitted last so that the reph-reordering step below moves it into place
    "ɟ": "ोंर्",  # ɟ -> ों + र्   (वषɟ -> वर्षों)
    "ȶ": "ेर्",        # ȶ -> े + र्    (खचȶ -> खर्चे)
}

_CONS = "[क-हक़-य़]़?"                 # consonant (+ optional nukta)
_CLUSTER = f"(?:{_CONS}्)*{_CONS}"                        # C(्C)*
_VSIGNS = "[ा-ौँ-ःॢॣ]"          # dependent vowel signs, ं ँ ः

_I_MATRA = re.compile(f"ि({_CLUSTER})")                   # ि + cluster  -> cluster + ि
_REPH = re.compile(f"({_CLUSTER})({_VSIGNS}*)र्")     # syllable + र् -> र् + syllable

SUSPICIOUS = re.compile("[" + "".join(GLYPH_MAP) + "]")


def repair(text: str) -> str:
    """Return logically ordered Unicode Devanagari for text extracted from the PDF."""
    text = "".join(GLYPH_MAP.get(ch, ch) for ch in text)
    text = _I_MATRA.sub(lambda m: m.group(1) + "ि", text)
    text = _REPH.sub(lambda m: "र्" + m.group(1) + m.group(2), text)
    return text


def residual_problems(text: str) -> list[str]:
    """Patterns that indicate the repair did not fully succeed (used as a QA check)."""
    problems = []
    if SUSPICIOUS.search(text):
        problems.append("unmapped legacy glyph")
    if re.search(r"(^|[\s।])ि", text):
        problems.append("i-matra at word start")
    if re.search(r"(^|\s)र्(\s|$)", text):
        problems.append("dangling reph")
    return problems
