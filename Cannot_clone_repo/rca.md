# Gold RCA

## Scenario
A Jenkins job (`testguide_ipnext_testcases_extraction` / agent label `Rivian2`) tries to clone the corporate Git repo `https://git.technica-engineering.net/data/data-flow-hub` during the `Deploy` stage. The TLS handshake and HTTP request succeed (the GitLab server responds), but the GitLab server itself returns a not-found / not-authorised response. After the configured retries the pipeline aborts. Every downstream stage is skipped "due to earlier failure(s)".

## Terminal Failure
- Stage: `Deploy`
- Correct class: `CODEBASE_ISSUE` (specifically pipeline-wiring / SCM-config defect)
- Correct RCA Subtype: `PIPELINE_OR_GROOVY_LOGIC` (acceptable: `MISSING_CREDENTIAL` if the token-permission hypothesis is favoured). The RCA prompt's enum has no distinct "SCM misconfiguration" value; the wiring lives in `Jenkinsfile` / `ci/checkout_config.groovy`, so `PIPELINE_OR_GROOVY_LOGIC` is the canonical class.
- Correct Investigator Defect Type: `pipeline_wiring_issue` (acceptable: `misconfiguration`)
- Terminal error literal in the log:
  - `remote: The project you were looking for could not be found or you don't have permission to view it.`
  - `fatal: repository 'https://git.technica-engineering.net/data/data-flow-hub.git/' not found`
  - Wrapped by `hudson.plugins.git.GitException: Command "git fetch ..." returned status code 128`
  - Finally: `ERROR: Maximum checkout retry attempts reached, aborting`

This is **NOT** a network/timeout/connectivity failure: the TLS handshake completed (the agent connected to `git.technica-engineering.net:443`, received headers, got a 404-ish response). The defect is at the SCM-config layer — the configured URL or the configured credential is wrong for this repo right now.

## Root Cause In This Fixture
The Jenkinsfile (and `ci/checkout_config.groovy`) hardcode two values:
- `url: 'https://git.technica-engineering.net/data/data-flow-hub'`
- `credentialsId: 'token_gitlab_techinca_qqtechdataactivities'`

One of the following is true (the log alone cannot disambiguate which, and the agent must say so):
1. The repository was renamed / moved / deleted on the GitLab side and this URL no longer resolves.
2. The token `token_gitlab_techinca_qqtechdataactivities` has lost (or never had) permission to read this repo, and GitLab returns "not found" instead of 401 for security reasons.
3. The URL itself has a typo (compare with the Groovy helper `checkoutDataFlowHub()` — both files must agree).

The Jenkinsfile + `ci/checkout_config.groovy` are the verified surface to inspect. The pipeline retry mechanism made the failure terminal but is not the cause.

## Defective Location
- Primary file: `Jenkinsfile` (and `ci/checkout_config.groovy` — they duplicate the URL + credentialsId)
- Defective declarations:
  - `Jenkinsfile`: `git branch: 'main', credentialsId: env.GIT_CREDENTIALS, url: env.DATA_FLOW_HUB_REPO` (lines 11-16)
  - `ci/checkout_config.groovy`: `git branch: 'main', credentialsId: 'token_gitlab_techinca_qqtechdataactivities', url: 'https://git.technica-engineering.net/data/data-flow-hub'`
- Defect type: `pipeline_wiring_issue` (acceptable: `misconfiguration`)

## Evidence The Agent Should Use
- [Jenkinsfile](./Jenkinsfile) — proves the URL and credentialsId being used at runtime.
- [ci/checkout_config.groovy](./ci/checkout_config.groovy) — proves the duplicated wiring in the helper.
- Log line `remote: The project ... could not be found or you don't have permission` — proves it is a GitLab-side resolution issue, not a transport failure.
- Log line `fatal: repository '...' not found` — confirms the same.

## How The Agent Should Reason
1. Parse the log. The `fatal: repository ... not found` line and the `remote: ... could not be found or you don't have permission` line together prove the GitLab server replied to the agent — therefore network/TLS is healthy.
2. Eliminate `NETWORK_TIMEOUT_OR_CONNECTIVITY` — the connection itself worked.
3. The defect must live at the SCM wiring layer (URL or token scope). Inspect `Jenkinsfile` and `ci/checkout_config.groovy` to surface the exact URL + credentialsId.
4. Report which two values are wired in this repo. Suggestor recommends verifying the repo still exists at that URL on the GitLab server and that the credential token still has read access.

## What A Strong Answer Must Say
- Terminal failure is GitLab returning "not found / no permission", NOT a network timeout. Class = `CODEBASE_ISSUE` / pipeline-wiring, not infrastructure.
- The two files that wire the broken checkout are `Jenkinsfile` and `ci/checkout_config.groovy` (both must be reconciled).
- The hardcoded URL `https://git.technica-engineering.net/data/data-flow-hub` and credentialsId `token_gitlab_techinca_qqtechdataactivities` are the candidates to validate.
- The Suggestor must propose verifying the URL + token, NOT a network/DNS/agent fix.
- Investigator MUST NOT short-circuit to `SKIPPED_INFRA`; this is codebase-side.

## What Should Be Marked Wrong
- Classifying as `INFRASTRUCTURE_ISSUE / NETWORK_TIMEOUT_OR_CONNECTIVITY` and triggering `SKIPPED_INFRA`. The remote responded with a 404-style error — the network is fine.
- Recommending DNS / firewall / VPN fixes. Irrelevant.
- Suggesting the repo URL/credentials are correct without inspecting `Jenkinsfile` / `ci/checkout_config.groovy`.
- Failing to mention BOTH possible root causes (URL gone vs token permission lost) — the log alone cannot disambiguate, so the answer must flag the ambiguity, not pretend to know.
- LIMITED_ADVISORY — there IS a clear next action: read the two files, verify the repo + token on GitLab.
