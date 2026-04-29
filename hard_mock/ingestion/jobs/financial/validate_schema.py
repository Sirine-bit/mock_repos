from ingestion.jobs.financial.transform import build_financial_dataframe
from ingestion.jobs.financial.validators.schema import FinancialSchemaValidator


def main() -> None:
    validator = FinancialSchemaValidator()
    df = build_financial_dataframe()
    validator.enforce_strict_schema(df, target_table="PRD_FIN_TRANSACTIONS")


if __name__ == "__main__":
    main()
