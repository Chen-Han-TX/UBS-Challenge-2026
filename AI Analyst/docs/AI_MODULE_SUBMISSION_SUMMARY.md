# AI Module — Submission summary (current state)

UBS Finance Challenge 2026 | Long DEC (1072.HK) / Short GEV | **Last verified:** regenerate `momentum_score.json` with `python3 ai_trade_flow_analyzer.py --charts-only` before locking the deck.

This document is the **single handoff** for teammates and judges’ appendix context. Detailed methodology lives in **`AI_MODULE_METHODOLOGY.md`**; rehearsed Q&A in **`QA_AI_MODULE.md`**.

---

## 1. What the pipeline does

| Piece | Role |
|--------|------|
| **`data/deals/export_deal_database.csv`** | **Canonical ground truth** — **8** curated export / pipeline deals (aligned with Excel SOTP where applicable). |
| **`data/transcripts/gev_mentions_by_quarter.csv`** | **8 quarters** of aggregated GEV transcript mention counts (China, competition, capacity, pricing, backlog). |
| **`ai_trade_flow_analyzer.py`** | Loads the above, computes the **China Export Momentum Score**, writes **`outputs/momentum_score.json`**, generates **deck charts** under **`outputs/charts/`**. |
| **Chinese news (`data/news/raw/*.txt`)** | Optional **Claude** extraction — demonstrates NLP capability; **not** auto-promoted into the headline score. |

---

## 2. Commands (what to run when)

| Command | When |
|---------|------|
| **`python3 ai_trade_flow_analyzer.py --charts-only`** | **Default for submission freeze.** No API key. Refreshes **all charts**, **`momentum_score.json`**, **`chart_manifest.json`** from the **8-row** deal CSV + transcript CSV. |
| **`python3 ai_trade_flow_analyzer.py --full`** | Runs news extraction (needs **`ANTHROPIC_API_KEY`**), writes **`outputs/api_extraction_raw_output.csv`**, **still** scores/charts from **curated deals only** unless you opt in (see below). |
| **`python3 ai_trade_flow_analyzer.py --extract-news`** | Same extraction + raw merge file as `--full`, without implying “full pipeline” semantics beyond that. |
| **`--include-extractions-in-score`** | **Sandbox only.** Merges NLP rows into the deal list used for score/charts — can **double-count** the same economics as the curated DB; **do not** use for the main deck narrative. |

---

## 3. Headline numbers to cite (after `--charts-only`)

Always read **`AI Analyst/outputs/momentum_score.json`** after your last run — that file is the **source of truth** for Slide 18.

**Example from a clean run on the current curated inputs:**

| Field | Value |
|--------|--------|
| **Composite** | **66.5 / 100** (“moderate momentum”) |
| Deal flow | 49.7 |
| Incumbent anxiety | 56.2 |
| Order conversion | 62.5 |
| Geographic diversification | 100.0 |
| Technology validation | 100 |
| **Deals in score** | **8** |
| **Transcript quarters** | **8** |

**Deck / Excel alignment**

- **Do not** cite old placeholder scores (**~71**, **68.7**) or any **merged-NLP** composite (historically **~85.7** when extractions were wrongly folded into scoring).
- **Canada row** in the deal CSV uses **RMB 200M/unit × 20 = RMB 4.0B** equipment value; **`est_value_usd_m`** is consistent with **RMB ÷ 7.2** for chart scaling — match **Sheet / SOTP**, not a higher per-unit tier.

---

## 4. What was fixed (why `--full` no longer poisons the score)

**Problem:** Earlier, **`--full`** appended API-extracted rows to the **same** list used for **`compute_momentum_score`** and **`generate_all_charts`**. Multiple Chinese articles described **deals already in the curated table**, so the same orders were **counted twice**, and loose NLP **status** fields inflated **order conversion**. That produced a **misleadingly high** composite (e.g. **~85.7**).

**Fix (current behavior):**

1. **`deals_curated`** = load **`export_deal_database.csv`** only.
2. **`deals_for_score`** = copy of curated list **by default**.
3. After extraction, **`api_extraction_raw_output.csv`** = **curated + normalized NLP rows** (appendix / human QC).
4. Score and charts use **`deals_for_score`** = curated **unless** **`--include-extractions-in-score`** is passed.

**`deal_id` for NLP rows:** `EXT_{news_file_stem}_{index:03d}_{YYYYMMDD}` so IDs do **not** collide across files (previously many rows shared the same `EXT_YYYYMMDD_001`-style id).

---

## 5. Artifacts: what goes in the deck vs appendix

| Artifact | Deck / main model | Appendix / narrative |
|----------|-------------------|----------------------|
| **`momentum_score.json`** (from **`--charts-only`**) | **Yes** — cite composite + interpretation | Optional JSON |
| **`outputs/charts/*.png`** (same run as JSON) | **Yes** — Slide 6, GEV charts, gauge | Duplicates OK |
| **`api_extraction_raw_output.csv`** | **No** for headline metrics | **Yes** — “raw NLP + curated merge; requires **dedup** and **human validation** before model integration” |
| **`export_deal_database.csv`** | Ground truth input | Yes |

**Limitations paragraph (deduplication):** Documented under **Limitations** in **`AI_MODULE_METHODOLOGY.md`** — raw NLP can duplicate curated deals; production workflow dedupes against the curated database.

---

## 6. Pre-submission checklist

1. Run **`cd "AI Analyst" && python3 ai_trade_flow_analyzer.py --charts-only`**.
2. Open **`outputs/momentum_score.json`** — use **`composite_score`** on Slide 18 (and align Excel **AI Module** tab if present).
3. Confirm **`outputs/chart_manifest.json`** **`generated_at`** matches the chart freeze you intend.
4. If you ran **`--full`**, include **`api_extraction_raw_output.csv`** only as **raw pipeline output**, not as the score basis.
5. Purge deck references to **85.7**, **71**, stale **68.7** if they no longer match the JSON.

---

## 7. File map (quick)

```
AI Analyst/
  ai_trade_flow_analyzer.py
  data/deals/export_deal_database.csv      # canonical 8 deals — do not inflate via NLP for headline score
  data/transcripts/gev_mentions_by_quarter.csv
  data/news/raw/*.txt                      # optional Claude input
  outputs/momentum_score.json              # cite this after --charts-only
  outputs/chart_manifest.json
  outputs/charts/                          # Bible names + chart1–4
  outputs/api_extraction_raw_output.csv    # only after --full / --extract-news
  docs/AI_MODULE_METHODOLOGY.md
  docs/QA_AI_MODULE.md
  submission_appendix_ai_module/README.md
```

---

## 8. Sanity checks performed

- **`python3 -m py_compile ai_trade_flow_analyzer.py`** — passes.
- **`--charts-only`** — loads **8** deals, **8** transcript quarters, writes **66.5** composite and regenerates charts + manifest.

If any of these diverge after you edit the CSV or transcript aggregate, **re-run `--charts-only`** and update the deck from the new JSON.
