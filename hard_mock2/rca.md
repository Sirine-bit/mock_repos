# Gold RCA

## Scenario
The log includes an API timeout during extraction, but it recovers on retry. The real terminal failure happens later during SQL staging insert.

## Terminal Failure
- Stage: `Process_And_Cleanse`
- Correct class: `CODEBASE_ISSUE`
- Terminal error: SQL Server cannot convert `'UNKNOWN_CLIENT'` to `INT`

## Root Cause In This Fixture
In [src/transformation/process_sales.py](./src/transformation/process_sales.py), `normalize_client_ids()` replaces missing `client_id` values with the sentinel string `UNKNOWN_CLIENT`. That transformed dataframe is then inserted unchanged by [src/infra/database.py](./src/infra/database.py) into a table whose schema defines `client_id` as `INT` in [sql/staging/STG_SALES_DAILY.sql](./sql/staging/STG_SALES_DAILY.sql).

## Defective Location
- Primary file: `src/transformation/process_sales.py`
- Function: `normalize_client_ids`
- Secondary confirmation files: `src/infra/database.py`, `sql/staging/STG_SALES_DAILY.sql`
- Defect type: `wrong_type`

## Evidence The Agent Should Use
- [src/transformation/process_sales.py](./src/transformation/process_sales.py) shows the string sentinel assignment.
- [src/infra/database.py](./src/infra/database.py) shows the dataframe is inserted without type guard/casting.
- [sql/staging/STG_SALES_DAILY.sql](./sql/staging/STG_SALES_DAILY.sql) proves `client_id` is an integer column.

## How The Agent Should Reason
1. Ignore the earlier Salesforce timeout because the log shows the retry succeeds.
2. Start from the SQL conversion traceback.
3. Inspect the transformation that prepares `client_id`.
4. Cross-check the database schema to confirm type incompatibility.
5. Conclude the true defect is the sentinel value strategy in transformation code.

## What A Strong Answer Must Say
- The failing value is `UNKNOWN_CLIENT`.
- The incompatible target column is `STG_SALES_DAILY.client_id`.
- The origin of the bad value is `normalize_client_ids()` in `process_sales.py`.

## What Should Be Marked Wrong
- Treating the recovered API timeout as terminal.
- Blaming only `to_sql()` without identifying where the bad value was created.
- Calling this a pure database outage.
