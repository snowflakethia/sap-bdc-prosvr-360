CREATE OR REPLACE VIEW ACOCO_L1.TIME.PLANNED_WORKING_TIME
  COMMENT = 'L1 TIME.PLANNED_WORKING_TIME: one row per business object; sources BDC_CLD. Generated from tools/l1_map.yml - do not edit.'
AS
  SELECT
    CAST(p."id" AS VARCHAR) AS PLANNED_TIME_ID,
    CAST(p."assignmentId" AS VARCHAR) AS ASSIGNMENT_ID,
    CAST(m.USER_ID AS VARCHAR) AS PERSON_ID,
    CAST(p."startDate" AS DATE) AS START_DATE,
    CAST(p."endDate" AS DATE) AS END_DATE,
    CAST(p."plannedWorkingTime" AS NUMBER(6,2)) AS PLANNED_WORKING_HOURS,
    CAST(p."nonWorkingDay" AS BOOLEAN) AS IS_NON_WORKING_DAY,
    CAST(p."holiday" AS BOOLEAN) AS IS_HOLIDAY,
    'BDC_CLD' AS SOURCE_SYSTEM
  FROM WORKFORCEPLANNEDWORKINGTIME_V1."workforceplannedworkingtime"."plannedworkingtime" p
  LEFT JOIN ACOCO_DB.OPS.MAP_ASSIGNMENT_USER m ON m.ASSIGNMENT_ID = p."assignmentId";
