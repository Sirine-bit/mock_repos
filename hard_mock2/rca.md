# Gold RCA

## Scenario
A sales ETL job runs `python -m src.transformation.process_sales`, normalises Salesforce opportunity rows, and bulk-inserts them into the SQL Server staging table `STG_SALES_DAILY`. While normalising, the code replaces a `None` `client_id` with the literal string `'UNKNOWN_CLIENT'`. The downstream `INSERT` then sends that string into a column declared `INT NOT NULL`, and the SQL Server driver rejects the conversion. The build fails on chunk 16.

## Terminal Failure
- Stage: `Process_And_Cleanse`
- Correct class: `CODEBASE_ISSUE`
- Correct RCA Subtype: `SQL_QUERY_FAILURE` (acceptable: `APPLICATION_EXCEPTION`, `SQL_SCHEMA_MISMATCH`). The driver raises at INSERT execution, so the RCA enum value sits on the SQL side, not the data-validation side.
- Correct Investigator Defect Type: `wrong_type` (acceptable: `schema_mismatch`)
- Terminal error literal: `pyodbc.DataError: ('22018', "[22018] [Microsoft][ODBC SQL Server Driver][SQL Server]Conversion failed when converting the varchar value 'UNKNOWN_CLIENT' to data type int. (245) (SQLExecDirectW)")`, wrapped by `sqlalchemy.exc.DataError` with `[SQL: INSERT INTO STG_SALES_DAILY (opportunity_id, amount, client_id, close_date) VALUES (?, ?, ?, ?)][parameters: ('006D000000rGjT1', 1500.00, 'UNKNOWN_CLIENT', '2026-03-25')]`. Followed by `ERROR: script returned exit code 1`.

## Root Cause In This Fixture
[src/transformation/process_sales.py](./src/transformation/process_sales.py) defines:
```python
def normalize_client_ids(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized["client_id"] = normalized["client_id"].fillna("UNKNOWN_CLIENT")
    return normalized
```

The `fillna("UNKNOWN_CLIENT")` substitutes a STRING into a column whose target schema type is `INT NOT NULL` (per [sql/staging/STG_SALES_DAILY.sql](./sql/staging/STG_SALES_DAILY.sql) line 4: `client_id INT NOT NULL`). The SQL Server driver cannot convert `'UNKNOWN_CLIENT'` to int, so the bulk insert fails with SQLSTATE `22018`.

The defect is the chosen sentinel value: a non-numeric string cannot satisfy an INT NOT NULL contract. Either:
- The sentinel must be numeric (e.g. `0` or `-1`), AND the downstream consumers must agree that this value means "unknown".
- The schema must change `client_id` to `NULL`-able or `VARCHAR`, and the code can keep the string sentinel.
- The row must be dropped / quarantined when `client_id` is `None`.

[src/infra/database.py](./src/infra/database.py) uses `df.to_sql(..., if_exists="append")` and is correct (it forwards what it was given); the defect is upstream in `normalize_client_ids`.

## Defective Location
- Primary file: `src/transformation/process_sales.py`
- Function: `normalize_client_ids`
- Defective expression: `normalized["client_id"] = normalized["client_id"].fillna("UNKNOWN_CLIENT")`
- Schema confirmation file: `sql/staging/STG_SALES_DAILY.sql` (defines `client_id INT NOT NULL`)
- Defect type: `wrong_type` (acceptable: `schema_mismatch`)

## Evidence The Agent Should Use
- [src/transformation/process_sales.py](./src/transformation/process_sales.py) — proves `fillna("UNKNOWN_CLIENT")` substitutes a string into `client_id`.
- [sql/staging/STG_SALES_DAILY.sql](./sql/staging/STG_SALES_DAILY.sql) — declares `client_id INT NOT NULL`. The contract mismatch between this column type and the string sentinel is the smoking gun.
- [src/infra/database.py](./src/infra/database.py) — proves the insert path is generic `df.to_sql(..., append)`; it is NOT the defect.
- The driver's error literal (column `client_id`, value `'UNKNOWN_CLIENT'`, target type `int`) — directly names the column and the bad value.

`get_schema` against a real running DB instance is OPTIONAL here because the schema is checked in at `sql/staging/STG_SALES_DAILY.sql`. The agent should read the SQL file first; only call `get_schema` if the file is missing or if it wants to confirm the deployed schema matches.

## How The Agent Should Reason
1. Read the traceback. The terminal frame is `database.py / to_sql`, but the actual driver error names the column (`client_id`), the failing value (`'UNKNOWN_CLIENT'`), and the target type (`int`). That trio already isolates the defect to the upstream producer of that column.
2. Inspect `process_sales.py` to find what populates `client_id`. `normalize_client_ids` substitutes `'UNKNOWN_CLIENT'` via `fillna`. Defect identified.
3. Confirm the schema contract by reading `sql/staging/STG_SALES_DAILY.sql`. Line 4 declares `client_id INT NOT NULL`. The mismatch (string vs int) is confirmed.
4. Status = `CONFIRMED`, Defect Type = `wrong_type`. Suggestor patches `normalize_client_ids` to either use a numeric sentinel (e.g. `-1`), drop the row, OR coordinates with the schema owner to widen `client_id` and drop NOT NULL.

## What A Strong Answer Must Say
- Terminal failure is SQLSTATE `22018`: the driver cannot convert the string `'UNKNOWN_CLIENT'` to `INT`.
- The defect is in `src/transformation/process_sales.py:normalize_client_ids`, line `fillna("UNKNOWN_CLIENT")`.
- The schema contract `client_id INT NOT NULL` (per `sql/staging/STG_SALES_DAILY.sql`) is the canonical authority.
- The fix is a code patch in `process_sales.py` (numeric sentinel / drop / split into NULL-able schema), NOT a `to_sql` parameter tweak.
- Defect Type MUST be `wrong_type` (acceptable: `schema_mismatch`).
- Suggestor Mode = `CODE_OR_CONFIG_PATCH`.
- Investigator MUST cite BOTH `process_sales.py` AND `sql/staging/STG_SALES_DAILY.sql`.

## What Should Be Marked Wrong
- Diagnosing as `INFRASTRUCTURE_ISSUE` / `NETWORK_TIMEOUT_OR_CONNECTIVITY` / `EXTERNAL_SERVICE_FAILURE` — the DB is reachable; the insert reached SQL Server, which rejected the value at execution time.
- Patching `database.py` — it's generic and correct.
- Suggesting `try/except DataError` around the insert — masks the data-quality defect without fixing it.
- Defect Type values like `null_reference`, `missing_key`, `truncation`, `pipeline_wiring_issue`, `import_or_dependency_failure`. The precise enum is `wrong_type`.
- Chasing `.env.example` or any credential / `withCredentials` path — this is a data-type defect, not an env-var misconfig. The investigator's two-signal env-var rule MUST NOT apply here.
- Stopping at `INCONCLUSIVE` after only running `get_schema` against an unavailable DB — the source-of-truth schema is checked in at `sql/staging/STG_SALES_DAILY.sql`; read THAT instead.
- Suggestor Mode = `INFRA_OR_OPERATIONAL_DIRECTIVE` or `LIMITED_ADVISORY` — a clear, narrow code patch is available.
