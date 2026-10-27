CREATE OR REPLACE VIEW ACOCO_L1.ORGANISATION.COST_CENTER_HIERARCHY
  COMMENT = 'L1 ORGANISATION.COST_CENTER_HIERARCHY: one row per business object; sources BDC_CLD. Generated from tools/l1_map.yml - do not edit.'
AS
  SELECT
    CAST(n."CostCenterHierarchy" AS VARCHAR) AS HIERARCHY_ID,
    CAST(n."HierarchyNode" AS VARCHAR) AS NODE_ID,
    CAST(n."ParentNode" AS VARCHAR) AS PARENT_NODE_ID,
    CAST(TRY_TO_NUMBER(n."HierarchyNodeLevel"::VARCHAR) AS NUMBER) AS NODE_LEVEL,
    CAST(n."NodeType" AS VARCHAR) AS NODE_TYPE,
    CAST(NULLIF(UPPER(TRIM(n."CostCenter")), '') AS VARCHAR) AS COST_CENTER_ID,
    CAST(t."HierarchyNodeText" AS VARCHAR) AS NODE_TEXT,
    CAST(TRY_TO_DATE(n."ValidityStartDate"::VARCHAR) AS DATE) AS VALID_FROM,
    CAST(TRY_TO_DATE(n."ValidityEndDate"::VARCHAR) AS DATE) AS VALID_TO,
    'BDC_CLD' AS SOURCE_SYSTEM
  FROM COSTCENTER_V1."costcenter"."costcenterhierarchynode" n
  LEFT JOIN COSTCENTER_V1."costcenter"."costcenterhierarchynodetext" t
    ON t."CostCenterHierarchy" = n."CostCenterHierarchy" AND t."HierarchyNode" = n."HierarchyNode"
   AND t."ValidityEndDate" = n."ValidityEndDate" AND t."Language" = 'EN'
  WHERE n."CostCenterHierarchy" = '0101/A000/0001';
