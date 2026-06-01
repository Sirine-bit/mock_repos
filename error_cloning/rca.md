# Gold RCA

## Scenario
A Jenkins job (`codebeamer_ingestion`) is pinned to the agent label `WIN_LOW_MEM_AGENT`. During the `Deploy` stage, `git init D:\_jenkins_4\workspace\codebeamer_ingestion\data_flow_hub` fails with `fatal: not enough memory for initialization`. Git never even gets to fetch — the agent process cannot allocate enough memory to initialize the working tree. The retry policy fires and the pipeline aborts.

## Terminal Failure
- Stage: `Deploy`
- Correct class: `INFRASTRUCTURE_ISSUE`
- Correct RCA Subtype: `RESOURCE_EXHAUSTION` (acceptable: `AGENT_OR_NODE_FAILURE`)
- Correct Investigator Defect Type: `infrastructure_failure`
- Terminal error literal in the log:
  - `Caused by: hudson.plugins.git.GitException: Command "git init D:\_jenkins_4\workspace\codebeamer_ingestion\data_flow_hub" returned status code 128:`
  - `stderr: fatal: not enough memory for initialization`
  - Wrapped by `hudson.plugins.git.GitException: Could not init ...`
  - Finally: `ERROR: Maximum checkout retry attempts reached, aborting`

## Root Cause In This Fixture
The Jenkins agent named `WIN_LOW_MEM_AGENT` (per `ci/Jenkinsfile` line 2) does not have enough free RAM for the OS to satisfy `git init`'s allocation. The defect is operational: the agent is undersized for the workload, or the agent JVM/Windows session is leaking / holding memory from a previous build. **No code, schema, or SCM-config change in this repository can fix this** — the only fix lives outside the repo (agent capacity / cleanup / migration to a different label).

## Defective Location
- Primary defect: **infrastructure — Jenkins agent host out of memory**, not any file in this repository.
- The `ci/Jenkinsfile` pins the job to `WIN_LOW_MEM_AGENT` (line 2); that label is the symptom surface but rewiring the label is a workaround, not a fix.
- Defect type: `infrastructure_failure`
- Suggested operator scope: Jenkins agent host admin (RAM, swap, stale processes), or pipeline-ops (re-pin the job to a larger node label).

## Evidence The Agent Should Use
This scenario is intentionally infra-class. The expected path is:
1. Parser surfaces the `fatal: not enough memory for initialization` line as the terminal failure.
2. RCA classifies `Primary Class = INFRASTRUCTURE_ISSUE`, `Subtype = RESOURCE_EXHAUSTION`.
3. Investigator short-circuits (`Status = SKIPPED_INFRA`, 0 tool calls, 0 rounds).
4. Suggestor emits `INFRA_OR_OPERATIONAL_DIRECTIVE`.

`ci/Jenkinsfile` is only mildly useful (it names the agent label `WIN_LOW_MEM_AGENT`). If the agent inspects it, it should ONLY use it to confirm the label name; the fix is not a Jenkinsfile patch.

## How The Agent Should Reason
1. Read the LAST traceback. `fatal: not enough memory for initialization` returned by `git init` is the terminal failure — git couldn't even allocate the empty index. That is unambiguously an agent-host resource issue, not a network/credential issue.
2. The agent label `WIN_LOW_MEM_AGENT` in the Jenkinsfile is consistent with the symptom name (deliberate naming).
3. Skip code inspection. Suggestor recommends one or more of: free memory on the agent (kill stale workspaces / Java processes), increase the agent's heap/RAM, or re-pin the job to a larger agent label.

## What A Strong Answer Must Say
- Terminal failure is `fatal: not enough memory for initialization` on `git init` — an OOM at the agent host, not a network or credentials issue.
- The defect class is `INFRASTRUCTURE_ISSUE` and the subtype is `RESOURCE_EXHAUSTION`.
- Investigator must `SKIPPED_INFRA` with 0 tool calls and 0 rounds.
- Suggestor must be `INFRA_OR_OPERATIONAL_DIRECTIVE` with `Change Type = operational_action`, `Confidence ≤ medium` (no code evidence was gathered), and concrete actions: clean up the agent's workspace, monitor RAM, possibly migrate the job off `WIN_LOW_MEM_AGENT`.

## What Should Be Marked Wrong
- Calling this a network / connectivity / TLS / DNS / proxy issue. The error is OOM, the network was never reached.
- Treating the Jenkinsfile as the defect — re-pinning labels is a workaround, the underlying agent is the issue.
- Recommending a code patch in this repo (nothing to patch).
- Defect Type values like `null_reference`, `missing_key`, `truncation`, `wrong_type`, `logic_error`, `pipeline_wiring_issue`. The only correct value is `infrastructure_failure`.
- Investigation Status = `INCONCLUSIVE` or `CONFIRMED` instead of `SKIPPED_INFRA`.
- LIMITED_ADVISORY — there IS a clear operational directive.
