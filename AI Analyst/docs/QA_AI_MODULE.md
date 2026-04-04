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

---

## Q5: Your own AI score is ~66.5 (“moderate”). Why are you still structurally bullish DEC?

**A:** The score measures **current observable momentum** in disclosed deals and transcript language — **not** terminal fair value. At **~66**, the market has **not** fully priced a sustained Chinese OEM export cycle; **Deal Flow (~50)** and **Incumbent Anxiety (~56)** are the honest weak links. If the composite were already **90**, the trade would largely be **priced in** and there would be **no alpha**. **Moderate momentum + early-stage pipeline** is consistent with **being early** on the thesis.

---

## Q6: Which deals count toward Order Conversion (5/8 → 62.5)?

**A:** See **`order_conversion_included`** in **`outputs/momentum_score.json`** after each run. On the canonical 8-row CSV, the five are: **Pakistan** (In Progress), **Kazakhstan** (Delivered), **Bangladesh** (Contract Signed), **Uzbekistan** (Contract Signed), **Canada** (Confirmed). **Negotiating / Early Stage / Exploratory** are excluded by design. Matching uses **regex word boundaries** so a hypothetical **“Unconfirmed”** label would **not** match **“confirmed.”** *“Contract Signed”* does **not** double-count via a stray **“confirmed”** substring — it is its own category in the rule string.

---

## Q7: Chart 1 shows China mentions collapse after Q1 2025 — doesn’t that mean the threat went away?

**A:** **No.** The pattern is **episodic commentary**, not structural competitive relief. Framing: management **addressed DEC/China when it was in the news**, then **largely stopped naming it** while **backlog language intensified**. **Strategic silence** on China alongside **backlog emphasis** is consistent with **capacity rationing** and **selective disclosure** — not with Chinese competition disappearing.

---

## Q8: Competition mentions are tiny (1–3 per quarter). Isn’t that “noise”?

**A:** **Low counts are the point.** GEV does **not** need to **verbally** foreground Chinese OEMs while it is **sold out** on a multi-year view. The question for the short leg is whether a **valuation premium** tied to **scarcity pricing** survives as **DEC and peers fill supply gaps** GEV cannot serve — not whether **keyword counts** are high **today**.

---

## Q9: Slide 6 (hockey stick) has two y-axes — quarterly MW vs cumulative MW. Why the different scales?

**A:** **Left axis:** **MW per quarter** (bars). **Right axis:** **cumulative MW** (line), which **sums across quarters** and therefore **runs much higher** than any single quarter’s bar. Same chart, **two metrics** — standard dual-axis **stock + flow** presentation.

---

## Q10: Excel / deck — what number do we paste for the AI Module?

**A:** Use **`outputs/momentum_score.json` → `composite_score`** after **`python3 ai_trade_flow_analyzer.py --charts-only`** (currently **66.5**). **Manually align** the Excel **AI Module** tab (e.g. Sheet 16) and any deck callouts to that JSON — **not** older placeholders (**~71**, **~68.7**) or any **NLP-merged** run (**~85.7**). This repo does **not** store the `.xlsx`; the team must update the workbook locally.

---

## Q11: I see an 18-row deal CSV next to the 8-row canonical file — which is “real”?

**A:** **Headline model:** only **`data/deals/export_deal_database.csv`** (8 rows). After **`--full` / `--extract-news`**, the pipeline writes **`outputs/api_extraction_raw_output.csv`** (curated **plus** raw NLP) for **appendix / QC** — it is **not** fed into the default score. The legacy filename **`export_deal_database_updated.csv`** is **removed** from this project; if you still have a stray copy locally, **delete or archive** it so judges do not confuse it with ground truth.
