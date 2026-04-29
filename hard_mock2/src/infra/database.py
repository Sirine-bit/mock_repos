from sqlalchemy import create_engine


ENGINE_URL = "mssql+pyodbc://warehouse/staging"


def insert_dataframe(df, table: str):
    engine = create_engine(ENGINE_URL)
    df.to_sql(table, con=engine, if_exists="append", index=False)
