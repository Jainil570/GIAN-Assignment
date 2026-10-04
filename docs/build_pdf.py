"""Render docs/*.md to PDF (Markdown -> HTML -> headless Microsoft Edge 'print to PDF').

    python docs/build_pdf.py DATA_ANALYSIS_REPORT.md SYSTEM.md
"""
import subprocess
import sys
from pathlib import Path

import markdown

DOCS = Path(__file__).resolve().parent
EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
CSS = """
body { font-family: 'Segoe UI', 'Nirmala UI', Arial, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #1b1b1b;
       max-width: 100%; margin: 0; }
h1 { font-size: 20pt; border-bottom: 2px solid #c8a200; padding-bottom: 4px; }
h2 { font-size: 14pt; margin-top: 18pt; border-bottom: 1px solid #ddd; padding-bottom: 2px; }
h3 { font-size: 11.5pt; margin-top: 12pt; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt; font-size: 9pt; page-break-inside: auto; }
th, td { border: 1px solid #bbb; padding: 3px 5px; vertical-align: top; text-align: left; }
th { background: #f3f0e0; }
tr { page-break-inside: avoid; }
code { font-family: Consolas, monospace; font-size: 8.8pt; background: #f4f4f4; padding: 0 2px; }
pre { background: #f6f6f6; border: 1px solid #ddd; padding: 6px; white-space: pre-wrap; font-size: 8.5pt; }
@page { size: A4; margin: 16mm 14mm; }
"""


def build(md_name: str) -> Path:
    src = DOCS / md_name
    body = markdown.markdown(src.read_text(encoding="utf-8"), extensions=["tables", "fenced_code", "sane_lists"])
    html = DOCS / (src.stem + ".html")
    html.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>",
                    encoding="utf-8")
    pdf = DOCS / (src.stem + ".pdf")
    edge = next(p for p in EDGE if Path(p).exists())
    subprocess.run([edge, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}",
                    html.as_uri()], check=True, capture_output=True, timeout=120)
    html.unlink()
    return pdf


if __name__ == "__main__":
    for name in sys.argv[1:] or ["DATA_ANALYSIS_REPORT.md"]:
        print("written", build(name))
