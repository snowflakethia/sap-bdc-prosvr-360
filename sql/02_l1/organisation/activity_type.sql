CREATE OR REPLACE VIEW ACOCO_L1.ORGANISATION.ACTIVITY_TYPE
  COMMENT = 'L1 ORGANISATION.ACTIVITY_TYPE: one row per business object; sources BDC_CLD, SIMULATED. Generated from tools/l1_map.yml - do not edit.'
AS
  SELECT
    CAST(a."ControllingArea" AS VARCHAR) AS CONTROLLING_AREA,
    CAST(UPPER(TRIM(a."CostCtrActivityType")) AS VARCHAR) AS ACTIVITY_TYPE,
    CAST(TRIM(t."CostCtrActivityTypeName") AS VARCHAR) AS ACTIVITY_TYPE_NAME,
    CAST(a."CostCtrActivityTypeQtyUnit" AS VARCHAR) AS UNIT,
    CAST(a."AllocationCostElement" AS VARCHAR) AS COST_ELEMENT,
    CAST(NULL AS NUMBER(18,2)) AS PLANNED_PRICE,
    CAST(NULL AS VARCHAR) AS SENDER_COST_CENTER_ID,
    CAST(DECODE(a."CostCtrActivityType", 'ML-100', 'Analyst', 'ML-101', 'Consultant', 'ML-103', 'Manager', 'ML-104', 'Senior Manager', 'ML-105', 'Principal') AS VARCHAR) AS LEVEL,
    CAST(FALSE AS BOOLEAN) AS IS_AI_AGENT,
    'BDC_CLD' AS SOURCE_SYSTEM
  FROM COSTCENTERACTIVITYTYPE_V1."costcenteractivitytype"."costcenteractivitytype" a
  LEFT JOIN COSTCENTERACTIVITYTYPE_V1."costcenteractivitytype"."costcenteractivitytypetext" t
    ON t."ControllingArea" = a."ControllingArea" AND t."CostCtrActivityType" = a."CostCtrActivityType"
   AND t."ValidityEndDate" = a."ValidityEndDate" AND t."Language" = 'EN'
  WHERE a."ControllingArea" = 'A000' AND a."ValidityEndDate" = '9999-12-31'
  UNION ALL
  SELECT
    CAST(x."ControllingArea" AS VARCHAR) AS CONTROLLING_AREA,
    CAST(UPPER(TRIM(x."CostCtrActivityType")) AS VARCHAR) AS ACTIVITY_TYPE,
    CAST(x."CostCtrActivityTypeName" AS VARCHAR) AS ACTIVITY_TYPE_NAME,
    CAST(x."CostCtrActivityTypeQtyUnit" AS VARCHAR) AS UNIT,
    CAST(x."AllocationCostElement" AS VARCHAR) AS COST_ELEMENT,
    CAST(x."PlannedPrice" AS NUMBER(18,2)) AS PLANNED_PRICE,
    CAST(x."SenderCostCenter" AS VARCHAR) AS SENDER_COST_CENTER_ID,
    CAST(NULL AS VARCHAR) AS LEVEL,
    CAST(TRUE AS BOOLEAN) AS IS_AI_AGENT,
    'SIMULATED' AS SOURCE_SYSTEM
  FROM ACOCO_SIM.FINANCE_ACOCO.ACTIVITYTYPE_EXT x;
