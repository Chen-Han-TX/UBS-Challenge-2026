#!/usr/bin/env bash
# Refresh canonical data/ inputs from Week 1 working folders.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/data/transcripts" "$ROOT/data/news/raw"
cp "$ROOT/week_1/outputs/gev_mentions_by_quarter.csv" \
  "$ROOT/data/transcripts/gev_mentions_by_quarter.csv"
cp "$ROOT/week_1/data/news/raw/"dec_news_*.txt "$ROOT/data/news/raw/"
echo "Synced transcript CSV and news .txt files into $ROOT/data/"
