# Measured story anchors (PRD 6.3)

Measured 2026-10-27 against ACOCO_L2 as of 2026-10-01 by `tools/validate.py --step anchors`.
Design targets are from PRD 6.3; `MISS` = outside the band, with the proposed fix (decision needed - a
generator change returns to CP-02 and is re-measured here).

| ID | Anchor | Design target | Measured | Status | Proposed fix |
|---|---|---|---|---|---|
| A1 | One Large FS fixed-price project in loss at FY26 close | forecast margin < 0 %, CPI ~0.73 (0.65-0.80), SPI ~0.8 (0.75-0.90) | P-0635 (FS, Large, FIXED_PRICE): forecast margin -15.5 %, CPI 0.70, SPI 0.97 | **MISS** | SPI above band: lower the story project's critical-path productivity (0.58) or lengthen its slip; CP-02 generator |
| A2 | FY26 firm Delivery share / bench | ~72 % (70-74) / 1-2 %, bench < 3 % every year | Delivery 70.4 %, bench 1.4 %; bench by FY {2022: 2.3, 2023: 1.6, 2024: 1.7, 2025: 1.6, 2026: 1.4} | **OK** |  |
| A3 | FS roll-off before 30 Dec 2026 without successor | 30-40 people; > 75 % below the pipeline's required AI-skill level | 34 people; 82 % below pipeline AI level | **OK** |  |
| A4 | Voluntary attrition trend | FY22 peak ~18 % (16-20) -> FY26 ~13 % (11-15) | by FY {2022: 21.7, 2023: 16.6, 2024: 16.2, 2025: 14.6, 2026: 14.3} | **MISS** | Attrition is measured on the whole firm, but only the simulated pool leaves (real SF records carry ~20 terminations); either measure on the simulated pool only or raise simulated leavers (CP-02 ATTRITION) |
| A5 | AI return (FY26, FS): People+Agents vs People-only | margin ~+10 pts (7-13); CPI > 1.1 vs ~1.0 | margin 33.6 % vs 26.6 % (+6.9 pts); median CPI 1.15 vs 1.06 (n 15 / 12) | **MISS** | Agent hours are billed as cost but not priced into the contract: raise HUMAN_AGENT / AGENT_LED sold margin (contract value) or their productivity in the generator (CP-02) |
| A6 | Pre-sales intensity and win-rate (within size class) | above-median ~50 % vs below ~30 % (gap 15-25 pts) | above 52.6 % vs below 23.8 % (gap 28.9 pts; firm win-rate 38 %) | **MISS** | Effect direction right but the base win-rate is ~58 % (design ~40 %): lower the generator's base win probability (CP-02) |
| A7 | Pursuit-team skill fit and win-rate | fit >= 0.8 ~55 % vs < 0.5 ~30 % (gap >= 15 pts) | high 54.3 % (n 1014) vs low 10.5 % (n 583) | **OK** |  |
| A8 | Asset harvest and reuse | harvest FY22 ~15 % -> FY26 ~40 %; reuse CPI ~1.05 vs ~0.95; story project reused none of 2-3 matching assets | harvest by FY {2022: 13.0, 2023: 21.0, 2024: 25.0, 2025: 30.0, 2026: 35.0}; median CPI reuse 1.112 vs none 1.022; story project uses 0, matching assets available at its start 23 | **OK** |  |
| A9 | Time mix (FS, FY26) | Delivery ~72 (70-74) / Bid ~16 (14-18) / Learning ~10 (8-12) / Admin ~1.5 (< 5) / Bench ~1.7 (< 3) % | Delivery 72.0 / Bid 15.7 / Learning 9.6 / Admin 1.4 / Bench 1.4 % | **OK** |  |
| A10 | AI productivity uplift (FS, FY26), within level x work type | ~+0.08 (0.05-0.11), 90 % CI excluding zero; skilled-but-inactive ~0 | uplift +0.064, 90 % CI [+0.044, +0.084] (381 people); skilled-inactive PI 1.036 vs other non-active 1.044 | **OK** |  |
| A11 | Learning payback (6 months after vs before, vs matched comparison) | AI curriculum ~+4 % (+0.03-0.05), significant; non-AI smaller, not significant | AI +0.0401 (se 0.0018, n 3,334); non-AI -0.0351 (se 0.0011) | **OK** |  |
| A12 | AI skilled but inactive (FS, Jul-Sep 2026) | ~20 % (15-25) of FS people with AI-skill >= 3 have no AI-tool use | 46 of 174 (26 %) | **MISS** | Adjust the share of AI-skilled people with zero telemetry in the generator (CP-02) |
| A13 | Large-project revenue share (portfolio shape) | 0.72-0.79 of revenue | FY22-26 73.3 %; by FY {2022: 72.8, 2023: 76.8, 2024: 69.0, 2025: 73.1, 2026: 74.7} | **OK** |  |

**8 OK, 5 MISS** of 13.
