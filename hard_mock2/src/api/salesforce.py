class APIConnectionError(Exception):
    pass


class SalesforceClient:
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds

    def query_all(self, query: str):
        return {"query": query, "rows": 2450123}
