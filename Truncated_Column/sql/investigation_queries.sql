USE TEST_TOOL_PRE_PROD_INFRA;
GO

-- 1. Inspect the live runtime schema. This is the authoritative check.
SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'raw_requirements_ipnext_codebeamer_daily'
ORDER BY ORDINAL_POSITION;
GO

-- 2. Focus on the exact failing column from the Jenkins log.
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'raw_requirements_ipnext_codebeamer_daily'
  AND COLUMN_NAME = 'assigned_to';
GO

-- 3. Compare the ETL sample value length captured for debugging.
SELECT
    tracker,
    tracker_id,
    assigned_to_preview,
    assigned_to_length
FROM dbo.raw_requirements_ipnext_codebeamer_daily_debug;
GO

-- 4. One-row comparison showing why the insert fails.
SELECT
    c.COLUMN_NAME,
    c.CHARACTER_MAXIMUM_LENGTH AS runtime_column_length,
    d.assigned_to_length AS produced_value_length,
    CASE
        WHEN d.assigned_to_length > c.CHARACTER_MAXIMUM_LENGTH THEN 'WOULD_TRUNCATE'
        ELSE 'SAFE'
    END AS comparison_result
FROM INFORMATION_SCHEMA.COLUMNS c
CROSS JOIN dbo.raw_requirements_ipnext_codebeamer_daily_debug d
WHERE c.TABLE_NAME = 'raw_requirements_ipnext_codebeamer_daily'
  AND c.COLUMN_NAME = 'assigned_to';
GO
