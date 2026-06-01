# Gold RCA

## Scenario
A Redmine ingestion job (`redmine_ingestion / redmine`) imports `ingestion/jobs/redmine_ingestion/__init__.py`, which transitively imports `config.py`. The module reads `KAP_API_KEY` from the process environment via `os.environ["KAP_API_KEY"]`. The variable is not present in the runtime environment, so the import fails with `KeyError: 'KAP_API_KEY'` and the pipeline aborts before any business logic runs.

## Terminal Failure
- Stage: `redmine`
- Correct class: `CODEBASE_ISSUE` (specifically a credential-injection / pipeline-wiring contract that the operator side did not satisfy)
- Correct RCA Subtype: `ENV_VAR_MISCONFIGURATION` (acceptable: `MISSING_CREDENTIAL`, `PIPELINE_OR_GROOVY_LOGIC`)
- Correct Investigator Defect Type: `missing_key` (acceptable: `credential_issue`)
- Terminal error literal: `KeyError: 'KAP_API_KEY'`, raised at `config.py` on the line `KAP_API_KEY = os.environ["KAP_API_KEY"]`, surfaced through `runpy._get_module_details → __import__ → from .config import (...)` in `ingestion/jobs/redmine_ingestion/__init__.py`.
- Followed by `ERROR: script returned exit code 1` and `Setting overall build result to FAILURE`.

## Root Cause In This Fixture
[ingestion/jobs/redmine_ingestion/config.py](./ingestion/jobs/redmine_ingestion/config.py) reads `KAP_API_KEY` with unguarded `os.environ[KEY]`, which raises `KeyError` on absence. The expected runtime contract (documented by `.env.example` listing `KAP_API_KEY=<injected-by-jenkins>`) is that **the Jenkins pipeline injects this key at runtime via `withCredentials([string(credentialsId: 'kap_api_key', variable: 'KAP_API_KEY')]) { ... }`** (or equivalent `withEnv`). In this fixture, no `Jenkinsfile` exists in the repo — that absence is itself the wiring defect: the pipeline configuration that should inject `KAP_API_KEY` is missing from this fixture's repo. The credential exists on the Jenkins side but is not wired into the build's environment.

The fix is operational + pipeline-wiring: add or correct the Jenkins `withCredentials` block so `KAP_API_KEY` is injected before the Python entrypoint runs. **No code change in `config.py` is the right answer** — silently defaulting a secret to `None` or an empty string would mask the misconfig and is a security anti-pattern.

## Defective Location
- Surface symptom file: `ingestion/jobs/redmine_ingestion/config.py` (unguarded `os.environ["KAP_API_KEY"]`)
- Actual defect: the pipeline-side `withCredentials` / `withEnv` wiring that should inject `KAP_API_KEY` is missing or incorrect (no `Jenkinsfile` in this fixture's repo).
- Defect type: `missing_key` (acceptable: `credential_issue` since the key name implies a secret/token)

## Evidence The Agent Should Use
- [ingestion/jobs/redmine_ingestion/config.py](./ingestion/jobs/redmine_ingestion/config.py) — proves the unguarded `os.environ["KAP_API_KEY"]` access pattern.
- [.env.example](./.env.example) — proves the expected runtime convention: `KAP_API_KEY=<injected-by-jenkins>` (operator wires it via Jenkins, NOT via a checked-in `.env`).
- The masked log line `Masking supported pattern matches of %db_pwd% or %redmine_pwd%` confirms `withCredentials` injects `db_pwd` and `redmine_pwd` but NOT `KAP_API_KEY` — direct evidence of the wiring gap.
- The absence of a `Jenkinsfile` in this fixture is itself part of the evidence: the wiring artefact that should declare `withCredentials([string(credentialsId: 'kap_api_key', variable: 'KAP_API_KEY')])` is missing.

## How The Agent Should Reason
1. Read the traceback. The `KeyError: 'KAP_API_KEY'` is raised inside `os.environ.__getitem__` at the `KAP_API_KEY = os.environ["KAP_API_KEY"]` line of `config.py` during the package import — before any user code logic. That fingerprints an environment-variable misconfiguration.
2. Fetch `config.py` to confirm the unguarded `os.environ[KEY]` pattern.
3. Fetch `.env.example` to read the operator convention. `KAP_API_KEY=<injected-by-jenkins>` proves the key is meant to come from Jenkins credentials, not a checked-in `.env`.
4. CONFIRMED, Defect Type = `missing_key`. The fix is to add a `withCredentials([string(credentialsId: 'kap_api_key', variable: 'KAP_API_KEY')]) { ... }` wrapper around the failing `bat` step in the Jenkinsfile (which is itself missing from this fixture; the strong answer points this out).

## What A Strong Answer Must Say
- Terminal failure is `KeyError: 'KAP_API_KEY'` during import of `config.py`.
- The key is meant to be injected at the pipeline level (per `.env.example`) — NOT defaulted in code.
- Suggestor Mode = `INFRA_OR_OPERATIONAL_DIRECTIVE` (the fix is a Jenkinsfile wiring change + a Jenkins credentials store entry, not a repo code patch). `CODE_OR_CONFIG_PATCH` is acceptable ONLY if the patch targets a `Jenkinsfile` and adds the `withCredentials` block; it is NOT acceptable for `config.py`.
- Defect Type MUST be `missing_key` (acceptable: `credential_issue`).
- Investigator MUST cite both `config.py` AND `.env.example` to anchor the two-signal evidence.

## What Should Be Marked Wrong
- Adding a default value or `os.environ.get("KAP_API_KEY", "")` in `config.py` — silently masks the missing credential and is a security regression.
- Suggesting the operator check in a `.env` file with the real key value — secrets MUST NOT be committed.
- Classifying as `INFRASTRUCTURE_ISSUE` and triggering `SKIPPED_INFRA` — the failure has a concrete codebase / wiring fix.
- Recommending the agent's `KAP_API_KEY` rotation as the fix — the key may exist correctly in Jenkins, but it's not being injected; rotation does not fix the wiring.
- Stopping at `INCONCLUSIVE` after reading `config.py` and `.env.example` — the two signals jointly confirm the defect.
- Defect Type values like `wrong_type`, `null_reference`, `truncation`, `import_or_dependency_failure`, `logic_error` — those are wrong; the precise enum is `missing_key`.
