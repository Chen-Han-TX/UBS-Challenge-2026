# AI Analyst Workspace

This folder contains everything needed to execute the **AI Analyst** workstream (Claude/Anthropic pipeline + Chinese-language research automation) for the UBS Finance Challenge submission.

## Quick start (macOS / zsh)

### 1) Activate the workspace virtual environment

```bash
cd "/Users/chenhan/Library/Mobile Documents/com~apple~CloudDocs/NTU/Hacks/UBS 2026/UBS"
source .venv/bin/activate
python -c "import anthropic; print('anthropic', anthropic.__version__)"
```

### 2) Set your API key (recommended: environment variable)

```bash
export ANTHROPIC_API_KEY="YOUR_KEY_HERE"
```

To persist it across sessions, add the export line to `~/.zshrc` (or use a secrets manager).

### 3) Run the Week 1 transcript extractor on one file

**Quarter / year in JSON:** For files named `GEV_Q1_2024.txt`, `GEV_Q4_2025.txt`, etc., the script sets `metadata.period` from the filename (e.g. `Q1 2024`) so it cannot drift to the wrong quarter.

1. Put a transcript text file into:
   - `week_1/data/transcripts/raw/`
2. Run:

```bash
source .venv/bin/activate
python "AI Analyst/week_1/scripts/extract_gev_transcript.py" \
  --input "AI Analyst/week_1/data/transcripts/raw/example.txt" \
  --output "AI Analyst/week_1/data/transcripts/processed/example.extracted.json"
```

## Folder layout

- `week_1/`: Week 1 execution, scripts, and outputs
  - `scripts/`: runnable Python tools
  - `data/`: raw + processed transcripts/news
  - `outputs/`: charts and derived artifacts you will paste into the deck/appendix
  - `docs/`: methodology, prompt templates, and source notes

