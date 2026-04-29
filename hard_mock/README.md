# hard_mock

Financial ingestion fixture with two notable signals:

- an earlier SQL connectivity timeout that recovers on retry
- a terminal schema validation failure caused by missing mandatory columns

The terminal failure is the code-level schema mismatch in the validation stage.
