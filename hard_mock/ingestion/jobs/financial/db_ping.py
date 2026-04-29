from sqlalchemy import create_engine


def ping(connection_string: str):
    engine = create_engine(connection_string)
    return engine.connect()
