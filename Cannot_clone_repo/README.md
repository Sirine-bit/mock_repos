# Cannot_clone_repo

Mock Jenkins checkout fixture for a repository-access failure.

The interesting artifact here is the checkout configuration itself: the job points
to a URL that is redirected and then resolved to a repository the token cannot
access.
