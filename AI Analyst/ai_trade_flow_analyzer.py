"""
AI TRADE FLOW ANALYZER — Cross-Border Power Equipment Intelligence
===================================================================
UBS Finance Challenge 2026 | Long DEC / Short GEV

A functioning Python pipeline that:
  A. Structures gas turbine export deals from public announcements
  B. Parses GEV earnings call transcripts for competition/China mentions
  C. Computes a China Export Momentum Score (0-100)
  D. Generates deck-ready charts (Slide 6 hockey stick, market share, GEV NLP, pipeline, score) + Bible filenames

Usage:
  # Full pipeline: NLP extraction saves merged CSV artifact only; score & charts
  # use the curated deal database unless you pass --include-extractions-in-score.
  python ai_trade_flow_analyzer.py --full

  # Charts + score only (no API key needed, uses pre-processed data):
  python ai_trade_flow_analyzer.py --charts-only

  # Extract deals from Chinese news (requires API key); same scoring rule as --full.
  python ai_trade_flow_analyzer.py --extract-news

  # Extract from GEV transcript (requires API key):
  python ai_trade_flow_analyzer.py --extract-transcript path/to/transcript.txt

Dependencies:
  pip install matplotlib numpy anthropic
"""

import os
import re
import sys
import json
import csv
import shutil
import argparse
import math
from datetime import datetime
from pathlib import Path

import env_bootstrap

env_bootstrap.load_dotenv_if_present()

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TRANSCRIPT_CSV = DATA_DIR / "transcripts" / "gev_mentions_by_quarter.csv"
DEAL_DB_PATH = DATA_DIR / "deals" / "export_deal_database.csv"
NEWS_RAW_DIR = DATA_DIR / "news" / "raw"
OUTPUT_DIR = BASE_DIR / "outputs"
CHART_DIR = OUTPUT_DIR / "charts"

# Ensure output dirs exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "transcripts").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "deals").mkdir(parents=True, exist_ok=True)
NEWS_RAW_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Model for API calls
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Rough USD→CNY for charting when only USD estimates exist in the legacy deal CSV
USD_TO_CNY_FOR_CHARTS = 7.2

# Momentum score weights (must sum to 1.0). If real GEV mentions lack a clean uptrend,
# you may shift 5pp from incumbent_anxiety → deal_flow per team methodology note.
SCORE_WEIGHTS = {
    "deal_flow": 0.30,
    "incumbent_anxiety": 0.25,
    "order_conversion": 0.20,
    "geographic_diversification": 0.15,
    "technology_validation": 0.10,
}

# Order conversion sub-score: word-boundary match so "Unconfirmed" is not counted as "confirmed".
_ORDER_CONVERSION_STATUS_RE = re.compile(
    r"\b(?:delivered|confirmed|in\s+progress|contract\s+signed)\b",
    re.IGNORECASE,
)


def _status_counts_toward_order_conversion(status: str) -> bool:
    return bool(_ORDER_CONVERSION_STATUS_RE.search(str(status or "")))


# Illustrative global market-share stacks (2020–2027E) for appendix / Slide 7.
# NOT customs-derived — see methodology doc. Replace if team obtains licensed market data.
MARKET_SHARE_ILLUSTRATIVE = {
    "2020": {"GE Vernova": 38, "Siemens Energy": 28, "Mitsubishi Power": 18, "Other Western": 12, "Chinese OEMs": 4},
    "2021": {"GE Vernova": 37, "Siemens Energy": 27, "Mitsubishi Power": 18, "Other Western": 13, "Chinese OEMs": 5},
    "2022": {"GE Vernova": 36, "Siemens Energy": 27, "Mitsubishi Power": 17, "Other Western": 13, "Chinese OEMs": 7},
    "2023": {"GE Vernova": 35, "Siemens Energy": 26, "Mitsubishi Power": 17, "Other Western": 12, "Chinese OEMs": 10},
    "2024": {"GE Vernova": 34, "Siemens Energy": 25, "Mitsubishi Power": 16, "Other Western": 12, "Chinese OEMs": 13},
    "2025E": {"GE Vernova": 33, "Siemens Energy": 24, "Mitsubishi Power": 15, "Other Western": 11, "Chinese OEMs": 17},
    "2026E": {"GE Vernova": 31, "Siemens Energy": 23, "Mitsubishi Power": 14, "Other Western": 10, "Chinese OEMs": 22},
    "2027E": {"GE Vernova": 29, "Siemens Energy": 22, "Mitsubishi Power": 13, "Other Western": 9, "Chinese OEMs": 27},
}

# ---------------------------------------------------------------------------
# SECTION A: DEAL DATABASE — Load, Structure, Extract
# ---------------------------------------------------------------------------

def _normalize_loaded_deal(row: dict, index: int) -> dict:
    """
    Map team CSV columns (buyer, country, est_value_usd_m) to the schema this
    module uses internally (buyer_entity, buyer_country, est_value_cny_m).
    """
    r = dict(row)
    for field in ["units", "mw_per_unit", "total_mw"]:
        if r.get(field) not in (None, ""):
            try:
                r[field] = int(float(r[field]))
            except (ValueError, TypeError):
                r[field] = 0
        else:
            r[field] = 0
    for field in ["est_value_usd_m", "est_value_cny_m"]:
        if r.get(field) not in (None, ""):
            try:
                r[field] = float(r[field])
            except (ValueError, TypeError):
                r[field] = 0.0
        else:
            r[field] = 0.0

    if not str(r.get("buyer_country", "")).strip() and r.get("country"):
        r["buyer_country"] = str(r["country"]).strip()
    if not str(r.get("buyer_entity", "")).strip() and r.get("buyer"):
        r["buyer_entity"] = str(r["buyer"]).strip()

    if r.get("est_value_cny_m", 0) == 0 and r.get("est_value_usd_m", 0) > 0:
        r["est_value_cny_m"] = round(float(r["est_value_usd_m"]) * USD_TO_CNY_FOR_CHARTS, 1)

    if not str(r.get("deal_id", "")).strip():
        d = str(r.get("date", "UNK")).replace(" ", "_")
        r["deal_id"] = f"DB_{index + 1:03d}_{d}"

    if not str(r.get("confidence", "")).strip():
        r["confidence"] = "MEDIUM"

    return r


def load_deal_database() -> list[dict]:
    """Load the existing deal database from CSV."""
    deals = []
    if not DEAL_DB_PATH.exists():
        print(f"  [WARN] Deal database not found at {DEAL_DB_PATH}")
        return deals
    with open(DEAL_DB_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            deals.append(_normalize_loaded_deal(row, i))
    print(f"  [OK] Loaded {len(deals)} deals from database")
    return deals


def _deal_quarter_sort_key(q: str) -> tuple:
    """Sort key for CSV `date` labels like 2025-Q1, 2026-Q2E (pipeline quarters end with E)."""
    s = (q or "").strip().upper()
    pipeline = len(s) >= 2 and s.endswith("E")
    core = s[:-1] if pipeline else s
    m = re.match(r"^(\d{4})-Q([1-4])$", core)
    if not m:
        return (9999, 9, 9)
    y, qn = int(m.group(1)), int(m.group(2))
    return (y, qn, 1 if pipeline else 0)


def build_quarterly_export_mw_series(deals: list[dict]) -> list[dict]:
    """
    Aggregate total_mw by deal `date` quarter label, chronological order.
    Pipeline styling: quarter label ends with 'E' (team convention).
    """
    buckets: dict[str, int] = {}
    for deal in deals:
        q = str(deal.get("date", "")).strip()
        if not q:
            continue
        mw = int(deal.get("total_mw", 0) or 0)
        buckets[q] = buckets.get(q, 0) + mw
    ordered = sorted(buckets.keys(), key=_deal_quarter_sort_key)
    out = []
    cum = 0
    for q in ordered:
        mw = buckets[q]
        cum += mw
        pipeline = q.upper().endswith("E")
        out.append(
            {
                "quarter": q,
                "mw": mw,
                "cum_mw": cum,
                "is_pipeline": pipeline,
            }
        )
    return out


def _safe_deal_id_slug(name: str) -> str:
    """ASCII slug from a news filename stem for unique EXT_* deal_ids."""
    s = re.sub(r"[^A-Za-z0-9]+", "_", (name or "news").strip()).strip("_") or "news"
    return s[:48]


def extract_deals_from_chinese_text(
    text: str, source_url: str = "", source_file_slug: str = ""
) -> list[dict]:
    """
    Use Claude API to extract structured deal data from Chinese-language text.
    Returns a list of deal dicts matching the database schema.
    """
    try:
        import anthropic
    except ImportError:
        print("  [ERROR] 'anthropic' package not installed. Run: pip install anthropic")
        return []

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  [ERROR] ANTHROPIC_API_KEY not set. Add it to AI Analyst/.env or run:")
        print("          export ANTHROPIC_API_KEY='your-key-here'")
        return []

    client = anthropic.Anthropic(api_key=api_key)

    extraction_prompt = """You are a structured data extraction tool for gas turbine export deals.

Analyze the following Chinese-language text and extract ALL gas turbine export deals mentioned.

For each deal, return a JSON object with these exact fields:
- date: quarter/year (e.g., "2026-Q1")
- chinese_oem: manufacturer name in English (e.g., "Dongfang Electric")
- buyer_country: country name
- buyer_entity: buyer organization name
- product: turbine model (e.g., "G50 (50MW)")
- units: number of units (integer, 0 if not stated)
- mw_per_unit: MW per unit (integer, 0 if not stated)
- total_mw: total MW (integer, 0 if not stated)
- est_value_usd_m: estimated value in USD millions (0 if not stated)
- est_value_cny_m: estimated value in CNY millions (0 if not stated)
- status: one of [Delivered, Confirmed, In Progress, MOU Signed, Negotiating, Early Stage, Mentioned]
- confidence: one of [HIGH, MEDIUM, LOW]
- notes: brief English summary of what was stated

If NO deals are found in the text, return an empty JSON array: []

Return ONLY valid JSON — an array of objects. No markdown, no explanation."""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": f"{extraction_prompt}\n\n--- TEXT ---\n{text}\n--- END ---"
                }
            ]
        )

        raw = response.content[0].text.strip()
        # Clean potential markdown fences
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

        deals = json.loads(raw)
        if not isinstance(deals, list):
            deals = [deals]

        slug = _safe_deal_id_slug(source_file_slug)
        day = datetime.now().strftime("%Y%m%d")
        # Per-file index + source stem avoids duplicate EXT_* ids across articles.
        for i, deal in enumerate(deals):
            deal["source"] = source_url or "Chinese news extraction (Claude API)"
            deal["deal_id"] = f"EXT_{slug}_{i + 1:03d}_{day}"

        print(f"  [OK] Extracted {len(deals)} deals from text")
        return deals

    except json.JSONDecodeError as e:
        print(f"  [ERROR] Failed to parse API response as JSON: {e}")
        print(f"  Raw response: {raw[:200]}")
        return []
    except Exception as e:
        print(f"  [ERROR] API call failed: {e}")
        return []


def process_all_news_files() -> list[dict]:
    """Process all Chinese news files in data/news/raw/ and extract deals."""
    all_deals = []
    if not NEWS_RAW_DIR.exists():
        print(f"  [WARN] News directory not found: {NEWS_RAW_DIR}")
        return all_deals

    news_files = sorted(NEWS_RAW_DIR.glob("*.txt"))
    if not news_files:
        print(f"  [WARN] No .txt files found in {NEWS_RAW_DIR}")
        return all_deals

    print(f"\n  Processing {len(news_files)} news files...")
    for fpath in news_files:
        print(f"    → {fpath.name}")
        text = fpath.read_text(encoding="utf-8")

        # Extract source URL from text if present
        source_url = ""
        for line in text.split("\n"):
            if line.strip().lower().startswith("url:"):
                source_url = line.split(":", 1)[1].strip()
                break

        deals = extract_deals_from_chinese_text(
            text, source_url, source_file_slug=fpath.stem
        )
        all_deals.extend(deals)

    return all_deals


def save_deals_to_csv(deals: list[dict], output_path: Path):
    """Save deals list to CSV."""
    if not deals:
        print("  [WARN] No deals to save")
        return

    fieldnames = [
        "deal_id", "date", "chinese_oem", "buyer_country", "buyer_entity",
        "product", "units", "mw_per_unit", "total_mw",
        "est_value_usd_m", "est_value_cny_m", "status", "source",
        "confidence", "notes"
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for deal in deals:
            row = {k: deal.get(k, "") for k in fieldnames}
            writer.writerow(row)

    print(f"  [OK] Saved {len(deals)} deals to {output_path}")


# ---------------------------------------------------------------------------
# SECTION B: TRANSCRIPT ANALYSIS — Parse GEV Earnings Calls
# ---------------------------------------------------------------------------

def load_transcript_data() -> list[dict]:
    """
    Load pre-aggregated GEV transcript mention counts.

    Accepts either:
      - Canonical headers: quarter, china_mentions, competition_mentions, ...
      - Week-1 aggregate headers: period, china_count_est, competition_count_est, ...
    """
    if not TRANSCRIPT_CSV.exists():
        print(f"  [WARN] Transcript CSV not found at {TRANSCRIPT_CSV}")
        return []

    rows_out: list[dict] = []
    with open(TRANSCRIPT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            q = (raw.get("quarter") or raw.get("period") or "").strip()
            out = {
                "quarter": q,
                "call_date": (raw.get("call_date") or "").strip(),
                "china_mentions": 0,
                "competition_mentions": 0,
                "capacity_mentions": 0,
                "pricing_mentions": 0,
                "backlog_mentions": 0,
            }
            alias = [
                ("china_mentions", ["china_mentions", "china_count_est"]),
                ("competition_mentions", ["competition_mentions", "competition_count_est"]),
                ("capacity_mentions", ["capacity_mentions", "capacity_count_est"]),
                ("pricing_mentions", ["pricing_mentions", "pricing_count_est"]),
                ("backlog_mentions", ["backlog_mentions", "backlog_count_est"]),
            ]
            for canon, keys in alias:
                val = 0
                for k in keys:
                    if k in raw and raw[k] not in (None, ""):
                        try:
                            val = int(float(raw[k]))
                            break
                        except (ValueError, TypeError):
                            val = 0
                out[canon] = val
            rows_out.append(out)

    print(f"  [OK] Loaded {len(rows_out)} quarters of transcript data")
    return rows_out


def extract_transcript_mentions(transcript_text: str, quarter: str) -> dict:
    """
    Use Claude API to extract structured mention data from a GEV earnings
    call transcript. Returns a dict with mention counts and key snippets.
    """
    try:
        import anthropic
    except ImportError:
        print("  [ERROR] 'anthropic' package not installed")
        return {}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  [ERROR] ANTHROPIC_API_KEY not set (use AI Analyst/.env or export)")
        return {}

    client = anthropic.Anthropic(api_key=api_key)

    prompt = """Analyze this GE Vernova earnings call transcript. Count and extract mentions in these categories:

1. CHINA mentions: Any reference to China, Chinese manufacturers, Chinese competition, DEC, Dongfang, Shanghai Electric, Harbin Electric
2. COMPETITION mentions: Any reference to competition, competitive pressure, pricing pressure, market share loss, new entrants
3. CAPACITY mentions: Any reference to capacity constraints, backlog, production limits, ramp-up, manufacturing expansion, lead times
4. PRICING mentions: Any reference to pricing power, price increases, price discipline, margins, cost pressure
5. BACKLOG mentions: Any reference to order backlog, order book, pipeline, reservations, commitments, sold out

Return ONLY a JSON object with this exact structure:
{
  "china_mentions": <int>,
  "competition_mentions": <int>,
  "capacity_mentions": <int>,
  "pricing_mentions": <int>,
  "backlog_mentions": <int>,
  "key_china_snippets": ["quote1", "quote2"],
  "key_competition_snippets": ["quote1", "quote2"],
  "key_capacity_snippets": ["quote1"],
  "key_risk_flags": ["flag1"],
  "overall_tone_on_competition": "one sentence summary"
}

No markdown. No explanation. Just JSON."""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\nQUARTER: {quarter}\n\n--- TRANSCRIPT ---\n{transcript_text[:15000]}\n--- END ---"
                }
            ]
        )

        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]

        result = json.loads(raw.strip())
        result["quarter"] = quarter
        print(f"  [OK] Extracted mentions for {quarter}")
        return result

    except Exception as e:
        print(f"  [ERROR] Transcript extraction failed: {e}")
        return {}


# ---------------------------------------------------------------------------
# SECTION C: CHINA EXPORT MOMENTUM SCORE (0–100)
# ---------------------------------------------------------------------------

def compute_momentum_score(deals: list[dict], transcript_data: list[dict]) -> dict:
    """
    Compute the China Export Momentum Score — a composite indicator (0-100)
    measuring the momentum of Chinese gas turbine exports.

    Sub-components (each 0-100, then weighted):
      1. Deal Flow (30%): Volume and value of deals in trailing 12 months
      2. Incumbent Anxiety (25%): China/competition mention growth in GEV calls
      3. Order Conversion (20%): Ratio of Confirmed+Delivered to total pipeline
      4. Geographic Diversification (15%): Number of distinct buyer countries
      5. Technology Validation (10%): Existence of operational proof points

    Returns dict with composite score and sub-scores.
    """
    print("\n--- Computing China Export Momentum Score ---")

    # ---- Sub-component 1: Deal Flow (30%) ----
    # Count deals in recent period, weight by status
    status_weights = {
        "Delivered": 1.0, "Confirmed": 0.9, "In Progress": 0.7,
        "MOU Signed": 0.5, "Negotiating": 0.3, "Early Stage": 0.15,
        "Mentioned": 0.05
    }
    weighted_deal_count = 0
    total_value_cny = 0
    for deal in deals:
        weight = 0.15
        for status_key, w in status_weights.items():
            if status_key.lower() in str(deal.get("status", "")).lower():
                weight = w
                break
        weighted_deal_count += weight
        total_value_cny += float(deal.get("est_value_cny_m", 0)) * weight

    # Normalize: 0 deals = 0, 10+ weighted deals = 100
    deal_flow_raw = min(weighted_deal_count / 10.0, 1.0) * 100

    # Value factor: 0 = 0, RMB 10B+ = 100
    value_factor = min(total_value_cny / 10000.0, 1.0) * 100

    deal_flow_score = 0.6 * deal_flow_raw + 0.4 * value_factor
    print(f"  1. Deal Flow: {deal_flow_score:.1f}/100 "
          f"(weighted deals: {weighted_deal_count:.1f}, "
          f"weighted value: CNY {total_value_cny:.0f}M)")

    # ---- Sub-component 2: Incumbent Anxiety ----
    # Growth rate of China+competition mentions in GEV calls (first vs second half)
    incumbent_anxiety_score = 0.0
    growth_rate = 0.0
    if len(transcript_data) >= 2:
        early = transcript_data[: len(transcript_data) // 2]
        late = transcript_data[len(transcript_data) // 2 :]

        early_avg = sum(
            int(q.get("china_mentions", 0)) + int(q.get("competition_mentions", 0))
            for q in early
        ) / max(len(early), 1)

        late_avg = sum(
            int(q.get("china_mentions", 0)) + int(q.get("competition_mentions", 0))
            for q in late
        ) / max(len(late), 1)

        if early_avg > 0:
            growth_rate = (late_avg - early_avg) / early_avg
        else:
            growth_rate = 1.0 if late_avg > 0 else 0.0

        # Normalize: 0% growth = 30, 100% growth = 80, 200%+ = 100
        incumbent_anxiety_score = min(30 + growth_rate * 35, 100)
    print(f"  2. Incumbent Anxiety: {incumbent_anxiety_score:.1f}/100 "
          f"(mention growth: {growth_rate:.0%})")

    # ---- Sub-component 3: Order Conversion (20%) ----
    total_deals = len(deals) if deals else 1
    order_conv_rows: list[dict] = []
    for d in deals:
        st = str(d.get("status", ""))
        if _status_counts_toward_order_conversion(st):
            order_conv_rows.append(
                {
                    "deal_id": str(d.get("deal_id", "")).strip(),
                    "status": st.strip(),
                    "buyer_country": str(d.get("buyer_country", "")).strip(),
                }
            )
    confirmed_or_delivered = len(order_conv_rows)
    conversion_rate = confirmed_or_delivered / total_deals
    conversion_score = conversion_rate * 100
    print(
        f"  3. Order Conversion: {conversion_score:.1f}/100 "
        f"({confirmed_or_delivered}/{total_deals} delivered / confirmed / in-progress / contract-signed)"
    )

    # ---- Sub-component 4: Geographic Diversification (15%) ----
    countries = set()
    for deal in deals:
        country = deal.get("buyer_country", "").strip()
        if country:
            countries.add(country)
    # Normalize: 1 country = 20, 3 = 50, 5 = 75, 8+ = 100
    geo_score = min(len(countries) / 8.0, 1.0) * 100
    print(f"  4. Geographic Diversification: {geo_score:.1f}/100 "
          f"({len(countries)} countries: {', '.join(sorted(countries))})")

    # ---- Sub-component 5: Technology Validation (10%) ----
    # Binary factors: has operational units? has developed-market order?
    has_operational = any(
        "delivered" in str(d.get("status", "")).lower() for d in deals
    )
    _developed = {"Canada", "USA", "United States", "Australia", "Japan", "Germany", "UK"}
    has_developed_market = any(str(d.get("buyer_country", "")).strip() in _developed for d in deals)
    tech_score = 0
    if has_operational:
        tech_score += 50
    if has_developed_market:
        tech_score += 50
    print(f"  5. Technology Validation: {tech_score:.1f}/100 "
          f"(operational: {has_operational}, developed market: {has_developed_market})")

    # ---- COMPOSITE SCORE ----
    weights = dict(SCORE_WEIGHTS)
    wsum = sum(weights.values())
    if abs(wsum - 1.0) > 1e-6:
        print(f"  [WARN] SCORE_WEIGHTS sum to {wsum:.4f}, not 1.0 — normalizing.")
        weights = {k: v / wsum for k, v in weights.items()}

    composite = (
        weights["deal_flow"] * deal_flow_score
        + weights["incumbent_anxiety"] * incumbent_anxiety_score
        + weights["geographic_diversification"] * geo_score
        + weights["order_conversion"] * conversion_score
        + weights["technology_validation"] * tech_score
    )

    result = {
        "composite_score": round(composite, 1),
        "sub_scores": {
            "deal_flow": round(deal_flow_score, 1),
            "incumbent_anxiety": round(incumbent_anxiety_score, 1),
            "order_conversion": round(conversion_score, 1),
            "geographic_diversification": round(geo_score, 1),
            "technology_validation": round(tech_score, 1),
        },
        "weights": weights,
        "computed_at": datetime.now().isoformat(),
        "deal_count": len(deals),
        "transcript_quarters": len(transcript_data),
        "order_conversion_rule": (
            "Counts deals whose status matches whole words: Delivered, Confirmed, "
            "In Progress, or Contract Signed (regex word boundaries; e.g. Unconfirmed excluded)."
        ),
        "order_conversion_included": order_conv_rows,
    }

    print(f"\n  ★ CHINA EXPORT MOMENTUM SCORE: {composite:.1f} / 100")
    print(f"    Interpretation: ", end="")
    if composite >= 75:
        print("STRONG MOMENTUM — export inflection underway")
    elif composite >= 50:
        print("MODERATE MOMENTUM — early signs of acceleration")
    elif composite >= 25:
        print("EMERGING — thesis requires more catalysts")
    else:
        print("WEAK — insufficient evidence of export traction")

    return result


# ---------------------------------------------------------------------------
# SECTION D: CHART GENERATION — Slide 6 + appendix + NLP + pipeline + score
# ---------------------------------------------------------------------------

def generate_all_charts(deals: list[dict], transcript_data: list[dict],
                        score_result: dict):
    """Generate all deck charts, including Master Bible filenames (Slide 6, appendix)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
        import numpy as np
    except ImportError:
        print("  [ERROR] matplotlib not installed. Run: pip install matplotlib")
        return

    # Style settings for all charts
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "figure.facecolor": "white",
        "axes.facecolor": "#FAFAFA",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
    })

    COLORS = {
        "primary": "#1A1A2E",
        "accent": "#E94560",
        "green": "#27AE60",
        "blue": "#2980B9",
        "amber": "#F39C12",
        "gray": "#95A5A6",
        "light_blue": "#D6EAF8",
        "light_red": "#FADBD8",
    }

    # ---- SLIDE 6 (Bible): China gas turbine export MW — hockey stick ----
    print("\n  Generating Slide 6: china_gas_turbine_exports_by_quarter.png ...")
    qseries = build_quarterly_export_mw_series(deals)
    if not qseries:
        print("    [WARN] No deal dates/MW — skipping hockey stick chart.")
    else:
        fig, ax1 = plt.subplots(figsize=(12, 6))
        quarters_hs = [r["quarter"] for r in qseries]
        quarterly_mw = [r["mw"] for r in qseries]
        cum_mw = [r["cum_mw"] for r in qseries]
        bar_colors = [
            "#90CAF9" if r["is_pipeline"] else "#1F4E79" for r in qseries
        ]
        x_hs = range(len(quarters_hs))
        ax1.bar(x_hs, quarterly_mw, color=bar_colors, alpha=0.75, width=0.55,
                label="Quarterly MW (tracked deals)")
        ax2 = ax1.twinx()
        ax2.plot(x_hs, cum_mw, color="#E74C3C", linewidth=2.8, marker="o",
                 markersize=7, label="Cumulative MW")
        ax1.set_xticks(x_hs)
        ax1.set_xticklabels(quarters_hs, rotation=45, ha="right")
        ax1.set_ylabel("Quarterly MW", color="#1F4E79", fontweight="bold")
        ax2.set_ylabel("Cumulative MW", color="#E74C3C", fontweight="bold")
        ax1.set_title(
            "China Gas Turbine Export Orders — MW by Quarter (Deal Database)\n"
            "Dark = disclosed / non-E quarter labels; light = pipeline (…E) rows in CSV",
            fontsize=12, fontweight="bold", pad=12,
        )
        if "2026-Q1" in quarters_hs:
            idx_ca = quarters_hs.index("2026-Q1")
            ax2.annotate(
                "Milestone:\nCanada 20×50MW (1,000 MW)\nRMB 4B @ 200M/unit",
                xy=(idx_ca, cum_mw[idx_ca]),
                xytext=(max(0, idx_ca - 1.2), cum_mw[idx_ca] + max(cum_mw) * 0.12),
                fontsize=9, fontweight="bold", color="#E74C3C",
                arrowprops=dict(arrowstyle="->", color="#E74C3C", lw=1.5),
            )
        # Confirmed vs pipeline divider (first pipeline quarter index)
        pipe_idx = next((i for i, r in enumerate(qseries) if r["is_pipeline"]), None)
        if pipe_idx is not None and pipe_idx > 0:
            ax1.axvline(x=pipe_idx - 0.5, color="gray", linestyle="--", alpha=0.55)
            ax1.text(
                (pipe_idx - 1) / 2, max(quarterly_mw or [1]) * 0.92,
                "DISCLOSED / ORDERED", ha="center", fontsize=8, color="#1F4E79", fontweight="bold",
            )
            ax1.text(
                pipe_idx + (len(quarters_hs) - pipe_idx - 1) / 2, max(quarterly_mw or [1]) * 0.92,
                "PIPELINE", ha="center", fontsize=8, color="#5DADE2", fontweight="bold",
            )
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8, framealpha=0.92)
        fig.tight_layout()
        path_hs = CHART_DIR / "china_gas_turbine_exports_by_quarter.png"
        fig.savefig(path_hs, dpi=220, bbox_inches="tight")
        plt.close(fig)
        print(f"    → Saved: {path_hs}")

    # ---- APPENDIX: illustrative market share stack (not customs data) ----
    print("\n  Generating market_share_shift.png (illustrative scenario) ...")
    fig, ax = plt.subplots(figsize=(12, 6))
    years = list(MARKET_SHARE_ILLUSTRATIVE.keys())
    players = ["GE Vernova", "Siemens Energy", "Mitsubishi Power", "Other Western", "Chinese OEMs"]
    colors_ms = ["#1F4E79", "#2980B9", "#7FB3D8", "#BDC3C7", "#E74C3C"]
    bottom = [0.0] * len(years)
    for player, color in zip(players, colors_ms):
        values = [MARKET_SHARE_ILLUSTRATIVE[y][player] for y in years]
        ax.bar(years, values, bottom=bottom, color=color, label=player, width=0.65)
        if player == "Chinese OEMs":
            for j, (y, v) in enumerate(zip(years, values)):
                if v >= 4:
                    ax.text(j, bottom[j] + v / 2, f"{v}%", ha="center", va="center",
                            fontsize=8, fontweight="bold", color="white")
        bottom = [b + float(v) for b, v in zip(bottom, values)]
    ax.set_ylabel("Market share (%)", fontweight="bold")
    ax.set_title(
        "Global Gas Turbine Market Share — Illustrative Scenario\n"
        "NOT UN Comtrade / customs-derived; team scenario for narrative framing (see methodology)",
        fontsize=11, fontweight="bold", pad=10,
    )
    ax.legend(loc="upper right", fontsize=8, framealpha=0.92)
    ax.set_ylim(0, 105)
    fig.tight_layout()
    path_ms = CHART_DIR / "market_share_shift.png"
    fig.savefig(path_ms, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"    → Saved: {path_ms}")

    # ---- CHART 1: GEV Competition & China Mentions (stacked bar) ----
    print("\n  Generating Chart 1: GEV Competition Mentions...")
    fig, ax1 = plt.subplots(figsize=(10, 5.5))

    quarters = [q["quarter"] for q in transcript_data]
    china = [int(q.get("china_mentions", 0)) for q in transcript_data]
    comp = [int(q.get("competition_mentions", 0)) for q in transcript_data]
    backlog = [int(q.get("backlog_mentions", 0)) for q in transcript_data]

    x = range(len(quarters))
    bar_w = 0.5
    bars1 = ax1.bar(x, china, bar_w, label="China Mentions",
                    color=COLORS["accent"], alpha=0.85)
    bars2 = ax1.bar(x, comp, bar_w, bottom=china, label="Competition Mentions",
                    color=COLORS["amber"], alpha=0.85)
    ax1.set_xlabel("Quarter")
    ax1.set_ylabel("Mention Count", color=COLORS["primary"])
    ax1.set_xticks(x)
    ax1.set_xticklabels(quarters, rotation=45, ha="right")
    ax1.set_title("GEV Earnings Calls: China & Competition Mentions\n"
                   "Counts from real transcript aggregates (see methodology doc)",
                   pad=12)

    # Secondary axis: backlog/(china+comp) ratio
    ax2 = ax1.twinx()
    ratios = []
    for i in range(len(quarters)):
        denom = china[i] + comp[i]
        ratios.append(backlog[i] / denom if denom > 0 else 0)
    ax2.plot(x, ratios, "s--", color=COLORS["blue"], linewidth=2,
             markersize=6, label="Backlog / (China+Comp) Ratio")
    ax2.set_ylabel("Backlog Ratio", color=COLORS["blue"])
    ax2.tick_params(axis="y", labelcolor=COLORS["blue"])

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left",
               fontsize=8, framealpha=0.9)

    fig.tight_layout()
    path1 = CHART_DIR / "chart1_gev_competition_mentions.png"
    fig.savefig(path1, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"    → Saved: {path1}")
    shutil.copy2(path1, CHART_DIR / "gev_competition_mentions.png")
    print(f"    → Alias:  {CHART_DIR / 'gev_competition_mentions.png'}")

    # ---- CHART 2: GEV Keyword Trends (multi-line) ----
    print("  Generating Chart 2: GEV Keyword Trends...")
    fig, ax = plt.subplots(figsize=(10, 5.5))

    dimensions = [
        ("china_mentions", "China", COLORS["accent"], "o"),
        ("competition_mentions", "Competition", COLORS["amber"], "s"),
        ("capacity_mentions", "Capacity", COLORS["blue"], "^"),
        ("pricing_mentions", "Pricing", COLORS["green"], "D"),
        ("backlog_mentions", "Backlog", COLORS["gray"], "v"),
    ]
    for key, label, color, marker in dimensions:
        vals = [int(q.get(key, 0)) for q in transcript_data]
        ax.plot(quarters, vals, marker=marker, label=label, color=color,
                linewidth=2, markersize=6)

    ax.set_xlabel("Quarter")
    ax.set_ylabel("Mention Count")
    ax.set_title("GEV Earnings Calls: All Keyword Dimensions Over Time\n"
                  "Real counts from Claude-structured transcripts (aggregate CSV)",
                  pad=12)
    ax.legend(fontsize=9, framealpha=0.9)
    plt.xticks(rotation=45, ha="right")

    fig.tight_layout()
    path2 = CHART_DIR / "chart2_gev_keyword_trends.png"
    fig.savefig(path2, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"    → Saved: {path2}")

    # ---- CHART 3: Deal Pipeline Waterfall ----
    print("  Generating Chart 3: Deal Pipeline Waterfall...")
    fig, ax = plt.subplots(figsize=(10, 6))

    # Group deals by status (include labels present in team CSV + extractions)
    status_order = [
        "Delivered",
        "Confirmed",
        "In Progress",
        "Contract Signed",
        "MOU Signed",
        "Negotiating",
        "Early Stage",
        "Exploratory",
        "Mentioned",
    ]
    status_colors = {
        "Delivered": COLORS["green"],
        "Confirmed": "#2ECC71",
        "In Progress": COLORS["blue"],
        "Contract Signed": "#5DADE2",
        "MOU Signed": COLORS["amber"],
        "Negotiating": "#E67E22",
        "Early Stage": COLORS["gray"],
        "Exploratory": "#BDC3C7",
        "Mentioned": "#D7BDE2",
    }

    status_groups = {}
    for deal in deals:
        raw_status = deal.get("status", "Unknown")
        # Map to canonical status
        matched = "Early Stage"
        for s in status_order:
            if s.lower() in raw_status.lower():
                matched = s
                break
        if matched not in status_groups:
            status_groups[matched] = {"units": 0, "value_cny_m": 0, "deals": []}
        status_groups[matched]["units"] += int(deal.get("units", 0))
        status_groups[matched]["value_cny_m"] += float(deal.get("est_value_cny_m", 0))
        status_groups[matched]["deals"].append(deal)

    # Build horizontal bars
    y_labels = []
    y_values = []
    bar_colors = []
    unit_counts = []

    for status in status_order:
        if status in status_groups:
            y_labels.append(status)
            y_values.append(status_groups[status]["value_cny_m"])
            bar_colors.append(status_colors.get(status, COLORS["gray"]))
            unit_counts.append(status_groups[status]["units"])

    y_pos = range(len(y_labels))
    bars = ax.barh(y_pos, y_values, color=bar_colors, alpha=0.85, height=0.6)

    # Add value labels
    for i, (bar, val, units) in enumerate(zip(bars, y_values, unit_counts)):
        if val > 0:
            ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2,
                    f"CNY {val:,.0f}M  ({units} units)",
                    va="center", fontsize=9, color=COLORS["primary"])

    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("Contract Value (CNY Millions)")
    ax.invert_yaxis()

    # Annotation line: higher-certainty statuses (includes Contract Signed from team CSV)
    confirmed_val = sum(
        status_groups.get(s, {}).get("value_cny_m", 0)
        for s in ["Delivered", "Confirmed", "In Progress", "Contract Signed"]
    )
    ax.axvline(x=confirmed_val, color=COLORS["accent"], linestyle="--",
               alpha=0.7, linewidth=1.5)

    ax.set_title(
        "China Gas Turbine Export Pipeline by Status\n"
        f"Delivered + confirmed + in-progress + contract-signed ≈ CNY {confirmed_val:,.0f}M "
        f"(USD×{USD_TO_CNY_FOR_CHARTS} where CNY missing)",
        pad=12,
    )

    fig.tight_layout()
    path3 = CHART_DIR / "chart3_deal_pipeline_waterfall.png"
    fig.savefig(path3, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"    → Saved: {path3}")

    # ---- CHART 4: China Export Momentum Score ----
    print("  Generating Chart 4: China Export Momentum Score...")
    fig, (ax_gauge, ax_breakdown) = plt.subplots(1, 2, figsize=(12, 5),
                                                  gridspec_kw={"width_ratios": [1, 1.3]})

    # Left panel: Gauge-style score display
    composite = score_result["composite_score"]
    ax_gauge.set_xlim(-1.5, 1.5)
    ax_gauge.set_ylim(-0.2, 1.5)
    ax_gauge.set_aspect("equal")
    ax_gauge.axis("off")

    # Draw arc background
    theta = np.linspace(np.pi, 0, 100)
    ax_gauge.plot(np.cos(theta), np.sin(theta), color="#E0E0E0", linewidth=20,
                  solid_capstyle="round")

    # Draw filled arc
    fill_frac = composite / 100.0
    theta_fill = np.linspace(np.pi, np.pi - fill_frac * np.pi, 100)
    color = COLORS["green"] if composite >= 60 else (
        COLORS["amber"] if composite >= 40 else COLORS["accent"])
    ax_gauge.plot(np.cos(theta_fill), np.sin(theta_fill), color=color,
                  linewidth=20, solid_capstyle="round")

    # Score text
    ax_gauge.text(0, 0.35, f"{composite:.0f}", fontsize=48, fontweight="bold",
                  ha="center", va="center", color=COLORS["primary"])
    ax_gauge.text(0, 0.05, "/ 100", fontsize=16, ha="center", va="center",
                  color=COLORS["gray"])
    ax_gauge.text(0, -0.15, "CHINA EXPORT\nMOMENTUM SCORE", fontsize=10,
                  ha="center", va="center", color=COLORS["primary"],
                  fontweight="bold")

    # Right panel: Sub-score breakdown (horizontal bars)
    sub = score_result["sub_scores"]
    weights = score_result["weights"]
    components = [
        ("Deal Flow", sub["deal_flow"], weights["deal_flow"]),
        ("Incumbent Anxiety", sub["incumbent_anxiety"], weights["incumbent_anxiety"]),
        ("Order Conversion", sub["order_conversion"], weights["order_conversion"]),
        ("Geo Diversification", sub["geographic_diversification"],
         weights["geographic_diversification"]),
        ("Tech Validation", sub["technology_validation"],
         weights["technology_validation"]),
    ]

    comp_labels = [c[0] for c in components]
    comp_scores = [c[1] for c in components]
    comp_weights = [c[2] for c in components]

    y_pos = range(len(comp_labels))
    bar_colors = [COLORS["green"] if s >= 60 else
                  COLORS["amber"] if s >= 40 else COLORS["accent"]
                  for s in comp_scores]

    bars = ax_breakdown.barh(y_pos, comp_scores, color=bar_colors, alpha=0.8,
                             height=0.6)

    for i, (bar, score, weight) in enumerate(zip(bars, comp_scores, comp_weights)):
        ax_breakdown.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height()/2,
                         f"{score:.0f}/100  (wt: {weight:.0%})",
                         va="center", fontsize=9, color=COLORS["primary"])

    ax_breakdown.set_yticks(y_pos)
    ax_breakdown.set_yticklabels(comp_labels)
    ax_breakdown.set_xlim(0, 120)
    ax_breakdown.set_xlabel("Sub-Score (0-100)")
    ax_breakdown.set_title("Score Decomposition", fontweight="bold")
    ax_breakdown.invert_yaxis()
    ax_breakdown.axvline(x=50, color=COLORS["gray"], linestyle="--", alpha=0.3)

    fig.suptitle("China Gas Turbine Export Momentum — Composite Indicator",
                 fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    path4 = CHART_DIR / "chart4_momentum_score.png"
    fig.savefig(path4, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"    → Saved: {path4}")
    shutil.copy2(path4, CHART_DIR / "export_momentum_score.png")
    print(f"    → Alias:  {CHART_DIR / 'export_momentum_score.png'}")

    manifest = {
        "generated_at": datetime.now().isoformat(),
        "chart_dir": str(CHART_DIR),
        "files": sorted(p.name for p in CHART_DIR.glob("*.png")),
    }
    with open(OUTPUT_DIR / "chart_manifest.json", "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, indent=2)
    print(f"    → Manifest: {OUTPUT_DIR / 'chart_manifest.json'}")

    print(f"\n  ✓ All charts saved to {CHART_DIR}/")
    print("    Bible names: china_gas_turbine_exports_by_quarter.png, market_share_shift.png,")
    print("                 gev_competition_mentions.png, export_momentum_score.png")
    print("    Plus: chart1–chart4_*.png")


# ---------------------------------------------------------------------------
# MAIN — CLI ENTRYPOINT
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="AI Trade Flow Analyzer — Cross-Border Power Equipment Intelligence"
    )
    parser.add_argument("--full", action="store_true",
                        help="Run full pipeline (API + charts)")
    parser.add_argument("--charts-only", action="store_true",
                        help="Generate charts from existing data (no API needed)")
    parser.add_argument("--extract-news", action="store_true",
                        help="Extract deals from Chinese news files (needs API key)")
    parser.add_argument("--extract-transcript", type=str, default=None,
                        help="Extract mentions from a transcript file (needs API key)")
    parser.add_argument("--score-only", action="store_true",
                        help="Compute momentum score from existing data")
    parser.add_argument(
        "--include-extractions-in-score",
        action="store_true",
        help="After news extraction, merge NLP rows into deals used for score/charts "
        "(default: curated CSV only; raw merge is still saved to api_extraction_raw_output.csv)",
    )
    args = parser.parse_args()

    # Default to --charts-only if no flags
    if not any([args.full, args.charts_only, args.extract_news,
                args.extract_transcript, args.score_only]):
        args.charts_only = True

    print("=" * 65)
    print("  AI TRADE FLOW ANALYZER")
    print("  Cross-Border Power Equipment Intelligence")
    print("  UBS Finance Challenge 2026")
    print("=" * 65)

    # Step 1: Load deal database (canonical ground truth for score/charts by default)
    print("\n[STEP 1] Loading deal database...")
    deals_curated = load_deal_database()
    deals_for_score = list(deals_curated)

    # Step 2: Extract from news (if requested) — saves merged artifact; does not
    # inflate the headline score unless --include-extractions-in-score.
    if args.full or args.extract_news:
        print("\n[STEP 2] Extracting deals from Chinese news...")
        new_deals = process_all_news_files()
        if new_deals:
            base_len = len(deals_curated)
            normalized_new = [
                _normalize_loaded_deal(nd, base_len + i)
                for i, nd in enumerate(new_deals)
            ]
            merged = list(deals_curated) + normalized_new
            output_path = OUTPUT_DIR / "api_extraction_raw_output.csv"
            save_deals_to_csv(merged, output_path)
            print(
                "  [NOTE] Score & charts use curated deals only (see data/deals/export_deal_database.csv)."
            )
            print(
                "         Raw NLP + curated merge is in api_extraction_raw_output.csv (appendix / QC)."
            )
            if args.include_extractions_in_score:
                deals_for_score = merged
                print(
                    "  [WARN] --include-extractions-in-score: composite may double-count vs Excel SOTP."
                )
    else:
        print("\n[STEP 2] Skipping news extraction (use --extract-news)")

    # Step 3: Extract from transcript (if requested)
    if args.extract_transcript:
        print(f"\n[STEP 3] Extracting from transcript: {args.extract_transcript}")
        tpath = Path(args.extract_transcript)
        if tpath.exists():
            text = tpath.read_text(encoding="utf-8")
            quarter = tpath.stem.replace("GEV_", "").replace(".txt", "")
            result = extract_transcript_mentions(text, quarter)
            if result:
                out = OUTPUT_DIR / f"{tpath.stem}.extracted.json"
                with open(out, "w") as f:
                    json.dump(result, f, indent=2)
                print(f"  [OK] Saved to {out}")
        else:
            print(f"  [ERROR] File not found: {tpath}")
    else:
        print("\n[STEP 3] Skipping transcript extraction (use --extract-transcript)")

    # Step 4: Load transcript data
    print("\n[STEP 4] Loading transcript data...")
    transcript_data = load_transcript_data()

    # Step 5: Compute momentum score
    print("\n[STEP 5] Computing China Export Momentum Score...")
    score_result = compute_momentum_score(deals_for_score, transcript_data)

    # Save score
    score_path = OUTPUT_DIR / "momentum_score.json"
    with open(score_path, "w") as f:
        json.dump(score_result, f, indent=2)
    print(f"  [OK] Score saved to {score_path}")

    # Step 6: Generate charts
    if args.full or args.charts_only:
        print("\n[STEP 6] Generating charts...")
        generate_all_charts(deals_for_score, transcript_data, score_result)
    else:
        print("\n[STEP 6] Skipping charts (use --charts-only)")

    # Summary
    print("\n" + "=" * 65)
    print("  PIPELINE COMPLETE")
    print(f"  Deals in score/charts: {len(deals_for_score)}")
    print(f"  Transcript quarters:  {len(transcript_data)}")
    print(f"  Momentum Score:       {score_result['composite_score']:.1f} / 100")
    print(f"  Charts generated in:  {CHART_DIR}/")
    print("=" * 65)


if __name__ == "__main__":
    main()