# redmine_down

Redmine ingestion fixture for a server-side TLS failure.

The pipeline runs three Redmine stages successfully against the KAP server, then
fails when the `redmine` stage targets the training-process Redmine instance,
whose HTTPS certificate has expired.
