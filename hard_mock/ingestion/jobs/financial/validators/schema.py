class DataValidationError(Exception):
    pass


REQUIRED_COLUMNS = {
    "PRD_FIN_TRANSACTIONS": [
        "transaction_id",
        "account_id",
        "transaction_hash",
        "currency_code",
        "amount",
        "booking_date",
    ]
}


class FinancialSchemaValidator:
    def enforce_strict_schema(self, df, target_table):
        expected = REQUIRED_COLUMNS[target_table]
        missing_cols = [column for column in expected if column not in df.columns]
        if missing_cols:
            raise DataValidationError(
                f"Missing expected mandatory columns: {missing_cols}"
            )
        return True
