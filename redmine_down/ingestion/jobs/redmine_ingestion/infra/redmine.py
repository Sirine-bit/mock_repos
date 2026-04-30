import logging

from redminelib import Redmine


LOGGER = logging.getLogger(__name__)


class RedmineConnector:
    """Establish and validate a connection to a Redmine server."""

    def __init__(self, base_url: str, username: str, password: str):
        self._base_url = base_url
        self._username = username
        self._password = password
        self._client = None

    @property
    def client(self) -> Redmine:
        if self._client is None:
            self._client = Redmine(
                self._base_url,
                username=self._username,
                password=self._password,
            )
        return self._client

    def connect_to_redmine(self):
        LOGGER.info("Trying to connect to the redmine server...")
        connector = self.client
        try:
            connector.user.get("current")
        except Exception as e:
            raise Exception(
                "unable to connect to redmine server ",
                "Error : " + str(e),
            )
