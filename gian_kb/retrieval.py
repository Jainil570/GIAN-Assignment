"""Hybrid retrieval over the pgvector knowledge base.

Three signals are fused with Reciprocal Rank Fusion (RRF):
    1. dense   - bge-m3 cosine similarity (pgvector HNSW), works across Hindi/English
    2. lexical - PostgreSQL full-text search (English stemming + 'simple' tokens for
                 Hindi words, names, numbers)
    3. entity  - entities recognised in the question by alias matching (exact surface
                 forms recorded during curation, plus conservative fuzzy matching for
                 multi-word names); chunks that mention them are pulled in

Query understanding = language detection + entity linking. The linked entities are also
shown to the user and used to pick the innovator/innovation lines of the attribution block.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from rapidfuzz import fuzz

from .config import DATABASE_URL
from .embed import embed_query

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
STOPWORDS = set("""a an and are as at be been but by can could did do does for from had has have how i if in into is it its
of on or our she he they them their there these this those to was were what when where which who whom whose why will with
would you your about tell me give list name names any some all also other more most much many than then so such only
please explain describe according sources source information info details detail know known kb knowledge base
का के की में से को और है हैं था थी थे यह वह क्या कौन कितना कितनी कितने किस किसने ने पर भी एक""".split())
# aliases too generic to be used for entity-based retrieval on their own
GENERIC_ALIASES = {"shodhyatra", "shodhyatras", "शोधयात्रा", "apple", "apples", "crutch", "bonsai", "khejri",
                   "tractors", "methi", "ker", "gir", "tlm", "मेहुल", "अशोक", "विजय", "आदेश", "हांडी", "महुआ", "महुवा",
                   "gian", "mehul", "vishnu", "simran", "satish", "gujarat", "rajasthan", "madhya pradesh",
                   "मध्यप्रदेश", "मध्य प्रदेश", "गुजरात"}


@dataclass
class LinkedEntity:
    entity_id: str
    name: str
    type: str
    matched: str
    score: float
    chunk_count: int = 0
    link_note: str = ""
    flags: list = field(default_factory=list)

    @property
    def specific(self) -> bool:
        return self.matched.lower() not in GENERIC_ALIASES and self.chunk_count <= 25


@dataclass
class Hit:
    chunk_id: str
    rrf: float = 0.0
    dense: float = 0.0
    dense_rank: int | None = None
    lexical_rank: int | None = None
    entity_hits: list = field(default_factory=list)
    graph_hits: int = 0
    row: dict = field(default_factory=dict)


class Retriever:
    def __init__(self, url: str = DATABASE_URL):
        self.conn = psycopg.connect(url, autocommit=True)
        register_vector(self.conn)
        self._load_aliases()

    # ------------------------------------------------------------------ entity linking
    def _load_aliases(self):
        rows = self.conn.execute(
            """SELECT e.entity_id, e.type, e.name, e.aliases, coalesce(e.link_note, ''), coalesce(e.flags, '{}'),
                      (SELECT count(*) FROM entity_mentions m WHERE m.entity_id = e.entity_id)
               FROM entities e""").fetchall()
        self.entities = {}
        self.aliases: list[tuple[str, str]] = []           # (alias, entity_id) for curated/PDF entities
        self.gn_names: dict[str, str] = {}                  # exact lower-case name -> entity_id (GIAN Nidhi people/projects/institutions)
        for eid, typ, name, aliases, note, flags, n in rows:
            self.entities[eid] = {"name": name, "type": typ, "aliases": aliases, "link_note": note, "flags": flags, "chunks": n}
            if eid.startswith(("PER-GN-", "PRJ-", "INS-")):
                for a in aliases:
                    a2 = re.sub(r"\s+", " ", a.lower()).strip(" .")
                    if len(a2.split()) >= 2 and len(a2) >= 8:
                        self.gn_names.setdefault(a2, eid)
            else:
                for a in aliases:
                    if len(a) >= 3:
                        self.aliases.append((a, eid))
        self.aliases.sort(key=lambda t: -len(t[0]))

    @staticmethod
    def _norm(s: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^\wऀ-ॿ]+", " ", s.lower())).strip()

    def link_entities(self, question: str) -> list[LinkedEntity]:
        q = question
        ql = self._norm(q)
        found: dict[str, LinkedEntity] = {}
        taken: list[tuple[int, int, str]] = []

        def add(eid, matched, score):
            e = self.entities[eid]
            cur = found.get(eid)
            if cur is None or score > cur.score:
                found[eid] = LinkedEntity(eid, e["name"], e["type"], matched, score, e["chunks"], e["link_note"], list(e["flags"] or []))

        # 1) exact alias occurrences (longest first, no overlaps). An alias shared by several
        #    entities (e.g. 'Ashok' = two different people) links ALL of them, so the answer can
        #    tell them apart instead of silently picking one.
        for alias, eid in self.aliases:
            if DEVANAGARI.search(alias):
                pat = re.compile(r"(?<![ऀ-ॿ])" + re.escape(alias) + r"(?![क-ह])")
            else:
                pat = re.compile(r"(?<![\w])" + re.escape(alias) + r"(?![\w])", re.I)
            for m in pat.finditer(q):
                span_alias = alias.lower()
                if any(s < m.end() and m.start() < e and a != span_alias for s, e, a in taken):
                    continue
                taken.append((m.start(), m.end(), span_alias))
                add(eid, m.group(0), 1.0)
        # 2) conservative fuzzy match for multi-word names (spelling variants, missing 'ji')
        words = ql.split()
        for alias, eid in self.aliases:
            al = self._norm(alias)
            n = len(al.split())
            if n < 2 or DEVANAGARI.search(al) or eid in found:
                continue
            for i in range(len(words) - n + 1):
                gram = " ".join(words[i:i + n])
                if fuzz.ratio(gram, al) >= 88:
                    add(eid, " ".join(words[i:i + n]), fuzz.ratio(gram, al) / 100)
                    break
        # 3) GIAN Nidhi participants / projects / institutions: exact multi-word names, then fuzzy for long names
        for name, eid in self.gn_names.items():
            if name in ql and eid not in found:
                add(eid, name, 1.0)
        if not any(k.startswith(("PRJ-", "INS-")) for k in found) and len(words) >= 2:
            for name, eid in self.gn_names.items():
                if not eid.startswith(("PRJ-", "INS-")) or len(name) < 14:
                    continue
                if fuzz.partial_ratio(name, ql) >= 92 and fuzz.token_set_ratio(name, ql) >= 70:
                    add(eid, name, 0.9)
        return sorted(found.values(), key=lambda x: (-x.score, x.chunk_count))

    # ------------------------------------------------------------------ signals
    def dense(self, qvec, k: int = 30) -> list[tuple[str, float]]:
        self.conn.execute("SET hnsw.ef_search = 100")
        return self.conn.execute(
            "SELECT chunk_id, 1 - (embedding <=> %s) FROM chunks ORDER BY embedding <=> %s LIMIT %s",
            (qvec, qvec, k)).fetchall()

    def salient_terms(self, question: str) -> list[str]:
        toks = re.findall(r"[\wऀ-ॿ]+", question.lower())
        return [t for t in toks if t not in STOPWORDS and (len(t) >= 3 or t.isdigit())]

    def lexical(self, question: str, k: int = 30) -> list[tuple[str, float]]:
        terms = self.salient_terms(question)
        if not terms:
            return []
        latin = [t for t in terms if not DEVANAGARI.search(t)]
        q_en = " | ".join(latin)
        q_simple = " | ".join(re.sub(r"[^\wऀ-ॿ]", "", t) for t in terms)
        return self.conn.execute(
            """SELECT chunk_id, greatest(
                      CASE WHEN %(en)s <> '' THEN ts_rank_cd(tsv_english, to_tsquery('english', %(en)s)) ELSE 0 END,
                      ts_rank_cd(tsv_simple, to_tsquery('simple', %(si)s))) AS r
               FROM chunks
               WHERE (%(en)s <> '' AND tsv_english @@ to_tsquery('english', %(en)s)) OR tsv_simple @@ to_tsquery('simple', %(si)s)
               ORDER BY r DESC LIMIT %(k)s""",
            {"en": q_en, "si": q_simple, "k": k}).fetchall()

    TARGET_TYPES = [
        (re.compile(r"organi[sz]|institution|agenc|sanstha|संस्था|support|sponsor|logo|partner", re.I),
         ("organisation", "institution", "community")),
        (re.compile(r"\bwho\b|innovator|person|people|farmer|teacher|artist|कौन|किसने", re.I), ("person",)),
        (re.compile(r"\bwhere\b|village|district|place|route|location|कहाँ|गांव", re.I), ("place",)),
        (re.compile(r"award|honou?r|padma|सम्मान|पुरस्कार", re.I), ("award",)),
    ]

    def graph_chunks(self, question: str, linked: list[LinkedEntity]) -> list[tuple[str, str]]:
        """Relation-aware retrieval: if the question asks for organisations / people / places / awards
        connected to a recognised entity, return the evidence chunks of those curated relationships."""
        types = sorted({t for rx, ts in self.TARGET_TYPES if rx.search(question) for t in ts})
        ids = [le.entity_id for le in linked if le.specific or le.type in ("event",)]
        if not types or not ids:
            return []
        rows = self.conn.execute(
            """SELECT r.rel_id, unnest(r.evidence_chunk_ids) FROM relationships r
               JOIN entities s ON s.entity_id = r.subject_id JOIN entities o ON o.entity_id = r.object_id
               WHERE r.status IN ('stated', 'probable')
                 AND ((r.subject_id = ANY(%(ids)s) AND o.type = ANY(%(t)s)) OR (r.object_id = ANY(%(ids)s) AND s.type = ANY(%(t)s)))""",
            {"ids": ids, "t": types}).fetchall()
        return [(cid, rel) for rel, cid in rows]

    def entity_chunks(self, linked: list[LinkedEntity], qvec, per_entity: int = 8) -> list[tuple[str, str]]:
        out = []
        for le in linked:
            if not le.specific:
                continue
            rows = self.conn.execute(
                """SELECT c.chunk_id FROM entity_mentions m JOIN chunks c USING (chunk_id)
                   WHERE m.entity_id = %s ORDER BY c.embedding <=> %s LIMIT %s""",
                (le.entity_id, qvec, per_entity)).fetchall()
            out += [(r[0], le.entity_id) for r in rows]
        return out

    # ------------------------------------------------------------------ fusion
    def search(self, question: str, k: int = 8, linked: list[LinkedEntity] | None = None) -> dict:
        qvec = np.asarray(embed_query(question), dtype=np.float32)    # numpy -> pgvector 'vector'
        linked = self.link_entities(question) if linked is None else linked
        dense = self.dense(qvec)
        lex = self.lexical(question)
        ent = self.entity_chunks(linked, qvec)
        hits: dict[str, Hit] = {}
        K = 60
        for r, (cid, sim) in enumerate(dense, start=1):
            h = hits.setdefault(cid, Hit(cid))
            h.dense, h.dense_rank = float(sim), r
            h.rrf += 1.0 / (K + r)
        for r, (cid, _) in enumerate(lex, start=1):
            h = hits.setdefault(cid, Hit(cid))
            h.lexical_rank = r
            h.rrf += 0.8 / (K + r)
        ent_rank: dict[str, int] = {}
        for cid, eid in ent:
            hits.setdefault(cid, Hit(cid)).entity_hits.append(eid)
        for h in hits.values():
            if h.entity_hits:
                # more distinct linked entities in one chunk -> stronger evidence
                ent_rank[h.chunk_id] = len(set(h.entity_hits))
        for r, cid in enumerate(sorted(ent_rank, key=lambda c: -ent_rank[c]), start=1):
            hits[cid].rrf += 1.2 * ent_rank[cid] / (K + r)
        graph: dict[str, int] = {}
        for cid, _rel in self.graph_chunks(question, linked):
            graph[cid] = graph.get(cid, 0) + 1
        for r, cid in enumerate(sorted(graph, key=lambda c: -graph[c]), start=1):
            h = hits.setdefault(cid, Hit(cid))
            h.graph_hits = graph[cid]
            h.rrf += 1.0 / (K + r)
        missing = [cid for cid, h in hits.items() if h.dense_rank is None]
        if missing:                                    # dense score for chunks found only by other signals
            for cid, sim in self.conn.execute(
                    "SELECT chunk_id, 1 - (embedding <=> %s) FROM chunks WHERE chunk_id = ANY(%s)", (qvec, missing)).fetchall():
                hits[cid].dense = float(sim)
        ranked = sorted(hits.values(), key=lambda h: -h.rrf)
        top = ranked[:k]
        # cross-source questions: when the question names entities attested in different
        # documents, make sure each of those documents contributes its best chunks
        docs_needed = {d for le in linked if le.specific for d in self._entity_docs(le.entity_id)}
        if len(docs_needed) > 1:
            doc_of = {cid: ("SY51" if d.startswith("SY51") else d) for cid, d in self.conn.execute(
                "SELECT chunk_id, document_id FROM chunks WHERE chunk_id = ANY(%s)",
                ([h.chunk_id for h in ranked[:60]],)).fetchall()}
            per_doc = max(1, k // len(docs_needed))
            chosen = []
            for d in sorted(docs_needed):
                chosen += [h for h in ranked[:60] if doc_of.get(h.chunk_id) == d][:per_doc]
            chosen += [h for h in ranked if h not in chosen]
            top = sorted(chosen[:k], key=lambda h: -h.rrf)
        by_id = self._rows([h.chunk_id for h in top])
        for h in top:
            h.row = by_id[h.chunk_id]
        terms = self.salient_terms(question)
        best = top[0] if top else None
        coverage = 0.0
        if best and terms:
            blob = (best.row["text"] + " " + best.row["text_original"] + " " + (best.row["title"] or "")).lower()
            coverage = sum(1 for t in terms if t in blob) / len(terms)
        return {"question": question, "linked": linked, "hits": top,
                "max_dense": max((h.dense for h in top), default=0.0),
                "lexical_hits": len(lex), "top_coverage": coverage, "salient_terms": terms}

    ROW_COLS = ["chunk_id", "document_id", "data_category", "content_type", "language", "title", "section", "source",
                "source_url", "document_title", "author", "publication_name", "publication_issue", "publication_year",
                "locator", "locator_type", "printed_pages", "pdf_pages", "slides", "record_ids", "innovator_names",
                "innovation_names", "persons", "organisations", "places", "awards", "entity_ids", "text", "text_original",
                "text_en", "image_text", "quality_flags", "conflict_ids", "curation_notes", "translation"]

    def _rows(self, chunk_ids: list[str]) -> dict[str, dict]:
        rows = self.conn.execute(
            f"""SELECT {', '.join(c if c != 'translation' else "metadata->'translation'" for c in self.ROW_COLS)}
                FROM chunks WHERE chunk_id = ANY(%s)""", (chunk_ids,)).fetchall()
        return {r[0]: dict(zip(self.ROW_COLS, r)) for r in rows}

    LIST_GENERIC = {"project", "projects", "student", "students", "gian", "nidhi", "list", "institution", "institutions",
                    "related", "records", "record", "there", "any", "polytechnic", "college", "colleges", "them", "titles"}

    def keyword_records(self, question: str, limit: int = 40) -> tuple[list[Hit], int, list[str]]:
        """Exhaustive keyword search over ALL GIAN Nidhi records (for 'list / how many' questions,
        where top-k semantic retrieval would silently miss matching records).
        Returns (hits sorted title-matches first, total number of matching chunks, search terms)."""
        terms = [t for t in self.salient_terms(question) if t not in self.LIST_GENERIC and not DEVANAGARI.search(t)]
        if not terms:
            return [], 0, []
        rows, total = [], 0
        for op in (" & ", " | "):
            tsq = op.join(terms)
            total = self.conn.execute(
                """SELECT count(*) FROM chunks WHERE document_id = 'GIAN-NIDHI' AND content_type = 'record'
                   AND tsv_english @@ to_tsquery('english', %s)""", (tsq,)).fetchone()[0]
            if total:
                rows = self.conn.execute(
                    """SELECT chunk_id FROM chunks WHERE document_id = 'GIAN-NIDHI' AND content_type = 'record'
                       AND tsv_english @@ to_tsquery('english', %s) ORDER BY chunk_id LIMIT %s""", (tsq, limit)).fetchall()
                break
        ids = [r[0] for r in rows]
        by_id = self._rows(ids)
        hits = []
        for cid in ids:
            h = Hit(cid, row=by_id[cid])
            title = (by_id[cid]["innovation_names"] or [""])[0].lower()
            h.row["match_field"] = "title" if any(t[:5] in title for t in terms) else "abstract"
            hits.append(h)
        hits.sort(key=lambda h: (h.row["match_field"] != "title", h.chunk_id))
        return hits, total, terms

    def _entity_docs(self, entity_id: str) -> set[str]:
        """Documents in which the entity is actually mentioned (from entity_mentions)."""
        rows = self.conn.execute(
            """SELECT DISTINCT CASE WHEN c.document_id LIKE 'SY51%%' THEN 'SY51' ELSE c.document_id END
               FROM entity_mentions m JOIN chunks c USING (chunk_id) WHERE m.entity_id = %s""", (entity_id,)).fetchall()
        return {r[0] for r in rows}

    def entity_details(self, entity_ids: list[str]) -> dict[str, dict]:
        return {e: self.entities[e] for e in entity_ids if e in self.entities}

    def mention_surface(self, chunk_id: str) -> dict[str, str]:
        return dict(self.conn.execute(
            "SELECT entity_id, surface_form FROM entity_mentions WHERE chunk_id = %s AND surface_form <> ''",
            (chunk_id,)).fetchall())
