# build_triggered_another_build_that_was_failed

Mock orchestration repository for the `ipnext_validation_processing` Jenkins job.

The local stages succeed, then the pipeline triggers a downstream job:

- `testguide_ipnext_testcases_extraction`

This fixture gives the investigator enough context to confirm that the local repo
mainly orchestrates downstream execution rather than failing on its own code path.
