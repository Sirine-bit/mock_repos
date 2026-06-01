# Gold RCA

## Scenario
A scheduled Jenkins job (`zuul_ingestion / get_pregate_tcs_executions`) opens a SQL Server connection at the start of its Python entrypoint. The connection attempt is refused at the transport layer by the SQL Server DBNETLIB driver before any business logic runs. The pipeline aborts during connection setup.

## Terminal Failure
- Stage: `get_pregate_tcs_executions`
- Correct class: `INFRASTRUCTURE_ISSUE`
- Correct RCA Subtype: `NETWORK_TIMEOUT_OR_CONNECTIVITY` (acceptable: `EXTERNAL_SERVICE_FAILURE`). The RCA prompt's enum has no distinct "database unreachable" value; SQL Server connection-open at the transport layer is reported as the network/connectivity class. Either valid value triggers the P0 short-circuit.
- Correct Investigator Defect Type: `infrastructure_failure`
- Terminal error literal:
  - `pyodbc.OperationalError: ('08001', "[08001] [Microsoft][ODBC SQL Server Driver][DBNETLIB]SQL Server n'existe pas ou son accès est refusé. (17) (SQLDriverConnect); [08001] [Microsoft][ODBC SQL Server Driver][DBNETLIB]ConnectionOpen (Connect()). (53)")`
  - Wrapped by `sqlalchemy.exc.OperationalError`
  - Followed by `ERROR: script returned exit code 1`

## Root Cause In This Fixture
SQLState `08001` from the SQL Server DBNETLIB driver means the client could not reach the database listener at the transport layer — server down, listener on a different port, firewall blocking the route, hostname not resolving, or wrong named instance. The error fires inside `pyodbc.connect()` / `sqlalchemy.create_engine` **before any project code runs**, so no code/schema/pipeline change in this repository can resolve it. The defect is an infrastructure / connectivity incident on the database side.

## Defective Location
- Primary defect: **infrastructure — SQL Server instance unreachable**, not any file in this repository.
- This repo intentionally contains no application code for the fixture (only this `rca.md`); the agent cannot, and should not, inspect application files.
- Defect type: `infrastructure_failure`
- Suggested operator scope: SQL Server availability + listener port; DNS resolution for the configured host; firewall egress from the Jenkins agent; ODBC driver / DSN; connection-string host vs. named instance.

## Evidence The Agent Should Use
This scenario is intentionally infra-class. Expected path:
1. Parser surfaces the `pyodbc.OperationalError 08001 / SQLDriverConnect` line as the terminal failure.
2. RCA classifies `Primary Class = INFRASTRUCTURE_ISSUE`, `Subtype = NETWORK_TIMEOUT_OR_CONNECTIVITY` (acceptable: `EXTERNAL_SERVICE_FAILURE`).
3. Investigator short-circuits (`Status = SKIPPED_INFRA`, 0 tool calls, 0 rounds). Tools like `get_schema`, `execute_select`, `get_file_contents`, `list_directory`, `get_jenkins_pipeline_code` MUST NOT be called — there is nothing to gather code-side, and probing the unreachable DB only repeats the same failure.
4. Suggestor emits `INFRA_OR_OPERATIONAL_DIRECTIVE` with operator actions.

## How The Agent Should Reason
1. The traceback origin is `pyodbc.connect` / `sqlalchemy.create_engine`. The error fires before any application import or query — that proves it is not a logic / schema / data defect.
2. SQLState `08001` (`SQLDriverConnect` / `ConnectionOpen`) is by definition a transport-layer failure.
3. Classify `INFRASTRUCTURE_ISSUE` with a subtype in the short-circuit allow-list. Skip the Investigator agent.
4. Suggestor outputs operator directives: confirm SQL Server is up; verify host/port/listener; check firewall egress from the Jenkins agent; verify ODBC driver + DSN; then re-run.

## What A Strong Answer Must Say
- Terminal failure is `08001 / DBNETLIB ConnectionOpen` — transport-level, NOT auth and NOT application logic.
- Defect class is `INFRASTRUCTURE_ISSUE` with RCA Subtype `NETWORK_TIMEOUT_OR_CONNECTIVITY` (acceptable: `EXTERNAL_SERVICE_FAILURE`).
- Investigator must `SKIPPED_INFRA` with `0` tool calls and `0` rounds.
- Suggestor must be `INFRA_OR_OPERATIONAL_DIRECTIVE` with `Change Type = operational_action` and `Confidence ≤ medium` (no code evidence was gathered).

## What Should Be Marked Wrong
- Any code patch suggestion for the repo (CODE_OR_CONFIG_PATCH is wrong here).
- Calling `get_file_contents` / `search_code` / `list_directory` / `get_jenkins_pipeline_code` / `get_schema` / `execute_select` — every such call is wasted budget and contradicts the P0 short-circuit contract.
- Investigation Status = `INCONCLUSIVE` or `CONFIRMED` — the canonical status for this class is `SKIPPED_INFRA`.
- Defect Type other than `infrastructure_failure` (NOT `null_reference`, `missing_key`, `truncation`, `wrong_type`, `credential_issue`, etc.).
- Recommending credential rotation — SQLState `08001` is `ConnectionOpen`, the credential layer is not reached; the transport layer failed first.
- LIMITED_ADVISORY — there IS a clear operational directive; issue it.
