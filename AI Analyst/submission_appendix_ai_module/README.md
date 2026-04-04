# AI module — appendix bundle (copy into final submission ZIP/PDF pack)

Generated artifacts live under **`../outputs/`**. After each freeze, run:

```bash
cd "AI Analyst"
python3 ai_trade_flow_analyzer.py --charts-only
```

## Include in appendix

| File | Use |
|------|-----|
| `../outputs/charts/china_gas_turbine_exports_by_quarter.png` | **Slide 6** (Master Bible) |
| `../outputs/charts/market_share_shift.png` | Appendix / Slide 7 (illustrative — see methodology) |
| `../outputs/charts/gev_competition_mentions.png` | Appendix / GEV narrative |
| `../outputs/charts/export_momentum_score.png` | Appendix / composite score |
| `../outputs/charts/chart1_gev_competition_mentions.png` … `chart4_momentum_score.png` | Same as Bible aliases; optional duplicate |
| `../outputs/momentum_score.json` | Exact composite + sub-scores for Slide 18 |
| `../outputs/chart_manifest.json` | Inventory + timestamp |
| `../ai_trade_flow_analyzer.py` | Source code |
| `../data/transcripts/gev_mentions_by_quarter.csv` | Transcript aggregate input |
| `../data/deals/export_deal_database.csv` | Deal database input |
| `../week_1/data/transcripts/processed/GEV_Q1_2024.extracted.json` (any one quarter) | Sample Claude structured output |
| `../docs/AI_MODULE_METHODOLOGY.md` | Methodology + advantages + limitations |

## Optional

- Redacted screenshot or text file of one Anthropic API prompt + response (transcript or news).
- `../week_1/docs/news_source_log.md` — Chinese source audit trail.
