# Gold RCA

## Scenario
The job dies during repository initialization/checkout because the Jenkins agent runs out of memory.

## Terminal Failure
- Stage: `Deploy`
- Correct class: `INFRASTRUCTURE_ISSUE`
- Terminal symptom from the log: `fatal: not enough memory for initialization`

## Root Cause In This Fixture
There is no actionable application-code defect inside this repo. The failure is environmental: checkout is scheduled on a low-memory Windows agent, modeled here by [Jenkinsfile](./Jenkinsfile) using label `WIN_LOW_MEM_AGENT` and the supporting note in [ci/agent_notes.md](./ci/agent_notes.md).

## Defective Location
- File: `Jenkinsfile`
- Block: agent/checkout configuration
- Defect type: `misconfiguration` at infrastructure level

## Evidence The Agent Should Use
- [Jenkinsfile](./Jenkinsfile) shows the job is assigned to a constrained agent.
- [ci/agent_notes.md](./ci/agent_notes.md) explains the low-memory condition.

## How The Agent Should Reason
1. Identify checkout as the terminal failure boundary.
2. Notice no repo files are actually executed.
3. Classify this as an infrastructure issue, not a code defect.
4. Stop after confirming the pipeline is pinned to an unsuitable agent.

## What A Strong Answer Must Say
- The failure is environmental and occurs before repo code runs.
- The memory issue happens during Git initialization/checkout.
- A correct diagnosis should not invent a Python or SQL defect.

## What Should Be Marked Wrong
- Proposing fixes in business logic files.
- Claiming the repo contents caused the crash.
- Treating skipped later stages as separate failures.
