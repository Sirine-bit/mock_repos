# Gold RCA

## Scenario
This fixture contains two notable signals: an earlier SQL connectivity timeout that recovers, and a later schema validation error that actually terminates the pipeline.

## Terminal Failure
- Stage: `Data_Quality_Validation`
- Correct class: `CODEBASE_ISSUE`
- Terminal error: missing mandatory columns `transaction_hash` and `currency_code`

## Root Cause In This Fixture
The transformed dataframe built in [ingestion/jobs/financial/transform.py](./ingestion/jobs/financial/transform.py) does not produce the required target schema:
- it omits `transaction_hash`
- it keeps `currency` instead of the required `currency_code`

The validator in [ingestion/jobs/financial/validators/schema.py](./ingestion/jobs/financial/validators/schema.py) is correctly surfacing that mismatch.

## Defective Location
- Primary file: `ingestion/jobs/financial/transform.py`
- Secondary confirmation file: `ingestion/jobs/financial/validators/schema.py`
- Defect type: `logic_error` / schema-mapping defect

## Evidence The Agent Should Use
- [ingestion/jobs/financial/validate_schema.py](./ingestion/jobs/financial/validate_schema.py) shows the validation entry point.
- [ingestion/jobs/financial/validators/schema.py](./ingestion/jobs/financial/validators/schema.py) shows the expected columns and raised exception.
- [ingestion/jobs/financial/transform.py](./ingestion/jobs/financial/transform.py) proves the upstream dataframe is missing the required fields.
- [config/target_tables.yaml](./config/target_tables.yaml) confirms the target table contract.

## How The Agent Should Reason
1. Ignore the earlier DB timeout because the log shows it recovers successfully.
2. Start from the validation traceback, then inspect the validator.
3. Confirm the validator is enforcing a real schema contract.
4. Trace one step upstream to the transformation output and verify the missing/renamed columns.
5. Conclude that the real defect is in transformation/schema mapping, not transient infrastructure.

## What A Strong Answer Must Say
- The terminal failure is the schema mismatch, not the recovered connection timeout.
- `transform.py` fails to provide `transaction_hash` and `currency_code`.
- `schema.py` is the confirmation point, not necessarily the true origin of the defect.

## What Should Be Marked Wrong
- Choosing the recovered DB ping timeout as the root cause.
- Saying the validator is wrong without checking the declared target schema.
- Ignoring the upstream transformation file.
