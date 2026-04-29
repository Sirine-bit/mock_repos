# Gold RCA

## Scenario
The upstream pipeline succeeds in its own repo work, then triggers the downstream Jenkins job `testguide_ipnext_testcases_extraction`, which is the build that actually fails.

## Terminal Failure
- Failing unit: downstream job `testguide_ipnext_testcases_extraction`
- Correct class: `CODEBASE_ISSUE`
- Important nuance: the upstream repo is not the true failing code path; the failure lives in the downstream project nested inside this fixture.

## Root Cause In This Fixture
The downstream script [testguide_ipnext_testcases_extraction/src/extract_testcases.py](./testguide_ipnext_testcases_extraction/src/extract_testcases.py) contains a typo in `run_extraction()`: it iterates over `tcket_ids`, which is undefined, causing a `NameError` and immediate process exit.

## Defective Location
- File: `testguide_ipnext_testcases_extraction/src/extract_testcases.py`
- Function: `run_extraction`
- Defect type: `logic_error`

## Evidence The Agent Should Use
- [testguide_ipnext_testcases_extraction/Jenkinsfile](./testguide_ipnext_testcases_extraction/Jenkinsfile) shows what the downstream job executes.
- [testguide_ipnext_testcases_extraction/src/extract_testcases.py](./testguide_ipnext_testcases_extraction/src/extract_testcases.py) contains the actual crash site.
- [README_failure_map.md](./README_failure_map.md) documents the intended downstream failure mapping.

## How The Agent Should Reason
1. Ignore the successful upstream SQL/task-id stage.
2. Treat the downstream build failure as the terminal failure on the critical path.
3. Inspect the downstream folder, not just the upstream repo root.
4. Read the downstream `Jenkinsfile` to find the executed script.
5. Extract or read `run_extraction()` and confirm the undefined `tcket_ids` symbol.

## What A Strong Answer Must Say
- The failure is caused by the downstream project, not the upstream orchestration step.
- The concrete defect is the undefined variable `tcket_ids` in `run_extraction()`.
- The defective file is `testguide_ipnext_testcases_extraction/src/extract_testcases.py`.

## What Should Be Marked Wrong
- Claiming the upstream `main_get_task_ids.py` logic failed.
- Calling this a pure Jenkins infrastructure issue.
- Stopping at "downstream build failed" without naming the downstream defective file/function.
