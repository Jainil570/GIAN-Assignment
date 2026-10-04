"""Source-attributed, non-fabricating RAG over the GIAN knowledge base.

Pipeline
    1. understand the query   - language detection + entity linking (retrieval.Retriever)
    2. retrieve               - hybrid dense + lexical + entity search, RRF fusion
    3. gate                   - if nothing relevant was retrieved, refuse *without* calling the LLM
    4. generate               - LLM answers from numbered excerpts only, JSON output with citations
    5. verify                 - citations must point to provided excerpts; every number and proper
                                name in the answer must occur in the cited excerpts (one retry,
                                then unsupported sentences are removed or the system refuses)
    6. attribute              - the 'Relevant Information' block is rendered from database
                                metadata of the cited chunks (never written by the LLM), so
                                sources, pages, records, authors and URLs cannot be fabricated
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field

from rapidfuzz import fuzz

from .llm import get_llm
from .retrieval import DEVANAGARI, Hit, Retriever

REFUSAL = "The available sources do not provide sufficient information to answer this."
IDENTITY_Q = re.compile(r"\bsame (?:person|people|individual|one|organi[sz]ation|entity)\b|\bsame as\b|\bidentical\b|एक ही", re.I)
NAME_Q = re.compile(r"(?:\bname|spell|spelt|written).{0,60}(?:same|consistent|differ|both|vari|correct)"
                    r"|(?:same|consistent|differ).{0,40}(?:\bname|spell)", re.I)
BOTH_Q = re.compile(r"\bboth\b|\bin common\b|\bcommon to\b|\bshared by\b|दोनों", re.I)
ATTRIB_Q = re.compile(r"\bwhere (?:does|did|do|is) .{0,100}\b(?:come from|from|mentioned|described|found)\b"
                      r"|\bwhich (?:source|document|publication|page|slide)s?\b|\bwhat is the source\b"
                      r"|\bsource of (?:the |this )?information\b|कहाँ से", re.I)
_ABBREV = re.compile(r"(?:\b(?:Mr|Mrs|Ms|Dr|Prof|Smt|Shri|Shree|St|No|Vol|vol|pp?|Rs|e\.g|i\.e|etc|vs)|\b[A-Z])\.$")


def split_sentences(text: str) -> list[str]:
    """Split on sentence ends, but not after abbreviations or initials ('Mr.', 'Rs.', 'V.')."""
    out: list[str] = []
    for part in re.split(r"(?<=[.!?।])\s+", text):
        if out and _ABBREV.search(out[-1]):
            out[-1] += " " + part
        else:
            out.append(part)
    return out


PRED_TEXT = {"organised_by": "organised it", "supported_by": "supported it", "logo_shown": "its logo is shown",
             "worked_with": "worked with it", "described_in": "described it", "part_of_series": "part of the series"}
LIST_Q = re.compile(r"\b(?:list|all|which projects|what projects|how many projects|projects (?:about|on|related))\b", re.I)

SYSTEM_PROMPT = """You are the GIAN Knowledge Base assistant. You answer questions about grassroots innovators, innovations, Shodhyatras and GIAN Nidhi student projects using ONLY the numbered source excerpts given in the user message. The excerpts come from: (1) Honey Bee newsletter articles about the 51st Shodhyatra (2024), (2) the 53rd Shodhyatra presentation (2025, originally in Hindi; English translations are provided), and (3) GIAN Nidhi project records from gian.org.

Rules:
1. Use only facts that are explicitly stated in the excerpts. Never use outside knowledge, even if you are confident it is true. Do not generalise beyond the excerpts (no inferred categories, purposes or trends).
2. Never invent or change names of innovators, authors, innovations, organisations, awards, dates, places, numbers, publications, technical details, sources, or relationships between entities. Copy names and numbers exactly as they are written in the excerpts.
3. After every sentence that states a fact, add a citation such as [S2] pointing to the excerpt(s) that state it. Cite only excerpts that actually contain that fact. When a sentence combines facts from several excerpts, cite each of them.
4. If excerpts disagree (different spellings of a name or different numbers), report each version with its own citation and do not choose between them. Use the name exactly as written in the excerpt you cite for that sentence.
5. Different people can have the same or similar names. Treat two mentions as the same person only if the excerpts or the linking notes say so; otherwise say the sources do not establish that they are the same person.
6. An author, date or award is known only if an excerpt states it. Never guess them.
7. If the excerpts do not contain the information needed, set status to "insufficient" and set answer to exactly: "The available sources do not provide sufficient information to answer this." If the excerpts answer only part of the question, set status to "partial", answer the supported part, and then add that exact sentence for the part that is not supported.
8. Some excerpts may be unrelated to the question; ignore them. If any excerpt states the answer, give it - do not refuse because other excerpts are unrelated.
9. If asked whether two mentions refer to the same person or thing, say what the excerpts state about each one (with citations) and then say clearly whether the excerpts establish that they are the same. Use the linking notes for this judgement.
10. Be concise and direct (at most about 150 words; at most about 80 words when answering in Hindi). Answer in the language of the question.

Return only JSON that matches the schema: {"status": "answered" | "partial" | "insufficient", "answer": "...", "citations": ["S1", ...]}."""

FLAG_NOTES = {
    "name_variant": "a name in this excerpt is spelled differently in other places in the sources",
    "name_conflict": "the sources spell this person's name in conflicting ways",
    "conflicting_values": "the source gives different values for the same fact - report each value",
    "hidden_text_in_pdf": "part of this text is hidden behind an image in the PDF and is not visible on the rendered slide",
    "visual_transcription": "part of this text was transcribed from an image (photo, graphic or newspaper clipping)",
    "unclear_wording": "some original wording is unclear; unclear parts are marked [unclear in source]",
    "missing_unit": "a number in the source has no unit",
    "editorial_artifact": "the slide contains a leftover chatbot-style sentence that is not content",
    "pii_redacted": "phone numbers were removed for privacy",
    "innovator_not_named": "the source does not name the innovator",
    "inconsistent_gender_marking": "the source's grammar is inconsistent about this person's gender",
    "unverified_historical_claims": "historical statements are reproduced as printed and were not verified",
    "probable_duplicate": "this record looks like a duplicate of another record with the same title and team",
    "missing_abstract": "the record has no abstract",
    "missing_institution": "the record does not state an institution",
    "abstract_recovered_from_institution_column": "the abstract was stored in the institution column of the source table",
    "conflicting_institution_across_duplicates": "duplicate copies of this record name different institutions",
    "participant_split_ambiguous": "the participant list in the source is ambiguously separated",
    "placeholder_project_name": "the project name in the source is a placeholder",
    "shares_title_with_different_team": "another record has the same title but a different team (a different project)",
}
NAME_STOP = {"The", "This", "These", "That", "Those", "However", "Answer", "According", "Sources", "Source", "Yes", "No",
             "It", "In", "On", "At", "He", "She", "They", "Their", "His", "Her", "A", "An", "And", "But", "Both", "Also",
             "Note", "Not", "Some", "Each", "Shri", "Smt", "Mr", "Mrs", "Ms", "Ji", "Its", "There", "Here", "While",
             "When", "Where", "Which", "Who", "What", "If", "As", "For", "From", "With", "By", "Of", "To", "Neither",
             "Nor", "Only", "Other", "Another", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
             "Ten", "Slide", "Slides", "Page", "Record", "Part", "English", "Hindi", "Translation", "I", "We", "S"}


@dataclass
class RAGResult:
    question: str
    status: str
    answer: str
    citations: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    entities: list = field(default_factory=list)
    retrieved: list = field(default_factory=list)
    verification: dict = field(default_factory=dict)
    model: str = ""
    timings: dict = field(default_factory=dict)
    markdown: str = ""


class GianRAG:
    def __init__(self, model: str | None = None, k: int = 6):
        self.retriever = Retriever()
        self.llm = get_llm(model)
        self.k = k
        self.docs = {r[0]: {"author_note": r[1], "document_title_en": r[2]} for r in self.retriever.conn.execute(
            "SELECT document_id, author_note, document_title_en FROM documents").fetchall()}
        self.n_records = self.retriever.conn.execute("SELECT count(*) FROM gian_nidhi_projects").fetchone()[0]

    # ------------------------------------------------------------------ public API
    def answer(self, question: str) -> RAGResult:
        t0 = time.time()
        question = question.strip()
        hi = bool(DEVANAGARI.search(question))
        linked = self.retriever.link_entities(question)
        k = self.k
        list_mode = bool(LIST_Q.search(question) and re.search(r"project|nidhi|student|record", question, re.I))
        ret = self.retriever.search(question, k=k, linked=linked)
        records, total, terms = self.retriever.keyword_records(question) if list_mode else ([], 0, [])
        if records:                                      # exhaustive keyword matches replace top-k for list questions
            ret["hits"] = records
            ret["list_mode"] = {"keyword_matches": total, "shown": len(records), "terms": terms,
                                "title_matches": sum(r.row["match_field"] == "title" for r in records)}
        t_ret = time.time() - t0
        res = RAGResult(question=question, status="insufficient", answer=REFUSAL, model=self.llm.label,
                        entities=[{"entity_id": e.entity_id, "name": e.name, "type": e.type, "matched": e.matched,
                                   "from": "question"} for e in linked],
                        retrieved=[{"label": f"S{i}", "chunk_id": h.chunk_id, "locator": h.row["locator"],
                                    "dense": round(h.dense, 3), "dense_rank": h.dense_rank,
                                    "lexical_rank": h.lexical_rank, "entity_hits": sorted(set(h.entity_hits)),
                                    "graph_hits": h.graph_hits, "keyword_match": h.row.get("match_field"),
                                    "rrf": round(h.rrf, 4), "title": h.row["title"]}
                                   for i, h in enumerate(ret["hits"], start=1)])
        if ret.get("list_mode"):
            res.verification["list_mode"] = ret["list_mode"]
        if records:
            # 'list / how many' over the structured GIAN Nidhi table: answer deterministically from
            # every keyword match, so the list is complete and nothing can be invented
            labels = {item["label"]: h for item, h in zip(res.retrieved, ret["hits"])}
            res.status, res.answer, res.citations = "answered", self._list_answer(labels, ret["list_mode"]), list(labels)
            res.verification["answer_mode"] = "structured listing of all keyword matches (no LLM involved)"
            return self._finish(res, labels, linked, t0, t_ret)
        gate = self._gate(ret, linked)
        res.verification["gate"] = gate
        if not gate["pass"]:
            res.timings = {"retrieval_s": round(t_ret, 2), "total_s": round(time.time() - t0, 2)}
            res.markdown = self.render(res)
            return res

        # relevance filter: keep excerpts close to the best match or backed by an entity/keyword hit;
        # marginal excerpts only distract the model (they stay visible in the retrieval trace)
        cutoff = max(0.45, ret["max_dense"] - 0.25)
        kept = [h for h in ret["hits"] if h.dense >= cutoff or h.entity_hits or h.graph_hits or (h.lexical_rank or 99) <= 3]
        kept = kept or ret["hits"][:1]
        for item, h in zip(res.retrieved, ret["hits"]):
            item["sent_to_llm"] = h in kept
        labels = {item["label"]: h for item, h in zip(res.retrieved, ret["hits"]) if h in kept}

        # questions answered from the curated knowledge structure rather than free generation
        if IDENTITY_Q.search(question):
            ident = self._identity_answer(linked, labels)
            if ident:
                res.status, res.answer, res.citations = "answered", ident[0], ident[1]
                res.verification["answer_mode"] = "curated entity-linking decision with its evidence (no LLM involved)"
                return self._finish(res, labels, linked, t0, t_ret)
        if ATTRIB_Q.search(question):
            at = self._attribution_answer(linked, labels)
            if at:
                res.status, res.answer, res.citations = "answered", at[0], at[1]
                res.verification["answer_mode"] = "provenance listing from chunk metadata (no LLM involved)"
                return self._finish(res, labels, linked, t0, t_ret)
        if NAME_Q.search(question):
            nv = self._name_variant_answer(linked, labels)
            if nv:
                res.status, res.answer, res.citations = "answered", nv[0], nv[1]
                res.verification["answer_mode"] = "name-variant report from the entity mentions table (no LLM involved)"
                return self._finish(res, labels, linked, t0, t_ret)
        if BOTH_Q.search(question):
            cm = self._common_answer(question, linked, labels, res)
            if cm:
                res.status, res.answer, res.citations = "answered", cm[0], cm[1]
                res.verification["answer_mode"] = "intersection of curated relationships with evidence (no LLM involved)"
                return self._finish(res, labels, linked, t0, t_ret)

        user = self._user_prompt(question, labels, linked, hi)
        raw = self.llm.generate(SYSTEM_PROMPT, user)
        out, problems, repairs = self._verify(raw, labels, question)
        docs_needed = self._docs_needed(linked, labels)
        problems += self._doc_coverage(out, labels, docs_needed)
        attempts = 1
        if problems:
            attempts += 1
            feedback = ("Your previous answer had these problems: " + "; ".join(problems) +
                        ". Answer again using only the excerpts. Copy names and numbers exactly as written, cite every "
                        "factual sentence, and use status 'insufficient' if the excerpts do not support an answer.")
            out2, problems2, repairs2 = self._verify(self.llm.generate(SYSTEM_PROMPT, user + "\n\n" + feedback), labels, question)
            problems2 += self._doc_coverage(out2, labels, docs_needed)
            if out2 is not None and (out is None or len(problems2) <= len(problems)):
                out, problems, repairs = out2, problems2, repairs2
        coverage_note = [p for p in problems if p.startswith("the question concerns several sources")]
        problems = [p for p in problems if p not in coverage_note]     # a coverage gap is reported, not removed
        if coverage_note:
            res.verification["coverage_warning"] = coverage_note[0]
        removed = []
        if problems and out and out["status"] != "insufficient":
            out, removed = self._drop_unsupported(out, labels, question)
        res.verification.update({"attempts": attempts, "remaining_problems": problems,
                                 "citation_repairs": repairs, "removed_sentences": removed})
        if not out or out["status"] == "insufficient" or not out["answer"].strip() or not out["citations"]:
            res.status, res.answer, res.citations = "insufficient", REFUSAL, []
        else:
            ans = out["answer"].strip()
            if not re.search(r"\[S\d+\]", ans):          # model listed citations but no inline markers
                ans += " " + "".join(f"[{c}]" for c in out["citations"])
            note, note_cites = self._variant_note(ans, labels)
            if note:
                ans += " " + note
                res.verification["name_variant_note"] = note
            cnote, cnote_cites = self._conflict_note(ans, labels)
            if cnote:
                ans += " " + cnote
                note_cites += cnote_cites
                res.verification["conflict_note"] = cnote
            res.status, res.answer = out["status"], ans
            res.citations = list(dict.fromkeys(out["citations"] + note_cites))
        if res.status == "insufficient" and IDENTITY_Q.search(question):
            ident = self._identity_answer(linked, labels)
            if ident:
                res.status, res.answer, res.citations = "answered", ident[0], ident[1]
                res.verification["identity_resolution"] = "answered from the curated entity-linking decision and its evidence"
        return self._finish(res, labels, linked, t0, t_ret)

    def _finish(self, res, labels, linked, t0, t_ret) -> RAGResult:
        res.sources = [self._source_block(lbl, labels[lbl], res.answer, linked) for lbl in res.citations]
        for s in res.sources:
            for e in s["entities_in_answer"]:
                if e["entity_id"] not in {x["entity_id"] for x in res.entities}:
                    res.entities.append({**e, "from": f"answer [{s['label']}]"})
        res.timings = {"retrieval_s": round(t_ret, 2), "total_s": round(time.time() - t0, 2)}
        res.markdown = self.render(res)
        return res

    # ------------------------------------------------------------------ structured answer paths
    @staticmethod
    def _short_loc(locator: str) -> str:
        return locator.split(" (PDF")[0].replace("53rd Shodhyatra presentation, ", "53rd Shodhyatra presentation ")

    @staticmethod
    def _core_name(form: str) -> str:
        return re.sub(r"^(shri|shree|mr\.?|smt\.?)\s+|\s+(ji)$", "", form.strip(), flags=re.I).lower()

    def _name_variant_answer(self, linked, labels):
        """'Is the name written the same way?' - report every spelling found in the excerpts."""
        flagged = [e for e in self._flagged_entities(labels)
                   if "name_conflict" in (self.retriever.entity_details([e]).get(e, {}).get("flags") or [])]
        if not flagged:
            return None
        linked_ids = {e.entity_id for e in linked}
        rel_people = set()
        if linked_ids:
            rel_people = {r[0] for r in self.retriever.conn.execute(
                "SELECT subject_id FROM relationships WHERE object_id = ANY(%s) UNION SELECT object_id FROM relationships "
                "WHERE subject_id = ANY(%s)", (list(linked_ids), list(linked_ids))).fetchall()}
        person = next((e for e in flagged if e in linked_ids), None) or next((e for e in flagged if e in rel_people), None)
        if not person:
            return None
        innov = [e for e in linked_ids if e.startswith("INN-")]
        groups: dict[str, list] = {}
        for lbl, h in labels.items():
            if innov and not set(innov) & set(h.row["entity_ids"] or []):
                continue
            sf = self.retriever.mention_surface(h.chunk_id).get(person)
            if sf:
                groups.setdefault(self._core_name(sf), []).append((sf, lbl, self._short_loc(h.row["locator"])))
        if len(groups) < 2:
            return None
        parts = [f"\"{items[0][0]}\" (" + "; ".join(f"{loc} [{lbl}]" for _, lbl, loc in items) + ")" for items in groups.values()]
        inno_txt = ""
        if innov:
            iname = self.retriever.entity_details(innov[:1])[innov[0]]["name"]
            inno_txt = f" All of these mentions credit the person with: {iname}."
        text = ("No - the sources do not write this name the same way: " + " vs ".join(parts) + "." + inno_txt +
                " The sources do not say which spelling is correct.")
        cites = [lbl for items in groups.values() for _, lbl, _ in items]
        return text, list(dict.fromkeys(cites))

    def _common_answer(self, question, linked, labels, res):
        """'Which X are associated with both A and B?' - intersect curated relationships of A and B."""
        anchors = [e for e in linked if e.specific and e.type in ("event", "person", "organisation", "institution")]
        if len(anchors) < 2:
            return None
        types = sorted({t for rx, ts in self.retriever.TARGET_TYPES if rx.search(question) for t in ts}) or ["organisation"]
        neigh: list[dict] = []
        for a in anchors[:3]:
            rows = self.retriever.conn.execute(
                """SELECT CASE WHEN r.subject_id = %(a)s THEN r.object_id ELSE r.subject_id END AS other,
                          r.predicate, r.evidence_chunk_ids
                   FROM relationships r JOIN entities s ON s.entity_id = r.subject_id JOIN entities o ON o.entity_id = r.object_id
                   WHERE r.status IN ('stated', 'probable')
                     AND ((r.subject_id = %(a)s AND o.type = ANY(%(t)s)) OR (r.object_id = %(a)s AND s.type = ANY(%(t)s)))""",
                {"a": a.entity_id, "t": types}).fetchall()
            d: dict[str, list] = {}
            for other, pred, ev in rows:
                d.setdefault(other, []).append((pred, ev))
            neigh.append(d)
        common = set(neigh[0]).intersection(*neigh[1:])
        if not common:
            return None
        chunk_label = {h.chunk_id: l for l, h in labels.items()}

        def label_for(cid):
            if cid not in chunk_label:                   # evidence chunk not retrieved yet: add it as a source
                row = self.retriever._rows([cid]).get(cid)
                if not row:
                    return None
                lbl = f"S{len(res.retrieved) + 1}"
                labels[lbl] = Hit(cid, row=row)
                chunk_label[cid] = lbl
                res.retrieved.append({"label": lbl, "chunk_id": cid, "locator": row["locator"], "dense": None,
                                      "dense_rank": None, "lexical_rank": None, "entity_hits": [], "graph_hits": 1,
                                      "keyword_match": None, "rrf": None, "title": row["title"], "sent_to_llm": False,
                                      "added_by": "relationship evidence"})
            return chunk_label[cid]

        ents = self.retriever.entity_details(sorted(common) + [a.entity_id for a in anchors])
        lines, cites = [], []
        for other in sorted(common, key=lambda x: ents[x]["name"]):
            per_anchor = []
            for a, d in zip(anchors, neigh):
                bits = []
                for pred, ev in d[other]:
                    lbl = label_for(ev[0]) if ev else None
                    if lbl:
                        bits.append(f"{PRED_TEXT.get(pred, pred.replace('_', ' '))} [{lbl}]")
                        cites.append(lbl)
                if bits:
                    per_anchor.append(f"{a.name.split(' (')[0]}: " + ", ".join(dict.fromkeys(bits)))
            if len(per_anchor) == len(anchors):
                lines.append(f"- {ents[other]['name']} - " + "; ".join(per_anchor))
        if not lines:
            return None
        names = " and ".join(a.name.split(" (")[0] for a in anchors)
        kind = "organisation" if "organisation" in types else types[0]
        head = f"According to the sources, {len(lines)} {kind}(s) are linked to both {names}:"
        return head + "\n" + "\n".join(lines), list(dict.fromkeys(cites))

    def _attribution_answer(self, linked, labels):
        """'Where does the information about X come from?' - list every excerpt that mentions X, with its
        exact locator and the opening words of the source text (verbatim)."""
        ids = {e.entity_id for e in linked if e.specific and e.type not in ("event", "event_series")}
        if not ids:
            return None
        hits = [(l, h) for l, h in labels.items() if ids & set(h.row["entity_ids"] or [])]
        if not hits:
            return None
        lines = []
        for l, h in hits:
            r = h.row
            if r["document_id"].startswith("SY51"):
                src = f"Honey Bee newsletter {r['publication_issue']}, article \"{r['document_title']}\""
            elif r["document_id"] == "SY53-PPT":
                src = "53rd Shodhyatra presentation (Hindi slides; English translation in the knowledge base)"
            else:
                src = "GIAN NIDHI project table on gian.org"
            quote = re.sub(r"\s+", " ", r["text"]).strip()[:170].rsplit(" ", 1)[0]
            lines.append(f"- {src} - {self._short_loc(r['locator'])}: \"{quote} ...\" [{l}]")
        names = ", ".join(self.retriever.entity_details(sorted(ids))[i]["name"] for i in sorted(ids))
        return (f"The information about {names} comes from {len(lines)} place(s) in the sources:\n" + "\n".join(lines),
                [l for l, _ in hits])

    def _conflict_note(self, answer: str, labels) -> tuple[str, list[str]]:
        """If the answer reports only some of the values of a known conflict, list all of them."""
        cids = sorted({c for h in labels.values() for c in (h.row.get("conflict_ids") or [])})
        if not cids:
            return "", []
        ans_l = answer.lower()
        notes, cites = [], []
        for cid, attr, kws, values in self.retriever.conn.execute(
                "SELECT conflict_id, attribute, keywords, values FROM known_conflicts WHERE conflict_id = ANY(%s)", (cids,)):
            if not any(k.lower() in ans_l for k in (kws or [])):
                continue
            if all(any(t.lower() in ans_l for t in v["value_terms"]) for v in values):
                continue
            parts = []
            for v in values:
                lbl = next((l for l, h in labels.items() if h.chunk_id in v["chunk_ids"]), None)
                if lbl:
                    parts.append(f"{v['value']} ({v['where']}) [{lbl}]")
                    cites.append(lbl)
            if len(parts) >= 2:
                notes.append(f"Note: the sources give different values for {attr}: " + "; ".join(parts) + ".")
        return " ".join(notes), list(dict.fromkeys(cites))

    def _list_answer(self, labels, info) -> str:
        def line(lbl, h):
            r = h.row
            g = (r.get("text") or "")
            name = (r["innovation_names"] or ["(untitled)"])[0]
            inst = re.search(r"Institution: (.*)", g)
            inst = inst.group(1).strip() if inst else "institution not stated"
            people = "; ".join(r["innovator_names"] or []) or "participants not listed"
            ids = ", ".join(map(str, r["record_ids"] or []))
            return f"- {name} (record {ids}) - {inst}; participants: {people} [{lbl}]"
        title = [(l, h) for l, h in labels.items() if h.row.get("match_field") == "title"]
        other = [(l, h) for l, h in labels.items() if h.row.get("match_field") != "title"]
        term = " / ".join(info["terms"])
        out = [f"A keyword search for '{term}' over all {self.n_records} GIAN Nidhi records found {info['keyword_matches']} "
               f"matching record(s)" + (f" (showing {info['shown']})" if info["shown"] < info["keyword_matches"] else "") + "."]
        if title:
            out.append(f"Projects with '{term}' in the title:")
            out += [line(l, h) for l, h in title]
        if other:
            out.append(f"Projects that mention '{term}' only in the abstract:")
            out += [line(l, h) for l, h in other]
        return "\n".join(out)

    # ------------------------------------------------------------------ cross-source coverage
    DOC_NAMES = {"SY51": "the 51st Shodhyatra articles (Honey Bee)", "SY53-PPT": "the 53rd Shodhyatra presentation",
                 "GIAN-NIDHI": "GIAN Nidhi"}

    @staticmethod
    def _doc_key(document_id: str) -> str:
        return "SY51" if document_id.startswith("SY51") else document_id

    def _docs_needed(self, linked, labels) -> set[str]:
        """Sources the question explicitly spans (each named entity attested in exactly one source)."""
        need = set()
        for e in linked:
            if e.specific and e.type in ("event", "person", "organisation", "institution"):
                docs = self.retriever._entity_docs(e.entity_id)
                if len(docs) == 1:
                    need |= docs
        available = {self._doc_key(h.row["document_id"]) for h in labels.values()}
        return need & available

    def _doc_coverage(self, out, labels, docs_needed) -> list[str]:
        if not out or out.get("status") == "insufficient" or len(docs_needed) < 2:
            return []
        cited = {self._doc_key(labels[c].row["document_id"]) for c in out.get("citations", []) if c in labels}
        missing = docs_needed - cited
        if not missing:
            return []
        return ["the question concerns several sources; also cite the excerpts from " +
                " and ".join(self.DOC_NAMES.get(m, m) for m in sorted(missing)) + " that support your statements"]

    # ------------------------------------------------------------------ identity questions
    def _identity_answer(self, linked, labels) -> tuple[str, list[str]] | None:
        """'Is X the same person as Y?' - when the model declines, answer from the curated linking
        decision (distinct_from / possible_same_as) and cite the excerpts that describe X and Y."""
        ids = [e.entity_id for e in linked if e.type in ("person", "organisation", "institution")]
        if len(ids) < 2:
            return None
        row = self.retriever.conn.execute(
            """SELECT subject_id, predicate, object_id, note FROM relationships
               WHERE predicate IN ('distinct_from', 'possible_same_as')
                 AND subject_id = ANY(%s) AND object_id = ANY(%s) LIMIT 1""", (ids, ids)).fetchone()
        if not row:
            return None
        s_id, pred, o_id, note = row
        ents = self.retriever.entity_details([s_id, o_id])

        def lbl(eid):
            return next((l for l, h in labels.items() if eid in (h.row["entity_ids"] or [])), None)

        la, lb = lbl(s_id), lbl(o_id)
        if not la or not lb:
            return None
        rows = dict(self.retriever.conn.execute("SELECT entity_id, description FROM entities WHERE entity_id = ANY(%s)",
                                                ([s_id, o_id],)).fetchall())
        desc = {e: re.sub(r"\s*\([^)]*(?:p\.|slide|Part)[^)]*\)", "", rows[e]).strip() for e in (s_id, o_id)}
        a, b = ents[s_id]["name"], ents[o_id]["name"]
        if pred == "distinct_from":
            text = (f"No - the sources do not identify them as the same person. {a}: {desc[s_id]} [{la}] "
                    f"{b}: {desc[o_id]} [{lb}] The knowledge base keeps them as separate entities: {note}")
        else:
            text = (f"The sources do not establish that they are the same person. {a}: {desc[s_id]} [{la}] "
                    f"{b}: {desc[o_id]} [{lb}] The knowledge base records only a possible, unverified link: {note}")
        return text, list(dict.fromkeys([la, lb]))

    # ------------------------------------------------------------------ gating
    @staticmethod
    def _gate(ret: dict, linked) -> dict:
        specific = [e.entity_id for e in linked if e.specific]
        g = {"max_dense": round(ret["max_dense"], 3), "specific_entities": specific,
             "top_term_coverage": round(ret["top_coverage"], 2), "lexical_hits": ret["lexical_hits"]}
        g["pass"] = bool(ret["hits"]) and (ret["max_dense"] >= 0.42 or bool(specific) or
                                          (ret["top_coverage"] >= 0.6 and ret["max_dense"] >= 0.35))
        return g

    # ------------------------------------------------------------------ prompt building
    def _user_prompt(self, question, labels, linked, hi) -> str:
        parts = [f"Question: {question}", ""]
        if linked:
            parts.append("Entities recognised in the question: " +
                         "; ".join(f"{e.name} ({e.type})" for e in linked[:8]))
        notes = self._linking_notes(linked, labels)
        if notes:
            parts.append("Linking notes from the knowledge-base curation (guidance about identities; not a citable source):")
            parts += [f"- {n}" for n in notes]
        key = self._key_statements(linked, labels)
        if key:
            parts.append("Key statements in the excerpts about the entities above (compare them; report every version):")
            parts += [f"- {k}" for k in key]
        parts += ["", "Source excerpts:"]
        budget = 15000
        for lbl, h in labels.items():
            r = h.row
            flag_txt = [FLAG_NOTES[f] for f in (r["quality_flags"] or []) if f in FLAG_NOTES]
            block = [f"[{lbl}] {r['locator']} | {r['document_title']}" + (f" | Section: {r['section']}" if r["section"] else "")]
            if r["language"] == "hi+en":
                block.append("(Excerpt is an English translation of Hindi slide text.)")
            if flag_txt:
                block.append("Notes: " + "; ".join(flag_txt) + ".")
            text = r["text"]
            if hi and r["language"] == "hi+en":
                text += "\nOriginal Hindi: " + r["text_original"]
            if r["image_text"] and r["language"] != "hi+en":
                text += "\n" + r["image_text"]
            text = text[:max(1200, budget // max(len(labels), 1))]
            block.append(text)
            parts.append("\n".join(block))
            parts.append("")
        lang = "Hindi" if hi else "English"
        parts.append(f"Answer in {lang}. Cite excerpts as [S1], [S2], ... Return JSON only.")
        return "\n".join(parts)

    def _flagged_entities(self, labels) -> list[str]:
        ids = sorted({e for h in labels.values() for e in (h.row["entity_ids"] or [])
                      if not e.startswith(("PER-GN-", "PRJ-", "INS-"))})
        if not ids:
            return []
        return [r[0] for r in self.retriever.conn.execute(
            "SELECT entity_id FROM entities WHERE entity_id = ANY(%s) AND flags && ARRAY['name_conflict', 'conflicting_values']",
            (ids,)).fetchall()]

    def _key_statements(self, linked, labels) -> list[str]:
        """Sentences from each excerpt that mention a linked or conflict-flagged entity, labelled by excerpt."""
        ids = [e.entity_id for e in linked if e.specific and e.type not in ("event", "event_series")]
        ids += [e for e in self._flagged_entities(labels) if e not in ids]
        ents = self.retriever.entity_details(ids)
        out = []
        for eid in ids[:4]:
            e = ents.get(eid)
            if not e:
                continue
            forms = sorted({a for a in e["aliases"] if len(a) >= 5 and not DEVANAGARI.search(a)}, key=len, reverse=True)
            if not forms:
                continue
            for lbl, h in labels.items():
                text = h.row["text"] + " " + (h.row["image_text"] or "")
                for sent in re.split(r"(?<=[.!?])\s+|\n+", text):
                    if any(f.lower() in sent.lower() for f in forms):
                        out.append(f"[{lbl}] \"{sent.strip()[:240]}\"")
                        break
        return list(dict.fromkeys(out))[:10]

    def _variant_note(self, answer: str, labels) -> tuple[str, list[str]]:
        """If the answer names a person whose spelling differs across the provided excerpts but shows only
        one form, add a sentence listing each spelling with its citation (from the mentions table)."""
        notes, cites = [], []
        for eid in self._flagged_entities(labels):
            e = self.retriever.entity_details([eid]).get(eid)
            if not e or e["type"] != "person" or "name_conflict" not in (e["flags"] or []):
                continue
            forms = {}
            for lbl, h in labels.items():
                sf = self.retriever.mention_surface(h.chunk_id).get(eid)
                if sf:
                    forms.setdefault(sf, lbl)
            core = lambda f: re.sub(r"^(shri|mr\.?|smt\.?)\s+|\s+(ji)$", "", f.strip(), flags=re.I).lower()
            distinct = {}
            for f, lbl in forms.items():
                distinct.setdefault(core(f), (f, lbl))
            if len(distinct) < 2:
                continue
            ans_l = answer.lower()
            if not any(c in ans_l for c in distinct):
                continue                                     # this person is not part of the answer
            if all(c in ans_l for c in distinct):
                continue                                     # every spelling already reported
            listed = " and ".join(f"\"{f}\" [{lbl}]" for f, lbl in distinct.values())
            notes.append(f"Note: the sources write this name in different ways: {listed}.")
            cites += [lbl for _, lbl in distinct.values()]
        return " ".join(notes), cites

    def _linking_notes(self, linked, labels=None) -> list[str]:
        ids = [e.entity_id for e in linked]
        # entities in the excerpts whose names/values conflict across sources (e.g. Rahulchand vs Rawalchand)
        in_excerpts = sorted({e for h in (labels or {}).values() for e in (h.row["entity_ids"] or [])
                              if not e.startswith(("PER-GN-", "PRJ-", "INS-"))})
        flagged = self.retriever.conn.execute(
            """SELECT name, link_note FROM entities WHERE entity_id = ANY(%s)
               AND (flags && ARRAY['name_conflict', 'conflicting_values']) AND coalesce(link_note, '') <> ''""",
            (in_excerpts,)).fetchall() if in_excerpts else []
        if not ids and not flagged:
            return []
        rows = self.retriever.conn.execute(
            """SELECT s.name, r.predicate, o.name, r.status, r.note FROM relationships r
               JOIN entities s ON s.entity_id = r.subject_id JOIN entities o ON o.entity_id = r.object_id
               WHERE (r.subject_id = ANY(%s) OR r.object_id = ANY(%s))
                 AND r.predicate IN ('possible_same_as', 'distinct_from', 'name_conflict')""", (ids, ids)).fetchall()
        notes = []
        for s, p, o, st, note in rows:
            if p == "possible_same_as":
                notes.append(f"'{s}' and '{o}' MAY be the same, but this is NOT established by the sources ({note})")
            elif p == "distinct_from":
                notes.append(f"'{s}' and '{o}' are different people/entities ({note})")
            else:
                notes.append(f"{s}: {note}")
        for e in linked:
            if e.link_note and not any(e.name in n for n in notes):
                notes.append(f"{e.name}: {e.link_note}")
        for name, note in flagged:
            if not any(name in n for n in notes):
                notes.append(f"{name}: {note}")
        return notes[:8]

    # ------------------------------------------------------------------ verification
    @staticmethod
    def _parse(raw: str) -> dict | None:
        try:
            d = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            m = re.search(r"\{.*\}", raw or "", re.S)
            if not m:
                return None
            try:
                d = json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
        if not isinstance(d, dict) or "answer" not in d:
            return None
        d.setdefault("status", "answered")
        d.setdefault("citations", [])
        return d

    @staticmethod
    def _context_blob(labels, cites) -> str:
        parts = []
        for c in cites:
            r = labels[c].row
            # only text that is actually in the source (+ its locator); merged entity names and curated
            # titles are excluded so a spelling from another source cannot 'verify' a sentence
            parts += [r["text"], r["text_original"], r["image_text"] or "", r["locator"], r["document_title"]]
        return " ".join(parts)

    @staticmethod
    def _numbers(s: str) -> set[str]:
        s = s.translate(str.maketrans("०१२३४५६७८९", "0123456789"))
        return {n.replace(",", "").rstrip(".") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", s)}

    @staticmethod
    def _normalise_markers(text: str) -> str:
        """'[S1, S2]' / '[S1; S2]' / '(S1)' -> '[S1][S2]'; markers after the sentence end move inside it."""
        text = re.sub(r"[\[(]\s*((?:S\d+\s*[,;/&]?\s*(?:and\s+)?)+)[\])]",
                      lambda m: "".join(f"[{x.upper()}]" for x in re.findall(r"S\d+", m.group(1), re.I)), text, flags=re.I)
        return re.sub(r"([.!?।])\s*((?:\[S\d+\])+)", r" \2\1", text)

    def _checkable(self, sentence: str) -> list[str]:
        """Numbers and proper-name terms in a sentence - the things that must not be fabricated."""
        body = re.sub(r"\[S\d+\]", "", sentence)
        toks = [f"#{n}" for n in self._numbers(body)]
        for m in re.finditer(r"\b[A-Z][\w'.-]*(?:\s+[A-Z][\w'.-]*)*", body):
            words = m.group(0).strip(".'-").split()
            while words and words[0] in NAME_STOP:          # trim leading/trailing filler only; keep
                words.pop(0)                                # internal words ('Likhimdas Ji Mandir')
            while words and words[-1] in NAME_STOP:
                words.pop()
            term = " ".join(words).strip(".'-")
            if len(term) >= 3:
                toks.append(term)
        return list(dict.fromkeys(toks))

    def _supported(self, tok: str, ctx: str) -> bool:
        if tok.startswith("#"):
            return tok[1:] in self._numbers(ctx)
        ctx_l = ctx.lower()
        return tok.lower() in ctx_l or fuzz.partial_ratio(tok.lower(), ctx_l) >= 90

    def _anchors(self, sentence: str) -> list[str]:
        """Words that tie a number to its subject: the first proper-name term of the sentence, or
        (Hindi / no names) the sentence's content words."""
        names = [t for t in self._checkable(sentence) if not t.startswith("#")]
        if names:
            return [w.lower() for w in names[0].split() if len(w) >= 4] or [names[0].lower()]
        words = re.findall(r"[\w\u0900-\u097F]{4,}", re.sub(r"\[S\d+\]", "", sentence).lower())
        return [w for w in words if not w.isdigit()][:10]

    def _tok_ok(self, tok: str, sentence: str, labels, lbls) -> bool:
        """Is a checkable token of `sentence` supported by excerpts `lbls`? Names: present in the source
        text. Numbers: present in the source text within 250 characters of the sentence's subject, so a
        number cannot be borrowed from an unrelated statement (e.g. an issue date reused as an award year)."""
        if not tok.startswith("#"):
            return self._supported(tok, self._context_blob(labels, lbls))
        num, anchors = tok[1:], self._anchors(sentence)
        loc_ok = bool(re.search(r"\b(page|pages|p\.|pp\.|slide|slides|record|records|vol)\b", sentence, re.I))
        for l in lbls:
            r = labels[l].row
            for t in (r["text"], r["text_original"], r["image_text"] or "", r["document_title"]):   # titles are printed source text
                tn = t.translate(str.maketrans("०१२३४५६७८९", "0123456789")).replace(",", "")
                for m in re.finditer(r"(?<![\d.])" + re.escape(num) + r"(?!\d)", tn):
                    win = tn[max(0, m.start() - 250): m.end() + 250].lower()
                    if not anchors or any(a in win for a in anchors):
                        return True
            if loc_ok and num in self._numbers(r["locator"] + " " + r["document_title"]):
                return True
        return False

    def _verify(self, raw, labels, question):
        """Check every sentence against the excerpts it cites; repair wrong citation labels when
        another provided excerpt contains the fact; report what cannot be supported at all."""
        d = self._parse(raw)
        if d is None:
            return None, ["output was not valid JSON"], []
        if d["status"] == "insufficient" or d["answer"].strip() == REFUSAL:
            d.update(status="insufficient", citations=[])
            return d, [], []
        listed = [c.strip("[] ").upper() for c in d.get("citations", []) if str(c).strip("[] ").upper() in labels]
        d["answer"] = self._normalise_markers(d["answer"])
        d["answer"] = re.sub(r"(?m)^(\s*)\d{1,2}[.)]\s+", r"\1- ", d["answer"].strip())   # list numbering is not a fact
        sentences = [s for s in split_sentences(d["answer"]) if s]
        new, problems, repairs = [], [], []
        for s in sentences:
            if REFUSAL in s:
                new.append(s)
                continue
            marks = [m.upper() for m in re.findall(r"\[(S\d+)\]", s, flags=re.I)]
            if not re.sub(r"\[S\d+\]", "", s, flags=re.I).strip(" .;,"):     # a stray '[S2]' fragment
                if new:
                    have = set(re.findall(r"\[(S\d+)\]", new[-1]))
                    extra = "".join(f"[{m}]" for m in marks if m in labels and m not in have)
                    if extra:
                        m2 = re.match(r"(.*?)([.!?।]*)$", new[-1].rstrip(), re.S)
                        new[-1] = m2.group(1) + extra + m2.group(2)
                continue
            valid = [m for m in dict.fromkeys(marks) if m in labels]
            toks = [t for t in self._checkable(s) if not self._supported(t, question)]
            ctx_lbls = valid or listed
            if not toks or all(self._tok_ok(t, s, labels, ctx_lbls) for t in toks):
                s2 = re.sub(r"\s*\[S\d+\]", "", s) if len(valid) < len(marks) else s   # drop non-existent labels
                if toks and not valid:
                    # factual sentence without its own marker: cite the excerpt(s) that contain its facts
                    cover = []
                    for t in toks:
                        cands = [l for l in ctx_lbls if self._tok_ok(t, s, labels, [l])]
                        if cands and not any(c in cover for c in cands):
                            cover.append(cands[0])
                    core = s2.rstrip()
                    m = re.match(r"(.*?)([.!?।]*)$", core, re.S)
                    s2 = m.group(1) + " " + "".join(f"[{c}]" for c in (cover or ctx_lbls)) + m.group(2)
                elif s2 != s:
                    s2 = s2.rstrip() + "".join(f"[{c}]" for c in ctx_lbls)
                elif not toks and not valid:
                    # no names/numbers and no marker: cite the excerpt it overlaps most with (if clearly)
                    words = {w for w in re.findall(r"[a-zऀ-ॿ]{4,}", s.lower())}
                    if len(words) >= 5:
                        best = max(labels, key=lambda l: len(words & set(re.findall(
                            r"[a-zऀ-ॿ]{4,}", self._context_blob(labels, [l]).lower()))))
                        ov = len(words & set(re.findall(r"[a-zऀ-ॿ]{4,}", self._context_blob(labels, [best]).lower())))
                        if ov / len(words) >= 0.6:
                            m = re.match(r"(.*?)([.!?।]*)$", s2.rstrip(), re.S)
                            s2 = m.group(1) + f" [{best}]" + m.group(2)
                new.append(s2)
                continue
            cover, ok = [], True
            for t in toks:
                cands = [l for l in labels if self._tok_ok(t, s, labels, [l])]
                if not cands:
                    ok = False
                    problems.append(t.lstrip("#"))
                    continue
                pick = next((c for c in cands if c in cover), None) or next((c for c in cands if c in ctx_lbls), None) or cands[0]
                if pick not in cover:
                    cover.append(pick)
            if ok:
                core = re.sub(r"\s*\[S\d+\]", "", s).rstrip()
                m = re.match(r"(.*?)([.!?।]*)$", core, re.S)
                new.append(m.group(1) + " " + "".join(f"[{c}]" for c in cover) + m.group(2))
                repairs.append({"sentence": core, "cited": valid, "corrected_to": cover})
            else:
                new.append(s)
        d["answer"] = " ".join(new)
        d["citations"] = [c for c in dict.fromkeys(m.upper() for m in re.findall(r"\[(S\d+)\]", d["answer"], re.I)) if c in labels] or listed
        if not d["citations"]:
            problems.append("no valid citations")
        if problems:
            problems = ["these names/numbers do not appear in any provided excerpt: " + ", ".join(dict.fromkeys(problems))]
        return d, problems, repairs

    def _drop_unsupported(self, d, labels, question):
        keep, removed = [], []
        for sent in split_sentences(d["answer"]):
            toks = [t for t in self._checkable(sent) if not self._supported(t, question)]
            bad = REFUSAL not in sent and any(not self._tok_ok(t, sent, labels, list(labels)) for t in toks)
            (removed if bad else keep).append(sent)
        d["answer"] = " ".join(keep).strip()
        d["citations"] = [c for c in dict.fromkeys(m.upper() for m in re.findall(r"\[(S\d+)\]", d["answer"], re.I)) if c in labels]
        if not d["citations"]:
            d["status"] = "insufficient"
        elif removed:
            d["status"] = "partial"
        return d, removed

    # ------------------------------------------------------------------ attribution
    def _source_block(self, label, hit, answer, linked) -> dict:
        r = hit.row
        ents = self.retriever.entity_details(r["entity_ids"] or [])
        surface = self.retriever.mention_surface(r["chunk_id"])
        linked_ids = {e.entity_id for e in linked}
        ans_l = answer.lower()

        def in_answer(eid):
            e = ents.get(eid)
            if not e:
                return False
            forms = [e["name"].split(" (")[0]] + list(e["aliases"]) + ([surface[eid]] if eid in surface else [])
            return any(len(f) >= 4 and f.lower() in ans_l for f in forms)

        def pick(names, types):
            ids = [eid for eid, e in ents.items() if e["name"] in (names or []) and e["type"] in types]
            chosen = [eid for eid in ids if eid in linked_ids or in_answer(eid)]
            if not chosen and len(ids) <= 3:
                chosen = ids
            out = []
            for eid in chosen:
                nm = ents[eid]["name"]
                sf = surface.get(eid)
                out.append(nm + (f" (written here as \"{sf}\")" if sf and sf.lower() not in nm.lower() else ""))
            return out

        person_types = {"person"}
        inno_types = {"innovation", "practice", "craft", "idea", "product", "crop_variety", "traditional_knowledge",
                      "traditional_food", "art_form", "project"}
        if r["data_category"] == "student_project":
            innovators = list(r["innovator_names"] or [])
            innovations = list(r["innovation_names"] or [])
        else:
            innovators = pick(r["innovator_names"], person_types)
            innovations = pick(r["innovation_names"], inno_types)
        if r["document_id"].startswith("SY51"):
            src = f"Honey Bee newsletter, {r['publication_issue']} - \"{r['document_title']}\""
        elif r["document_id"] == "SY53-PPT":
            src = f"53rd Shodhyatra presentation (Hindi) - \"{self.docs['SY53-PPT']['document_title_en']}\""
        else:
            src = "GIAN NIDHI - Diploma & ITI Projects, gian.org"
        notes = [FLAG_NOTES[f] for f in (r["quality_flags"] or []) if f in FLAG_NOTES]
        if r["language"] == "hi+en":
            notes.insert(0, "English text is a translation of the Hindi slide; the Hindi original is stored with the chunk")
        ents_in_answer = [{"entity_id": eid, "name": e["name"], "type": e["type"]} for eid, e in ents.items()
                          if in_answer(eid) and not eid.startswith("PER-GN-")]
        return {
            "label": label, "chunk_id": r["chunk_id"], "document_id": r["document_id"],
            "innovator": innovators or ["Not specified in this source"],
            "innovation": innovations or ["Not specified in this source"],
            "author": r["author"] or ("Not stated in the source - " + (self.docs.get(r["document_id"], {}).get("author_note") or "")),
            "source": src, "page_record": r["locator"], "url": r["source_url"],
            "notes": notes, "entities_in_answer": ents_in_answer,
        }

    # ------------------------------------------------------------------ rendering
    @staticmethod
    def render(res: RAGResult) -> str:
        md = ["### Answer", res.answer, ""]
        md.append("### Relevant Information")
        if not res.sources:
            md.append("- No retrieved source supports an answer, so none is cited.")
        for i, s in enumerate(res.sources, start=1):
            md.append(f"**Source {i} [{s['label']}]**")
            md.append(f"- **Innovator:** {'; '.join(s['innovator'])}")
            md.append(f"- **Innovation:** {'; '.join(s['innovation'])}")
            md.append(f"- **Author:** {s['author']}")
            md.append(f"- **Source:** {s['source']}")
            md.append(f"- **Page/Record:** {s['page_record']} - [{s['url']}]({s['url']})")
            if s["notes"]:
                md.append(f"- **Notes:** {'; '.join(s['notes'])}")
            md.append("")
        if res.entities:
            md.append("### Entities identified")
            md += [f"- {e['name']} ({e['type']}, `{e['entity_id']}`) - from {e['from']}" for e in res.entities]
        return "\n".join(md)
