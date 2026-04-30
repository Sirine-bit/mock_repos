# could_not_auth

GitHub testcase ingestion fixture for a credential-injection failure.

The pipeline reaches `get_tcs_jc_master`, calls `git_connector.clone_git_repo`,
and the underlying `git clone` is rejected by `cc-github.clientgroup.net` with
`HTTP 401 / fatal: Authentication failed`. The credentials bound by Jenkins
(`CC_GITHUB_IPNEXT_CREDENTIALS`) do not authorize access to the target
repository.
