# error_cloning

Mock repository for a checkout that fails before any application code runs.

The failure is designed to look like a low-memory Jenkins agent issue during
`git init` / checkout setup.

# Agent Notes

- Jenkins label: `WIN_LOW_MEM_AGENT`
- Workspace disk is shared with other checkout-heavy jobs.
- Large checkouts should avoid running on this node without a memory headroom check.
