# Gold RCA

## Scenario
A CodeBeamer ingestion job extracts requirements pages and bulk-inserts them into a SQL Server staging table via SQLAlchemy + pyodbc. The job runs cleanly through extraction and only fails when the final `df.to_sql(... if_exists='append')` is issued — SQL Server rejects the batch insert because a VARCHAR column is too narrow for the value being written.

## Terminal Failure
- Stage: `Get_Requirements_Ipnext`
- Correct class: `CODEBASE_ISSUE`
- Correct RCA Subtype: `SQL_SCHEMA_MISMATCH` (acceptable: `SQL_QUERY_FAILURE`)
- Correct Investigator Defect Type: `truncation` (acceptable: `schema_mismatch`)
- Terminal error: `pyodbc.ProgrammingError 42000 / 2628` — "String or binary data would be truncated in table `TEST_TOOL_PRE_PROD_INFRA.dbo.raw_requirements_ipnext_codebeamer_daily`, column `assigned_to`. Truncated value: `'q477433, q560470, qxz4zdz, qxz57it, qxz6j0f, qxz44kv, qxz4z31, qxz5rqi, qxz5bgs, qxz6ine, q549798, q'`"

## Root Cause In This Fixture
The destination column `dbo.raw_requirements_ipnext_codebeamer_daily.assigned_to` is declared `VARCHAR(80)`, but the ingestion job concatenates the comma-separated list of CodeBeamer reviewer IDs into this column and the resulting string overflows 80 characters as soon as a requirement has more than ~7 reviewers. The defect is in the table contract, not in the Python code: the Python code is delivering the agreed payload shape, and the SQL Server schema is the side that needs to widen.

The cited `db_connector.insert_dataframe_into_table` and the calling pipeline `get_requirements_ipnext_pipeline` are correctly forwarding the dataframe — they are NOT the defect.

## Defective Location
- Primary defect: SQL Server table `dbo.raw_requirements_ipnext_codebeamer_daily`, column `assigned_to` (declared `VARCHAR(80)`)
- Confirmation surface: `ingestion/jobs/codebeamer_ingestion/infra/db_connector.py` (`insert_dataframe_into_table`) — the call site that triggers the truncation, NOT the source of the bug
- Defect type: `truncation` (acceptable: `schema_mismatch`)

## Evidence The Agent Should Use
- `get_schema(table_name_list='raw_requirements_ipnext_codebeamer_daily')` → must return the `assigned_to VARCHAR(80)` definition. The width IS the smoking gun.
- `execute_select('SELECT MAX(LEN(assigned_to)) FROM raw_requirements_ipnext_codebeamer_daily')` → sizes the actual reviewer-list length so the remediation can size the new column safely (e.g. measured + 2× safety margin). Failures here (empty table in dev) are tolerable as long as the agent says so explicitly in §[7] and the Suggestor degrades to a wider-by-default `VARCHAR(1000)` / `NVARCHAR(MAX)`.
- `get_file_contents` on the pipeline + `db_connector` files is fine for context but does NOT alone confirm the defect — only the schema width does.

## How The Agent Should Reason
1. Read the traceback: the failure is in the SQL Server insert, not in the Python data extraction.
2. Use `get_schema` to confirm the destination column type. Match it against the truncated value cited in the error.
3. If `get_schema` confirms a width that the cited truncated value already exceeds → mark `Status = CONFIRMED`, `Defect Type = truncation`. Do NOT downgrade to INCONCLUSIVE just because the live failure was not reproduced — the schema width is sufficient evidence.
4. Run ONE `execute_select MAX(LEN(...))` to size the remediation, and surface the measured value (or the lack thereof) in §[5] and §[7].
5. Recommend an `ALTER TABLE ... ALTER COLUMN assigned_to ...` to widen the column, preserving collation and nullability from `get_schema`. Default to measured + safety margin; if no measurement was possible, fall back to `VARCHAR(MAX)` or `NVARCHAR(MAX)` and call this out in `§[8] Limitations`.

## What A Strong Answer Must Say
- The terminal failure is a destination-side schema constraint, not a Python defect.
- The defective object is `dbo.raw_requirements_ipnext_codebeamer_daily.assigned_to`, declared `VARCHAR(80)`.
- The remediation is a narrow `ALTER COLUMN` widening, preserving collation (`French_CI_AS`) and nullability.
- Mention whether the actual maximum source-data length was measured; if not, justify the `(MAX)` fallback and flag it in `§[8] Limitations`.

## What Should Be Marked Wrong
- Calling this a `null_reference`, `wrong_type`, `missing_key`, or `import_or_dependency_failure` — the enum value MUST be `truncation` (or `schema_mismatch`).
- Patching `db_connector.py` or `get_requirements_ipnext.py` to truncate / silently drop values — that hides the contract mismatch, not fixes it.
- Recommending `VARCHAR(MAX)` without a `§[8] Limitations` note about indexing/storage trade-offs and without first attempting `MAX(LEN(...))`.
- Concluding INCONCLUSIVE after only running `get_schema` — the schema width already confirms the defect.
