# AI Analyst Workspace — Unified Pipeline

Everything for the **AI Analyst** workstream: Claude extraction, Chinese news processing, GEV transcript aggregates, **Slide 6 hockey stick + market share + four analytic charts**, and the **China Export Momentum Score**.

## Canonical layout

| Path | Role |
|------|------|
| **`ai_trade_flow_analyzer.py`** | Main entrypoint (charts, score, optional API extraction). |
| **`data/transcripts/gev_mentions_by_quarter.csv`** | Real GEV mention aggregates (copy from `week_1/outputs/` after aggregation). |
| **`data/deals/export_deal_database.csv`** | Deal database (keep aligned with `Existing/export_deal_database.csv` if you edit either). |
| **`data/news/raw/*.txt`** | Chinese news text files for `--extract-news`. |
| **`outputs/`** | Charts (incl. **Master Bible** names: `china_gas_turbine_exports_by_quarter.png`, `market_share_shift.png`, `gev_competition_mentions.png`, `export_momentum_score.png`), `chart_manifest.json`, `momentum_score.json`, and after `--full` / `--extract-news`: **`api_extraction_raw_output.csv`** (curated + NLP merge for appendix — not used for the headline score unless `--include-extractions-in-score`). |
| **`submission_appendix_ai_module/`** | What to bundle for judges — see `README.md` there. |
| **`week_1/`** | Upstream workspace: raw transcripts, per-call JSON, extract/aggregate scripts, `docs/news_source_log.md`. |
| **`docs/AI_MODULE_METHODOLOGY.md`** | Slide 18 text, advantages/limitations, Siemens scope, Q5 template. |
| **`docs/AI_MODULE_SUBMISSION_SUMMARY.md`** | **Handoff:** current pipeline behavior, headline numbers, what to cite vs appendix. |
| **`docs/QA_AI_MODULE.md`** | Short judge Q&A (Canada vs Excel, market share, score from **`momentum_score.json`**). |
| **`.env`** (you create) | `ANTHROPIC_API_KEY=...` — loaded automatically; **never commit** (gitignored). See **`.env.example`**. |
| **`env_bootstrap.py`** | Loads `.env` before API calls. |

## API key (Claude / Anthropic)

1. Copy **`AI Analyst/.env.example`** → **`AI Analyst/.env`**
2. Put one line: `ANTHROPIC_API_KEY=sk-ant-api03-...`
3. Run scripts as usual — no `export` needed. If the variable is already set in your shell, that **wins** over `.env`.

Install once: `pip install -r requirements.txt` (includes `python-dotenv`).

## Quick commands

From the **`AI Analyst`** directory:

```bash
# Install dependencies (use your team venv if you have one)
python3 -m pip install -r requirements.txt

# Regenerate all charts (Slide 6 + market share + GEV + pipeline + score) — NO API key
python3 ai_trade_flow_analyzer.py --charts-only

# Optional: refresh data/ from week_1 outputs + news
./scripts/sync_inputs_from_week1.sh

# Extract deals from Chinese news (requires API key in .env or env; review output)
python3 ai_trade_flow_analyzer.py --extract-news
```

## Week 1 — regenerating the transcript CSV

```bash
python3 week_1/scripts/aggregate_gev_extracts.py
cp week_1/outputs/gev_mentions_by_quarter.csv data/transcripts/gev_mentions_by_quarter.csv
```

## Score weights

Edit **`SCORE_WEIGHTS`** near the top of `ai_trade_flow_analyzer.py` if you apply a documented adjustment (see methodology doc). Weights must sum to **1.0**.

## Legacy

- **`Existing/ai_trade_flow_analyzer.py`** — early prototype with simulated GEV series; submission should cite **`AI Analyst/ai_trade_flow_analyzer.py`** + real `data/` inputs.
- **`week_2/scripts/build_real_week2_outputs.py`** — optional; superseded by the main module’s `--charts-only`.
