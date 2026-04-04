# AI module — short Q&A (rehearsal)

Use numbers from the latest **`outputs/momentum_score.json`** after each `--charts-only` run. **After aligning the Canada row to RMB 4B (Citi 200M/unit),** the composite **deal-flow sub-score drops slightly** — e.g. **66.5 / 100** (gauge may show **67** rounded). Always cite whatever the JSON says after your last run; do **not** use old **71** or **68.7** if the file has moved.

---

## Q1: Your deal chart shows a different Canada contract value than the Excel SOTP. Which is right?

**A:** They are now aligned on economics. The **Excel SOTP** uses the **conservative Citi-disclosed case: RMB 200 million per unit × 20 units = RMB 4.0 billion** equipment revenue for the Canadian order. The **AI deal database CSV** uses **`est_value_usd_m ≈ 555.56`**, which is **RMB 4.0B ÷ 7.2** so the Python charts plot **~RMB 4B** in CNY (same **7.2** FX proxy as the methodology doc). **Dongwu’s ~RMB 300M/unit** tier applies to other contexts (e.g. Kazakhstan full GTCC); we do **not** use it for the Canada row so judges do not see a fake premium on the confirmed developed-market deal.

---

## Q2: What about the market share chart — is that real customs data?

**A:** **No.** `market_share_shift.png` is an **illustrative scenario** (labeled on the chart) for narrative framing only. It is **not** UN Comtrade or OEM-reported statistics. We keep it in the **appendix** unless the team replaces it with licensed or primary data. The **thesis evidence** for exports is the **disclosed deal database**, **FY2025 segment disclosure** (exports not yet in gas revenue), and optional **HS 8411** work from the team.

---

## Q3: What is the momentum score and why should we trust it?

**A:** **See `momentum_score.json`** — e.g. **66.5 / 100** after Canada value correction (moderate momentum). It is a **transparent composite** from five sub-scores: deal flow, incumbent anxiety (GEV transcript mention **first-half vs second-half** growth in China+competition counts), order conversion, geographic breadth of tracked deals, and a simple technology validation flag (e.g. delivered units + developed-market exposure). It is **not** a black box: inputs are **`export_deal_database.csv`** and **`gev_mentions_by_quarter.csv`**, and rerunning **`python ai_trade_flow_analyzer.py --charts-only`** reproduces the same charts and JSON. We state **limitations** on Slide 18 (mention volatility, pipeline rows, illustrative market share).

---

## Q4 (bonus): Did GEV keep talking about China every quarter?

**A:** **No.** Real extracts show **China mentions spiked in Q1 2025** then were **sparse** in several later quarters; **competition** language is more **steady but low**. We do not claim a smooth monotonic “fear index” — we show the **actual series** and explain the **score’s** use of **half-sample averages** for the anxiety sub-component.
