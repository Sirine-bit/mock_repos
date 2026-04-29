# hard_mock2

Enterprise sales ETL fixture.

The terminal failure is a SQL Server type conversion error caused by the
transformation layer inserting the sentinel string `UNKNOWN_CLIENT` into
`STG_SALES_DAILY.client_id`, which is modeled as an integer.
