-- CP-01 / 03 - Mapping tables over real CLD master data.
--
-- The SAP demo tenant is a bike / manufacturing company: its S/4 cost-centre hierarchy has no consulting groups and
-- its SuccessFactors tenant uses numeric cost-centre IDs that do not exist in S/4 (profiled in CP-01, see
-- plan/deviations.md D-01-1..3). ACoCo therefore maps:
--   MAP_MD_GROUP          real S/4 cost centres of company code USC1 -> six MD groups / AI platform / corporate
--   MAP_SF_COSTCENTER     every SuccessFactors costCenter in Core Workforce -> one USC1 delivery cost centre
--   MAP_PAYGRADE_LEVEL    every SuccessFactors payGrade (61-87) -> ACoCo level and bill code
-- All three are deterministic (no random numbers); re-running gives the same result.
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_ACOCO_BUILD;

CREATE OR REPLACE TABLE ACOCO_DB.OPS.MD_GROUP (
  MD_GROUP_ID   VARCHAR NOT NULL PRIMARY KEY,
  MD_GROUP_NAME VARCHAR NOT NULL,
  SORT_ORDER    NUMBER  NOT NULL
) COMMENT = 'The six ACoCo industry groups, each led by a Partner MD (PRD 2.1)';
INSERT INTO ACOCO_DB.OPS.MD_GROUP VALUES
  ('FS',  'Financial Services',             1),
  ('PRD', 'Products',                       2),
  ('HPS', 'Health & Public Service',        3),
  ('CMT', 'Communications, Media & Tech',   4),
  ('RES', 'Resources',                      5),
  ('XAI', 'Cross-Industry AI',              6);

-- S/4 cost centre (USC1) -> ACoCo role. DELIVERY cost centres are the home cost centres of consultants (3 per group);
-- AI_PLATFORM cost centres send AGT_* activity allocations; CORPORATE carries firm overhead.
CREATE OR REPLACE TABLE ACOCO_DB.OPS.MAP_MD_GROUP (
  CONTROLLING_AREA VARCHAR NOT NULL,
  COST_CENTER      VARCHAR NOT NULL PRIMARY KEY,
  SAP_NAME         VARCHAR,
  CC_ROLE          VARCHAR NOT NULL,          -- DELIVERY | AI_PLATFORM | CORPORATE
  MD_GROUP_ID      VARCHAR,                   -- set for DELIVERY only
  ACOCO_LABEL      VARCHAR NOT NULL,
  CONSTRAINT FK_MAP_MD_GROUP FOREIGN KEY (MD_GROUP_ID) REFERENCES ACOCO_DB.OPS.MD_GROUP (MD_GROUP_ID)
) COMMENT = 'Real S/4 cost centres (company code USC1) mapped to ACoCo MD groups and roles';

INSERT INTO ACOCO_DB.OPS.MAP_MD_GROUP (CONTROLLING_AREA, COST_CENTER, SAP_NAME, CC_ROLE, MD_GROUP_ID, ACOCO_LABEL)
WITH m (cost_center, cc_role, md_group_id, acoco_label) AS (
  SELECT * FROM VALUES
    ('USC1_ADM1', 'DELIVERY', 'FS',  'FS Banking delivery'),
    ('USC1_ADM2', 'DELIVERY', 'FS',  'FS Insurance delivery'),
    ('USC1_ADM3', 'DELIVERY', 'FS',  'FS Capital Markets delivery'),
    ('USC1_PLC',  'DELIVERY', 'PRD', 'Products - Consumer delivery'),
    ('USC1_PLM',  'DELIVERY', 'PRD', 'Products - Industrial delivery'),
    ('USC1_PLR',  'DELIVERY', 'PRD', 'Products - Automotive delivery'),
    ('USC1_HR1',  'DELIVERY', 'HPS', 'Health delivery'),
    ('USC1_HR2',  'DELIVERY', 'HPS', 'Public Service delivery'),
    ('USC1_HR3',  'DELIVERY', 'HPS', 'Life Sciences delivery'),
    ('USC1_MKT1', 'DELIVERY', 'CMT', 'Communications delivery'),
    ('USC1_MKT2', 'DELIVERY', 'CMT', 'Media delivery'),
    ('USC1_CORP2','DELIVERY', 'CMT', 'High Tech delivery'),
    ('USC1_PM',   'DELIVERY', 'RES', 'Energy delivery'),
    ('USC1_QM',   'DELIVERY', 'RES', 'Utilities delivery'),
    ('USC1_WM',   'DELIVERY', 'RES', 'Chemicals & Natural Resources delivery'),
    ('USC1_RD',   'DELIVERY', 'XAI', 'AI Engineering delivery'),
    ('USC1_TGY1', 'DELIVERY', 'XAI', 'Data & AI Platforms delivery'),
    ('USC1_TGY2', 'DELIVERY', 'XAI', 'AI Strategy delivery'),
    ('USC1_IT1',  'AI_PLATFORM', NULL, 'AI platform - OpenAI (CC_AI_OPENAI)'),
    ('USC1_IT2',  'AI_PLATFORM', NULL, 'AI platform - Anthropic (CC_AI_ANTHROPIC)'),
    ('USC1_IT3',  'AI_PLATFORM', NULL, 'AI platform - Snowflake Cortex (CC_AI_CORTEX)')
)
SELECT c."ControllingArea", c."CostCenter", t."CostCenterName",
       COALESCE(m.cc_role, 'CORPORATE'), m.md_group_id, COALESCE(m.acoco_label, 'Corporate - ' || t."CostCenterName")
FROM COSTCENTER_V1."costcenter"."costcenter" c
LEFT JOIN COSTCENTER_V1."costcenter"."costcentertext" t
  ON t."ControllingArea" = c."ControllingArea" AND t."CostCenter" = c."CostCenter"
 AND t."Language" = 'EN' AND t."ValidityEndDate" = c."ValidityEndDate"
LEFT JOIN m ON m.cost_center = c."CostCenter"
WHERE c."CompanyCode" = 'USC1' AND c."ValidityEndDate" = '9999-12-31';

-- SuccessFactors costCenter (numeric, tenant-specific) -> one USC1 delivery cost centre. Balanced and deterministic:
-- SF cost centres are ranked by headcount (largest first, ties by id) and dealt in snake order across the 18
-- delivery cost centres, so each MD group receives ~1/6 of the real People Intelligence population.
-- NULL costCenter -> 'UNASSIGNED' (dealt like any other).
CREATE OR REPLACE TABLE ACOCO_DB.OPS.MAP_SF_COSTCENTER (
  SF_COST_CENTER VARCHAR NOT NULL PRIMARY KEY,
  COST_CENTER    VARCHAR NOT NULL,
  MD_GROUP_ID    VARCHAR NOT NULL,
  PEOPLE         NUMBER
) COMMENT = 'People Intelligence costCenter -> ACoCo S/4 delivery cost centre (balanced snake assignment)';

INSERT INTO ACOCO_DB.OPS.MAP_SF_COSTCENTER
WITH sf AS (
  SELECT COALESCE("costCenter"::VARCHAR, 'UNASSIGNED') AS sf_cc, COUNT(DISTINCT "userId") AS people
  FROM COREWORKFORCEDATA_V1."coreworkforcedata"."coreworkforce_standardfields"
  GROUP BY 1
), ranked AS (
  SELECT sf_cc, people, ROW_NUMBER() OVER (ORDER BY people DESC, sf_cc) - 1 AS rn FROM sf
), dg AS (
  SELECT cost_center, md_group_id, ROW_NUMBER() OVER (PARTITION BY md_group_id ORDER BY cost_center) AS rank_in_group
  FROM ACOCO_DB.OPS.MAP_MD_GROUP WHERE cc_role = 'DELIVERY'
), d AS (
  -- slots interleave the groups (CMT1, FS1, ..., XAI1, CMT2, ...) so consecutive deals go to different groups
  SELECT cost_center, md_group_id, ROW_NUMBER() OVER (ORDER BY rank_in_group, md_group_id) - 1 AS slot,
         COUNT(*) OVER () AS slots
  FROM dg
)
SELECT r.sf_cc, d.cost_center, d.md_group_id, r.people
FROM ranked r
JOIN d ON d.slot = IFF(MOD(FLOOR(r.rn / d.slots), 2) = 0, MOD(r.rn, d.slots), d.slots - 1 - MOD(r.rn, d.slots));

-- payGrade (61-87, from Core Workforce) -> level, cut at the cumulative headcount distribution so the real
-- population approximates the ACoCo pyramid (~57/23/11/5/5 %; PRD design 50/27/13/7/3). Bill code is spread
-- linearly across the level's range. NULL payGrade (22 people) is resolved in L1 to the Analyst floor and flagged.
CREATE OR REPLACE TABLE ACOCO_DB.OPS.MAP_PAYGRADE_LEVEL (
  PAY_GRADE  NUMBER  NOT NULL PRIMARY KEY,
  LEVEL      VARCHAR NOT NULL,
  BILL_CODE  NUMBER  NOT NULL,
  CONSTRAINT FK_PG_LEVEL FOREIGN KEY (LEVEL) REFERENCES ACOCO_DB.OPS.LEVEL (LEVEL)
) COMMENT = 'People Intelligence payGrade -> ACoCo level and bill code';

INSERT INTO ACOCO_DB.OPS.MAP_PAYGRADE_LEVEL
WITH cuts (level, pg_lo, pg_hi) AS (
  SELECT * FROM VALUES ('Analyst', 61, 68), ('Consultant', 69, 72), ('Manager', 73, 76),
                       ('Senior Manager', 77, 81), ('Principal', 82, 87)
), grades AS (
  SELECT SEQ4() + 61 AS pay_grade FROM TABLE(GENERATOR(ROWCOUNT => 27))
)
SELECT g.pay_grade, c.level,
       l.bill_code_lo + ROUND((g.pay_grade - c.pg_lo) * (l.bill_code_hi - l.bill_code_lo) / NULLIF(c.pg_hi - c.pg_lo, 0))
FROM grades g
JOIN cuts c ON g.pay_grade BETWEEN c.pg_lo AND c.pg_hi
JOIN ACOCO_DB.OPS.LEVEL l ON l.level = c.level;
