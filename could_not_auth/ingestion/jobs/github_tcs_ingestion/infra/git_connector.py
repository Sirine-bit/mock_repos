import logging
import os

import git


LOGGER = logging.getLogger(__name__)


class GitConnector:
    """Wrap the git clone step used by the GitHub TCs ingestion job."""

    def __init__(self, base_clone_dir: str):
        self._base_clone_dir = base_clone_dir

    def _build_authenticated_url(self, repo_url: str) -> str:
        usr = os.environ["CC_GITHUB_IPNEXT_CREDENTIALS"]
        psw = os.environ["CC_GITHUB_IPNEXT_CREDENTIALS_PSW"]
        # https://<usr>:<psw>@host/path
        prefix, rest = repo_url.split("://", 1)
        return f"{prefix}://{usr}:{psw}@{rest}"

    def clone_git_repo(self, branch: str, submodules: bool):
        repo_url = "https://cc-github.clientgroup.net/swh/safe-posix-platform.git"
        authenticated = self._build_authenticated_url(repo_url)
        target = os.path.join(self._base_clone_dir, "IPNEXT_JC")
        try:
            repo_path = git.Repo.clone_from(
                authenticated,
                target,
                branch=branch,
                multi_options=["--config=core.longpaths=true"],
            )
        except git.exc.GitCommandError:
            LOGGER.error("Error during clone or checkout of %s", branch)
            raise
        return repo_path

    def handle_repository_checkout(self, project_info: dict):
        branch = project_info.get("branch", "master")
        repo_path = self.clone_git_repo(branch, project_info.get("submodules"))
        return repo_path
