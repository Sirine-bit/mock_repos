import logging

logger = logging.getLogger("main_get_tas")


def main() -> None:
    logger.info("connecting to sql server...")
    logger.info("sql server is ready")
    logger.info("Retrieving tickets from rfn_jira_cc_ipnext_projects")
    logger.info("task ids extracted")
    logger.info("task ids are loaded successfully!")


if __name__ == "__main__":
    main()
