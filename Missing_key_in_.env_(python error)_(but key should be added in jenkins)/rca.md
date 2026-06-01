# Gold RCA

## Scenario
A Redmine ingestion job (`redmine_ingestion / redmine`) imports `ingestion/jobs/redmine_ingestion/__init__.py`, which transitively imports `config.py`. The module reads `KAP_API_KEY` from the process environment via `os.environ["KAP_API_KEY"]`. The variable is not present in the runtime environment of the Jenkins build, so the import fails with `KeyError: 'KAP_API_KEY'` and the pipeline aborts before any business logic runs.

The fixture name says "key should be added in jenkins" — that is exactly the conclusion the agent must reach: the key belongs in the **Jenkins pipeline credentials wiring**, not in a checked-in `.env` file and not as a default in code.

## Terminal Failure
- Stage: `redmine`
- Correct class: `CODEBASE_ISSUE` (specifically a credential-injection / pipeline-wiring contract that the operator side did not satisfy)
- Correct RCA Subtype: `ENV_VAR_MISCONFIGURATION` (acceptable: `MISSING_CREDENTIAL`, `PIPELINE_OR_GROOVY_LOGIC`)
- Correct Investigator Defect Type: `missing_key` (acceptable: `credential_issue`)
- Terminal error literal: `KeyError: 'KAP_API_KEY'`, raised at `config.py` on the line `KAP_API_KEY = os.environ["KAP_API_KEY"]`, surfaced through `runpy._get_module_details → __import__ → from .config import (...)` in `ingestion/jobs/redmine_ingestion/__init__.py`.
- Followed by `ERROR: script returned exit code 1` and `Setting overall build result to FAILURE`.

## Root Cause In This Fixture
[ingestion/jobs/redmine_ingestion/config.py](./ingestion/jobs/redmine_ingestion/config.py) reads `KAP_API_KEY` with unguarded `os.environ[KEY]`, which raises `KeyError` on absence. [.env.example](./.env.example) lists `KAP_API_KEY=<injected-by-jenkins>` — the operator convention is unambiguous: this key is meant to come from a Jenkins `withCredentials([string(credentialsId: 'kap_api_key', variable: 'KAP_API_KEY')]) { ... }` block (or equivalent `withEnv`).

The masked log line `Masking supported pattern matches of %db_pwd% or %redmine_pwd%` confirms that `withCredentials` injects `db_pwd` and `redmine_pwd`, but not `KAP_API_KEY` — direct evidence that the pipeline-side wiring is missing one credential.

The fix is operational + pipeline-wiring: add the `KAP_API_KEY` binding to the Jenkins `withCredentials` block surrounding the failing `bat` step. **No code change in `config.py` is the right answer** — silently defaulting a secret to `None` or an empty string would mask the misconfig and is a security anti-pattern.

## Defective Location
- Surface symptom file: `ingestion/jobs/redmine_ingestion/config.py` (unguarded `os.environ["KAP_API_KEY"]`)
- Actual defect: the pipeline-side `withCredentials` / `withEnv` wiring that should inject `KAP_API_KEY` is missing or incomplete (this fixture has no `Jenkinsfile` checked in).
- Defect type: `missing_key` (acceptable: `credential_issue`)

## Evidence The Agent Should Use
- [ingestion/jobs/redmine_ingestion/config.py](./ingestion/jobs/redmine_ingestion/config.py) — proves the unguarded `os.environ["KAP_API_KEY"]` access pattern (Signal 1).
- [.env.example](./.env.example) — proves the expected runtime convention `KAP_API_KEY=<injected-by-jenkins>` (Signal 2).
- The masked log line `Masking supported pattern matches of %db_pwd% or %redmine_pwd%` — direct evidence that other credentials are wired in but not `KAP_API_KEY`.
- The absence of a `Jenkinsfile` in this fixture is itself part of the evidence: the wiring artefact that should declare the `withCredentials` block is not checked in.

## How The Agent Should Reason
1. Read the traceback. The `KeyError: 'KAP_API_KEY'` is raised inside `os.environ.__getitem__` at the `KAP_API_KEY = os.environ["KAP_API_KEY"]` line of `config.py`, during package import — before any business logic runs. This fingerprints an environment-variable misconfiguration.
2. Apply the two-signal rule: `get_file_contents(config.py)` shows unguarded `os.environ[KEY]` (Signal 1); `get_file_contents(.env.example)` shows `KAP_API_KEY=<injected-by-jenkins>` and confirms the key is meant to come from Jenkins, not a local `.env` (Signal 2). Both signals hold → CONFIRMED, Defect Type = `missing_key`.
3. The Suggestor recommends adding `KAP_API_KEY` to the Jenkinsfile `withCredentials` block surrounding the failing step. The credential ID convention (per `.env.example`'s placeholder name) is `kap_api_key`. The recommendation is operational; no `config.py` patch is needed.

## What A Strong Answer Must Say
- Terminal failure is `KeyError: 'KAP_API_KEY'` during import of `config.py`.
- Two signals jointly CONFIRM: unguarded `os.environ` access (Signal 1) + `.env.example` says the key comes from Jenkins (Signal 2).
- Suggestor Mode = `INFRA_OR_OPERATIONAL_DIRECTIVE` (add `withCredentials([string(credentialsId: 'kap_api_key', variable: 'KAP_API_KEY')])` to the Jenkinsfile). `CODE_OR_CONFIG_PATCH` is acceptable ONLY if it targets a `Jenkinsfile` change.
- Defect Type MUST be `missing_key` (acceptable: `credential_issue`).
- The fix does NOT belong in `config.py` and does NOT belong in `.env.example`.

## What Should Be Marked Wrong
- Adding a default value or `os.environ.get("KAP_API_KEY", "")` in `config.py` — silently masks the missing credential and is a security regression.
- Suggesting the operator check in a `.env` file with the real key value — secrets MUST NOT be committed.
- Classifying as `INFRASTRUCTURE_ISSUE` and triggering `SKIPPED_INFRA` — the failure has a concrete codebase-wiring fix.
- Recommending `KAP_API_KEY` rotation as the fix — the key may exist correctly in the Jenkins credentials store; rotation does not fix the wiring.
- Stopping at `INCONCLUSIVE` after reading `config.py` and `.env.example` — the two signals jointly confirm the defect.
- Defect Type values like `wrong_type`, `null_reference`, `truncation`, `import_or_dependency_failure`, `logic_error` — the precise enum is `missing_key`.
