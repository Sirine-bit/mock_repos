IF DB_ID('TEST_TOOL_PRE_PROD_INFRA') IS NULL
BEGIN
    CREATE DATABASE TEST_TOOL_PRE_PROD_INFRA;
END
GO

USE TEST_TOOL_PRE_PROD_INFRA;
GO

IF SCHEMA_ID('dbo') IS NULL
BEGIN
    EXEC('CREATE SCHEMA dbo');
END
GO

IF OBJECT_ID('dbo.raw_requirements_ipnext_codebeamer_daily', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.raw_requirements_ipnext_codebeamer_daily;
END
GO

CREATE TABLE dbo.raw_requirements_ipnext_codebeamer_daily (
    tracker VARCHAR(120) NOT NULL,
    tracker_id BIGINT NOT NULL,
    assigned_to VARCHAR(80) NULL,
    status VARCHAR(50) NULL
);
GO

IF OBJECT_ID('dbo.raw_requirements_ipnext_codebeamer_daily_debug', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.raw_requirements_ipnext_codebeamer_daily_debug;
END
GO

CREATE TABLE dbo.raw_requirements_ipnext_codebeamer_daily_debug (
    tracker VARCHAR(120) NOT NULL,
    tracker_id BIGINT NOT NULL,
    assigned_to_preview VARCHAR(255) NOT NULL,
    assigned_to_length INT NOT NULL,
    captured_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

INSERT INTO dbo.raw_requirements_ipnext_codebeamer_daily_debug (
    tracker,
    tracker_id,
    assigned_to_preview,
    assigned_to_length
)
VALUES (
    'A05_System Requirements',
    34158092,
    'q477433, q560470, qxz4zdz, qxz57it, qxz6j0f, qxz44kv, qxz4z31, qxz5rqi, qxz5bgs, qxz6ine, q549798, q551230',
    LEN('q477433, q560470, qxz4zdz, qxz57it, qxz6j0f, qxz44kv, qxz4z31, qxz5rqi, qxz5bgs, qxz6ine, q549798, q551230')
);
GO

CREATE OR ALTER VIEW dbo.vw_requirements_ipnext_runtime_schema AS
SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'raw_requirements_ipnext_codebeamer_daily';
GO

SELECT * FROM dbo.vw_requirements_ipnext_runtime_schema;
GO
