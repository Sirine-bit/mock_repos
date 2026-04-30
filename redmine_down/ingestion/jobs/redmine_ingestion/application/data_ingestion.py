import logging

from ingestion.jobs.redmine_ingestion.infra.redmine import RedmineConnector


LOGGER = logging.getLogger(__name__)


def ingest_project_data(mssql_usr, mssql_psw, project, redmine_usr, redmine_psw):
    LOGGER.info("connecting to sql server...")
    LOGGER.info("sql server is ready!")

    LOGGER.info("connecting to redmine server...")
    rc = RedmineConnector(project["base_url"], redmine_usr, redmine_psw)
    rc.connect_to_redmine()
    LOGGER.info("redmine server is ready!")

    # downstream extraction + load steps would run here
