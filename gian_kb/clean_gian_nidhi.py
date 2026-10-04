"""Clean and structure the GIAN Nidhi table into the assignment CSV.

Every transformation is conservative and logged in ``data_quality_log.csv``:

* exact duplicate rows returned by the endpoint are dropped (each ID came back twice);
* HTML entities, line breaks, non-breaking spaces and mojibake are repaired, but the raw
  value is always kept next to the cleaned one;
* abstracts that the source stored in the "College Status" column are moved back;
* participants are split into a list (initial-only fragments such as ``"B."`` are re-attached);
* institution names get a *deterministic* canonical key (abbreviation expansion +
  punctuation removal). Fuzzy look-alikes are only reported for review, never merged;
* projects with the same title are linked as duplicates only when participants also
  match - a shared title alone is not evidence of the same project.

Outputs (data/processed/): gian_nidhi_projects.csv, gian_nidhi_institutions.csv,
data_quality_log_gian_nidhi.csv
"""
from __future__ import annotations

import csv
import html
import json
import re
from collections import Counter, defaultdict

import ftfy
from rapidfuzz import fuzz

from .config import CURATED, DOCUMENTS, PROCESSED, RAW

RAW_DIR = RAW / "gian_nidhi"
SOURCE_COLUMNS = ["ID", "Column Status", "Sr No", "Project Name", "Participants", "Abstracts", "College Status"]
HONORIFICS = re.compile(r"^(mr|mrs|ms|miss|dr|prof|shri|smt|kum|km)(\.\s*|\s+)", re.I)
PLACEHOLDERS = {"not available", "na", "n/a", "-", "nil", "none"}

dq_log: list[dict] = []


def log(record_id, field, issue, action, before="", after=""):
    dq_log.append({"source": "GIAN-NIDHI", "record_id": record_id, "field": field, "issue": issue,
                   "action": action, "value_before": str(before)[:200], "value_after": str(after)[:200]})


def clean_text(v: str) -> str:
    v = html.unescape(v or "")
    v = ftfy.fix_text(v)
    v = re.sub(r"<br\s*/?>", " ", v, flags=re.I)
    v = v.replace(" ", " ").replace("\r", " ").replace("\n", " ")
    v = v.replace("’", "'").replace("‘", "'")
    v = re.sub(r"\s+", " ", v).strip()
    return v


def clean_institution(v: str) -> str:
    v = clean_text(v)
    v = re.sub(r"^(NAME\s*::|:)\s*", "", v)        # form artefacts seen in the source ("NAME::", ": ")
    v = re.sub(r"\s+,", ",", v)
    v = re.sub(r",(?=\S)", ", ", v)
    v = v.strip(" .,;=")
    return v


ABBREV = [(r"\bgovt\b\.?", "government"), (r"\bengg\b\.?", "engineering"), (r"\btech\b\.?", "technology"),
          (r"\binst\b\.?", "institute"), (r"&", " and "), (r"\bresidental\b", "residential"),
          (r"\bwoman's\b", "women's"), (r"\bahmednager\b", "ahmednagar")]


def institution_key(v: str) -> str:
    k = v.lower()
    for pat, rep in ABBREV:
        k = re.sub(pat, rep, k)
    k = re.sub(r"[^a-z0-9]+", " ", k)
    return re.sub(r"\s+", " ", k).strip()


def split_participants(raw: str) -> list[str]:
    v = clean_text(raw)
    if not v or v.lower() in PLACEHOLDERS:
        return []
    v = re.sub(r"\s+(and|&)\s+", ",", v, flags=re.I)
    v = re.sub(r"[;/]", ",", v)
    parts = [p.strip(" .") for p in v.split(",")]
    out: list[str] = []
    for p in parts:
        if not p:
            continue
        if re.fullmatch(r"(?:[A-Za-z]\.?\s*){1,3}", p) and out:   # initials only -> belongs to previous name
            out[-1] = f"{out[-1]} {p}."
            continue
        out.append(re.sub(r"\s+", " ", p))
    return out


def name_key(n: str) -> str:
    n = HONORIFICS.sub("", n.strip())
    return re.sub(r"[^a-z]", "", n.lower())


def text_key(v: str) -> str:
    return re.sub(r"[^a-z0-9]", "", v.lower())


def main() -> dict:
    dq_log.clear()
    rows = json.loads((RAW_DIR / "api_rows_raw.json").read_text(encoding="utf-8"))
    fetch_log = json.loads((RAW_DIR / "fetch_log.json").read_text(encoding="utf-8"))
    retrieved_at = fetch_log["retrieved_at"]

    # 1) exact duplicate rows from the endpoint -------------------------------------------
    by_id: dict[str, list] = {}
    for r in rows:
        if r[0] in by_id:
            if by_id[r[0]] != r:
                log(r[0], "*", "conflicting rows with same ID", "kept first occurrence")
            continue
        by_id[r[0]] = r
    log("*", "*", f"endpoint returned {len(rows)} rows for {len(by_id)} unique IDs (each ID twice, identical content)",
        "dropped exact duplicate rows")

    records = []
    for rid in sorted(by_id, key=int):
        r = by_id[rid]
        raw = dict(zip(SOURCE_COLUMNS, r))
        rec = {
            "record_id": int(rid),
            "sr_no": int(raw["Sr No"]) if raw["Sr No"].strip().isdigit() else raw["Sr No"],
            "record_status": clean_text(raw["Column Status"]),
            "project_name": clean_text(raw["Project Name"]),
            "participants_raw": raw["Participants"],
            "abstract": clean_text(raw["Abstracts"]),
            "institution_raw": raw["College Status"],
            "institution_name": clean_institution(raw["College Status"]),
            "flags": [],
        }
        for fld, rv in (("project_name", raw["Project Name"]), ("abstract", raw["Abstracts"]),
                        ("institution_name", raw["College Status"])):
            if rv and rec[fld] != rv.strip():
                kinds = []
                if "&" in rv and re.search(r"&[a-z#0-9]+;", rv): kinds.append("html entities")
                if re.search("Ã|â€", rv): kinds.append("mojibake")
                if " " in rv: kinds.append("non-breaking spaces")
                if "\n" in rv or "<br" in rv: kinds.append("line breaks")
                if kinds:
                    log(rid, fld, ", ".join(kinds), "normalised text (raw value kept)", rv, rec[fld])

        # 2) abstract stored in the institution column ------------------------------------
        if not rec["abstract"] and len(rec["institution_name"]) > 100:
            log(rid, "College Status", "abstract text found in institution column (column shift)",
                "moved to abstract; institution set to unknown", rec["institution_name"], "")
            rec["abstract"], rec["institution_name"] = rec["institution_name"], ""
            rec["flags"].append("abstract_recovered_from_institution_column")

        # 3) placeholders and missing values ------------------------------------------------
        if rec["project_name"].lower() in PLACEHOLDERS:
            rec["flags"].append("placeholder_project_name")
            log(rid, "Project Name", "placeholder value", "kept, flagged", rec["project_name"])
        if rec["abstract"].lower() in PLACEHOLDERS:
            log(rid, "Abstracts", "placeholder value", "set to empty", rec["abstract"])
            rec["abstract"] = ""
        if not rec["abstract"]:
            rec["flags"].append("missing_abstract")
        if not rec["institution_name"]:
            rec["flags"].append("missing_institution")

        # 4) participants ---------------------------------------------------------------------
        parts = split_participants(raw["Participants"])
        rec["participants"] = parts
        if not parts:
            rec["flags"].append("missing_participants")
        if any(len(p.split()) == 1 for p in parts):
            rec["flags"].append("participant_split_ambiguous")
        if any(re.match(r"(dr|prof)\b", p, re.I) for p in parts):
            rec["flags"].append("participants_include_faculty_titles")
        records.append(rec)

    # 5) institution canonicalisation ------------------------------------------------------
    #    a) deterministic key (abbreviations expanded, punctuation/case removed)
    #    b) manually reviewed merges from data/curated/institution_review.json
    #    c) remaining fuzzy look-alikes are only *reported* (possible_same_as), never merged
    for rec in records:
        rec["institution_key"] = institution_key(rec["institution_name"]) if rec["institution_name"] else ""
    keys = sorted({r["institution_key"] for r in records if r["institution_key"]})
    parent = {k: k for k in keys}

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    review = json.loads((CURATED / "institution_review.json").read_text(encoding="utf-8"))["decisions"]
    reviewed_pairs: dict[frozenset, dict] = {}
    for d in review:
        dkeys = []
        for n in d["names"]:
            k = institution_key(clean_institution(n))
            if k not in parent:
                raise ValueError(f"institution_review.json name not found in data: {n!r}")
            dkeys.append(k)
        for a in dkeys:
            for b in dkeys:
                if a < b:
                    reviewed_pairs[frozenset((a, b))] = d
        if d["decision"] == "merge":
            for k in dkeys[1:]:
                parent[find(k)] = find(dkeys[0])
            log("*", "College Status", "reviewed institution variants", "merged: " + d["reason"], " | ".join(d["names"]))
        else:
            log("*", "College Status", f"reviewed look-alike institutions ({d['decision']})", "NOT merged: " + d["reason"],
                " | ".join(d["names"]))

    clusters: dict[str, list[str]] = defaultdict(list)
    for rec in records:
        if rec["institution_key"]:
            clusters[find(rec["institution_key"])].append(rec["institution_name"])
    inst_rows, root_to_id = [], {}
    for i, (root, variants) in enumerate(sorted(clusters.items(), key=lambda kv: (-len(kv[1]), kv[0])), start=1):
        cnt = Counter(variants)
        canonical = sorted(cnt.items(), key=lambda kv: (-kv[1], -len(kv[0])))[0][0]
        iid = f"INS-{i:04d}"
        root_to_id[root] = (iid, canonical)
        inst_rows.append({"institution_id": iid, "canonical_name": canonical,
                          "match_keys": " | ".join(sorted({institution_key(v) for v in cnt})),
                          "record_count": len(variants), "name_variants": " | ".join(sorted(cnt)),
                          "possible_same_as": "", "reviewed_not_same_as": ""})
    by_id = {r["institution_id"]: r for r in inst_rows}

    def add(iid, col, other):
        cur = set(by_id[iid][col].split()) if by_id[iid][col] else set()
        by_id[iid][col] = " ".join(sorted(cur | {other}))

    # cluster-level decision: an explicit keep_separate review wins over fuzzy similarity
    pair_state: dict[frozenset, str] = {}
    for a_i, a in enumerate(keys):
        for b in keys[a_i + 1:]:
            ra, rb = find(a), find(b)
            if ra == rb:
                continue
            cp = frozenset((ra, rb))
            d = reviewed_pairs.get(frozenset((a, b)))
            if d and d["decision"] == "keep_separate":
                pair_state[cp] = "keep_separate"
            elif pair_state.get(cp) != "keep_separate":
                if d and d["decision"] == "unresolved":
                    pair_state[cp] = "unresolved"
                elif fuzz.token_sort_ratio(a, b) >= 92 and cp not in pair_state:
                    pair_state[cp] = "fuzzy"
    for cp, state in pair_state.items():
        ra, rb = sorted(cp)
        ia, ib = root_to_id[ra][0], root_to_id[rb][0]
        col = "reviewed_not_same_as" if state == "keep_separate" else "possible_same_as"
        add(ia, col, ib); add(ib, col, ia)
        if state == "fuzzy":
            log(f"{ia}~{ib}", "College Status", "near-identical institution names (unreviewed)",
                "NOT merged; flagged possible_same_as", root_to_id[ra][1], root_to_id[rb][1])
    for rec in records:
        if rec["institution_key"]:
            rec["institution_id"], rec["institution_canonical"] = root_to_id[find(rec["institution_key"])]
            if rec["institution_canonical"] != rec["institution_name"]:
                log(rec["record_id"], "College Status", "institution name variant", "mapped to canonical name",
                    rec["institution_name"], rec["institution_canonical"])
        else:
            rec["institution_id"], rec["institution_canonical"] = "", ""

    # 6) duplicate projects: same title AND same participant set -------------------------------
    by_title: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        if "placeholder_project_name" not in rec["flags"]:
            by_title[text_key(rec["project_name"])].append(rec)
    for rec in records:
        rec.update({"duplicate_group_id": "", "duplicate_status": "unique", "duplicate_of": ""})
    gid = 0
    for title, recs in by_title.items():
        if len(recs) < 2:
            continue
        clusters: list[list[dict]] = []
        for rec in recs:
            pset = frozenset(name_key(p) for p in rec["participants"])
            for cl in clusters:
                qset = frozenset(name_key(p) for p in cl[0]["participants"])
                if pset and qset and (pset == qset or len(pset & qset) / max(len(pset | qset), 1) >= 0.75):
                    cl.append(rec)
                    break
            else:
                clusters.append([rec])
        for cl in clusters:
            if len(cl) < 2:
                for rec in cl:
                    rec["flags"].append("shares_title_with_different_team")
                continue
            gid += 1
            canon = min(cl, key=lambda x: x["record_id"])
            exact = all(text_key(r["abstract"]) == text_key(canon["abstract"])
                        and r["institution_key"] == canon["institution_key"] for r in cl)
            conflicting_inst = len({r["institution_id"] or "?" for r in cl}) > 1
            for rec in cl:
                rec["duplicate_group_id"] = f"DUP-{gid:03d}"
                if rec is canon:
                    rec["duplicate_status"] = "canonical"
                else:
                    rec["duplicate_status"] = "exact_duplicate" if exact else "probable_duplicate"
                    rec["duplicate_of"] = str(canon["record_id"])
                if conflicting_inst:
                    rec["flags"].append("conflicting_institution_across_duplicates")
            log(",".join(str(r["record_id"]) for r in cl), "Project Name",
                "same title and same team" + (" (identical content)" if exact else " (content differs)"),
                f"linked as DUP-{gid:03d}; canonical record {canon['record_id']}; no record deleted")

    # 7) write CSVs -----------------------------------------------------------------------------
    PROCESSED.mkdir(parents=True, exist_ok=True)
    src = DOCUMENTS["GIAN-NIDHI"]
    cols = ["record_id", "sr_no", "project_name", "participants", "participant_count", "abstract", "abstract_word_count",
            "institution_name", "institution_canonical", "institution_id", "record_status", "duplicate_group_id",
            "duplicate_status", "duplicate_of", "data_quality_flags", "participants_raw", "institution_raw",
            "source", "source_url", "retrieved_at"]
    with open(PROCESSED / "gian_nidhi_projects.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for rec in records:
            w.writerow({**{k: rec.get(k, "") for k in cols},
                        "participants": "; ".join(rec["participants"]),
                        "participant_count": len(rec["participants"]),
                        "abstract_word_count": len(rec["abstract"].split()),
                        "data_quality_flags": "; ".join(sorted(set(rec["flags"]))),
                        "participants_raw": clean_text(rec["participants_raw"]) if rec["participants_raw"] else "",
                        "institution_raw": rec["institution_raw"].replace(" ", " ").strip(),
                        "source": src["source"], "source_url": src["source_url"], "retrieved_at": retrieved_at})
    with open(PROCESSED / "gian_nidhi_institutions.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(inst_rows[0]))
        w.writeheader()
        w.writerows(inst_rows)
    with open(PROCESSED / "data_quality_log_gian_nidhi.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(dq_log[0]))
        w.writeheader()
        w.writerows(dq_log)
    (PROCESSED / "gian_nidhi_projects.json").write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")

    flags = Counter(f for r in records for f in set(r["flags"]))
    dup = Counter(r["duplicate_status"] for r in records)
    return {"rows_raw": len(rows), "records": len(records), "institution_strings": len({r["institution_name"] for r in records if r["institution_name"]}),
            "institutions_canonical": len(inst_rows), "duplicate_status": dict(dup), "flags": dict(flags),
            "dq_log_entries": len(dq_log)}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
