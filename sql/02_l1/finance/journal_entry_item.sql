CREATE OR REPLACE VIEW ACOCO_L1.FINANCE.JOURNAL_ENTRY_ITEM
  COMMENT = 'L1 FINANCE.JOURNAL_ENTRY_ITEM: one row per business object; sources BDC_CLD, SIMULATED. Generated from tools/l1_map.yml - do not edit.'
AS
  SELECT
    CAST(j."CompanyCode" AS VARCHAR) AS COMPANY_CODE,
    CAST(TRY_TO_NUMBER(j."FiscalYear"::VARCHAR) AS NUMBER) AS FISCAL_YEAR,
    CAST(j."AccountingDocument" AS VARCHAR) AS ACCOUNTING_DOCUMENT,
    CAST(j."AccountingDocumentItem" AS VARCHAR) AS DOCUMENT_ITEM,
    CAST(TRY_TO_NUMBER(j."FiscalPeriod"::VARCHAR) AS NUMBER) AS FISCAL_PERIOD,
    CAST(TRY_TO_DATE(j."PostingDate"::VARCHAR) AS DATE) AS POSTING_DATE,
    CAST(j."AccountingDocumentType" AS VARCHAR) AS DOCUMENT_TYPE,
    CAST(j."GLAccount" AS VARCHAR) AS GL_ACCOUNT,
    CAST(NULLIF(UPPER(TRIM(j."CostCenter")), '') AS VARCHAR) AS COST_CENTER_ID,
    CAST(NULLIF(UPPER(TRIM(j."ProfitCenter")), '') AS VARCHAR) AS PROFIT_CENTER_ID,
    CAST(j."WBSElementInternalID"::VARCHAR AS VARCHAR) AS WBS_ID,
    CAST(NULLIF(j."OrderID"::VARCHAR, '') AS VARCHAR) AS ORDER_ID,
    CAST(NULLIF(UPPER(TRIM(j."CostCtrActivityType")), '') AS VARCHAR) AS ACTIVITY_TYPE,
    CAST(NULLIF(j."PersonnelNumber"::VARCHAR, '') AS VARCHAR) AS PERSON_ID,
    CAST(NULLIF(j."Customer"::VARCHAR, '') AS VARCHAR) AS CUSTOMER_ID,
    CAST(j."AmountInCompanyCodeCurrency" AS NUMBER(18,2)) AS AMOUNT,
    CAST(j."CompanyCodeCurrency" AS VARCHAR) AS CURRENCY,
    CAST(j."Quantity" AS NUMBER(18,3)) AS QUANTITY,
    CAST(j."BaseUnit" AS VARCHAR) AS UNIT,
    CAST(j."DebitCreditCode" AS VARCHAR) AS DEBIT_CREDIT,
    CAST(NULL AS VARCHAR) AS BILLABLE_CONTROL,
    CAST(h."ReverseDocument" IS NOT NULL AS BOOLEAN) AS IS_REVERSAL_RELATED,
    'BDC_CLD' AS SOURCE_SYSTEM
  FROM ENTRYVIEWJOURNALENTRY_V1."entryviewjournalentry"."operationalacctgdocitem" j
  LEFT JOIN JOURNALENTRYHEADER_V1."journalentryheader"."journalentry" h
    ON h."CompanyCode" = j."CompanyCode" AND h."FiscalYear" = j."FiscalYear" AND h."AccountingDocument" = j."AccountingDocument"
  WHERE j."CompanyCode" = 'USC1' AND (j."WBSElementInternalID"::VARCHAR LIKE 'P-%' OR j."OrderID"::VARCHAR LIKE 'IO%')
  UNION ALL
  SELECT
    CAST(j."CompanyCode" AS VARCHAR) AS COMPANY_CODE,
    CAST(TRY_TO_NUMBER(j."FiscalYear") AS NUMBER) AS FISCAL_YEAR,
    CAST(j."AccountingDocument" AS VARCHAR) AS ACCOUNTING_DOCUMENT,
    CAST(j."AccountingDocumentItem" AS VARCHAR) AS DOCUMENT_ITEM,
    CAST(TRY_TO_NUMBER(j."FiscalPeriod") AS NUMBER) AS FISCAL_PERIOD,
    CAST(j."PostingDate" AS DATE) AS POSTING_DATE,
    CAST(j."AccountingDocumentType" AS VARCHAR) AS DOCUMENT_TYPE,
    CAST(j."GLAccount" AS VARCHAR) AS GL_ACCOUNT,
    CAST(UPPER(TRIM(j."CostCenter")) AS VARCHAR) AS COST_CENTER_ID,
    CAST(UPPER(TRIM(j."ProfitCenter")) AS VARCHAR) AS PROFIT_CENTER_ID,
    CAST(j."WBSElement" AS VARCHAR) AS WBS_ID,
    CAST(j."OrderID" AS VARCHAR) AS ORDER_ID,
    CAST(UPPER(TRIM(j."CostCtrActivityType")) AS VARCHAR) AS ACTIVITY_TYPE,
    CAST(j."PersonnelNumber" AS VARCHAR) AS PERSON_ID,
    CAST(j."Customer"::VARCHAR AS VARCHAR) AS CUSTOMER_ID,
    CAST(j."AmountInCompanyCodeCurrency" AS NUMBER(18,2)) AS AMOUNT,
    CAST(j."CompanyCodeCurrency" AS VARCHAR) AS CURRENCY,
    CAST(j."Quantity" AS NUMBER(18,3)) AS QUANTITY,
    CAST(j."BaseUnit" AS VARCHAR) AS UNIT,
    CAST(j."DebitCreditCode" AS VARCHAR) AS DEBIT_CREDIT,
    CAST(j."ZZ_BILLABLE_CONTROL" AS VARCHAR) AS BILLABLE_CONTROL,
    CAST(COALESCE(h."IsReversal", FALSE) OR COALESCE(h."IsReversed", FALSE) AS BOOLEAN) AS IS_REVERSAL_RELATED,
    'SIMULATED' AS SOURCE_SYSTEM
  FROM ACOCO_SIM.FINANCE_ACOCO.OPERATIONALACCTGDOCITEM j
  LEFT JOIN ACOCO_SIM.FINANCE_ACOCO.JOURNALENTRY h
    ON h."CompanyCode" = j."CompanyCode" AND h."FiscalYear" = j."FiscalYear" AND h."AccountingDocument" = j."AccountingDocument";
