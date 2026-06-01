# Gold RCA

## Scenario
A `github_tcs_ingestion` Jenkins job completes the initial workspace + SCM checkout fine (the upstream `data-flow-hub` clone succeeds), then runs `python ... get_ipnext_jc_tcs.py` which programmatically clones a *second* repository — `https://cc-github.clientgroup.net/swh/safe-posix-platform.git` — via `git.Repo.clone_from` from `git_connector.py`. That second clone gets `HTTP/2 401 www-authenticate: Basic realm="GitHub"` repeatedly and fails with `fatal: Authentication failed`, propagating as `git.exc.GitCommandError: Cmd('git') failed due to: exit code(128)`. The pipeline aborts.

## Terminal Failure
- Stage: `Deploy` (downstream Python `get_ipnext_jc_pipeline`)
- Correct class: `CODEBASE_ISSUE` (specifically a credential-wiring contract that the operator side did not satisfy). Acceptable alternative read: `INFRASTRUCTURE_ISSUE / MISSING_CREDENTIAL` — both must converge on the same operator action.
- Correct RCA Subtype: `MISSING_CREDENTIAL` (acceptable: `PIPELINE_OR_GROOVY_LOGIC` if the wiring-mistake hypothesis is favoured)
- Correct Investigator Defect Type: `credential_issue` (acceptable: `pipeline_wiring_issue`)
- Terminal error literal:
  - `fatal: Authentication failed for 'https://cc-github.clientgroup.net/swh/safe-posix-platform.git/'`
  - `git.exc.GitCommandError: Cmd('git') failed due to: exit code(128)`
  - Preceded by repeated `<= Recv header: HTTP/2 401` and `www-authenticate: Basic realm="GitHub"` from the GitHub Enterprise server (`cc-github.clientgroup.net`).
- The Basic-auth attempts use `user 'xpadtech'` — the user identity is reaching the server, but credentials are rejected. This is auth-layer failure, NOT transport / DNS / TLS.

## Root Cause In This Fixture
The job's `Jenkinsfile` wires five credentials into the build via `withCredentials([...])`:
- `GITHUB_SWBK_CREDENTIALS → GITHUB_SWBK_TOKEN`
- `GITLAB_CARIAD_CREDENTIALS → GITLAB_CARIAD_TOKEN`
- `CC_GITHUB_IPNEXT_CREDENTIALS → GITHUB_IPNEXT_TOKEN`
- `MSSQL → MSSQL_CREDS`
- `GITLAB_CREDENTIALS → GITLAB_TOKEN`

The downstream Python `git_connector.py` calls `git.Repo.clone_from(...)` against `cc-github.clientgroup.net`. That host is the GitHub Enterprise instance the `CC_GITHUB_IPNEXT_CREDENTIALS / GITHUB_IPNEXT_TOKEN` binding is meant for. Either:
1. The token in `CC_GITHUB_IPNEXT_CREDENTIALS` has expired / been revoked on the GitHub Enterprise side.
2. The token is valid but the **user identity** `xpadtech` no longer has access to `swh/safe-posix-platform`.
3. The Python code constructs the clone URL with the wrong env var (e.g. it embeds `GITHUB_SWBK_TOKEN` instead of `GITHUB_IPNEXT_TOKEN`).

The log alone cannot disambiguate (1) vs (2) vs (3). The strong answer flags all three and points the operator at: GitHub Enterprise (rotate / re-grant), Jenkins credentials store (verify `CC_GITHUB_IPNEXT_CREDENTIALS` value), AND the downstream code (`git_connector.py`) to confirm which env var it consumes — that file is NOT in this fixture's repo so the code-side check is documented as a follow-up.

## Defective Location
- Pipeline-wiring surface: `Jenkinsfile` (defines the `withCredentials` bindings).
- Code-side surface (NOT in this fixture, named in the traceback): `ingestion/jobs/github_tcs_ingestion/infra/git_connector.py:94` (`git.Repo.clone_from(...)`). The investigator must NOT pretend it inspected this file when the repo does not contain it.
- Authentication target: `cc-github.clientgroup.net` (GitHub Enterprise instance, user `xpadtech`).
- Defect type: `credential_issue` (acceptable: `pipeline_wiring_issue`)

## Evidence The Agent Should Use
- [Jenkinsfile](./Jenkinsfile) — proves the five `withCredentials` bindings and that `CC_GITHUB_IPNEXT_CREDENTIALS → GITHUB_IPNEXT_TOKEN` is the binding intended for `cc-github.clientgroup.net`.
- Log lines `Recv header: HTTP/2 401`, `www-authenticate: Basic realm="GitHub"`, `Server auth using Basic with user 'xpadtech'` — direct proof the GitHub server rejected the supplied credentials.
- Log line `fatal: Authentication failed for 'https://cc-github.clientgroup.net/swh/safe-posix-platform.git/'` — terminal error literal.
- The python traceback names `git_connector.py:94` and `git_connector.py:193` (`handle_repository_checkout → clone_git_repo → git.Repo.clone_from`). The agent should note that file path but must NOT fetch it from this fixture (the repo only contains `Jenkinsfile` + `README.md` + `rca.md`); attempting to read it returns 404 and that is acceptable.

## How The Agent Should Reason
1. The transport-layer is healthy: TLS handshake completed, the server replied with `HTTP/2 401 www-authenticate`. So NETWORK_TIMEOUT_OR_CONNECTIVITY is wrong.
2. The 401 + `user 'xpadtech'` proves the request reached auth and was rejected. This isolates the defect to credential validity OR credential wiring.
3. Fetch `Jenkinsfile`. Confirm `CC_GITHUB_IPNEXT_CREDENTIALS → GITHUB_IPNEXT_TOKEN` is wired. Note the failing host (`cc-github.clientgroup.net`) matches that credential's name pattern.
4. Without the downstream `git_connector.py` (not in this fixture), the agent cannot confirm WHICH env var the code consumes. It should explicitly say so, list the three candidate root causes (token expired / token has no access / code uses wrong env var), and produce an operator directive.

## What A Strong Answer Must Say
- The transport is fine; the failure is at the auth layer (`HTTP/2 401`, `Basic realm="GitHub"`, user `xpadtech`).
- Defect class is `CODEBASE_ISSUE` / `MISSING_CREDENTIAL` (or `INFRASTRUCTURE_ISSUE / MISSING_CREDENTIAL` — either is acceptable provided the operator action set is the same).
- Defect Type MUST be `credential_issue` (acceptable: `pipeline_wiring_issue`).
- The credential binding to verify is `CC_GITHUB_IPNEXT_CREDENTIALS → GITHUB_IPNEXT_TOKEN` from the Jenkinsfile.
- The strong answer flags BOTH the token-validity hypothesis AND the code-side hypothesis (`git_connector.py` may consume the wrong env var) — the log cannot disambiguate.
- Suggestor Mode = `INFRA_OR_OPERATIONAL_DIRECTIVE`: rotate / re-grant the GitHub Enterprise token for user `xpadtech` against `swh/safe-posix-platform`, AND verify the Python code uses `GITHUB_IPNEXT_TOKEN` (not a different env var).

## What Should Be Marked Wrong
- Classifying as `NETWORK_TIMEOUT_OR_CONNECTIVITY` / `EXTERNAL_SERVICE_FAILURE`. The remote responded with structured headers — the network and TLS are healthy.
- Treating the `warning: could not open '/c/git.log' for tracing: No such file or directory` lines as the defect — they are git tracing noise, NOT the cause.
- Defect Type values like `null_reference`, `missing_key`, `truncation`, `wrong_type`, `logic_error`, `import_or_dependency_failure`, `infrastructure_failure`. The precise enum is `credential_issue`.
- Pretending to have read `git_connector.py` when it is NOT in this fixture's repo. The investigator must document the 404 instead of fabricating its contents.
- Suggesting a patch to `Jenkinsfile` that adds yet another `withCredentials` binding — adding bindings does not fix an invalid token.
- Suggesting LIMITED_ADVISORY when a clear operator action exists (rotate / re-grant the GitHub Enterprise credential).
- SKIPPED_INFRA short-circuit: this fixture has codebase-side evidence (the Jenkinsfile binding) that must be read; skipping investigation entirely loses the credential-binding name.
