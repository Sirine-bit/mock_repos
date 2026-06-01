# Gold RCA

## Scenario
The `redmine_ingestion` Jenkins job extracts issues from the company Redmine server. The Python `redminelib` client calls `GET /users/current.json` to validate credentials, and the HTTPS handshake fails because the Redmine server's TLS certificate is expired. The pipeline aborts before any data ingestion happens.

## Terminal Failure
- Stage: `Deploy` (final python `ingest_redmine_training_issues`)
- Correct class: `INFRASTRUCTURE_ISSUE`
- Correct RCA Subtype: `EXTERNAL_SERVICE_FAILURE` (acceptable: `NETWORK_TIMEOUT_OR_CONNECTIVITY` — both belong to the P0 short-circuit allow-list)
- Correct Investigator Defect Type: `infrastructure_failure`
- Terminal error: `ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1007)` against `https://redmine.intranet.company.tn:443/users/current.json`, surfaced through `requests.exceptions.SSLError` and finally re-raised as `Exception("unable to connect to redmine server", ...)`.

## Root Cause In This Fixture
The TLS certificate served by the Redmine server (`redmine.intranet.company.tn`) is expired. Python's default certificate chain validation rejects the handshake, so every `redminelib` HTTP call fails before any business logic runs. **No code, schema, or Jenkins-side change in this repository can fix this.** This is an external-service / PKI incident: the Redmine operator must renew or rotate the server certificate (or the corporate CA bundle must be updated).

## Defective Location
- Primary defect: **infrastructure — expired TLS cert on the Redmine endpoint**, not any file in this repository.
- Defect type: `infrastructure_failure`
- Suggested operator scope: Redmine server admin / corporate PKI / Jenkins agent trust store (only if a private CA was rotated).

## Evidence The Agent Should Use
This scenario is intentionally infra-class. The repository for this fixture contains only `Jenkinsfile` + `README.md` (no Python under `data_flow_hub/`), so deep code inspection is impossible AND unnecessary.

Expected path:
1. Parser surfaces the SSL traceback as the terminal failure (NOT the earlier `git rev-parse --resolve-git-dir` warning, which is a non-fatal Jenkins-side check that prints `fatal: not a gitdir` but does not stop the pipeline).
2. RCA classifies `Primary Class = INFRASTRUCTURE_ISSUE`, `Subtype = EXTERNAL_SERVICE_FAILURE`.
3. Investigator short-circuits (`Status = SKIPPED_INFRA`, 0 tool calls, 0 rounds).
4. Suggestor emits `INFRA_OR_OPERATIONAL_DIRECTIVE`.

## How The Agent Should Reason
1. Read the LAST traceback in the console output. It is `requests.exceptions.SSLError` → `Exception("unable to connect to redmine server", ...)` raised by `connect_to_redmine()`. That is the terminal failure.
2. The earlier `git rev-parse --resolve-git-dir ... fatal: not a gitdir` is **noise from Jenkins's git-client pre-check**; the pipeline recovers and proceeds. Do NOT treat it as the root cause.
3. SSL cert expiry on a third-party HTTPS endpoint is by construction an infrastructure / PKI failure. Skip code inspection.
4. Suggestor recommends operational actions: renew the Redmine TLS certificate, confirm the corporate CA bundle on the Jenkins agent, re-run the pipeline once the cert chain validates.

## What A Strong Answer Must Say
- Terminal failure is the SSL cert expiry on `redmine.intranet.company.tn`, not the noisy `fatal: not a gitdir` line earlier in the log.
- The defect class is `INFRASTRUCTURE_ISSUE` and the subtype is `EXTERNAL_SERVICE_FAILURE`.
- The Investigator must `SKIPPED_INFRA` with 0 tool calls and 0 rounds.
- The Suggestor must be `INFRA_OR_OPERATIONAL_DIRECTIVE` with `Change Type = operational_action` and `Confidence ≤ medium` (no code evidence was gathered).
- Mention concretely: rotate / renew the Redmine server certificate; verify CA chain trusted by the Jenkins agent; re-run after the cert is valid.

## What Should Be Marked Wrong
- Treating the earlier `fatal: not a gitdir` line as the root cause — that's a transient git pre-check, not the terminal failure.
- Recommending a code patch in this repo (no Python file exists here; nothing to patch).
- Defect Type = `null_reference`, `missing_key`, `truncation`, `wrong_type`, etc. The only correct value is `infrastructure_failure`.
- Suggesting credential rotation as the fix — credentials reach the server fine; the TLS handshake fails BEFORE auth.
- Returning `INCONCLUSIVE` or `CONFIRMED` instead of the canonical `SKIPPED_INFRA` stub for this defect class.
- LIMITED_ADVISORY: a clear operational directive exists, issue it.
