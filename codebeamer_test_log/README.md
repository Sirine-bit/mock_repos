# codebeamer_test_log

Codebeamer ingestion fixture for a data-shape bug.

The `Get_Testcases_Ipnext` stage runs `etl/run.py`, which calls
`get_result_tcs_ipnext()`. The helper assumes every payload entry is a `dict`,
but the production payload includes nested `list` entries, so iteration crashes
with `AttributeError: 'list' object has no attribute 'get'`.
