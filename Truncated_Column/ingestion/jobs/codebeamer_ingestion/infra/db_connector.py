from sqlalchemy import create_engine


ENGINE_URL = "mssql+pyodbc://TEST_TOOL_PRE_PROD_INFRA/dbo"


def insert_dataframe_into_table(table_name, df, if_exists="append"):
    conn = create_engine(ENGINE_URL)
    df.to_sql(table_name, con=conn, if_exists=if_exists, index=False)


def fetch_target_table_metadata(table_name):
    """
    The production pipeline relies on the live SQL Server schema as the source of truth.
    Cached local schema files may lag behind DBA-managed changes.
    """
    conn = create_engine(ENGINE_URL)
    query = f"""
    SELECT
        COLUMN_NAME,
        DATA_TYPE,
        CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = '{table_name}'
    ORDER BY ORDINAL_POSITION
    """
    with conn.begin() as db_conn:
        return db_conn.exec_driver_sql(query).fetchall()
