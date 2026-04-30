# Gold RCA

## Scenario
The Redmine ingestion pipeline finishes the KAP versions, time entries, and issues stages, then crashes during the `redmine` stage when it tries to authenticate against the training Redmine server.

## Terminal Failure
- Stage: `redmine`
- Correct class: `INFRASTRUCTURE_ISSUE`
- Terminal error: `ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired`

## Root Cause In This Fixture
The application code in [ingestion/jobs/redmine_ingestion/infra/redmine.py](./ingestion/jobs/redmine_ingestion/infra/redmine.py) is correct. It opens a TLS session to `https://redmine.intranet.company.tn` and probes `/users/current.json`. The remote server is presenting an expired X.509 certificate, so `urllib3` aborts the TLS handshake before any application logic runs. Earlier stages succeed because they connect to a different KAP Redmine endpoint with a valid certificate.

## Defective Location
- File: server-side certificate on `redmine.intranet.company.tn`
- Confirmation file: `ingestion/jobs/redmine_ingestion/infra/redmine.py`
- Defect type: `infrastructure`

## Evidence The Agent Should Use
- [ingestion/jobs/redmine_ingestion/infra/redmine.py](./ingestion/jobs/redmine_ingestion/infra/redmine.py) shows the connector simply forwards the TLS error.
- [ingestion/jobs/redmine_ingestion/application/data_ingestion.py](./ingestion/jobs/redmine_ingestion/application/data_ingestion.py) shows `connect_to_redmine()` is called before any business logic.
- [ingestion/jobs/redmine_ingestion/pipeline/ingest_redmine_training_issues.py](./ingestion/jobs/redmine_ingestion/pipeline/ingest_redmine_training_issues.py) shows the failing stage targets the training Redmine host, not the KAP host used by the earlier successful stages.
- [Jenkinsfile](./Jenkinsfile) shows three KAP stages run before this one and complete normally.

## How The Agent Should Reason
1. Read the traceback bottom-up and identify the original `SSLCertVerificationError`.
2. Notice the cert has *expired*, not been misconfigured locally.
3. Confirm earlier stages connect successfully to a different host, ruling out a client-side trust store issue.
4. Conclude the failure is server-side infrastructure: the training Redmine certificate must be renewed.

## What A Strong Answer Must Say
- The failure is a TLS handshake error caused by an expired server certificate.
- The relevant host is `redmine.intranet.company.tn`.
- The application code did not change behavior; the fix is renewing the server certificate, not editing Python.

## What Should Be Marked Wrong
- Blaming `connect_to_redmine` for raising — it is correctly surfacing the underlying error.
- Suggesting `verify=False` as the fix.
- Treating earlier successful stages as unrelated and missing that they prove the client trust store is fine.
