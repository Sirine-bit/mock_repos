from src.api.salesforce import SalesforceClient


def main() -> None:
    client = SalesforceClient(timeout_seconds=30)
    client.query_all(
        "SELECT Id, Amount, ClientId FROM Opportunity WHERE CloseDate = YESTERDAY"
    )


if __name__ == "__main__":
    main()
