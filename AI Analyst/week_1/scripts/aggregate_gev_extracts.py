#!/usr/bin/env python3
"""
Read all GEV_*.extracted.json files from the processed transcripts folder and
write a single CSV for charts / Excel (mention counts by quarter).

Usage:
  python aggregate_gev_extracts.py
  python aggregate_gev_extracts.py --output ../outputs/gev_mentions_by_quarter.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _period_sort_key(period: str) -> Tuple[int, int]:
    m = re.match(r"^Q([1-4])\s+(\d{4})$", period.strip())
    if not m:
        return (9999, 99)
    q, y = int(m.group(1)), int(m.group(2))
    return (y, q)


def _safe_int(x: Any) -> Optional[int]:
    if x is None:
        return None
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return int(x)
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def load_extract(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate GEV transcript JSON extracts into one CSV.")
    parser.add_argument(
        "--processed-dir",
        default=None,
        help="Folder containing GEV_*.extracted.json (default: ../data/transcripts/processed next to this script)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output CSV path (default: ../outputs/gev_mentions_by_quarter.csv)",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    processed = Path(args.processed_dir) if args.processed_dir else here.parent / "data" / "transcripts" / "processed"
    out_path = Path(args.output) if args.output else here.parent / "outputs" / "gev_mentions_by_quarter.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    files = sorted(processed.glob("GEV_*.extracted.json"))
    if not files:
        raise SystemExit(f"No GEV_*.extracted.json files found in: {processed}")

    rows: List[Dict[str, Any]] = []
    for fp in files:
        data = load_extract(fp)
        ext = data.get("extracted") or {}
        meta = ext.get("metadata") or {}
        period = meta.get("period") or ""
        call_date = meta.get("date")
        mentions = ext.get("mentions") or {}

        def bucket(name: str) -> Dict[str, Any]:
            b = mentions.get(name) or {}
            return b if isinstance(b, dict) else {}

        row = {
            "period": period,
            "call_date": call_date or "",
            "source_file": data.get("source_filename", fp.name),
            "china_count_est": _safe_int(bucket("china").get("count_estimate")),
            "competition_count_est": _safe_int(bucket("competition").get("count_estimate")),
            "capacity_count_est": _safe_int(bucket("capacity").get("count_estimate")),
            "pricing_count_est": _safe_int(bucket("pricing").get("count_estimate")),
            "backlog_count_est": _safe_int(bucket("backlog").get("count_estimate")),
            "china_snippets_n": len(bucket("china").get("snippets") or []),
            "competition_snippets_n": len(bucket("competition").get("snippets") or []),
            "capacity_snippets_n": len(bucket("capacity").get("snippets") or []),
            "pricing_snippets_n": len(bucket("pricing").get("snippets") or []),
            "backlog_snippets_n": len(bucket("backlog").get("snippets") or []),
            "extracted_at_utc": data.get("extracted_at_utc", ""),
        }
        rows.append(row)

    rows.sort(key=lambda r: _period_sort_key(str(r.get("period", ""))))

    fieldnames = [
        "period",
        "call_date",
        "china_count_est",
        "competition_count_est",
        "capacity_count_est",
        "pricing_count_est",
        "backlog_count_est",
        "china_snippets_n",
        "competition_snippets_n",
        "capacity_snippets_n",
        "pricing_snippets_n",
        "backlog_snippets_n",
        "source_file",
        "extracted_at_utc",
    ]

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})

    print(f"Wrote: {out_path}")
    print(f"Rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
