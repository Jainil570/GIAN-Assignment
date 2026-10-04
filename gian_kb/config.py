"""Central configuration: paths, source registry, model and database settings.

Everything that describes *where data came from* lives in ``DOCUMENTS`` so that every
chunk can inherit the same, verified provenance fields (source URL, title, issue, ...).
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
CURATED = DATA / "curated"
PROCESSED = DATA / "processed"

PIPELINE_VERSION = "1.0.0"

# --------------------------------------------------------------------------------------
# Source files exactly as supplied with the assignment (kept untouched in sources/, not in git)
# --------------------------------------------------------------------------------------
PDF_SY53 = ROOT / "sources" / "53rd_Shodyatra_Presentation 1.pdf"
PDF_SY51 = ROOT / "sources" / "51-sy June 17 - 23, 2024, Harima-Chak Dhani  Rajasthan.pdf"

GIAN_NIDHI_URL = "https://gian.org/gian-nidhi/"
GIAN_AJAX_URL = "https://gian.org/wp-admin/admin-ajax.php"

# --------------------------------------------------------------------------------------
# Models / infrastructure (override in .env)
# --------------------------------------------------------------------------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3")          # BAAI/bge-m3 served by Ollama
EMBED_MODEL_HF = "BAAI/bge-m3"                              # same weights on Hugging Face
EMBED_DIM = 1024

LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b-instruct-q4_K_M")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gian:gian_local_dev@localhost:5433/gian_kb")

# --------------------------------------------------------------------------------------
# Source registry. One entry per *logical* document. Note that assignment PDF 2 contains
# two different newsletter articles (two Honey Bee issues), so it yields two documents.
# The Google Drive file IDs were verified against the Drive page titles.
# --------------------------------------------------------------------------------------
DRIVE_URL_SY53 = "https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view"
DRIVE_URL_SY51 = "https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view"

DOCUMENTS: dict[str, dict] = {
    "SY53-PPT": {
        "document_id": "SY53-PPT",
        "source": "53rd Shodhyatra presentation (assignment PDF 1)",
        "source_type": "pdf_presentation",
        "source_file": PDF_SY53.name,
        "source_url": DRIVE_URL_SY53,
        "document_title": "53 वीं शोधयात्रा: भूरीमाटी, जिला-झाबुआ, मध्यप्रदेश से अंबाला, जिला-छोटाउदेपुर, गुजरात (दिनांक: 04 से 10 जून, 2025)",
        "document_title_en": "53rd Shodhyatra: Bhurimati (Jhabua district, Madhya Pradesh) to Ambala (Chhota Udepur district, Gujarat), 04-10 June 2025",
        "author": None,
        "author_note": "No author or presenter is named on any slide. The PDF metadata field Author='Admin' is a generic account name and is not treated as an author.",
        "publication_name": None,
        "publication_issue": None,
        "publication_year": 2025,
        "date_note": "Event dates 04-10 June 2025 (title slide). PDF file created 2025-07-23 (file metadata).",
        "language": "hi",
        "organisations": ["Honey Bee Network", "SRISTI", "SRISTI Innovations", "GIAN"],
        "organisation_note": "Organisations shown as logos on the title slide (slide 1); roles (organiser/supporter) are not stated in this document.",
        "event_id": "EVT-SY53",
        "locator_unit": "slide",
    },
    "SY51-HB-P1": {
        "document_id": "SY51-HB-P1",
        "source": "Honey Bee newsletter article (assignment PDF 2, PDF pages 1-3)",
        "source_type": "pdf_newsletter_article",
        "source_file": PDF_SY51.name,
        "source_url": DRIVE_URL_SY51,
        "document_title": "51st Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani | Rajasthan : Part-I",
        "document_title_en": "51st Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani | Rajasthan : Part-I",
        "author": None,
        "author_note": "No byline is printed on the article pages.",
        "publication_name": "Honey Bee",
        "publication_issue": "Vol 35 (3) July - September 2024",
        "publication_year": 2024,
        "date_note": "Event dates June 17-23, 2024 (article title).",
        "language": "en",
        "organisations": [],
        "event_id": "EVT-SY51",
        "locator_unit": "page",
        "pdf_to_printed_page": {1: 13, 2: 14, 3: 15},
    },
    "SY51-HB-P2": {
        "document_id": "SY51-HB-P2",
        "source": "Honey Bee newsletter article (assignment PDF 2, PDF pages 4-6)",
        "source_type": "pdf_newsletter_article",
        "source_file": PDF_SY51.name,
        "source_url": DRIVE_URL_SY51,
        "document_title": "The pain behind the glitter! 51 Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani, Nagaur | Rajasthan : Part-II",
        "document_title_en": "The pain behind the glitter! 51 Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani, Nagaur | Rajasthan : Part-II",
        "author": None,
        "author_note": "No byline is printed on the article pages.",
        "publication_name": "Honey Bee",
        "publication_issue": "Vol 35 (4) October - December 2024",
        "publication_year": 2024,
        "date_note": "Event dates June 17-23, 2024 (article title).",
        "language": "en",
        "organisations": ["SRISTI", "GIAN", "Honey Bee Network"],
        "organisation_note": "'The Shodhyatra, organized by SRISTI, supported by GIAN and the Honey Bee Network' (printed p. 2).",
        "event_id": "EVT-SY51",
        "locator_unit": "page",
        "pdf_to_printed_page": {4: 2, 5: 3, 6: 4},
    },
    "GIAN-NIDHI": {
        "document_id": "GIAN-NIDHI",
        "source": "GIAN Nidhi web repository (gian.org)",
        "source_type": "web_table",
        "source_file": "data/processed/gian_nidhi_projects.csv",
        "source_url": GIAN_NIDHI_URL,
        "document_title": "GIAN NIDHI - Diploma & ITI Projects",
        "document_title_en": "GIAN NIDHI - Diploma & ITI Projects",
        "author": None,
        "author_note": "Records list project participants; no author of the web page/dataset is stated.",
        "publication_name": "GIAN website (gian.org)",
        "publication_issue": None,
        "publication_year": None,
        "date_note": "Records carry no dates; retrieval timestamp is stored per record (retrieved_at).",
        "language": "en",
        "organisations": ["GIAN"],
        "organisation_note": "Page text: 'GIANNIDHI: A national repository of projects carried out by the ITI and Polytechnic students ...'",
        "event_id": None,
        "locator_unit": "record",
    },
}
