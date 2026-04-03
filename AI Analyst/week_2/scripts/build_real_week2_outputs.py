#!/usr/bin/env python3
"""
Week 2 real-data output builder for AI Analyst.

What this script does:
1) Reads week_1 real transcript aggregates (gev_mentions_by_quarter.csv)
2) Builds the REAL gev_competition_mentions chart from those values
3) Builds a second chart for all tracked keyword trends
4) Creates a Week 2 deal database CSV by extending Existing/export_deal_database.csv
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[3]
WEEK1_CSV = ROOT / "AI Analyst" / "week_1" / "outputs" / "gev_mentions_by_quarter.csv"
BASE_DEAL_DB = ROOT / "Existing" / "export_deal_database.csv"
OUT_DIR = ROOT / "AI Analyst" / "week_2" / "outputs"
CHARTS_DIR = OUT_DIR / "charts"
OUT_DEAL_DB = OUT_DIR / "export_deal_database_week2.csv"


def load_mentions_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError(f"No rows found in {path}")
    return rows


def _to_int(value: str | None) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def generate_real_gev_competition_chart(rows: list[dict[str, str]]) -> Path:
    periods = [r["period"] for r in rows]
    china = [_to_int(r.get("china_count_est")) for r in rows]
    competition = [_to_int(r.get("competition_count_est")) for r in rows]
    backlog = [_to_int(r.get("backlog_count_est")) for r in rows]

    intensity = [c + k for c, k in zip(china, competition)]
    confidence_ratio = [b / max(i, 1) for b, i in zip(backlog, intensity)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.bar(periods, china, color="#E74C3C", alpha=0.8, label='"China" mentions')
    ax1.bar(periods, competition, bottom=china, color="#F39C12", alpha=0.8, label='"Competition" mentions')
    ax1.set_ylabel("Mention count")
    ax1.set_title("GEV Calls: China + Competition Mentions (REAL transcript extracts)")
    ax1.tick_params(axis="x", rotation=45)
    ax1.legend(fontsize=9)

    ax2.plot(periods, confidence_ratio, color="#1F4E79", linewidth=2.5, marker="o")
    ax2.fill_between(range(len(periods)), confidence_ratio, alpha=0.12, color="#1F4E79")
    ax2.set_title("Backlog / (China+Competition) ratio")
    ax2.set_ylabel("Ratio")
    ax2.set_xticks(range(len(periods)))
    ax2.set_xticklabels(periods, rotation=45, ha="right")
    ax2.axhline(y=2.0, color="red", linestyle="--", alpha=0.5, linewidth=1)

    plt.tight_layout()
    output = CHARTS_DIR / "gev_competition_mentions_real.png"
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output


def generate_keyword_trends_chart(rows: list[dict[str, str]]) -> Path:
    periods = [r["period"] for r in rows]
    series = {
        "China": [_to_int(r.get("china_count_est")) for r in rows],
        "Competition": [_to_int(r.get("competition_count_est")) for r in rows],
        "Capacity": [_to_int(r.get("capacity_count_est")) for r in rows],
        "Pricing": [_to_int(r.get("pricing_count_est")) for r in rows],
        "Backlog": [_to_int(r.get("backlog_count_est")) for r in rows],
    }

    fig, ax = plt.subplots(figsize=(11, 5))
    colors = {
        "China": "#E74C3C",
        "Competition": "#F39C12",
        "Capacity": "#3498DB",
        "Pricing": "#8E44AD",
        "Backlog": "#1F4E79",
    }
    for name, values in series.items():
        ax.plot(periods, values, marker="o", linewidth=2, label=name, color=colors[name])

    ax.set_title("GEV transcript keyword trends (Q1 2024 to Q4 2025)")
    ax.set_ylabel("Mention count estimate")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.25)
    ax.legend(ncol=3, fontsize=9)
    plt.tight_layout()

    output = CHARTS_DIR / "gev_keyword_trends_real.png"
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output


def build_week2_deal_database(base_path: Path, output_path: Path) -> Path:
    with base_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    rows.append(
        {
            "date": "2025-Q4",
            "chinese_oem": "Dongfang Electric",
            "buyer": "Undisclosed Middle East Counterparty",
            "country": "Undisclosed",
            "region": "Middle East",
            "product": "G50 Gas Turbine (50MW, self-developed)",
            "units": "0",
            "mw_per_unit": "50",
            "total_mw": "0",
            "est_value_usd_m": "0",
            "status": "Mentioned (size not disclosed)",
            "source": "Huatai Securities summary (Futunn), 2025-11-15",
            "notes": "Source indicates Middle East export orders landed, but no project size disclosed.",
        }
    )

    with output_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    return output_path


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    rows = load_mentions_csv(WEEK1_CSV)
    c1 = generate_real_gev_competition_chart(rows)
    c2 = generate_keyword_trends_chart(rows)
    db = build_week2_deal_database(BASE_DEAL_DB, OUT_DEAL_DB)

    print(f"Generated: {c1}")
    print(f"Generated: {c2}")
    print(f"Generated: {db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
