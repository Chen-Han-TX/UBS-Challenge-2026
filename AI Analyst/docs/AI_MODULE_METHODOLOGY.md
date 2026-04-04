# AI Module — Methodology & Presentation Notes

UBS Finance Challenge 2026 | AI Analyst | `ai_trade_flow_analyzer.py`

## Data layout (canonical)

All inputs for the main pipeline live under **`AI Analyst/data/`** (not scattered across week folders):

| Path | Contents |
|------|----------|
| `data/transcripts/gev_mentions_by_quarter.csv` | Real aggregates from Week 1 (`aggregate_gev_extracts.py`); re-copy after re-running extraction. |
| `data/deals/export_deal_database.csv` | Team deal table (same schema as `Existing/export_deal_database.csv`). |
| `data/news/raw/*.txt` | Chinese news captures (URL line optional; used by `--extract-news`). |

Outputs: **`AI Analyst/outputs/`** — charts, `momentum_score.json`, `chart_manifest.json`, and `export_deal_database_updated.csv` after news extraction.

## Chart outputs (Master Bible alignment)

| File | Role |
|------|------|
| `china_gas_turbine_exports_by_quarter.png` | **Slide 6** — quarterly + cumulative **MW** from **`export_deal_database.csv`**. Dark bars = quarter labels not ending in `E`; light bars = pipeline rows (`…E`). |
| `market_share_shift.png` | **Illustrative** global share stack (2020–2027E). **Not** customs data — labeled on-chart. Use for narrative context or replace with licensed data. |
| `gev_competition_mentions.png` | Alias of chart1 — GEV transcript mention aggregates. |
| `export_momentum_score.png` | Alias of chart4 — composite momentum score gauge + breakdown. |
| `chart1`–`chart4` | Same content with step-by-step filenames for internal review. |

## Advantages (Slide 18 — required)

- **Structured primary extraction:** Eight GEV earnings calls processed through a **fixed rubric** (China, competition, capacity, pricing, backlog) with JSON outputs suitable for audit.
- **Reproducible pipeline:** `python ai_trade_flow_analyzer.py --charts-only` regenerates **all** charts and the composite score from the same CSV inputs.
- **Cross-language coverage:** Chinese news `.txt` files can be processed with `--extract-news` (Claude) to suggest additional deal rows — with mandatory human review.
- **Deck integration:** Slide 6 hockey stick is **generated from the team deal database**, not hand-drawn.
- **Transparency:** USD-only deal values are converted to **CNY for display** using a documented FX proxy (**7.2**) for chart scaling only.

## Limitations (Slide 18 — required; be explicit)

- **Mention counts are estimates:** They depend on transcript wording and model extraction; they are **not** a substitute for a sell-side “keyword index.”
- **China + competition mentions are volatile** quarter-to-quarter; the **momentum score** uses **first-half vs second-half growth** for “incumbent anxiety,” which can diverge from a simple visual trend.
- **Backlog / (China+Comp) ratio** can **spike mechanically** when the denominator is near zero — interpret alongside **raw counts**.
- **Deal database** mixes **confirmed/disclosed** rows with **pipeline / exploratory** rows; judges should read **status** and **source** columns.
- **`market_share_shift.png`** is an **illustrative scenario**, not an official market-share survey — do **not** cite it as Comtrade or OEM-reported statistics unless replaced.
- **`--extract-news`** can **hallucinate** deal fields; **never** promote API rows to the model without verification.
- **Siemens Energy** transcripts are **not** in the automated NLP path (see below).

## Siemens Energy scope (explicit deprioritization)

**GEV is the primary monitoring target** because Dongfang’s G50 competes directly in the **F-class / ~50MW-class distributed generation segment** where GE Vernova is dominant and disclosure is rich (SEC transcripts).

**Siemens Energy** is **not processed in this submission pipeline** for time and segment-focus reasons: its public gas-turbine commentary is often **H-class / large-frame weighted**, which is a different competitive pocket than the core DEC vs GEV thesis. A fair statement for judges:

> *“GEV was prioritized as the primary monitoring target because DEC’s G50 competes directly in the F-class segment where GEV is dominant. Siemens Energy’s gas turbine business (often H-class / large-frame focused) remains architecturally queued for extension but was deprioritized given competition time constraints.”*

## Momentum score — how to present

The composite score is **data-driven** from (1) the deal CSV and (2) real GEV transcript mention trends. It will **not** match placeholder/sample runs once real CSVs are wired in.

**Example framing (adapt numbers to your latest `momentum_score.json`):**

> *“Our proprietary China Export Momentum Score is **[X] / 100**, in the **moderate momentum** band. The **incumbent anxiety** component reflects that GEV’s own calls show material variation in **China + competition** mentions across quarters when we parse transcripts with a fixed rubric. The **order conversion** component is intentionally conservative: several pipeline rows are early-stage or exploratory — which is consistent with a market that has **not fully priced** follow-on export orders.”*

## Q5-style answer (honest template)

> *“We built a Python pipeline (`ai_trade_flow_analyzer.py`) that reads our **aggregated GEV transcript CSV** (eight quarters, Claude-structured extracts) and our **export deal CSV**. Running `python ai_trade_flow_analyzer.py --charts-only` regenerates **Slide 6** (`china_gas_turbine_exports_by_quarter.png`) from **deal MW**, plus GEV mention charts and a **composite momentum score** stored in `momentum_score.json`. We do **not** claim monotonic quarter-by-quarter growth in China mentions — the data show an **episodic** pattern (e.g. elevated China-related counts in some 2025 calls). Appendix includes **code, inputs, one sample JSON extract, and this methodology.**”*

## Weight tuning (optional, must stay intellectually honest)

Sub-score weights are defined in **`SCORE_WEIGHTS`** at the top of `ai_trade_flow_analyzer.py` (default sums to 1.0).

If **incumbent anxiety** is noisy (flat or choppy real mention series), a defensible adjustment is to **shift ~5 percentage points** from `incumbent_anxiety` → `deal_flow`, **only if** the team documents the rationale in this file and keeps the math consistent (weights must still sum to 1.0).

## `--extract-news` limitations

Claude extraction from Chinese text can **hallucinate** units, countries, or values when the article is vague. **Human review is mandatory** before promoting any extracted row to the main deck or Excel model.

## Week 1 / Week 2 relationship

- **Week 1** folders remain the **upstream workspace** (raw transcripts, per-call JSON, `aggregate_gev_extracts.py`, `news_source_log.md`).
- **`data/`** is the **frozen input bundle** the submission script reads. After you regenerate Week 1 outputs, refresh the copies:

```bash
cp "AI Analyst/week_1/outputs/gev_mentions_by_quarter.csv" \
   "AI Analyst/data/transcripts/gev_mentions_by_quarter.csv"
cp "AI Analyst/week_1/data/news/raw/"dec_news_*.txt \
   "AI Analyst/data/news/raw/"
```

(Deal CSV: edit `Existing/export_deal_database.csv` or `data/deals/export_deal_database.csv` and keep them in sync if you maintain both.)
