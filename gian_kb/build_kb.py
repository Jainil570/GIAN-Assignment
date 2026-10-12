"""Build the AI-ready knowledge base: chunks + entities + mentions + relationships.

Inputs
    data/interim/sy51_paragraphs.json        (extract_pdfs)
    data/interim/sy53_slides_extracted.json  (extract_pdfs)
    data/processed/gian_nidhi_projects.json  (clean_gian_nidhi)
    data/curated/*.json                      (manual curation: slides, entities, relationships, image text)

Chunking strategy
    * 51st Shodhyatra articles: section-aware paragraph packing (<= ~230 words), never
      crossing a heading or an article boundary; photo captions stay with the page they
      belong to; text found only in images becomes separate 'image_text' chunks.
    * 53rd Shodhyatra deck: one chunk per curated *unit* = one story told over 1-4
      consecutive slides (e.g. a name slide + its description slide). Slide numbers are
      kept per sentence block ("[Slide 48] ...") so citations point to exact slides.
    * GIAN Nidhi: one chunk per project record; exact duplicate records are folded into
      the canonical record's chunk (all record IDs kept), probable duplicates keep their
      own chunk with a duplicate_group_id.

Every chunk carries the same metadata schema (see docs/METADATA_SCHEMA.md).

Outputs (data/processed/): documents.json, chunks.jsonl, entities.jsonl, entities.csv,
entity_mentions.csv, relationships.csv, data_quality_issues.csv
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from .config import CURATED, DOCUMENTS, INTERIM, PIPELINE_VERSION, PROCESSED, RAW

MAX_WORDS = 230
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
PHONE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}\s?\d{5}(?!\d)")
PHONE_MARK = {"hi": "[फ़ोन नंबर हटाया गया]", "en": "[phone number removed]"}

PERSONISH = {"person"}
INNOVATION_TYPES = {"innovation", "practice", "craft", "idea", "product", "crop_variety", "traditional_knowledge",
                    "traditional_food", "art_form", "project"}
ORG_TYPES = {"organisation", "institution", "community"}
INNOVATOR_PREDICATES = {"innovator_of", "idea_of", "created", "practises", "conserves", "conserved_and_promoted",
                        "promotes", "made", "knowledge_holder_of", "teaches", "led", "runs", "established",
                        "founded", "demonstrated", "grew", "has_participant"}


def _h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _base_meta(doc_id: str) -> dict:
    d = DOCUMENTS[doc_id]
    return {k: d.get(k) for k in ("document_id", "source", "source_type", "source_url", "source_file",
                                  "document_title", "document_title_en", "author", "author_note",
                                  "publication_name", "publication_issue", "publication_year")}


# ------------------------------------------------------------------------------------------
# entity alias matching (scoped to documents)
# ------------------------------------------------------------------------------------------
class AliasMatcher:
    def __init__(self, entities: list[dict]):
        self.by_doc: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for e in entities:
            for a in e.get("aliases", []):
                for d in e.get("documents", []):
                    self.by_doc[d].append((a, e["id"]))
        for d in self.by_doc:   # longest alias first so 'Rameshwar Lal ji' wins over 'Khejri' etc.
            self.by_doc[d].sort(key=lambda t: -len(t[0]))

    @staticmethod
    def _find(alias: str, text: str) -> list[int]:
        hits = []
        if DEVANAGARI.search(alias):
            start = 0
            while (i := text.find(alias, start)) != -1:
                before = text[i - 1] if i > 0 else " "
                after = text[i + len(alias)] if i + len(alias) < len(text) else " "
                if not DEVANAGARI.match(before) and not re.match(r"[क-ह]", after):
                    hits.append(i)
                start = i + 1
        else:
            for m in re.finditer(r"(?<![\w/])" + re.escape(alias) + r"(?![\w])", text, flags=re.I if len(alias) > 4 else 0):
                hits.append(m.start())
        return hits

    def match(self, doc_id: str, text: str) -> list[tuple[str, str]]:
        found, taken = [], []
        for alias, eid in self.by_doc.get(doc_id, []):
            for i in self._find(alias, text):
                span = (i, i + len(alias))
                if any(s < span[1] and span[0] < e for s, e in taken):
                    continue
                taken.append(span)
                found.append((eid, text[span[0]:span[1]]))
        return found


# ------------------------------------------------------------------------------------------
# 51st Shodhyatra (Honey Bee articles)
# ------------------------------------------------------------------------------------------
def build_sy51(matcher: AliasMatcher) -> list[dict]:
    paras = _load(INTERIM / "sy51_paragraphs.json")["paragraphs"]
    images = _load(CURATED / "sy51_image_text.json")["items"]
    chunks: list[dict] = []
    for doc_id in ("SY51-HB-P1", "SY51-HB-P2"):
        dp = [p for p in paras if p["document_id"] == doc_id]
        title = " ".join(p["text"] for p in dp if p["role"] == "title")
        sections: list[dict] = []
        cur = {"heading": "Introduction", "items": []}
        for p in dp:
            if p["role"] == "title":
                continue
            if p["role"] == "heading":
                if cur["items"]:
                    sections.append(cur)
                cur = {"heading": p["text"].rstrip(":"), "items": []}
                continue
            cur["items"].append(p)
        if cur["items"]:
            sections.append(cur)

        n = 0
        for sec in sections:
            texts = [p for p in sec["items"] if p["role"] in ("body", "standfirst")]
            caps = [p for p in sec["items"] if p["role"] == "caption"]
            groups, g, words = [], [], 0
            for p in texts:
                w = len(p["text"].split())
                if g and words + w > MAX_WORDS:
                    groups.append(g)
                    g, words = [], 0
                g.append(p)
                words += w
            if g:
                groups.append(g)
            # a photo caption goes to the group on its page that shares the most words with it
            cap_home: dict[int, int] = {}
            for ci, c in enumerate(caps):
                cw = set(re.findall(r"[a-z]{4,}", c["text"].lower()))
                cands = [gi for gi, g in enumerate(groups)
                         if c["printed_pages"][0] in {pg for p in g for pg in p["printed_pages"]}]
                if cands:
                    cap_home[ci] = max(cands, key=lambda gi: (len(cw & set(re.findall(r"[a-z]{4,}", " ".join(
                        p["text"] for p in groups[gi]).lower()))), gi))
            for gi, g in enumerate(groups):
                pages = sorted({pg for p in g for pg in p["printed_pages"]})
                pdf_pages = sorted({pg for p in g for pg in p["pdf_pages"]})
                my_caps = [c for ci, c in enumerate(caps) if cap_home.get(ci) == gi]
                body = "\n\n".join(p["text"] for p in g)
                if my_caps:
                    body += "\n\n" + "\n".join(f"[Photo caption, p. {c['printed_pages'][0]}] {c['text']}" for c in my_caps)
                n += 1
                chunks.append(_sy51_chunk(doc_id, f"{doc_id}-C{n:02d}", title, sec["heading"], body, pages, pdf_pages,
                                          "narrative", matcher))
        for im in [i for i in images if i["document_id"] == doc_id]:
            n += 1
            body = f"[Photo caption, p. {im['printed_page']}] {im['caption']}\n[Text read from the image] {im['text']}"
            ch = _sy51_chunk(doc_id, f"{doc_id}-C{n:02d}", title, "Image: " + im["caption"], body,
                             [im["printed_page"]], [im["pdf_page"]], "image_text", matcher)
            ch["extraction_method"] = "visual_transcription_of_image"
            ch["quality_flags"].append("visual_transcription")
            ch["_curated_entities"] = list(dict.fromkeys(ch["_curated_entities"] + im["entities"]))
            chunks.append(ch)
    return chunks


def _sy51_chunk(doc_id, chunk_id, title, section, body, pages, pdf_pages, content_type, matcher):
    d = DOCUMENTS[doc_id]
    page_label = f"p. {pages[0]}" if len(pages) == 1 else f"pp. {pages[0]}-{pages[-1]}"
    header = f"[Source: Honey Bee {d['publication_issue']} | {title} | {page_label} | Section: {section}]"
    flags = []
    if "Rahulchand" in body or "Rawalchand" in body:
        flags.append("name_variant")
    if "Rameshwar" in body:
        flags.append("name_variant")
    return {
        "chunk_id": chunk_id, **_base_meta(doc_id),
        "event_id": d["event_id"], "section": section, "content_type": content_type,
        "data_category": "shodhyatra_report", "language": "en",
        "locator_type": "page", "printed_pages": pages, "pdf_pages": pdf_pages,
        "slides": [], "record_ids": [],
        "title": f"{title} - {section} ({page_label})",
        "text": body, "text_original": body, "text_en": body, "image_text": "",
        "embedding_header": header,
        "extraction_method": "pdf_text_layer_layout_aware",
        "translation": None, "quality_flags": sorted(set(flags)), "pii_redacted": False,
        # match the chunk body only: places in the article title are document context, not mentions
        "_mentions": matcher.match(doc_id, body),
        "_curated_entities": [d["event_id"]],          # every chunk of the article is about this event
    }


# ------------------------------------------------------------------------------------------
# 53rd Shodhyatra presentation
# ------------------------------------------------------------------------------------------
def build_sy53(entity_ids: set[str]) -> list[dict]:
    """Mentions for the deck are curated per unit (more precise than alias matching on Hindi)."""
    ext = {s["slide"]: s for s in _load(INTERIM / "sy53_slides_extracted.json")["slides"]}
    cur = _load(CURATED / "sy53_slides.json")
    sec_of = {}
    for s in cur["sections"]:
        for sl in range(s["first_slide"], s["last_slide"] + 1):
            sec_of[sl] = s["name"]
    chunks = []
    for u in cur["units"]:
        missing = [e for e in u["entities"] if e not in entity_ids]
        if missing:
            raise ValueError(f"{u['unit_id']}: unknown entity ids {missing}")
        blocks, pii = [], False
        for sl in u["slides"]:
            t = ext[sl]["repaired_text"]
            for fx in cur["text_fixes"]:
                if sl in fx["slides"]:
                    t = t.replace(fx["find"], fx["replace"])
            t = re.sub(r"[ \t]*\n[ \t]*", " ", t)          # slide line breaks are layout, not meaning
            t = re.sub(r"\s*•\s*", " ", t)
            t = re.sub(r"\s{2,}", " ", t).strip()
            if PHONE.search(t):
                pii = True
                t = PHONE.sub(PHONE_MARK["hi"], t)
            if t:
                blocks.append(f"[स्लाइड {sl}] {t}")
            else:
                blocks.append(f"[स्लाइड {sl}] (स्लाइड पर टेक्स्ट नहीं; केवल चित्र)")
        text_hi = "\n".join(blocks)
        image_text = "\n".join(f"[Slide {it['slide']} image text] {PHONE.sub(PHONE_MARK['hi'], it['text'])}"
                               for it in u.get("image_text", []))
        slides = u["slides"]
        label = f"slide {slides[0]}" if len(slides) == 1 else f"slides {slides[0]}-{slides[-1]}"
        section = sec_of.get(slides[0], "")
        flags = list(u.get("flags", []))
        if pii and "pii_redacted" not in flags:
            flags.append("pii_redacted")
        d = DOCUMENTS["SY53-PPT"]
        header = (f"[Source: 53rd Shodhyatra presentation (04-10 June 2025, Jhabua/Alirajpur MP - Chhota Udepur Gujarat) "
                  f"| {label} | Section: {section} | Topic: {u['title_en']}]")
        chunks.append({
            "chunk_id": f"SY53-PPT-{u['unit_id']}", **_base_meta("SY53-PPT"),
            "event_id": d["event_id"], "section": section, "content_type": "slide_unit",
            "data_category": "shodhyatra_presentation", "language": "hi+en",
            "locator_type": "slide", "printed_pages": [], "pdf_pages": slides, "slides": slides, "record_ids": [],
            "title": f"{u['title_en']} ({label})",
            "text": u["text_en"], "text_original": text_hi, "text_en": u["text_en"], "image_text": image_text,
            "embedding_header": header,
            "extraction_method": "pdf_text_layer + deterministic Devanagari repair + manual review against rendered slides"
                                 + (" + visual transcription of image text" if image_text else ""),
            "translation": {"source_language": "hi", "target_language": "en",
                            "method": "LLM-assisted translation during preprocessing, reviewed against slide images; Hindi original is authoritative"},
            "quality_flags": sorted(set(flags)), "pii_redacted": pii,
            "curation_notes": u.get("notes", ""),
            "_curated_entities": u["entities"],
            "_mentions": [],
        })
    return chunks


# ------------------------------------------------------------------------------------------
# GIAN Nidhi
# ------------------------------------------------------------------------------------------
def gian_page_context() -> str:
    soup = BeautifulSoup((RAW / "gian_nidhi" / "page_snapshot.html").read_text(encoding="utf-8"), "lxml")
    for t in soup(["script", "style", "noscript", "svg", "nav", "header"]):
        t.decompose()
    txt = soup.get_text("\n", strip=True)
    start = txt.find("Diploma & ITI Projects")
    end = txt.find("Registration Nos")
    core = txt[start:end] if start != -1 and end != -1 else txt
    core = re.sub(r"\n(ID|Column Status|Sr No|Project Name|Participants|Abstracts|College Status)(?=\n)", "", core)
    core = re.sub(r"\s*\n\s*", " ", core)                                  # HTML line wraps are layout only
    core = re.sub(r"\s+(Contribute to GIAN NIDHI|GIANNIDHI:|Donate for a noble cause|GIAN is the first incubator)",
                  r"\n\1", core)
    core = core.replace("GIAN NIDHI FORM Donate", "GIAN NIDHI FORM\nDonate")
    return core.strip()


def build_gian(projects: list[dict]) -> list[dict]:
    log = _load(RAW / "gian_nidhi" / "fetch_log.json")
    dupes_of = defaultdict(list)
    for p in projects:
        if p["duplicate_status"] == "exact_duplicate":
            dupes_of[p["duplicate_of"]].append(p["record_id"])
    chunks = []
    ctx = gian_page_context()
    chunks.append({
        "chunk_id": "GIAN-NIDHI-PAGE", **_base_meta("GIAN-NIDHI"),
        "event_id": None, "section": "Page description", "content_type": "web_page_context",
        "data_category": "web_page_context", "language": "en",
        "locator_type": "record", "printed_pages": [], "pdf_pages": [], "slides": [], "record_ids": [],
        "title": "GIAN NIDHI page - description and GIAN background",
        "text": ctx, "text_original": ctx, "text_en": ctx, "image_text": "",
        "embedding_header": "[Source: GIAN website, GIAN NIDHI page https://gian.org/gian-nidhi/ | page text]",
        "extraction_method": "web_page_html_snapshot", "translation": None, "quality_flags": [], "pii_redacted": False,
        "curation_notes": "Page table columns: ID, Column Status, Sr No, Project Name, Participants, Abstracts, College Status. "
                          "Observed in the data: 'College Status' holds the institution name; 'Column Status' is 'active' for all rows.",
        "retrieved_at": log["retrieved_at"], "_curated_entities": ["ORG-GIAN", "ORG-SRISTI", "ORG-IIMA", "ORG-HBN", "ORG-GOVT-GUJARAT"],
        "_mentions": [],
    })
    for p in projects:
        if p["duplicate_status"] == "exact_duplicate":
            continue
        rid = p["record_id"]
        ids = [rid] + sorted(dupes_of.get(str(rid), []))
        lines = [f"Project: {p['project_name']}"]
        lines.append("Participants: " + ("; ".join(p["participants"]) if p["participants"] else "(not listed)"))
        lines.append("Institution: " + (p["institution_canonical"] or "(not stated in the source record)"))
        if p["institution_name"] and p["institution_name"] != p["institution_canonical"]:
            lines.append(f"Institution as written in this record: {p['institution_name']}")
        lines.append("Abstract: " + (p["abstract"] or "(no abstract in the source record)"))
        body = "\n".join(lines)
        id_label = f"Record ID {rid}" + (f" (identical duplicate records: {', '.join(map(str, ids[1:]))})" if len(ids) > 1 else "")
        flags = list(p["flags"])
        if p["duplicate_status"] == "probable_duplicate":
            flags.append("probable_duplicate")
        chunks.append({
            "chunk_id": f"GIAN-NIDHI-R{rid:04d}", **_base_meta("GIAN-NIDHI"),
            "event_id": None, "section": "Diploma & ITI Projects", "content_type": "record",
            "data_category": "student_project", "language": "en",
            "locator_type": "record", "printed_pages": [], "pdf_pages": [], "slides": [], "record_ids": ids,
            "title": f"GIAN Nidhi record {rid}: {p['project_name']}",
            "text": body, "text_original": body, "text_en": body, "image_text": "",
            "embedding_header": f"[Source: GIAN NIDHI - Diploma & ITI Projects (gian.org) | {id_label}]",
            "extraction_method": "web_ajax_api (WP Data Access) + cleaning",
            "translation": None, "quality_flags": sorted(set(flags)), "pii_redacted": False,
            "retrieved_at": log["retrieved_at"],
            "gian_nidhi": {"record_id": rid, "sr_no": p["sr_no"], "project_name": p["project_name"],
                           "participants": p["participants"], "institution_id": p["institution_id"],
                           "institution_canonical": p["institution_canonical"],
                           "duplicate_group_id": p["duplicate_group_id"], "duplicate_status": p["duplicate_status"],
                           "duplicate_of": p["duplicate_of"]},
            "_curated_entities": [], "_mentions": [],
        })
    return chunks


def gian_entities(projects: list[dict]) -> tuple[list[dict], list[dict]]:
    """Institutions, participants and projects from the cleaned table (+ their relationships)."""
    import csv as _csv
    ents, rels = [], []
    with open(PROCESSED / "gian_nidhi_institutions.csv", encoding="utf-8-sig") as f:
        for row in _csv.DictReader(f):
            ents.append({"id": row["institution_id"], "type": "institution", "name": row["canonical_name"],
                         "aliases": row["name_variants"].split(" | "), "documents": ["GIAN-NIDHI"],
                         "description": f"Institution named in {row['record_count']} GIAN Nidhi record(s).",
                         "attributes": {"possible_same_as": row["possible_same_as"].split(),
                                        "reviewed_not_same_as": row["reviewed_not_same_as"].split()}})
    people: dict[tuple, dict] = {}
    for p in projects:
        canon = p["record_id"] if p["duplicate_status"] != "exact_duplicate" else int(p["duplicate_of"])
        pid = f"PRJ-{p['record_id']:04d}"
        ents.append({"id": pid, "type": "project", "name": p["project_name"], "aliases": [p["project_name"]],
                     "documents": ["GIAN-NIDHI"], "description": f"GIAN Nidhi record {p['record_id']}",
                     "attributes": {"record_id": p["record_id"], "chunk_record_id": canon}})
        if p["institution_id"]:
            rels.append({"s": pid, "p": "submitted_by_institution", "o": p["institution_id"], "status": "stated",
                         "evidence_chunks": [f"GIAN-NIDHI-R{canon:04d}"], "note": ""})
        if p["duplicate_of"]:
            rels.append({"s": pid, "p": "duplicate_of", "o": f"PRJ-{int(p['duplicate_of']):04d}",
                         "status": "stated" if p["duplicate_status"] == "exact_duplicate" else "probable",
                         "evidence_chunks": [f"GIAN-NIDHI-R{canon:04d}"],
                         "note": f"{p['duplicate_status']} (same title and team)"})
        for name in p["participants"]:
            key = (re.sub(r"[^a-z]", "", re.sub(r"^(mr|mrs|ms|miss|dr|prof)(\.\s*|\s+)", "", name.lower())),
                   p["institution_id"] or f"REC{p['record_id']}")
            if key not in people:
                people[key] = {"id": f"PER-GN-{len(people) + 1:05d}", "type": "person", "name": name, "aliases": [name],
                               "documents": ["GIAN-NIDHI"], "description": "Participant in GIAN Nidhi student project(s).",
                               "roles": ["student project participant"],
                               "link_note": "Same name is merged only within the same institution; identical names at different institutions stay separate."}
                ents.append(people[key])
            elif name not in people[key]["aliases"]:
                people[key]["aliases"].append(name)
            rels.append({"s": pid, "p": "has_participant", "o": people[key]["id"], "status": "stated",
                         "evidence_chunks": [f"GIAN-NIDHI-R{canon:04d}"], "note": ""})
    return ents, rels


# ------------------------------------------------------------------------------------------
def resolve_evidence(ev: dict, chunks_by_doc: dict[str, list[dict]], s: str, o: str) -> list[str]:
    cands = []
    for ch in chunks_by_doc.get(ev["doc"], []):
        if "page" in ev and ev["page"] in ch["printed_pages"]:
            cands.append(ch)
        elif "slide" in ev and ev["slide"] in ch["slides"]:
            cands.append(ch)
        elif "record" in ev and ev["record"] == "page" and ch["chunk_id"] == "GIAN-NIDHI-PAGE":
            cands.append(ch)
    both = [c for c in cands if s in c["entity_ids"] and o in c["entity_ids"]]
    either = [c for c in cands if s in c["entity_ids"] or o in c["entity_ids"]]
    return [c["chunk_id"] for c in (both or either or cands)]


def main() -> dict:
    ent_doc = _load(CURATED / "entities.json")["entities"]
    ids = [e["id"] for e in ent_doc]
    dup = [k for k, v in Counter(ids).items() if v > 1]
    if dup:
        raise ValueError(f"duplicate entity ids: {dup}")
    entity_ids = set(ids)
    matcher = AliasMatcher(ent_doc)

    projects = _load(PROCESSED / "gian_nidhi_projects.json")
    chunks = build_sy51(matcher) + build_sy53(entity_ids) + build_gian(projects)
    gn_ents, gn_rels = gian_entities(projects)
    entities = ent_doc + gn_ents
    ent_by_id = {e["id"]: e for e in entities}

    # mentions --------------------------------------------------------------------------------
    mentions = []
    for ch in chunks:
        seen = set()
        for eid, surface in ch.pop("_mentions"):
            if eid not in seen:
                mentions.append({"chunk_id": ch["chunk_id"], "entity_id": eid, "surface_form": surface, "method": "alias_match"})
                seen.add(eid)
        for eid in ch.pop("_curated_entities", []):
            if eid not in seen:
                mentions.append({"chunk_id": ch["chunk_id"], "entity_id": eid, "surface_form": "", "method": "curated"})
                seen.add(eid)
        if ch["data_category"] == "student_project":
            g = ch["gian_nidhi"]
            for rid in ch["record_ids"]:
                mentions.append({"chunk_id": ch["chunk_id"], "entity_id": f"PRJ-{rid:04d}", "surface_form": g["project_name"], "method": "structured_field"})
            if g["institution_id"]:
                mentions.append({"chunk_id": ch["chunk_id"], "entity_id": g["institution_id"], "surface_form": g["institution_canonical"], "method": "structured_field"})
        ch["entity_ids"] = sorted(seen)
    for r in gn_rels:                         # participants of each record chunk
        if r["p"] == "has_participant":
            for cid in r["evidence_chunks"]:
                mentions.append({"chunk_id": cid, "entity_id": r["o"], "surface_form": ent_by_id[r["o"]]["name"], "method": "structured_field"})
    by_chunk = defaultdict(set)
    for m in mentions:
        by_chunk[m["chunk_id"]].add(m["entity_id"])
    for ch in chunks:
        ch["entity_ids"] = sorted(by_chunk[ch["chunk_id"]])

    # relationships -------------------------------------------------------------------------------
    chunks_by_doc = defaultdict(list)
    for ch in chunks:
        chunks_by_doc[ch["document_id"]].append(ch)
    rels = []
    for i, r in enumerate(_load(CURATED / "relationships.json")["relationships"], start=1):
        for k in ("s", "o"):
            if r[k] not in ent_by_id:
                raise ValueError(f"relationship {i}: unknown entity {r[k]}")
        ev_chunks = sorted({cid for ev in r["evidence"] for cid in resolve_evidence(ev, chunks_by_doc, r["s"], r["o"])})
        if not ev_chunks:
            raise ValueError(f"relationship {i} {r['s']} {r['p']} {r['o']}: evidence did not resolve")
        rels.append({"rel_id": f"REL-{i:04d}", "subject_id": r["s"], "predicate": r["p"], "object_id": r["o"],
                     "status": r["status"], "evidence_chunk_ids": ev_chunks,
                     "evidence_locators": r["evidence"], "note": r.get("note", "")})
    for j, r in enumerate(gn_rels, start=len(rels) + 1):
        rels.append({"rel_id": f"REL-{j:04d}", "subject_id": r["s"], "predicate": r["p"], "object_id": r["o"],
                     "status": r["status"], "evidence_chunk_ids": r["evidence_chunks"], "evidence_locators": [],
                     "note": r["note"]})

    # known conflicts: attach to the chunks that contain each stated value -----------------------
    conflicts = _load(CURATED / "conflicts.json")["conflicts"]
    for cf in conflicts:
        cf["chunk_ids"] = []
        for v in cf["values"]:
            ev = {"doc": v["doc"], **({"page": v["page"]} if "page" in v else {"slide": v["slide"]})}
            cids = [c["chunk_id"] for c in chunks_by_doc.get(ev["doc"], [])
                    if ("page" in ev and ev["page"] in c["printed_pages"]) or ("slide" in ev and ev["slide"] in c["slides"])]
            ents = set(cf["entity_ids"])
            cids = [c for c in cids if ents & set(next(x for x in chunks if x["chunk_id"] == c)["entity_ids"])] or cids
            v["chunk_ids"] = cids
            cf["chunk_ids"] += [c for c in cids if c not in cf["chunk_ids"]]
    for ch in chunks:
        ch["conflict_ids"] = [cf["conflict_id"] for cf in conflicts if ch["chunk_id"] in cf["chunk_ids"]]
    (PROCESSED / "conflicts.json").write_text(json.dumps(conflicts, ensure_ascii=False, indent=1), encoding="utf-8")
    _write_csv(PROCESSED / "known_conflicts.csv", [
        {"conflict_id": cf["conflict_id"], "attribute": cf["attribute"], "entity_ids": " | ".join(cf["entity_ids"]),
         "value": v["value"], "where": v["where"], "chunk_ids": " | ".join(v["chunk_ids"]), "note": cf.get("note", "")}
        for cf in conflicts for v in cf["values"]])

    # per-chunk entity roll-ups (attribution fields) ------------------------------------------------
    rel_by_chunk = defaultdict(list)
    for r in rels:
        for cid in r["evidence_chunk_ids"]:
            rel_by_chunk[cid].append(r)
    for ch in chunks:
        ents = [ent_by_id[e] for e in ch["entity_ids"]]
        innovators = []
        for r in rel_by_chunk[ch["chunk_id"]]:
            if r["predicate"] in INNOVATOR_PREDICATES and r["status"] in ("stated", "probable"):
                subj = ent_by_id[r["subject_id"]]
                if subj["type"] in PERSONISH and r["subject_id"] in ch["entity_ids"]:
                    innovators.append(subj["name"])
                if r["predicate"] == "has_participant":
                    innovators.append(ent_by_id[r["object_id"]]["name"])
        ch["innovator_names"] = sorted(set(innovators))
        ch["innovation_names"] = sorted({e["name"] for e in ents if e["type"] in INNOVATION_TYPES})
        ch["persons"] = sorted({e["name"] for e in ents if e["type"] in PERSONISH})
        ch["organisations"] = sorted({e["name"] for e in ents if e["type"] in ORG_TYPES})
        ch["places"] = sorted({e["name"] for e in ents if e["type"] == "place"})
        ch["awards"] = sorted({e["name"] for e in ents if e["type"] == "award"})
        ch["events"] = sorted({e["name"] for e in ents if e["type"] in ("event", "event_series", "tradition")})
        ch["other_entities"] = sorted({e["name"] for e in ents if e["type"] in ("publication",)})
        if ch["data_category"] == "student_project":
            ch["innovation_names"] = [ch["gian_nidhi"]["project_name"]]
        ch["embedding_text"] = _embedding_text(ch)
        ch["content_hash"] = _h(ch["embedding_text"])
        ch["pipeline_version"] = PIPELINE_VERSION
        ch["created_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # write -------------------------------------------------------------------------------------------
    PROCESSED.mkdir(parents=True, exist_ok=True)
    (PROCESSED / "documents.json").write_text(json.dumps(DOCUMENTS, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    with open(PROCESSED / "chunks.jsonl", "w", encoding="utf-8") as f:
        for ch in chunks:
            f.write(json.dumps(ch, ensure_ascii=False) + "\n")
    with open(PROCESSED / "entities.jsonl", "w", encoding="utf-8") as f:
        for e in entities:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    _write_csv(PROCESSED / "entities.csv", [
        {"entity_id": e["id"], "type": e["type"], "name": e["name"], "aliases": " | ".join(e.get("aliases", [])),
         "documents": " | ".join(e.get("documents", [])), "description": e.get("description", ""),
         "flags": " | ".join(e.get("flags", [])), "link_note": e.get("link_note", "")} for e in entities])
    _write_csv(PROCESSED / "entity_mentions.csv", mentions)
    _write_csv(PROCESSED / "relationships.csv", [
        {**{k: v for k, v in r.items() if k not in ("evidence_chunk_ids", "evidence_locators")},
         "evidence_chunk_ids": " | ".join(r["evidence_chunk_ids"]),
         "evidence_locators": json.dumps(r["evidence_locators"], ensure_ascii=False)} for r in rels])
    _write_dq(chunks)

    stats = {
        "chunks": len(chunks), "chunks_by_document": dict(Counter(c["document_id"] for c in chunks)),
        "entities": len(entities), "entities_by_type": dict(Counter(e["type"] for e in entities)),
        "mentions": len(mentions), "relationships": len(rels),
        "relationships_by_status": dict(Counter(r["status"] for r in rels)),
        "cross_document_entities": sorted(e for e, docs in _entity_docs(mentions, chunks).items() if len(docs) > 1),
    }
    (PROCESSED / "build_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def _entity_docs(mentions, chunks):
    doc_of = {c["chunk_id"]: c["document_id"].split("-HB-")[0] if c["document_id"].startswith("SY51") else c["document_id"] for c in chunks}
    out = defaultdict(set)
    for m in mentions:
        out[m["entity_id"]].add(doc_of[m["chunk_id"]])
    return out


def _embedding_text(ch: dict) -> str:
    parts = [ch["embedding_header"], f"Title: {ch['title']}"]
    names = ch["persons"][:12] + ch["innovation_names"][:8] + ch["organisations"][:6] + ch["places"][:8]
    if names:
        parts.append("Entities: " + "; ".join(names))
    if ch["language"] == "hi+en":
        parts.append("English: " + ch["text_en"])
        parts.append("Hindi (original): " + ch["text_original"])
    else:
        parts.append(ch["text"])
    if ch["image_text"]:
        parts.append(ch["image_text"])
    return "\n".join(parts)


def _write_csv(path, rows):
    if not rows:
        return
    cols = list(rows[0].keys())
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def _write_dq(chunks):
    rows = []
    with open(PROCESSED / "data_quality_log_gian_nidhi.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append({"source": r["source"], "location": f"record {r['record_id']}", "field": r["field"],
                         "issue": r["issue"], "action": r["action"], "value_before": r["value_before"],
                         "value_after": r["value_after"]})
    for ch in chunks:
        if ch["document_id"] == "GIAN-NIDHI":
            continue
        loc = (f"slides {ch['slides'][0]}-{ch['slides'][-1]}" if ch["slides"] else
               f"pp. {ch['printed_pages'][0]}-{ch['printed_pages'][-1]}")
        for fl in ch["quality_flags"]:
            rows.append({"source": ch["document_id"], "location": f"{ch['chunk_id']} ({loc})", "field": "text",
                         "issue": fl, "action": "kept as stated; flagged in chunk metadata",
                         "value_before": ch.get("curation_notes", "")[:200], "value_after": ""})
    _write_csv(PROCESSED / "data_quality_issues.csv", rows)


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2))
