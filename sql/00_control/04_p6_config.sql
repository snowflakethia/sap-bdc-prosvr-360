-- P6 redesign (spec docs/spec_p6_productivity.md v0.4): model prices, required curricula, WPS weights and the
-- seeded true effects. The generator reads OPS.AI_MODEL_PRICE, OPS.LEVEL_REQUIRED_CURRICULUM and
-- OPS.SIM_TRUTH_EFFECTS, so the coefficients it simulates and the values the gates check have one source.
-- Billability / utilization / learning targets reuse OPS.GEN_PARAMS_TIME_TARGET (decision 2026-11-05).
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_ACOCO_BUILD;

-- AI products and when they were available to ACoCo (decision 2026-11-05): chat assistants before the coding
-- products; Claude Code and Codex from 1 May 2025, Cortex Code / AISQL from 1 Nov 2025. Chat start dates are the
-- simulation's assumption (ChatGPT Enterprise / Claude for Work rollout), so FY22 has no AI usage.
CREATE OR REPLACE TABLE ACOCO_DB.OPS.AI_PRODUCT (
  PRODUCT        VARCHAR NOT NULL PRIMARY KEY,
  VENDOR         VARCHAR NOT NULL,
  PRODUCT_NAME   VARCHAR NOT NULL,
  PRODUCT_KIND   VARCHAR NOT NULL,
  AVAILABLE_FROM DATE NOT NULL,
  AVAILABLE_TO   DATE
) COMMENT = 'AI products by vendor channel with availability window (P6 spec 4.1); one product per vendor channel on any date';
INSERT INTO ACOCO_DB.OPS.AI_PRODUCT VALUES
  ('CHATGPT',     'OPENAI',    'ChatGPT Enterprise',  'CHAT_ASSISTANT', '2023-01-01', '2025-04-30'),
  ('CODEX',       'OPENAI',    'Codex',               'CODING_AGENT',   '2025-05-01', NULL),
  ('CLAUDE_CHAT', 'ANTHROPIC', 'Claude for Work',     'CHAT_ASSISTANT', '2023-07-01', '2025-04-30'),
  ('CLAUDE_CODE', 'ANTHROPIC', 'Claude Code',         'CODING_AGENT',   '2025-05-01', NULL),
  ('CORTEX',      'CORTEX',    'Cortex Code / AISQL', 'CODING_AGENT',   '2025-11-01', NULL);

-- Models by product with availability windows (approximate public release dates; a model is used from its release
-- until it is superseded) and simulated list prices, USD per million tokens. MIX_SHARE is renormalised over the
-- models available on a day. Cortex model names checked against SHOW MODELS 2026-11-05.
CREATE OR REPLACE TABLE ACOCO_DB.OPS.AI_MODEL_PRICE (
  VENDOR              VARCHAR NOT NULL,
  PRODUCT             VARCHAR NOT NULL,
  MODEL               VARCHAR NOT NULL,
  MODEL_FAMILY        VARCHAR NOT NULL,
  MIX_SHARE           NUMBER(4,2) NOT NULL,
  INPUT_USD_PER_MTOK  NUMBER(8,3) NOT NULL,
  OUTPUT_USD_PER_MTOK NUMBER(8,3) NOT NULL,
  AVAILABLE_FROM      DATE NOT NULL,
  AVAILABLE_TO        DATE,
  PRIMARY KEY (PRODUCT, MODEL)
) COMMENT = 'AI model price list by product x model with availability window (simulated list prices) and the generator model mix (P6 spec 4.1)';
INSERT INTO ACOCO_DB.OPS.AI_MODEL_PRICE VALUES
  ('OPENAI',    'CHATGPT',     'gpt-3.5-turbo',     'GPT',    1.00,  1.50,  2.00, '2023-01-01', '2023-03-13'),
  ('OPENAI',    'CHATGPT',     'gpt-4',             'GPT',    1.00, 30.00, 60.00, '2023-03-14', '2024-05-12'),
  ('OPENAI',    'CHATGPT',     'gpt-4o',            'GPT',    1.00,  5.00, 15.00, '2024-05-13', NULL),
  ('ANTHROPIC', 'CLAUDE_CHAT', 'claude-2',          'CLAUDE', 1.00,  8.00, 24.00, '2023-07-01', '2024-03-03'),
  ('ANTHROPIC', 'CLAUDE_CHAT', 'claude-3-sonnet',   'CLAUDE', 1.00,  3.00, 15.00, '2024-03-04', '2024-06-19'),
  ('ANTHROPIC', 'CLAUDE_CHAT', 'claude-3-5-sonnet', 'CLAUDE', 1.00,  3.00, 15.00, '2024-06-20', NULL),
  ('ANTHROPIC', 'CLAUDE_CODE', 'claude-3-7-sonnet', 'CLAUDE', 1.00,  3.00, 15.00, '2025-05-01', '2025-05-21'),
  ('ANTHROPIC', 'CLAUDE_CODE', 'claude-sonnet-4',   'CLAUDE', 1.00,  3.00, 15.00, '2025-05-22', '2025-09-28'),
  ('ANTHROPIC', 'CLAUDE_CODE', 'claude-sonnet-4-5', 'CLAUDE', 0.85,  4.50, 22.50, '2025-09-29', NULL),
  ('ANTHROPIC', 'CLAUDE_CODE', 'claude-haiku-4-5',  'CLAUDE', 0.15,  1.50,  7.50, '2025-10-15', NULL),
  ('OPENAI',    'CODEX',       'gpt-4.1',           'GPT',    0.20,  2.00,  8.00, '2025-05-01', NULL),
  ('OPENAI',    'CODEX',       'codex-mini',        'GPT',    0.80,  1.50,  6.00, '2025-05-01', '2025-08-06'),
  ('OPENAI',    'CODEX',       'gpt-5',             'GPT',    0.80,  2.50, 20.00, '2025-08-07', NULL),
  ('CORTEX',    'CORTEX',      'claude-sonnet-4-5', 'CLAUDE', 0.35,  2.40, 12.00, '2025-11-01', NULL),
  ('CORTEX',    'CORTEX',      'claude-haiku-4-5',  'CLAUDE', 0.10,  0.80,  4.00, '2025-11-01', NULL),
  ('CORTEX',    'CORTEX',      'openai-gpt-5',      'GPT',    0.35,  1.60, 12.80, '2025-11-01', NULL),
  ('CORTEX',    'CORTEX',      'openai-gpt-4.1',    'GPT',    0.10,  1.20,  4.80, '2025-11-01', NULL),
  ('CORTEX',    'CORTEX',      'llama3.1-70b',      'OPEN',   0.05,  0.90,  0.90, '2025-11-01', NULL),
  ('CORTEX',    'CORTEX',      'mistral-large2',    'OPEN',   0.05,  1.00,  3.00, '2025-11-01', NULL);

-- Curricula required at each level every fiscal year (spec 2.3). AI_ANY = any one of the three AI curricula.
CREATE OR REPLACE TABLE ACOCO_DB.OPS.LEVEL_REQUIRED_CURRICULUM (
  LEVEL      VARCHAR NOT NULL,
  CURRICULUM VARCHAR NOT NULL,
  PRIMARY KEY (LEVEL, CURRICULUM),
  CONSTRAINT FK_LRC_LEVEL FOREIGN KEY (LEVEL) REFERENCES ACOCO_DB.OPS.LEVEL (LEVEL)
) COMMENT = 'Required curricula per level and fiscal year; AI_ANY = one of AGENTIC_AI_BUILD, PROMPT_COPILOT, CORTEX_DATA';
INSERT INTO ACOCO_DB.OPS.LEVEL_REQUIRED_CURRICULUM VALUES
  ('Analyst', 'AI_ANY'), ('Analyst', 'SAP_FUNCTIONAL'),
  ('Consultant', 'AI_ANY'), ('Consultant', 'PROJECT_MGMT'),
  ('Manager', 'AI_ANY'), ('Manager', 'LEADERSHIP'), ('Manager', 'COMMERCIAL_BID'),
  ('Senior Manager', 'AI_ANY'), ('Senior Manager', 'LEADERSHIP'), ('Senior Manager', 'COMMERCIAL_BID'),
  ('Principal', 'AI_ANY'), ('Principal', 'LEADERSHIP');

-- WPS pillar weights by level (spec 2.5). Rows sum to 100 (gate).
CREATE OR REPLACE TABLE ACOCO_DB.OPS.WPS_WEIGHTS (
  LEVEL VARCHAR NOT NULL PRIMARY KEY,
  VC NUMBER(5,1) NOT NULL, OE NUMBER(5,1) NOT NULL, PD NUMBER(5,1) NOT NULL, TM NUMBER(5,1) NOT NULL,
  CONSTRAINT FK_WPSW_LEVEL FOREIGN KEY (LEVEL) REFERENCES ACOCO_DB.OPS.LEVEL (LEVEL)
) COMMENT = 'WPS pillar weights by level; TM weight is redistributed pro-rata when TM does not apply (P6 spec 2.5)';
INSERT INTO ACOCO_DB.OPS.WPS_WEIGHTS VALUES
  ('Analyst', 15, 45, 40, 0), ('Consultant', 25, 40, 35, 0), ('Manager', 30, 30, 15, 25),
  ('Senior Manager', 40, 20, 10, 30), ('Principal', 50, 10, 10, 30);

-- Input weights inside each pillar, by level (spec 2.4). Each level x pillar sums to 100 (gate).
CREATE OR REPLACE TABLE ACOCO_DB.OPS.WPS_INPUT_WEIGHTS (
  LEVEL  VARCHAR NOT NULL,
  PILLAR VARCHAR NOT NULL,
  INPUT  VARCHAR NOT NULL,
  WEIGHT NUMBER(5,1) NOT NULL,
  PRIMARY KEY (LEVEL, PILLAR, INPUT)
) COMMENT = 'WPS input weights inside each pillar, by level (P6 spec 2.4)';
INSERT INTO ACOCO_DB.OPS.WPS_INPUT_WEIGHTS
SELECT l.LEVEL, w.PILLAR, w.INPUT,
       CASE WHEN w.PILLAR = 'PD' AND w.INPUT = 'BILL' THEN IFF(l.LEVEL_SORT <= 3, 30, 20)
            WHEN w.PILLAR = 'PD' AND w.INPUT = 'UTIL' THEN IFF(l.LEVEL_SORT <= 3, 20, 30)
            ELSE w.WEIGHT END
FROM ACOCO_DB.OPS.LEVEL l
CROSS JOIN (SELECT $1 PILLAR, $2 INPUT, $3 WEIGHT FROM VALUES
  ('VC', 'WIN', 50), ('VC', 'EFF', 50),
  ('OE', 'SCHED', 50), ('OE', 'EFF', 50),
  ('PD', 'BILL', 0), ('PD', 'UTIL', 0), ('PD', 'AREUSE', 20), ('PD', 'LEARN', 15), ('PD', 'ACREATE', 15),
  ('TM', 'TEAM', 100)) w;

-- Seeded true effects (spec 4.4). COEF is read by gen/acoco_gen.py; EXPECTED_SIGN is checked by the truth gates.
-- UNIT: OE_PROD = add to person productivity at full plateau; LOGIT = add to the win logit per named bid-team member,
-- centred on the weekly mean (win-rate level unchanged); PROD = multiplicative productivity uplift (CUR_PROJECT_MGMT:
-- x share of the work-package team); ALLOC = delivery allocation uplift; SHARE = factor.
CREATE OR REPLACE TABLE ACOCO_DB.OPS.SIM_TRUTH_EFFECTS (
  EFFECT_ID     VARCHAR NOT NULL,
  LEVEL         VARCHAR NOT NULL,
  EXPOSURE      VARCHAR NOT NULL,
  OUTCOME       VARCHAR NOT NULL,
  COEF          NUMBER(8,4) NOT NULL,
  UNIT          VARCHAR NOT NULL,
  EXPECTED_SIGN NUMBER(2,0) NOT NULL,
  NOTE          VARCHAR,
  PRIMARY KEY (EFFECT_ID, LEVEL)
) COMMENT = 'Ground truth of the effects seeded by the generator; gates check the analysis recovers them (P6 spec 4.4)';
INSERT INTO ACOCO_DB.OPS.SIM_TRUTH_EFFECTS
SELECT e.EFFECT_ID, l.LEVEL, e.EXPOSURE, e.OUTCOME,
       CASE l.LEVEL_SORT WHEN 1 THEN e.C1 WHEN 2 THEN e.C2 WHEN 3 THEN e.C3 WHEN 4 THEN e.C4 ELSE e.C5 END,
       e.UNIT,
       SIGN(CASE l.LEVEL_SORT WHEN 1 THEN e.C1 WHEN 2 THEN e.C2 WHEN 3 THEN e.C3 WHEN 4 THEN e.C4 ELSE e.C5 END),
       e.NOTE
FROM ACOCO_DB.OPS.LEVEL l
CROSS JOIN (SELECT $1 EFFECT_ID, $2 EXPOSURE, $3 OUTCOME, $4 C1, $5 C2, $6 C3, $7 C4, $8 C5, $9 UNIT, $10 NOTE FROM VALUES
  ('CORTEX_OE',      'Cortex tokens per delivery hour', 'EFF, SCHED', 0.16, 0.16, 0.09, 0.09, 0.09, 'OE_PROD',
   'Dose-response with plateau 1 - exp(-6 x); same for Claude and OpenAI model families; Cortex exists from 2025-11-01'),
  ('CORTEX_OPEN',    'Cortex open-model share',         'EFF, SCHED', 0.30, 0.30, 0.30, 0.30, 0.30, 'SHARE',
   'Open models carry this fraction of the Cortex OE effect (small)'),
  ('CLAUDE_CODE_WIN','Claude Code bid-team usage',      'WIN',        1.50, 1.50, 1.50, 0.00, 0.00, 'LOGIT',
   'Per named bid-team member: logit += COEF x (own usage x Claude Code share - weekly mean). Analyst weak: few bids'),
  ('CODEX_WIN',      'Codex bid-team usage',            'WIN',        0.00, 0.00, 0.00, 1.50, 1.50, 'LOGIT',
   'Per named bid-team member: logit += COEF x (own usage x Codex share - weekly mean)'),
  ('CLAUDE_CODE_OE', 'Claude Code tokens',              'EFF, SCHED', 0.00, 0.00, 0.00, 0.00, 0.00, 'OE_PROD',
   'Null by design: the OE lever is Cortex'),
  ('CODEX_OE',       'Codex tokens',                    'EFF, SCHED', 0.00, 0.00, 0.00, 0.00, 0.00, 'OE_PROD',
   'Null by design: the OE lever is Cortex'),
  ('ASSET_REUSE',    'Asset reused on the work package','EFF, SCHED', 0.07, 0.07, 0.07, 0.07, 0.07, 'PROD', NULL),
  ('CUR_AI',         'AI curriculum completed (26 wks)','EFF',        0.07, 0.07, 0.07, 0.07, 0.07, 'PROD',
   'AGENTIC_AI_BUILD, PROMPT_COPILOT, CORTEX_DATA'),
  ('CUR_PROJECT_MGMT','PROJECT_MGMT completed (26 wks)','SCHED',      0.06, 0.06, 0.06, 0.06, 0.06, 'PROD', NULL),
  ('CUR_COMMERCIAL', 'COMMERCIAL_BID completed (26 wks)','WIN',       0.60, 0.60, 0.60, 0.60, 0.60, 'LOGIT',
   'Per named bid-team member: logit += COEF x (completed in the 26 weeks before the bid - weekly mean)'),
  ('CUR_SAP',        'SAP_FUNCTIONAL completed (26 wks)','BILL',      0.04, 0.04, 0.04, 0.04, 0.04, 'ALLOC', NULL),
  ('CUR_LEADERSHIP', 'Manager LEADERSHIP completed (26 wks)', 'Reports EFF', 0.03, 0.03, 0.03, 0.03, 0.03, 'PROD', NULL),
  ('CUR_INDUSTRY',   'INDUSTRY completed',              'VC',         0.00, 0.00, 0.00, 0.00, 0.00, 'PROD',
   'Null by design')) e;
