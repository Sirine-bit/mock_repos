import logging
import sys

from ingestion.jobs.redmine_ingestion.application.data_ingestion import ingest_project_data


LOGGER = logging.getLogger(__name__)


redmine_training = {
    "name": "trainingprocess.tech",
    "base_url": "https://redmine.intranet.company.tn",
    "project_id": "data_team",
}


def main(redmine_usr, redmine_psw, mssql_usr, mssql_psw):
    LOGGER.info("treating training-process project...")
    ingest_project_data(mssql_usr, mssql_psw, redmine_training, redmine_usr, redmine_psw)


if __name__ == "__main__":
    redmine_usr = sys.argv[1]
    redmine_password = sys.argv[2]
    user_sql = sys.argv[3]
    password_sql = sys.argv[4]
    main(redmine_usr, redmine_password, user_sql, password_sql)
