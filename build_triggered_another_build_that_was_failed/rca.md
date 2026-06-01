# Gold RCA

## Scenario
The upstream Jenkins pipeline `ipnext_validation_processing` succeeds at its own work (SQL Server task-id extraction completes; `352 tickets ... task ids are loaded successfully!`), then triggers the downstream Jenkins job `testguide_ipnext_testcases_extraction #6606`. The downstream build fails immediately and the upstream pipeline propagates the failure. The terminal log line is `Build testguide_ipnext_testcases_extraction #6606 completed: FAILURE` — but the actual defect lives in the downstream project's Python code, not the upstream orchestrator.

## Terminal Failure
- Failing unit: **downstream** job `testguide_ipnext_testcases_extraction` (build #6606)
- Upstream stage that surfaces it: `get_task_ids` (catchError → triggered downstream `build` step)
- Correct class: `CODEBASE_ISSUE`
- Correct RCA Subtype: `APPLICATION_EXCEPTION` (acceptable: `PIPELINE_OR_GROOVY_LOGIC` since the failing unit is a separately-scheduled downstream Jenkins build). NOT `EXTERNAL_SERVICE_FAILURE` — the downstream code lives inside this fixture, so the agent CAN and MUST inspect it.
- Correct Investigator Defect Type: `logic_error` (acceptable: `syntax_error` for an identifier typo)
- Terminal error visible in the upstream log: only the line `Build testguide_ipnext_testcases_extraction #6606 completed: FAILURE`. The downstream Python traceback is NOT in this log; it must be retrieved from the downstream project's code.

## Root Cause In This Fixture
The downstream script [testguide_ipnext_testcases_extraction/src/extract_testcases.py](./testguide_ipnext_testcases_extraction/src/extract_testcases.py) has a hard-coded typo in `run_extraction()`: it iterates over `tcket_ids` (missing letter), which is never defined anywhere in scope. The `try` block catches the resulting `NameError`, prints `CRITICAL ERROR: ...`, and calls `sys.exit(1)` — which makes the downstream Jenkinsfile fail and propagates `FAILURE` back upstream.

The upstream `main_get_task_ids.py` and its surrounding orchestration code are healthy. The defect is downstream and only downstream.

## Defective Location
- Primary file: `testguide_ipnext_testcases_extraction/src/extract_testcases.py`
- Function: `run_extraction`
- Defective symbol: `tcket_ids` (line 19) — undefined name; intended `ticket_ids` (or `sys.argv[1:]`)
- Defect type: `logic_error` (acceptable: `syntax_error`)

## Evidence The Agent Should Use
- [testguide_ipnext_testcases_extraction/Jenkinsfile](./testguide_ipnext_testcases_extraction/Jenkinsfile) — proves the downstream stage `Extract Testcases` runs `python extract_testcases.py`. So the failure must come from that script.
- [testguide_ipnext_testcases_extraction/src/extract_testcases.py](./testguide_ipnext_testcases_extraction/src/extract_testcases.py) — contains the `for t_id in tcket_ids:` typo and the `sys.exit(1)` that turns it into a build failure.
- [README_failure_map.md](./README_failure_map.md) — documents the fixture intent (downstream typo = root cause).
- The upstream `ingestion/jobs/jira_cc_ipnext_executions_extraction/main_get_task_ids.py` is healthy; mentioning it as "the failing module" is wrong.

## How The Agent Should Reason
1. Read the log end-to-end. Upstream `get_task_ids` stage logged success: `task ids are loaded successfully!`. The upstream Python ran cleanly. Therefore the upstream code is NOT the defect.
2. The terminal failure marker is the `build` step that scheduled `testguide_ipnext_testcases_extraction #6606` and got `FAILURE`. The downstream build is the failing unit.
3. The log does NOT contain the downstream traceback. The agent must inspect the **downstream** files (`testguide_ipnext_testcases_extraction/Jenkinsfile` then `src/extract_testcases.py`) in this repo to find the real defect.
4. Read `Jenkinsfile` to learn the downstream stage runs `python extract_testcases.py`. Read `extract_testcases.py` to find `tcket_ids` undefined in `run_extraction()`.
5. Conclude: typo on `tcket_ids` causes `NameError` → `sys.exit(1)` → downstream FAILURE → upstream propagation.

## What A Strong Answer Must Say
- The failing unit is the downstream job `testguide_ipnext_testcases_extraction`, NOT the upstream orchestrator.
- The upstream SQL/task-id stage succeeded; ignore it.
- The concrete defect is the undefined identifier `tcket_ids` in `run_extraction()` at `testguide_ipnext_testcases_extraction/src/extract_testcases.py:19`.
- The remediation is a one-character typo fix (`tcket_ids` → `ticket_ids`, with the variable populated from `sys.argv[1:]` or upstream payload, per the comment at line 17). Suggestor Mode = `CODE_OR_CONFIG_PATCH`, Defect Type = `logic_error`.
- Investigator must NOT `SKIPPED_INFRA` here — this is codebase, not infra.

## What Should Be Marked Wrong
- Classifying as `INFRASTRUCTURE_ISSUE` / `EXTERNAL_SERVICE_FAILURE` / `NETWORK_TIMEOUT_OR_CONNECTIVITY` and short-circuiting to `SKIPPED_INFRA` — wrong defect class, the downstream build IS internal to this repo fixture.
- Saying the upstream `main_get_task_ids.py` logic failed — the log clearly shows it succeeded.
- Recommending SQL Server / Redmine / external-service operator actions.
- Stopping at "downstream build failed" without naming the downstream file/function/symbol.
- Inventing a Jenkins infrastructure change (agent label, credentials) — irrelevant here.
- Returning Suggestor Mode = `INFRA_OR_OPERATIONAL_DIRECTIVE` — the fix is a one-line code patch in the downstream Python.
