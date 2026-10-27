CREATE OR REPLACE VIEW ACOCO_L1.ORGANISATION.COST_CENTER
  COMMENT = 'L1 ORGANISATION.COST_CENTER: one row per business object; sources BDC_CLD. Generated from tools/l1_map.yml - do not edit.'
AS
  SELECT
    CAST(c."ControllingArea" AS VARCHAR) AS CONTROLLING_AREA,
    CAST(UPPER(TRIM(c."CostCenter")) AS VARCHAR) AS COST_CENTER_ID,
    CAST(c."CompanyCode" AS VARCHAR) AS COMPANY_CODE,
    CAST(UPPER(TRIM(c."ProfitCenter")) AS VARCHAR) AS PROFIT_CENTER_ID,
    CAST(c."CostCenterCategory" AS VARCHAR) AS COST_CENTER_CATEGORY,
    CAST(t."CostCenterName" AS VARCHAR) AS COST_CENTER_NAME,
    CAST(m.CC_ROLE AS VARCHAR) AS CC_ROLE,
    CAST(m.MD_GROUP_ID AS VARCHAR) AS MD_GROUP_ID,
    CAST(m.ACOCO_LABEL AS VARCHAR) AS ACOCO_LABEL,
    CAST(TRY_TO_DATE(c."ValidityStartDate"::VARCHAR) AS DATE) AS VALID_FROM,
    CAST(TRY_TO_DATE(c."ValidityEndDate"::VARCHAR) AS DATE) AS VALID_TO,
    'BDC_CLD' AS SOURCE_SYSTEM
  FROM COSTCENTER_V1."costcenter"."costcenter" c
  LEFT JOIN COSTCENTER_V1."costcenter"."costcentertext" t
    ON t."ControllingArea" = c."ControllingArea" AND t."CostCenter" = c."CostCenter"
   AND t."Language" = 'EN' AND t."ValidityEndDate" = c."ValidityEndDate"
  LEFT JOIN ACOCO_DB.OPS.MAP_MD_GROUP m ON m.COST_CENTER = c."CostCenter"
  WHERE c."CompanyCode" = 'USC1';
