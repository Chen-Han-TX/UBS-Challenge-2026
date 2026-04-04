# Optional appendix outputs

- **Raw NLP merge (after `--full` / `--extract-news`):** `../api_extraction_raw_output.csv` — curated rows plus machine-extracted rows; **human dedup required** before any model use.
- **Canonical ground truth** for scoring and charts is always **`../../data/deals/export_deal_database.csv`** (relative to this folder; i.e. `AI Analyst/data/deals/…`).

Do **not** resurrect **`export_deal_database_updated.csv`** — that name is retired to avoid confusion with the 8-row canonical database.
