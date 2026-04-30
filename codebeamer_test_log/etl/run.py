from ingestion.jobs.codebeamer_ingestion.data_access.utils import get_result_tcs_ipnext


def load_payload():
    return [
        {"team": {"id": 17, "name": "Platform QA"}, "title": "Happy path"},
        [{"team": {"id": 18, "name": "Nested unexpected entry"}}],
    ]


if __name__ == "__main__":
    data = load_payload()
    tcs = get_result_tcs_ipnext(data)
    print(tcs)
