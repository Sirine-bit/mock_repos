# Truncated_Column

Codebeamer requirements ingestion fixture.

The ETL flattens many assignees into one comma-separated string and then inserts
it into a SQL table whose `assigned_to` column is narrower than the produced
value.
