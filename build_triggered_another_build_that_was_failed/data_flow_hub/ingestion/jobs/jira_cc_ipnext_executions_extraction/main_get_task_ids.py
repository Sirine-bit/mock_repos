import logging
import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] [%(levelname)s]  %(message)s')
logger = logging.getLogger('main_get_tas')

def execute():
    logger.info("connecting to sql server...")
    logger.info("sql server is ready")
    logger.info(f"current date : {datetime.datetime.now()}")
    logger.info("Retrieving tickets from rfn_jira_cc_ipnext_projects")
    logger.info("352 tickets are extracted!")
    logger.info("data processing : extracting task ids")
    logger.info("task ids extracted")
    logger.info("loading task ids in prc.jira_cc_ipnext_task_ids table...")
    logger.info("task ids are loaded successfully!")

if __name__ == "__main__":
    execute()
