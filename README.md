These fixtures simulate repositories that the `InvestigatorAgentHandler` can inspect.

Each directory name matches `data/mock_logs/<log basename>.txt`.
When the handler receives a `log_identifier`, it resolves the mock repo at:

`data/mock_repos/<log basename>`

The fixtures are intentionally compact, but each one contains realistic files the
agent can discover with:

- `list_directory("")`
- `read_file(path)`
- `read_infra_file_tool(path)`
- `extract_python_ast(path, name)`

Scenarios covered:

- downstream job orchestration failures
- Git checkout and repo access issues
- missing environment variables in Jenkins
- Python data-shape bugs
- SQL schema and type mismatches
- frontend build memory pressure
