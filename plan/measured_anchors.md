# Measured story anchors (PRD 6.3)

Measured 2026-10-28 against ACOCO_L2 as of 2026-10-01 by `tools/validate.py --step anchors`.
Design targets are from PRD 6.3; `MISS` = outside the band, with the proposed fix (decision needed - a
generator change returns to CP-02 and is re-measured here).

| ID | Anchor | Design target | Measured | Status | Proposed fix |
|---|---|---|---|---|---|
| A1 | One Large FS fixed-price project in loss at FY26 close | forecast margin < 0 %, CPI ~0.73 (0.65-0.80), SPI ~0.8 (0.75-0.90) | P-0615 (FS, Large, FIXED_PRICE): forecast margin -16.9 %, CPI 0.70, SPI 0.96 | **MISS** | SPI above band: lower the story project's critical-path productivity (0.58) or lengthen its slip; CP-02 generator |
| A2 | FY26 firm Delivery share / bench | ~72 % (70-74) / 1-2 %, bench < 3 % every year | Delivery 70.9 %, bench 1.4 %; bench by FY {2022: 1.9, 2023: 1.7, 2024: 1.8, 2025: 1.5, 2026: 1.4} | **OK** |  |
| A3 | FS roll-off before 30 Dec 2026 without successor | 30-40 people; > 75 % below the pipeline's required AI-skill level | 36 people; 89 % below pipeline AI level | **OK** |  |
| A4 | Voluntary attrition trend | FY22 peak ~18 % (16-20) -> FY26 ~13 % (11-15) | by FY {2022: 19.6, 2023: 17.2, 2024: 15.2, 2025: 13.7, 2026: 12.9} | **OK** |  |
| A5 | AI return (FY26, FS): People+Agents vs People-only | margin ~+10 pts (7-13); CPI > 1.1 vs ~1.0 | margin 40.8 % vs 29.0 % (+11.8 pts); median CPI 1.20 vs 1.12 (n 21 / 13) | **OK** |  |
| A6 | Pre-sales intensity and win-rate (within size class) | above-median ~50 % vs below ~30 % (gap 15-25 pts) | above 54.6 % vs below 23.7 % (gap 30.8 pts; firm win-rate 39 %) | **MISS** | Effect direction right but the base win-rate is ~58 % (design ~40 %): lower the generator's base win probability (CP-02) |
| A7 | Pursuit-team skill fit and win-rate | fit >= 0.8 ~55 % vs < 0.5 ~30 % (gap >= 15 pts) | high 53.3 % (n 971) vs low 10.3 % (n 494) | **OK** |  |
| A8 | Asset harvest and reuse | harvest FY22 ~15 % -> FY26 ~40 %; reuse CPI ~1.05 vs ~0.95; story project reused none of 2-3 matching assets | harvest by FY {2022: 11.0, 2023: 17.0, 2024: 20.0, 2025: 32.0, 2026: 30.0}; median CPI reuse 1.122 vs none 1.029; story project uses 0, matching assets available at its start 18 | **MISS** | Calibrate HARVEST_P by FY and the number of assets matching the story project's work type (CP-02) |
| A9 | Time mix (FS, FY26) | Delivery ~72 (70-74) / Bid ~16 (14-18) / Learning ~10 (8-12) / Admin ~1.5 (< 5) / Bench ~1.7 (< 3) % | Delivery 71.3 / Bid 16.4 / Learning 9.5 / Admin 1.4 / Bench 1.4 % | **OK** |  |
| A10 | AI productivity uplift (FS, FY26), within level x work type | ~+0.08 (0.05-0.11), 90 % CI excluding zero; skilled-but-inactive ~0 | uplift +0.119, 90 % CI [+0.098, +0.138] (375 people); skilled-inactive PI 1.073 vs other non-active 1.037 | **MISS** |  |
| A11 | Learning payback (6 months after vs before, vs matched comparison) | AI curriculum ~+4 % (+0.03-0.05), significant; non-AI smaller, not significant | AI +0.0488 (se 0.0017, n 3,431); non-AI -0.0369 (se 0.0011) | **OK** |  |
| A12 | AI skilled but inactive (FS, Jul-Sep 2026) | ~20 % (15-25) of FS people with AI-skill >= 3 have no AI-tool use | 34 of 170 (20 %) | **OK** |  |
| A13 | Large-project revenue share (portfolio shape) | 0.72-0.79 of revenue | FY22-26 72.9 %; by FY {2022: 69.5, 2023: 78.5, 2024: 75.6, 2025: 70.2, 2026: 70.7} | **OK** |  |

**9 OK, 4 MISS** of 13.
