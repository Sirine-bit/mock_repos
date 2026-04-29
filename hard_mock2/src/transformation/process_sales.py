import pandas as pd

from src.infra.database import insert_dataframe


def normalize_client_ids(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized["client_id"] = normalized["client_id"].fillna("UNKNOWN_CLIENT")
    return normalized


def build_sales_chunks() -> list[pd.DataFrame]:
    source = pd.DataFrame(
        [
            {
                "opportunity_id": "006D000000rGjT1",
                "amount": 1500.00,
                "client_id": None,
                "close_date": "2026-03-25",
            }
        ]
    )
    return [normalize_client_ids(source)]


def main() -> None:
    for df_chunk in build_sales_chunks():
        insert_dataframe(df_chunk, table="STG_SALES_DAILY")


if __name__ == "__main__":
    main()
