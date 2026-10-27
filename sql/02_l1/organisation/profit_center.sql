CREATE OR REPLACE VIEW ACOCO_L1.ORGANISATION.PROFIT_CENTER
  COMMENT = 'L1 ORGANISATION.PROFIT_CENTER: one row per business object; sources BDC_CLD. Generated from tools/l1_map.yml - do not edit.'
AS
  SELECT
    CAST(p."ControllingArea" AS VARCHAR) AS CONTROLLING_AREA,
    CAST(UPPER(TRIM(p."ProfitCenter")) AS VARCHAR) AS PROFIT_CENTER_ID,
    CAST(p."CompanyCode" AS VARCHAR) AS COMPANY_CODE,
    CAST(t."ProfitCenterName" AS VARCHAR) AS PROFIT_CENTER_NAME,
    CAST(p."Segment" AS VARCHAR) AS SEGMENT,
    CAST(TRY_TO_DATE(p."ValidityStartDate"::VARCHAR) AS DATE) AS VALID_FROM,
    CAST(TRY_TO_DATE(p."ValidityEndDate"::VARCHAR) AS DATE) AS VALID_TO,
    'BDC_CLD' AS SOURCE_SYSTEM
  FROM PROFITCENTER_V1."profitcenter"."profitcenter" p
  LEFT JOIN PROFITCENTER_V1."profitcenter"."profitcentertext" t
    ON t."ControllingArea" = p."ControllingArea" AND t."ProfitCenter" = p."ProfitCenter"
   AND t."ValidityEndDate" = p."ValidityEndDate" AND t."Language" = 'EN'
  WHERE p."ControllingArea" = 'A000' AND p."ProfitCenter" IN (SELECT "ProfitCenter" FROM COSTCENTER_V1."costcenter"."costcenter" WHERE "CompanyCode" = 'USC1');
