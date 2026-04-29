import pandas as pd


def build_financial_dataframe() -> pd.DataFrame:
    source_rows = [
        {
            "transaction_id": "txn-1001",
            "account_id": "ACC-42",
            "currency": "EUR",
            "amount": 1400.50,
            "booking_date": "2026-03-26",
        }
    ]
    df = pd.DataFrame(source_rows)

    # The upstream payload never exposes a transaction hash, and the currency
    # field is left under the wrong column name for the target SQL table.
    return df[["transaction_id", "account_id", "currency", "amount", "booking_date"]]
