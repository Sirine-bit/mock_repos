from ingestion.jobs.codebeamer_ingestion.data_access.extract_requirements_ipnext import (
    extract_requirements,
)
from ingestion.jobs.codebeamer_ingestion.infra.db_connector import (
    insert_dataframe_into_table,
)


RQS_IPNEXT_TABLE_NAME = "raw_requirements_ipnext_codebeamer_daily"


def get_requirements_ipnext_pipeline():
    filtered_df = extract_requirements()
    insert_dataframe_into_table(RQS_IPNEXT_TABLE_NAME, filtered_df)


if __name__ == "__main__":
    get_requirements_ipnext_pipeline()
