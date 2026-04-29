# SQL Analysis Guide

## Purpose
This file documents:

- the SQL script needed to create the mock database used by the `Truncated_Column` scenario
- the read-only SQL tools the Investigator should have for secure database analysis

The investigator must be limited to `SELECT`-style access only.

## Mock Database Creation Script
Use this script to create the mock SQL Server database and tables for the `Truncated_Column` scenario.

```sql
IF DB_ID('TEST_TOOL_PRE_PROD_INFRA') IS NULL
BEGIN
    CREATE DATABASE TEST_TOOL_PRE_PROD_INFRA;
END
GO

USE TEST_TOOL_PRE_PROD_INFRA;
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
```

## Read-Only Investigator Tools
These are the general SQL analysis tools the Investigator should have access to.

### `list_tables(schema_name: str = "dbo")`
Purpose: discover which tables are available in the target schema.

Allowed query shape:
```sql
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
  AND TABLE_SCHEMA = @schema_name
ORDER BY TABLE_NAME;
```

### `describe_table(schema_name: str, table_name: str)`
Purpose: inspect authoritative column metadata from SQL Server.

Allowed query shape:
```sql
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = @schema_name
  AND TABLE_NAME = @table_name
ORDER BY ORDINAL_POSITION;
```

### `preview_rows(schema_name: str, table_name: str, top_n: int = 5)`
Purpose: inspect a few rows from a table for debugging.

Allowed query shape:
```sql
SELECT TOP (@top_n) *
FROM [schema_name].[table_name];
```

Security rule:
- `top_n` must be capped to a small number such as `5`, `10`, or `20`

### `run_safe_select(query: str)`
Purpose: allow flexible investigation for cases where fixed tools are not enough.

Security rules:
- must reject anything that is not a single `SELECT`
- must reject `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `EXEC`, `MERGE`, `TRUNCATE`
- must reject multiple statements
- should only allow queries against approved schemas or views

Examples of allowed usage:
```sql
SELECT
    COLUMN_NAME,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'raw_requirements_ipnext_codebeamer_daily';
```

```sql
SELECT
    tracker,
    tracker_id,
    assigned_to_length
FROM dbo.raw_requirements_ipnext_codebeamer_daily_debug;
```

### `compare_value_length_to_column(schema_name: str, table_name: str, column_name: str, debug_table_name: str)`
Purpose: compare produced payload length to the runtime column width.

Allowed query shape:
```sql
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
WHERE c.TABLE_SCHEMA = @schema_name
  AND c.TABLE_NAME = @table_name
  AND c.COLUMN_NAME = @column_name;
```

## Minimum SQL Workflow For This Scenario
For the `Truncated_Column` failure, the investigator should follow this order:

1. Use `describe_table("dbo", "raw_requirements_ipnext_codebeamer_daily")`
2. Confirm the live width of `assigned_to`
3. Query `raw_requirements_ipnext_codebeamer_daily_debug` to inspect `assigned_to_length`
4. Compare produced length against runtime column width
5. Combine that SQL evidence with the repo code in `extract_requirements_ipnext.py`

## Security Constraints
The investigator should never be allowed to:

- create, alter, or drop objects
- insert, update, or delete data
- execute stored procedures
- run multiple SQL statements in one call
- access non-approved databases or schemas

For production-like evaluation, the safest default is:

- metadata queries through `INFORMATION_SCHEMA`
- `SELECT TOP (N)` previews only
- a validated single-statement `SELECT` executor
