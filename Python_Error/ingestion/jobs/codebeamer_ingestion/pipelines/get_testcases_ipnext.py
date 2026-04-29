from ingestion.jobs.codebeamer_ingestion.data_access.extract_tcs_ipnext import (
    extract_testcases,
)


def get_testcases_ipnext_pipeline():
    information = [
        {"team": {"name": "Platform QA"}, "title": "Happy path"},
        [{"team": {"name": "Nested unexpected entry"}}],
    ]
    return extract_testcases(information)


if __name__ == "__main__":
    get_testcases_ipnext_pipeline()
