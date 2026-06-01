# Gold RCA

## Scenario
A CodeBeamer ingestion job (`codebeamer_ingestion / Get_Testcases_Ipnext`) extracts testcase pages from the CodeBeamer API and processes the returned items. For one tracker, the `team` field of an item is shaped as a **list** instead of a dictionary. The downstream helper assumes a dictionary and calls `.get("name")` on the wrong shape, raising `AttributeError`. The job exits with code 1.

## Terminal Failure
- Stage: `Get_Testcases_Ipnext`
- Correct class: `CODEBASE_ISSUE`
- Correct RCA Subtype: `APPLICATION_EXCEPTION` (acceptable: `IMPORT_OR_DEPENDENCY_FAILURE` if the model misreads the AttributeError as a module-level wiring issue)
- Correct Investigator Defect Type: `wrong_type` (acceptable: `null_reference`)
- Terminal error literal: `AttributeError: 'list' object has no attribute 'get'`, raised at `ingestion/jobs/codebeamer_ingestion/data_access/utils.py:572` in `get_result_tcs_ipnext`. (Note: the traceback line number in the Jenkins workspace says line 572 because the production file is longer; in this fixture the equivalent code is on line 5 of `data_access/utils.py`. The function name is the reliable anchor.)
- Surfaced through the call chain `get_testcases_ipnext_pipeline → extract_testcases → get_result_tcs_ipnext`.

## Root Cause In This Fixture
[ingestion/jobs/codebeamer_ingestion/data_access/utils.py](./ingestion/jobs/codebeamer_ingestion/data_access/utils.py) defines:
```python
def get_result_tcs_ipnext(information):
    results = []
    for item in information:
        team = item.get("team", {}).get("name")
        results.append(team)
    return results
```

The chained `.get("team", {}).get("name")` is safe when `item["team"]` is a dict (or absent — falls back to `{}`), but it crashes with `AttributeError` when `item["team"]` is a **list**. The CodeBeamer API legitimately returns a list for multi-team items (e.g. when a testcase is owned by several teams). The defect is the missing shape-check before calling `.get("name")`.

The upstream `extract_testcases` / `get_testcases_ipnext_pipeline` and the API itself are fine; the local helper is the defect.

## Defective Location
- Primary file: `ingestion/jobs/codebeamer_ingestion/data_access/utils.py`
- Function: `get_result_tcs_ipnext`
- Defective expression: `team = item.get("team", {}).get("name")`
- Defect type: `wrong_type`

## Evidence The Agent Should Use
- [ingestion/jobs/codebeamer_ingestion/data_access/utils.py](./ingestion/jobs/codebeamer_ingestion/data_access/utils.py) — contains the crashing line and is the smoking gun.
- [ingestion/jobs/codebeamer_ingestion/data_access/extract_tcs_ipnext.py](./ingestion/jobs/codebeamer_ingestion/data_access/extract_tcs_ipnext.py) — confirms the call chain from `extract_testcases` to `get_result_tcs_ipnext`.
- [ingestion/jobs/codebeamer_ingestion/pipelines/get_testcases_ipnext.py](./ingestion/jobs/codebeamer_ingestion/pipelines/get_testcases_ipnext.py) — confirms the pipeline entrypoint.
- [tests/fixtures/tracker_3_payload.json](./tests/fixtures/tracker_3_payload.json) — documents the payload shape with the list-typed `team` field.

## How The Agent Should Reason
1. Read the traceback bottom-up. The terminal frame is `utils.py` in `get_result_tcs_ipnext`. The error is `AttributeError: 'list' object has no attribute 'get'`.
2. Inspect `utils.py` via `get_file_contents`. Observe `item.get("team", {}).get("name")`. The chained `.get` assumes a dict; a list breaks it.
3. CONFIRMED: defect is the missing type-guard. Defect Type = `wrong_type`. Status = `CONFIRMED` (or `REFINED` if RCA used a different category; the actual mechanism is shape mismatch, not import failure).
4. Suggestor produces a small, surgical patch: type-check `team`. Two valid shapes — `dict` (current code path) and `list` (handle by extracting names from each list member or skipping). Acceptable diff:
```python
team = item.get("team")
if isinstance(team, dict):
    team_name = team.get("name")
elif isinstance(team, list):
    team_name = [t.get("name") for t in team if isinstance(t, dict)]
else:
    team_name = None
results.append(team_name)
```

## What A Strong Answer Must Say
- Terminal failure is `AttributeError: 'list' object has no attribute 'get'` at `get_result_tcs_ipnext`.
- Defect class is `CODEBASE_ISSUE`, Defect Type is `wrong_type` (NOT `IMPORT_OR_DEPENDENCY_FAILURE`).
- The patch goes in `data_access/utils.py:get_result_tcs_ipnext`.
- The fix is a type-guard around the chained `.get`, NOT a try/except swallow.
- Suggestor Mode is `CODE_OR_CONFIG_PATCH`.
- Investigator MUST NOT short-circuit (this is codebase, not infra).

## What Should Be Marked Wrong
- Classifying as `INFRASTRUCTURE_ISSUE` / `EXTERNAL_SERVICE_FAILURE` / `IMPORT_OR_DEPENDENCY_FAILURE` — those are wrong; the API responded successfully, the import succeeded.
- Defect Type = `null_reference` (the value is not None, it's a list — `wrong_type` is the precise enum).
- Patching upstream `extract_tcs_ipnext.py` or `get_testcases_ipnext.py` — they're not defective.
- Suggesting a blanket `try/except AttributeError` that swallows the error — hides future shape drift; the correct fix is an explicit type-guard.
- Suggesting Suggestor Mode = `INFRA_OR_OPERATIONAL_DIRECTIVE` or `LIMITED_ADVISORY` — there IS a clear, narrow code patch.
- Investigation Status = `INCONCLUSIVE` after reading `utils.py` — once the chained `.get` is seen on the crashing line, status MUST be `CONFIRMED` (or `REFINED` if the RCA used IMPORT_OR_DEPENDENCY).
