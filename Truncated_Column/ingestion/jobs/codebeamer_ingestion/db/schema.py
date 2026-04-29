from sqlalchemy import create_engine, Table, Column, String, MetaData

metadata = MetaData()

# Development cache only. This file is not authoritative for production because
# the table is managed directly by DBAs in SQL Server.
raw_requirements_ipnext_codebeamer_daily = Table(
    'raw_requirements_ipnext_codebeamer_daily', metadata,
    Column('tracker', String(255)),
    Column('assigned_to', String(255)),
    Column('status', String(50))
)

def get_engine():
    return create_engine("mssql+pyodbc:///?odbc_connect=...")
