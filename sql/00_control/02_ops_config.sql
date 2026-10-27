-- CP-01 / 02 - OPS configuration: generator parameters, as-of control, levels and time targets.
-- PRD 2.1 (levels, bill codes, five-way time targets), 6.1 (calendar), 6.2 (generator).
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_ACOCO_BUILD;

-- Key/value generator and calendar parameters (one source of truth for gen/ and L2 CORE).
CREATE OR REPLACE TABLE ACOCO_DB.OPS.GEN_PARAMS (
  PARAM_NAME  VARCHAR NOT NULL PRIMARY KEY,
  PARAM_VALUE VARIANT NOT NULL,
  DESCRIPTION VARCHAR
) COMMENT = 'ACoCo generator and calendar parameters (PRD 6.1, 6.2)';

INSERT INTO ACOCO_DB.OPS.GEN_PARAMS (PARAM_NAME, PARAM_VALUE, DESCRIPTION)
SELECT $1, PARSE_JSON($2), $3 FROM VALUES
  ('seed',                    '20261001',        'Generator random seed'),
  ('window_start',            '"2021-10-01"',    'First day of the data window (FY22 P01)'),
  ('window_end',              '"2026-09-30"',    'Last day of the data window (FY26 P12)'),
  ('forward_end',             '"2027-03-31"',    'Assignments and opportunities generated up to this date'),
  ('fiscal_year_variant',     '"V9"',            'FISCALYEAR_V1 variant: Oct-Sep, FY named by end year; covers to FY2026, FY27 forward months generated in L2 CORE'),
  ('fiscal_year_start_month', '10',              'Fiscal year starts 1 October'),
  ('company_code',            '"USC1"',          'S/4 company code standing in for ACoCo (46 cost centres under hierarchy node 0USC1)'),
  ('controlling_area',        '"A000"',          'S/4 controlling area'),
  ('cost_center_hierarchy',   '"0101/A000/0001"','S/4 standard cost-centre hierarchy'),
  ('headcount_avg',           '1000',            'Average headcount'),
  ('voluntary_attrition_pct', '14',              'Annual voluntary attrition, with hiring to match'),
  ('projects',                '400',             'Projects over five years'),
  ('opportunities',           '800',             'Opportunities over five years'),
  ('assets',                  '150',             'Asset library size over five years'),
  ('overhead_pct',            '35',              'Delivery overhead surcharge on direct people cost'),
  ('bench_transition_pct',    '2',               'Accepted structural bench (people between assignments)'),
  ('admin_ceiling_pct',       '5',               'Admin share ceiling');

CREATE OR REPLACE TABLE ACOCO_DB.OPS.AS_OF_CONTROL (
  AS_OF_DATE DATE NOT NULL,
  NOTE       VARCHAR
) COMMENT = 'Demo "today"; read only through ACOCO_L2.CORE.VW_AS_OF';
INSERT INTO ACOCO_DB.OPS.AS_OF_CONTROL VALUES ('2026-10-01', 'Demo today: FY26 closed, FY27 day 1 (PRD 6.1)');

-- Levels, bill codes and rates (PRD 2.1). Bill rate/day = BILL_RATE_BASE + BILL_RATE_STEP * (bill code - (BILL_CODE_LO - 1)).
CREATE OR REPLACE TABLE ACOCO_DB.OPS.LEVEL (
  LEVEL           VARCHAR NOT NULL PRIMARY KEY,
  LEVEL_SORT      NUMBER  NOT NULL,
  BILL_CODE_LO    NUMBER  NOT NULL,
  BILL_CODE_HI    NUMBER  NOT NULL,
  COST_PER_DAY    NUMBER(10,2) NOT NULL,
  BILL_RATE_BASE  NUMBER(10,2) NOT NULL,
  BILL_RATE_STEP  NUMBER(10,2) NOT NULL,
  HEADCOUNT_SHARE NUMBER(5,3)  NOT NULL,
  PYRAMID_ROLE    VARCHAR
) COMMENT = 'ACoCo career levels with bill-code ranges and day rates (PRD 2.1)';
INSERT INTO ACOCO_DB.OPS.LEVEL VALUES
  ('Analyst',        1, 30, 39,  300,  600, 20, 0.500, 'Builds'),
  ('Consultant',     2, 40, 49,  500, 1000, 30, 0.270, 'Builds, leads small teams'),
  ('Manager',        3, 50, 59,  800, 1500, 40, 0.130, 'Runs a team'),
  ('Senior Manager', 4, 60, 69, 1000, 2000, 50, 0.070, 'Owns a Small project or work package; co-leads bids'),
  ('Principal',      5, 70, 79, 1300, 2500, 60, 0.030, 'Leads Medium/Large projects and bids; 6 are MDs');

-- Five-way time targets by level, share of available hours (PRD 2.1). Rows sum to 100.
CREATE OR REPLACE TABLE ACOCO_DB.OPS.GEN_PARAMS_TIME_TARGET (
  LEVEL    VARCHAR NOT NULL PRIMARY KEY,
  DELIVERY NUMBER(5,1) NOT NULL,
  BID      NUMBER(5,1) NOT NULL,
  LEARNING NUMBER(5,1) NOT NULL,
  ADMIN    NUMBER(5,1) NOT NULL,
  BENCH    NUMBER(5,1) NOT NULL,
  CONSTRAINT FK_TT_LEVEL FOREIGN KEY (LEVEL) REFERENCES ACOCO_DB.OPS.LEVEL (LEVEL)
) COMMENT = 'Target share of available hours by time category and level (PRD 2.1). Delivery = target billability';
INSERT INTO ACOCO_DB.OPS.GEN_PARAMS_TIME_TARGET VALUES
  ('Analyst',        80,  8, 7, 3, 2),
  ('Consultant',     78, 12, 5, 3, 2),
  ('Manager',        70, 20, 5, 3, 2),
  ('Senior Manager', 55, 35, 5, 3, 2),
  ('Principal',      45, 45, 5, 3, 2);
