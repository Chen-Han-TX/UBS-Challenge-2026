# Week 2 (legacy helper)

The **primary** pipeline is now the unified module at **`../ai_trade_flow_analyzer.py`** with inputs under **`../data/`**.

- **`scripts/build_real_week2_outputs.py`** — early standalone chart builder; optional. Prefer:

```bash
cd "AI Analyst"
python3 ai_trade_flow_analyzer.py --charts-only
```

Outputs (four charts + score) are written to **`../outputs/`**.
