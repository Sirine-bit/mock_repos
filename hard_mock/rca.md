# Gold RCA

## Scenario
A financial ETL job runs `python -m ingestion.jobs.financial.validate_schema` against a transformed pandas DataFrame and compares it to the strict schema declared for the SQL target `PRD_FIN_TRANSACTIONS`. The DataFrame is missing two mandatory columns and the validator raises `DataValidationError`, ending the pipeline. An earlier SQL connectivity timeout in the same log recovers successfully and is noise, NOT the root cause.

## Terminal Failure
- Stage: `Data_Quality_Validation`
- Correct class: `CODEBASE_ISSUE`
- Correct RCA Subtype: `DATA_VALIDATION_FAILURE` (acceptable: `APPLICATION_EXCEPTION` since the failure surfaces as a `DataValidationError`)
- Correct Investigator Defect Type: `logic_error` (acceptable: `schema_mismatch`)
- Terminal error literal: `ingestion.core.exceptions.DataValidationError: Missing expected mandatory columns: ['transaction_hash', 'currency_code']`, followed by `ERROR: script returned exit code 1` and `Setting overall build result to FAILURE`.

## Root Cause In This Fixture
[ingestion/jobs/financial/validators/schema.py](./ingestion/jobs/financial/validators/schema.py) declares `REQUIRED_COLUMNS["PRD_FIN_TRANSACTIONS"]` = `["transaction_id", "account_id", "transaction_hash", "currency_code", "amount", "booking_date"]`. The validator compares this list against `df.columns` and raises on any missing column.

[ingestion/jobs/financial/transform.py](./ingestion/jobs/financial/transform.py) builds the DataFrame and returns `df[["transaction_id", "account_id", "currency", "amount", "booking_date"]]`. Two defects:
1. The column is named `currency` but the target schema expects `currency_code` — a rename / mapping defect.
2. `transaction_hash` is never produced — the transform omits it entirely.

The validator at `validators/schema.py` is **correctly enforcing the contract**. The defect is upstream in `transform.py`: the transformation does not produce the agreed target schema. The fix is to rename `currency` → `currency_code` and derive `transaction_hash` (e.g. `hash(transaction_id + booking_date)` or whichever deterministic recipe the contract requires).

## Defective Location
- Primary file: `ingestion/jobs/financial/transform.py`
- Function: `build_financial_dataframe`
- Defective expression: `return df[["transaction_id", "account_id", "currency", "amount", "booking_date"]]`
- Confirmation surface (not the defect): `ingestion/jobs/financial/validators/schema.py` (defines `REQUIRED_COLUMNS`)
- Defect type: `logic_error` (acceptable: `schema_mismatch`, `data_validation_failure`)

## Evidence The Agent Should Use
- [ingestion/jobs/financial/validate_schema.py](./ingestion/jobs/financial/validate_schema.py) — entrypoint that wires `build_financial_dataframe()` through `enforce_strict_schema`.
- [ingestion/jobs/financial/validators/schema.py](./ingestion/jobs/financial/validators/schema.py) — defines `REQUIRED_COLUMNS["PRD_FIN_TRANSACTIONS"]` (the contract) AND raises `DataValidationError`.
- [ingestion/jobs/financial/transform.py](./ingestion/jobs/financial/transform.py) — produces the dataframe and proves it omits `transaction_hash` and uses `currency` instead of `currency_code`.
- [config/target_tables.yaml](./config/target_tables.yaml) — supplementary contract documentation for the target table.

## How The Agent Should Reason
1. Read the traceback. The terminal frame is `enforce_strict_schema` at `validators/schema.py`, raising `DataValidationError: Missing expected mandatory columns: ['transaction_hash', 'currency_code']`. Note the exact missing column names.
2. The earlier `db_ping` SQL timeout in the same log recovers (the build proceeds past it). It is a red herring. Do not treat it as the root cause.
3. Fetch `validators/schema.py` to read `REQUIRED_COLUMNS`. Confirm `transaction_hash` and `currency_code` are mandatory.
4. Fetch `transform.py` to read `build_financial_dataframe`. Observe:
   - It selects `currency` (not `currency_code`) → rename defect.
   - It never adds a `transaction_hash` column → missing column.
5. CONFIRMED. Defect Type = `logic_error` (or `schema_mismatch`). The defect lives in `transform.py`, the validator is correct.
6. Suggestor patches `transform.py`: rename `currency` to `currency_code` (or add an alias mapping) AND derive `transaction_hash` from a stable subset of the row.

## What A Strong Answer Must Say
- Terminal failure is `DataValidationError: Missing expected mandatory columns: ['transaction_hash', 'currency_code']` raised by the validator in `validators/schema.py`, but the validator is CORRECT.
- The defect is in `transform.py:build_financial_dataframe`: the produced DataFrame omits `transaction_hash` and exposes `currency` instead of `currency_code`.
- The earlier `db_ping` SQL timeout is a red herring; it recovers.
- Suggestor Mode = `CODE_OR_CONFIG_PATCH`, patch targets `transform.py`.
- Defect Type MUST be `logic_error` (acceptable: `schema_mismatch`).
- Investigator MUST inspect BOTH `validators/schema.py` (for the contract) AND `transform.py` (for the producer); citing only one is insufficient.

## What Should Be Marked Wrong
- Diagnosing the root cause as the recovered `db_ping` SQL timeout.
- Patching `validators/schema.py` to relax the contract — that hides the actual defect, regressing data quality guarantees.
- Defect Type = `null_reference`, `missing_key`, `truncation`, `wrong_type`, `import_or_dependency_failure`, `pipeline_wiring_issue`, `infrastructure_failure`. None of those apply; the precise enum is `logic_error` (or `schema_mismatch`).
- Suggestor Mode = `INFRA_OR_OPERATIONAL_DIRECTIVE` or `LIMITED_ADVISORY` — there is a clear, narrow code patch in `transform.py`.
- Stopping at `INCONCLUSIVE` after reading only `validators/schema.py`; the answer is incomplete without inspecting `transform.py`.
- Chasing `.env.example` or any credential / withCredentials path — this is a data-pipeline logic defect, not an env-var misconfig. (The investigator's two-signal env-var rule MUST NOT apply here.)
