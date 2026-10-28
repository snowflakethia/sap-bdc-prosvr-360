# ACoCo ProServe360 - Presenter card

Measured figures only, as of 1 Oct 2026 (FY26 closed). Default view: **Business Group Financial Services (FS)**, FY22-FY26, all sizes, story project **P-0615**. Every row is re-measured by `tools/presenter_card.py` (also `tools/validate.py --step card`) from the same registry statement the page runs.

Honesty lines: simulated rows are demo data; hours saved are ESTIMATED; AI results are associations within level x work type (90 % CI), never causation; the attrition list is a conversation prompt, not a prediction.

Timing (dry run `logs/dry_run_cp11.md`): every page loads in about 1-2 s after the warm-up (`docs/RUNBOOK.md`). The Advisor takes about 1 minute for a simple question and about 2 minutes for the PMD-11 what-if - ask it at the start of the 24-28 beat and walk through P7 while it runs.


## 0-3 Framing min

| # | Page | Say | Figure | Source (registry statement -> object) |
|---|---|---|---|---|
| F1 | C1 | Firm FY26 revenue | **$327.94M** | `cx_firm` -> ACOCO_L2.SERVING.VW_SCORECARD_FY |
| F2 | C1 | Firm FY26 margin | **35.2 %** | `cx_firm` -> ACOCO_L2.SERVING.VW_SCORECARD_FY |
| F3 | C1 | Firm people at end FY26 | **1,956** | `cx_firm` -> ACOCO_L2.SERVING.VW_SCORECARD_FY |
| F4 | C1 | Firm FY26 Delivery share | **70.9 %** | `cx_firm` -> ACOCO_L2.SERVING.VW_SCORECARD_FY |
| F5 | C1 | Firm FY26 voluntary attrition | **12.9 %** | `cx_firm` -> ACOCO_L2.SERVING.VW_SCORECARD_FY |
| F6 | C1 | Firm FY26 win-rate | **49.7 %** | `cx_firm` -> ACOCO_L2.SERVING.VW_SCORECARD_FY |

## 3-5 Sources min

| # | Page | Say | Figure | Source (registry statement -> object) |
|---|---|---|---|---|
| S1 | P8 | Rows read from BDC CLDs (L0) | **16,944,014** | `ln_layers` -> ACOCO_L2.SERVING.VW_LINEAGE |
| S2 | P8 | CLD tables read (L0) | **13** | `ln_layers` -> ACOCO_L2.SERVING.VW_LINEAGE |
| S3 | P8 | Simulated tables (L0, ACOCO_SIM) | **34** | `ln_layers` -> ACOCO_L2.SERVING.VW_LINEAGE |

## 5-8 ProServe360 min

| # | Page | Say | Figure | Source (registry statement -> object) |
|---|---|---|---|---|
| O1 | P0 | FS FY26 margin | **34.3 %** | `ov_scorecard` -> ACOCO_L2.SERVING.VW_SCORECARD_FY |
| O2 | P0 | FS FY26 margin change vs FY25 | **-0.7 pts** | `ov_scorecard` -> ACOCO_L2.SERVING.VW_SCORECARD_FY |
| O3 | P0 | FS FY26 revenue | **$70.29M** | `ov_scorecard` -> ACOCO_L2.SERVING.VW_SCORECARD_FY |
| O4 | P0 | FS on-time (active projects) | **90.0 %** | `ov_on_time` -> ACOCO_L2.SERVING.VW_PROJECT_HEALTH_NOW |
| O5 | P0 | FS FY26 win-rate | **50.0 %** | `ov_scorecard` -> ACOCO_L2.SERVING.VW_SCORECARD_FY |
| O6 | P0 | FS FY26 Delivery share (target ~70 %) | **71.3 %** | `ov_scorecard` -> ACOCO_L2.SERVING.VW_SCORECARD_FY |
| O7 | P0 | FS FY26 bench share (allowance ~2 %) | **1.4 %** | `ov_scorecard` -> ACOCO_L2.SERVING.VW_SCORECARD_FY |
| O8 | P0 | FS FY26 voluntary attrition | **13.1 %** | `ov_scorecard` -> ACOCO_L2.SERVING.VW_SCORECARD_FY |

## 8-14 Operational Excellence min

| # | Page | Say | Figure | Source (registry statement -> object) |
|---|---|---|---|---|
| D1 | P1 / P2 | P-0615 (Atlas Bank, Large FS fixed price) forecast margin | **-16.9 %** | `pf_fp_watch` -> ACOCO_L2.SERVING.VW_PROJECT_HEALTH_NOW |
| D2 | P2 | P-0615 CPI | **0.70** | `pf_fp_watch` -> ACOCO_L2.SERVING.VW_PROJECT_HEALTH_NOW |
| D3 | P2 | P-0615 SPI | **0.96** | `pf_fp_watch` -> ACOCO_L2.SERVING.VW_PROJECT_HEALTH_NOW |
| D4 | P2 | P-0615 LD exposure | **$1.46M** | `pf_fp_watch` -> ACOCO_L2.SERVING.VW_PROJECT_HEALTH_NOW |
| D5 | P2 / P11 | P-0615 matching library assets it did not reuse | **3** | `pj_assets` -> ACOCO_L2.SERVING.VW_ASSET_MATCH |
| D6 | P11 | FS FY26 harvest rate (FY22 9.1 %) | **29.2 %** | `as_fy` -> ACOCO_L2.SERVING.VW_ASSET_FY |
| D7 | P11 | FS FY26 median CPI with reuse | **1.19** | `as_fy` -> ACOCO_L2.SERVING.VW_ASSET_FY |
| D8 | P11 | FS FY26 median CPI without reuse | **1.10** | `as_fy` -> ACOCO_L2.SERVING.VW_ASSET_FY |

## 14-18 Value Creation min

| # | Page | Say | Figure | Source (registry statement -> object) |
|---|---|---|---|---|
| V1 | P5 | FS Large bids, above-median intensity + high fit, win-rate | **55.2 %** | `pi_win_rate` -> ACOCO_L2.SERVING.VW_WIN_RATE_SEGMENTS |
| V2 | P5 | FS Large bids, below-median intensity + low fit, win-rate | **33.3 %** | `pi_win_rate` -> ACOCO_L2.SERVING.VW_WIN_RATE_SEGMENTS |
| V3 | P5 | FS open bids | **22** | `pi_open` -> ACOCO_L2.SERVING.VW_BENCH_TO_PIPELINE, ACOCO_L2.SERVING.VW_PIPELINE_OPEN |

## 18-24 People Development min

| # | Page | Say | Figure | Source (registry statement -> object) |
|---|---|---|---|---|
| P1 | P3 | FS people rolling off in the next 90 days | **36** | `wf_roll_off` -> ACOCO_L2.SERVING.VW_ROLL_OFF_90D |
| P2 | P3 | ... of whom below the pipeline's AI-skill level | **88.9 %** | `wf_roll_off` -> ACOCO_L2.SERVING.VW_ROLL_OFF_90D |
| P3 | P6 | FS AI-active productivity uplift FY26 (90 % CI [+9.8, +13.8 %], significant) | **+11.8 %** | `ov_ai_uplift` -> ACOCO_L2.SERVING.VW_AI_PRODUCTIVITY_TEST |
| P4 | P6 | FS skilled-but-inactive uplift (CI spans zero: no significant effect) | **+2.6 %** | `ov_ai_uplift` -> ACOCO_L2.SERVING.VW_AI_PRODUCTIVITY_TEST |
| P5 | P6 | FS people AI-skilled (3+) but not using AI tools, FY26 (test band) | **37** | `ai_test` -> ACOCO_L2.SERVING.VW_AI_PRODUCTIVITY_TEST |
| P6 | P6 | FS Agentic-AI curriculum payback (significant) | **+3.7 %** | `ai_payback` -> ACOCO_L2.SERVING.VW_LEARNING_PAYBACK_TEST |
| P7 | P6 | FS margin, Human + Agent delivery | **40.7 %** | `ai_delivery_model` -> ACOCO_L2.SERVING.VW_DELIVERY_MODEL_FY |
| P8 | P6 | FS margin, Human-only delivery | **26.3 %** | `ai_delivery_model` -> ACOCO_L2.SERVING.VW_DELIVERY_MODEL_FY |

## 24-28 What-if min

| # | Page | Say | Figure | Source (registry statement -> object) |
|---|---|---|---|---|
| R1 | P7 | FS projects forecast to finish at a loss | **1** | `rs_margin_leak` -> ACOCO_L2.SERVING.VW_RISK_REGISTER |

_37 / 37 figures verified against the pinned measured values._
