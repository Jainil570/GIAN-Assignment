"""Collect the GIAN Nidhi table from https://gian.org/gian-nidhi/.

The page renders an empty HTML table that the *WP Data Access* plugin fills through a
DataTables server-side AJAX call (``admin-ajax.php?action=wpda_datatables``). We make the
same request the browser makes (public endpoint, no login), page through all rows and
store the response untouched so that every later cleaning step is auditable.

Outputs (data/raw/gian_nidhi/):
    page_snapshot.html     the page as served (used to read nonce / publication id)
    api_rows_raw.json      every row exactly as returned by the endpoint
    fetch_log.json         timestamp, request parameters, counts
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone

import requests

from .config import GIAN_AJAX_URL, GIAN_NIDHI_URL, RAW

OUT = RAW / "gian_nidhi"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
    "Referer": GIAN_NIDHI_URL,
    "X-Requested-With": "XMLHttpRequest",
}


def _publication_params(html: str) -> dict:
    """Read table name, column list, publication id and nonce from the inline JS call."""
    cols = re.findall(r'data-column_name_search="([a-z_]+)"', html)
    columns = list(dict.fromkeys(cols))  # thead + tfoot repeat the same list
    call = re.search(r"wpda_datatables_ajax_call\((.*?)\);\s*\}\);", html, re.S)
    if not call:
        raise RuntimeError("WP Data Access call not found - page layout changed")
    args = [a.strip().strip('"') for a in call.group(1).split(",")]
    # positional args (see wpda_datatables.js): [2]=table_name, [14]=pub_id, [-2]=wpnonce
    return {"table_name": args[2], "pub_id": args[14], "wpnonce": args[-2], "columns": columns}


def fetch(page_size: int = 200, pause: float = 1.0) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    page = s.get(GIAN_NIDHI_URL, headers=HEADERS, timeout=60)
    page.raise_for_status()
    (OUT / "page_snapshot.html").write_text(page.text, encoding="utf-8")
    p = _publication_params(page.text)

    rows, start, draw, total = [], 0, 1, None
    while total is None or start < total:
        data = {
            "action": "wpda_datatables", "wpnonce": p["wpnonce"], "pubid": p["pub_id"],
            "draw": str(draw), "start": str(start), "length": str(page_size),
            "search[value]": "", "search[regex]": "false",
            "order[0][column]": "0", "order[0][dir]": "asc",
            "filter_field_name": "", "filter_field_value": "", "nl2br": "",
        }
        for i, c in enumerate(p["columns"]):
            data.update({
                f"columns[{i}][data]": str(i), f"columns[{i}][name]": c,
                f"columns[{i}][searchable]": "true", f"columns[{i}][orderable]": "true",
                f"columns[{i}][search][value]": "", f"columns[{i}][search][regex]": "false",
            })
        r = s.post(GIAN_AJAX_URL, data=data, headers=HEADERS, timeout=120)
        r.raise_for_status()
        js = r.json()
        total = int(js["recordsTotal"])
        if not js["data"]:
            break
        rows.extend(js["data"])
        start += page_size
        draw += 1
        time.sleep(pause)

    log = {
        "source_url": GIAN_NIDHI_URL,
        "endpoint": GIAN_AJAX_URL,
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "table_name": p["table_name"], "publication_id": p["pub_id"],
        "columns": p["columns"],
        "records_total_reported": total, "rows_received": len(rows),
    }
    (OUT / "api_rows_raw.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "fetch_log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    return log


if __name__ == "__main__":
    print(json.dumps(fetch(), indent=2))
