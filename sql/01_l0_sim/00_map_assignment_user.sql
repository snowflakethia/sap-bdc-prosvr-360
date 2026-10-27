-- CP-02 / 00 - Bridge between the two People Intelligence keys (inferred, deterministic).
--
-- In this tenant EMPLOYEEAVAILABILITY_V1 / WORKFORCEPLANNEDWORKINGTIME_V1 are keyed by a UUID assignmentId that
-- matches no key in COREWORKFORCEDATA_V1 (userId, personUuid, perPersonOid, jobDetailsId all tested: 0 matches;
-- plan/deviations.md D-02-2). Both carry department, jobCode, company and location, so on the reference day
-- 2025-07-01 people are paired 1:1 within each (department, jobCode, company, location) combination by rank of
-- id; the remaining assignments are paired with the remaining users by rank. Every pairing is labelled INFERRED.
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_ACOCO_BUILD;

CREATE OR REPLACE TABLE ACOCO_DB.OPS.MAP_ASSIGNMENT_USER (
  ASSIGNMENT_ID VARCHAR NOT NULL PRIMARY KEY,
  USER_ID       VARCHAR NOT NULL UNIQUE,
  MATCH_METHOD  VARCHAR NOT NULL          -- ATTRIBUTE_RANK | RESIDUAL_RANK
) COMMENT = 'INFERRED 1:1 bridge Employee Availability assignmentId -> Core Workforce userId (no shared key in tenant)';

INSERT INTO ACOCO_DB.OPS.MAP_ASSIGNMENT_USER
WITH e AS (
  SELECT "assignmentId" AS a, MAX("department") d, MAX("jobCode") j, MAX("company") c, MAX("location") l
  FROM EMPLOYEEAVAILABILITY_V1."employeeavailability"."employeeavailability"
  WHERE "workDate" = '2025-07-01' GROUP BY 1
), w AS (
  SELECT "userId" AS u, MAX("department") d, MAX("jobCode") j, MAX("company") c, MAX("location") l
  FROM COREWORKFORCEDATA_V1."coreworkforcedata"."coreworkforce_standardfields"
  WHERE "startDate" <= '2025-07-01' AND "endDate" >= '2025-07-01' GROUP BY 1
), er AS (
  SELECT a, d, j, c, l, ROW_NUMBER() OVER (PARTITION BY d, j, c, l ORDER BY a) rn FROM e
), wr AS (
  SELECT u, d, j, c, l, ROW_NUMBER() OVER (PARTITION BY d, j, c, l ORDER BY TRY_TO_NUMBER(u), u) rn FROM w
), m1 AS (
  SELECT er.a, wr.u FROM er JOIN wr
    ON er.d = wr.d AND er.j = wr.j AND er.c = wr.c AND er.l = wr.l AND er.rn = wr.rn
), ra AS (
  SELECT "assignmentId" a, ROW_NUMBER() OVER (ORDER BY "assignmentId") rn
  FROM (SELECT DISTINCT "assignmentId" FROM EMPLOYEEAVAILABILITY_V1."employeeavailability"."employeeavailability")
  WHERE "assignmentId" NOT IN (SELECT a FROM m1)
), ru AS (
  SELECT u, ROW_NUMBER() OVER (ORDER BY TRY_TO_NUMBER(u), u) rn
  FROM (SELECT DISTINCT "userId" u FROM COREWORKFORCEDATA_V1."coreworkforcedata"."coreworkforce_standardfields")
  WHERE u NOT IN (SELECT u FROM m1)
)
SELECT a, u, 'ATTRIBUTE_RANK' FROM m1
UNION ALL
SELECT ra.a, ru.u, 'RESIDUAL_RANK' FROM ra JOIN ru ON ra.rn = ru.rn;
