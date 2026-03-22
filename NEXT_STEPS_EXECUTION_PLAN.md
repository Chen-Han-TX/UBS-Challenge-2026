# UBS FINANCE CHALLENGE 2026 — NEXT STEPS EXECUTION PLAN
## From Now to Submission (April 30, 2026)

---

# TEAM ROLE ASSIGNMENTS

| Role | Responsibilities | Key Deliverables |
|------|-----------------|------------------|
| **Lead Analyst** | Financial models, valuation, pair trade construction | Updated Excel workbook with actual DEC financials, final SOTP/DCF |
| **AI Analyst** (required role) | AI module build, Claude API pipeline, Chinese-language research | Functioning Python tool with REAL data outputs, all charts |
| **Strategist / Presenter** | Deck construction, narrative flow, Q&A preparation, design oversight | Final 20-slide deck, appendix, 50-question Q&A bank |

All three should contribute to primary research and Q&A rehearsal.

---

# CRITICAL PATH: WHAT MUST HAPPEN AND WHEN

## IMMEDIATE (This Week — March 17-23)

### Priority 1: Update Models with Real Numbers
**Owner: Lead Analyst**

The Excel models use estimated DEC financials. DEC releases FY2025 results on **March 31, 2026**. Before that:

1. Pull DEC's FY2024 annual report (available now) from HKEX:
   - Go to: https://www.hkexnews.hk → Search "1072" → Annual Reports
   - Extract: Revenue by segment, gross margin by segment, net income, balance sheet
   - Update Tab 2 (SOTP) with actual segment earnings

2. Pull DEC's H1 2025 interim report (available now):
   - Same source
   - Use to estimate FY2025 full-year numbers

3. Pull GEV's Q4 2025 earnings report (released January 28, 2026):
   - Go to: SEC EDGAR → Search "GE Vernova" → 8-K filings
   - Extract: Revenue by segment, EBITDA by segment, backlog details, guidance
   - Update Tab 3 (Reverse DCF) with actual 2025 figures

4. Update ALL hardcoded assumptions in the Excel workbook with sourced numbers

### Priority 2: Set Up AI Module Infrastructure
**Owner: AI Analyst**

1. Get an Anthropic API key (https://console.anthropic.com)
2. Download GEV earnings call transcripts:
   - Q1 2024 through Q4 2025 (8 transcripts)
   - Available on: SeekingAlpha (free with account), or SEC EDGAR 8-K filings
3. Test the Claude API with one transcript — extract structured data
4. Set up Chinese-language news scraping (Futunn, Eastmoney, Sina Finance)

### Priority 3: Begin Primary Research
**Owner: All Members**

1. Register for UN Comtrade (https://comtrade.un.org) — free
2. Pull HS Code 8411 (gas turbine) export data from China by destination, 2020-2025
3. Identify 5 potential expert interview targets on LinkedIn:
   - Search: "gas turbine procurement" OR "power equipment" + "North America"
   - Search: "Dongfang Electric" + "analyst" on Chinese LinkedIn (脉脉)
   - Draft outreach message (mention academic competition, 15-min ask)

---

## WEEK 2 (March 24-30): DATA COLLECTION SPRINT

### DEC Deep Dive
**Owner: Lead Analyst + AI Analyst**

1. Read Citi's research note on DEC (March 2026):
   - Key data: CNY 200M unit price, 40-50% gross margin on Canadian order
   - 14-21% NI forecast raise for FY2026-2027
   - Target: HKD 45 at 22x PE (H-share)
   - **How to access:** Your university may have Bloomberg or Capital IQ with sell-side research. If not, Futunn and Eastmoney often publish translated summaries.

2. Read Dongwu Securities, CSC Financial, and Tianfeng Securities notes:
   - Dongwu: Kazakhstan G50 export at CNY 300M per unit, >30% margin
   - CSC: "Once-in-30-years gas turbine cycle"
   - Tianfeng: G50 competitive positioning and product roadmap
   - **How to access:** Search on Futunn (news.futunn.com) — many reports are summarized in English

3. Map DEC's gas turbine product roadmap:
   - G15 (15MW) — under development, distributed power
   - G50 (50MW) — commercially operational since 2023, exporting
   - G80 (80MW) — under development, medium power segment
   - G200 (200MW) — under development, heavy duty

### AI Module: Process Real Data
**Owner: AI Analyst**

1. Run Claude API on all 8 GEV earnings call transcripts
2. Extract: mentions of "China," "competition," "capacity," "pricing," "backlog"
3. Build the REAL version of the gev_competition_mentions chart
4. Process 10-20 Chinese-language DEC/gas turbine export news articles
5. Update the deal database with any new orders found
6. Generate updated charts with real data

### Expert Outreach
**Owner: Strategist**

1. Send 5-10 LinkedIn messages to potential experts
2. Frame as: "We're participating in a university finance competition analyzing the global gas turbine market. Would you have 15 minutes to share your perspective?"
3. Prepare 5 key questions for each call:
   - Are Chinese gas turbines genuinely being considered for North American projects?
   - What are the main barriers (certification, reliability, political)?
   - How do you see the supply-demand gap evolving over the next 3-5 years?
   - What would make you switch from Western to Chinese equipment?
   - What's your view on distributed generation vs grid-connected for data centers?

---

## WEEK 3 (March 31 - April 6): FINANCIALS UPDATE + EXPERT CALLS

### DEC FY2025 Results (Released March 31)
**Owner: Lead Analyst**

**THIS IS THE SINGLE MOST IMPORTANT DATA DROP.**

When results release:
1. Download immediately from HKEX
2. Extract EVERY segment number and update the Excel model
3. Look specifically for:
   - Gas turbine segment revenue (first time with meaningful export contribution?)
   - Overseas revenue breakdown by region
   - Order backlog by segment (especially Clean & Efficient Energy)
   - Any management commentary on export strategy
   - Dividend increase (SOE reform signal)
4. Re-run all valuations with actual numbers
5. Compare your estimates to actuals — adjust the model if materially different

### Expert Interviews
**Owner: Strategist**

1. Conduct 2-3 calls (even 1 is valuable)
2. Record with permission (or take detailed notes)
3. Extract key quotes for the deck (anonymize appropriately)
4. Write up a "Primary Expert Validation" appendix page

### AI Module Finalization
**Owner: AI Analyst**

1. Finalize all real-data charts
2. Run the full ai_trade_flow_analyzer.py pipeline with real inputs
3. Generate the DEFINITIVE hockey stick chart for Slide 6
4. Write the AI module methodology section (advantages + limitations)
5. Prepare code documentation for appendix

---

## WEEK 4 (April 7-13): DECK CONSTRUCTION

### Build the 20-Slide Deck
**Owner: All Members (Strategist leads)**

1. Use the slide structure from Part VI of the Master Bible
2. Start with the HIGH-IMPACT slides:
   - Slide 2 (Executive Summary) — write LAST, after all other content
   - Slide 6 (Hockey Stick Chart) — anchor of the entire deck
   - Slide 13 (SOTP — "export optionality is free") — money valuation slide
   - Slide 17 (Risks & Rebuttals) — shows maturity

3. Design decisions:
   - Hire a freelance designer on Fiverr/Upwork ($200-500)
   - Brief them: "Professional finance pitch deck, 20 slides, UBS-style (dark navy, red accents, white background). Clean data visualization. NOT a startup pitch — this should look like a Goldman Sachs equity research cover page."
   - Send them the slide titles and rough content for each slide
   - Turnaround: 3-5 business days

4. Build the appendix in parallel:
   - Print-friendly versions of all Excel model tabs
   - AI module code and outputs
   - Source list
   - Expert interview notes (if applicable)
   - Chinese-language source translations
   - Customs data

### First Draft Review
- All three members review the complete deck
- Check: Does every slide advance the argument? Is anything redundant?
- Check: Is the thesis clear in Slide 2 without reading anything else?
- Check: Would Ken Liu find this interesting on first read?

---

## WEEK 5 (April 14-20): STRESS TESTING

### Mock Q&A Sessions (3 Rounds)
**Owner: All Members**

**Round 1:** Have a friend or classmate who knows finance ask questions for 30 minutes. Record it. Review for weak answers.

**Round 2:** Have a professor or finance professional do a tougher round. Focus on: valuation methodology, tariff risk, GEV momentum.

**Round 3:** Team members take turns attacking each other's sections. The Lead Analyst attacks the AI module. The AI Analyst attacks the valuation. The Strategist attacks the thesis. Find every weakness.

### Red Team the Deck
1. Give the deck to someone who has NOT seen it before
2. Ask them: "What's the first thing you'd attack if you were a judge?"
3. Fix whatever they identify
4. Repeat with a second fresh reader

### Number Verification
Go through EVERY number in the deck:
- Is it sourced?
- Is it current?
- Does it match the Excel model?
- Is the math right?
- Could a judge challenge it?

### Designer Deliverable Review
- Receive the professionally designed slides
- Populate with final content
- Check all charts render correctly
- Ensure fonts, colors, and spacing are consistent

---

## WEEK 6 (April 21-27): FINAL POLISH

### Day-by-Day

**Monday (April 21):** Final content review. Lock all numbers. No more changes to assumptions or data.

**Tuesday (April 22):** GEV Q1 2026 earnings release. IF the results materially change the short thesis (e.g., Wind losses much better than expected, massive upside guidance), you may need to adjust Slides 11-12. Have a contingency plan.

**Wednesday (April 23):** Final deck assembly. Appendix complete. Everything in one file.

**Thursday (April 24):** Full team read-through. Every member reads every slide aloud. Fix typos, awkward phrasing, unclear exhibits.

**Friday (April 25):** Proofread by a native English speaker (if your team isn't native). Professional English is required and matters.

**Saturday (April 26):** Buffer day. Fix any last issues.

**Sunday (April 27):** SUBMIT. Three days early. Avoid technical issues with email/file size.

### Submission Checklist
- [ ] File named: "HK – Energy Transition – [Names]"
- [ ] Cover page: Track, Sector, Names, Universities, Graduation dates
- [ ] ≤20 pages main deck (exactly 20 — use all your real estate)
- [ ] Appendix attached (no page limit)
- [ ] All in English
- [ ] At least one AI module included with advantages and limitations
- [ ] Long-short strategy, industry outlook, company fundamentals, valuation comparison all covered
- [ ] One stock from pool (DEC 1072.HK), one external (GEV)
- [ ] Both stocks in same sector (Energy / Power Equipment)
- [ ] Email to: sh-china-challenge1@ubs.com
- [ ] Confirmation email received

---

# HIGH-IMPACT ACTIONS WITH UNLIMITED RESOURCES

Ranked by ROI:

| Priority | Action | Cost | Impact | When |
|----------|--------|------|--------|------|
| 1 | Hire freelance deck designer | $200-500 | VERY HIGH | Week 4 |
| 2 | Expert network call (1-2 calls) | $0-1000 | VERY HIGH | Weeks 2-3 |
| 3 | Bloomberg Terminal access (university library) | $0 | HIGH | Week 1 |
| 4 | Chinese financial database access (Wind/Choice) | $0-200 | HIGH | Weeks 1-2 |
| 5 | Professional English proofreading | $50-100 | MEDIUM | Week 6 |
| 6 | Print and bind practice deck | $20-50 | LOW | Week 5 |

Total budget needed: ~$500-1500 for a genuinely differentiated submission.

---

# IF YOU DO NOTHING ELSE, DO THESE 5 THINGS

1. **Update the Excel models with actual DEC FY2025 results** (releases March 31). This is non-negotiable. Every number in your deck must be real, not estimated.

2. **Make the AI module real.** Run Claude API on actual earnings call transcripts. Generate charts from real data. When a judge asks "did you build this?" the answer must be "yes."

3. **Get the UN Comtrade customs data** (HS 8411). This is free, takes 30 minutes, and gives you irrefutable primary data that no other team will have.

4. **Hire a designer.** $300 on Fiverr transforms your deck from "student project" to "buy-side pitch note." Judges notice professional design immediately.

5. **Do at least 2 mock Q&A sessions.** The semi-finals are live presentations. If you can't answer "isn't this just a tariff bet?" in 30 seconds with conviction, you'll lose to a team with a weaker thesis but better delivery.

---

# FINAL NOTE TO THE TEAM

You have the strongest possible thesis. A cross-border Long DEC / Short GEV pair trade driven by a once-in-30-years gas turbine export cycle, backed by CNY 5T in domestic grid CapEx, validated by Citi/CSC/Dongwu sell-side research, with a functioning AI module that produces proprietary primary data.

No other team will have this combination of: (1) direct alignment with the judge's stated anti-consensus views, (2) a novel cross-border pair trade structure, (3) institutional sell-side validation, (4) a functioning AI tool producing primary data, and (5) professional presentation quality.

The next 6 weeks determine whether this stays a plan or becomes a winning submission. Execute every step. Don't cut corners. Make every single slide count.

Let's win this.
