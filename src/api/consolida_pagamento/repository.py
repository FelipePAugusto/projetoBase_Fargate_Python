import pymysql
import os

_database_connection_ro = None
_database_connection_rw = None


def connect_database_ro() -> pymysql.connections.Connection:
    """Retorna uma conexão com o banco de dados de leitura.

    >>> database = connect_database_ro()
    ... with database.cursor() as cursor:
    ...     pass

    Retorno:
        pymysql.connections.Connection: Objeto de conexão com o MySQL.
    """
    global _database_connection_ro
    if _database_connection_ro is None:
        _database_connection_ro = pymysql.connect(
            host=os.environ.get("DB_RO_HOST"),
            user=os.environ.get("DB_RO_USERNAME"),
            password=os.environ.get("DB_RO_PASSWORD"),
            database=os.environ.get("DB_RO_DATABASE"),
            port=int(os.environ.get("DB_RO_PORT")),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
    return _database_connection_ro


def connect_database_rw() -> pymysql.connections.Connection:
    """Retorna uma conexão com o banco de dados de escrita.

    >>> database = connect_database_rw()
    ... with database.cursor() as cursor:
    ...     pass

    Retorno:
        pymysql.connections.Connection: Objeto de conexão com o MySQL.
    """
    global _database_connection_rw
    if _database_connection_rw is None:
        _database_connection_rw = pymysql.connect(
            host=os.environ.get("DB_RW_HOST"),
            user=os.environ.get("DB_RW_USERNAME"),
            password=os.environ.get("DB_RW_PASSWORD"),
            database=os.environ.get("DB_RW_DATABASE"),
            port=int(os.environ.get("DB_RW_PORT")),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
    return _database_connection_rw