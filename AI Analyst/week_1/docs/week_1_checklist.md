# AI Analyst — Week 1 Checklist (Mar 17–23)

This is a step-by-step execution checklist aligned to `NEXT_STEPS_EXECUTION_PLAN.md` (Priority 2) and the AI-module requirements in the submission bible.

## Step 0 — Environment (done once)

- [ ] Activate venv: `source .venv/bin/activate`
- [ ] Confirm `anthropic` works: `python -c "import anthropic; print(anthropic.__version__)"`
- [ ] Set key: `export ANTHROPIC_API_KEY="..."`

## Step 1 — Get Anthropic API key (Plan line 46)

- [ ] Create key at: `https://console.anthropic.com`
- [ ] Store it as `ANTHROPIC_API_KEY` (env var). Do **not** commit keys into files.

## Step 2 — Collect 8 GEV transcripts (Plan line 47–49)

Target set:
- Q1 2024
- Q2 2024
- Q3 2024
- Q4 2024
- Q1 2025
- Q2 2025
- Q3 2025
- Q4 2025

Where to get them:
- SeekingAlpha (often easiest, account needed)
- SEC EDGAR 8-K filings / investor relations attachments (sometimes contain prepared remarks / transcripts)

Storage rules:
- Save raw text files into `week_1/data/transcripts/raw/`
- File naming convention:
  - `GEV_Q1_2024.txt`, `GEV_Q2_2024.txt`, ... `GEV_Q4_2025.txt`

## Step 3 — Test Claude API on ONE transcript (Plan line 50)

- [ ] Start with **one** transcript (e.g. `GEV_Q4_2025.txt`)
- [ ] Run extractor:

```bash
source .venv/bin/activate
python "AI Analyst/week_1/scripts/extract_gev_transcript.py" \
  --input "AI Analyst/week_1/data/transcripts/raw/GEV_Q4_2025.txt" \
  --output "AI Analyst/week_1/data/transcripts/processed/GEV_Q4_2025.extracted.json"
```

- [ ] Open the produced JSON and sanity-check:
  - Mentions have short snippets that are verbatim from the transcript
  - Missing info is `null` (not invented)

## Step 4 — Batch all 8 transcripts (Week 2 requirement preview)

Once Step 3 looks good:
- [ ] Run the extractor for all 8 files and keep JSON outputs in `week_1/data/transcripts/processed/`
- [ ] Create a simple summary table (counts + top snippets) for your deck appendix

## Step 5 — Chinese-language news scraping setup (Plan line 51)

Targets:
- Futunn (news.futunn.com)
- Eastmoney
- Sina Finance

Week 1 output goal:
- [ ] Collect 10–20 relevant articles manually first (fastest, avoids engineering rabbit holes)
- [ ] Save raw article text into `week_1/data/news/raw/` as `.txt`
- [ ] Track sources in `week_1/docs/news_source_log.md` (title, date, url, key claim)

Week 2 output goal:
- [ ] Add automation (scraper / RSS / page fetch) once you confirm which sites are accessible and stable

