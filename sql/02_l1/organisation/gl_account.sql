CREATE OR REPLACE VIEW ACOCO_L1.ORGANISATION.GL_ACCOUNT
  COMMENT = 'L1 ORGANISATION.GL_ACCOUNT: one row per business object; sources BDC_CLD. Generated from tools/l1_map.yml - do not edit.'
AS
  SELECT
    CAST(g."ChartOfAccounts" AS VARCHAR) AS CHART_OF_ACCOUNTS,
    CAST(g."GLAccount" AS VARCHAR) AS GL_ACCOUNT,
    CAST(t."GLAccountName" AS VARCHAR) AS GL_ACCOUNT_NAME,
    CAST(g."GLAccountType" AS VARCHAR) AS GL_ACCOUNT_TYPE,
    CAST(g."GLAccountGroup" AS VARCHAR) AS GL_ACCOUNT_GROUP,
    CAST(g."IsProfitLossAccount"::VARCHAR IN ('true', 'X', '1') AS BOOLEAN) AS IS_PROFIT_LOSS,
    CAST(DECODE(g."GLAccount", '0041000000', 'REVENUE', '0012100000', 'RECEIVABLE', '0094233007', 'OVERHEAD', '0094308000', 'PEOPLE_PLAN_AGENT_COST', 'Z610500', 'PEOPLE_COST', 'Z610501', 'PEOPLE_COST', 'Z610503', 'PEOPLE_COST', 'Z610504', 'PEOPLE_COST', 'Z610505', 'PEOPLE_COST') AS VARCHAR) AS ACOCO_ROLE,
    'BDC_CLD' AS SOURCE_SYSTEM
  FROM GENERALLEDGERACCOUNT_V1."generalledgeraccount"."generalledgeraccount" g
  LEFT JOIN GENERALLEDGERACCOUNT_V1."generalledgeraccount"."generalledgeraccounttext" t
    ON t."ChartOfAccounts" = g."ChartOfAccounts" AND t."GLAccount" = g."GLAccount" AND t."Language" = 'EN'
  WHERE g."ChartOfAccounts" = 'YCOA';
