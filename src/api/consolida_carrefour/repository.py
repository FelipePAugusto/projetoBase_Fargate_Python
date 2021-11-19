import pymysql
from pymysql import Error
import os
from .errors import Errors
from .util import *


_database_connection_ro = None
_database_connection_rw = None

async def connect_database_ro() -> pymysql.connections.Connection:
    """ Retorna uma conexão com o banco de dados de leitura.

    >>> database = connect_database_ro()
    ... with database.cursor() as cursor:
    ...     pass

    Retorno:
        pymysql.connections.Connection: Objeto de conexão com o MySQL.
    """
    try:
        global _database_connection_ro
        print(f"os.environ.get('DB_RO_HOST'): {os.environ.get('DB_RO_HOST')}")
        print(f"os.environ.get('DB_RO_USERNAME'): {os.environ.get('DB_RO_USERNAME')}")
        print(f"os.environ.get('DB_RO_PASSWORD'): {os.environ.get('DB_RO_PASSWORD')}")
        print(f"os.environ.get('DB_RO_DATABASE'): {os.environ.get('DB_RO_DATABASE')}")
        print(f"os.environ.get('DB_RO_PORT'): {os.environ.get('DB_RO_PORT')}")

        if _database_connection_ro is None:
            _database_connection_ro = pymysql.connect(
                host=os.environ.get('DB_RO_HOST'),
                user=os.environ.get('DB_RO_USERNAME'),
                password=os.environ.get('DB_RO_PASSWORD'),
                database=os.environ.get('DB_RO_DATABASE'),
                port=int(os.environ.get('DB_RO_PORT')),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
        print("Connection OK")
        return _database_connection_ro
    except Error as e:
        print("Connection error: " + str(e))

async def connect_database_rw() -> pymysql.connections.Connection:
    """ Retorna uma conexão com o banco de dados de escrita.

    >>> database = connect_database_rw()
    ... with database.cursor() as cursor:
    ...     pass

    Retorno:
        pymysql.connections.Connection: Objeto de conexão com o MySQL.
    """
    try:
        global _database_connection_rw
        print(f"os.environ.get('DB_RW_HOST'): {os.environ.get('DB_RW_HOST')}")
        print(f"os.environ.get('DB_RW_USERNAME'): {os.environ.get('DB_RW_USERNAME')}")
        print(f"os.environ.get('DB_RW_PASSWORD'): {os.environ.get('DB_RW_PASSWORD')}")
        print(f"os.environ.get('DB_RW_DATABASE'): {os.environ.get('DB_RW_DATABASE')}")
        print(f"os.environ.get('DB_RW_PORT'): {os.environ.get('DB_RW_PORT')}")
        if _database_connection_rw is None:
            _database_connection_rw = pymysql.connect(
                host=os.environ.get('DB_RW_HOST'),
                user=os.environ.get('DB_RW_USERNAME'),
                password=os.environ.get('DB_RW_PASSWORD'),
                database=os.environ.get('DB_RW_DATABASE'),
                port=int(os.environ.get('DB_RW_PORT')),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
        print("Connection OK")
        return _database_connection_rw

    except Error as e:
        print("Connection error: " + str(e))


def upload_to_s3(*,file_name, bucket=os.environ.get('AWS_BUCKET'), object_name=None) -> bool:
    import boto3
    from botocore.exceptions import ClientError
    s3 = boto3.client('s3',aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))
    try:
        s3.upload_file(file_name, bucket, object_name)
        return True
    except ClientError as e:
        return False


def get_url_s3(*, obj_name: str, bucket_name: str=os.environ.get('AWS_BUCKET'), expiration: int=3600) -> str:
    import boto3
    from botocore.exceptions import ClientError
    s3 = boto3.client('s3',aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))
    try:
        response = s3.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': obj_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        print(e)
        return None

    return response

async def check_registros_anteriores(fonte_id: int, filial: str, data_recebimento: str) -> bool:
    """ Se houver registros anteriores, os remove antes para a soma não ficar errada
    Parametros:
        fonte_id: (int) ID da fonte de pagamento
        filial: (str) ID da filial
        data_recebimento: (str) A data de recebimento
    Retorno:
        bool: Se tudo ocorrer bem retorna True
    """
    try:
        database = await connect_database_ro()
        result = False

        with database.cursor() as cursor:
            cursor.execute("""
                SELECT id
                  FROM pgtos_analiticos FORCE INDEX (pgtos_analiticos_fonte_id_filial_data_recebimento_index)
                WHERE
                fonte_id = %s
                and filial = %s
                and data_recebimento = %s

            """
            ,(fonte_id, filial, data_recebimento))

        pagamentos_analiticos = cursor.fetchall()

        if len(pagamentos_analiticos):
            for pgto_analitico in pagamentos_analiticos:
                id = pgto_analitico.get('id', None) or None
                if id is not None:
                    database_rw = await connect_database_rw()
                    with database_rw.cursor() as cursor:
                        cursor.execute("""
                            DELETE
                                from pgtos_analiticos
                            WHERE id = %s
                        """, id)
            result = True
    except Error as e:
        result = False
        print(e)

    return result

async def save_pgto_analitico(dados: dict ):
    retorno = {}
    try:
        database_rw = await connect_database_rw()
        with database_rw.cursor() as cursor_save:
            cursor_save.execute("""
                INSERT INTO
                    pgtos_analiticos
                (fonte_id,
                filial,
                data_recebimento,
                data_enviado,
                saldo
                ) values (%s, %s, %s, %s, %s)
            """,(dados.get('fonte_id'),
                dados.get('filial'),
                dados.get('data_recebimento'),
                dados.get('data_enviado'),
                dados.get('saldo')))
            retorno['status'] = True
            retorno['id'] = cursor_save.lastrowid

    except Error as e:
        retorno['status'] = False
        retorno['error'] = e
    await create_logging_nr(message=retorno)
    return retorno

async def add_movimentacao_historico(data = dict):
    import time
    from datetime import datetime

    now = datetime.now()
    ts = datetime.timestamp(now)
    timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    try:
        movimentacao_historico = {}
        for key in data:
            if data[key] is not None:
                movimentacao_historico[key] = data[key]

        database_rw = await connect_database_rw()
        with database_rw.cursor() as cursor:
            cursor.execute("""
                INSERT INTO movimentacao_historico
                    (origem_id,
                    origem_analitico,
                    origem_consolidado,
                    origem_titulo,
                    destino_id,
                    destino_analitico,
                    destino_consolidado,
                    destino_titulo,
                    movimento_valor,
                    movimento_data,
                    movimento_historico,
                    usuario_id)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,(movimentacao_historico['origem_id'],
                 True,
                 False,
                 False,
                 None,
                 0,
                 0,
                 0,
                 movimentacao_historico['saldo'],
                 timestamp,
                 f"""Analítico ID {movimentacao_historico['origem_id']},
                     Fonte ID {movimentacao_historico['fonte_id']} ,
                     Filial {movimentacao_historico['filial']}
                     na data de recebimento {movimentacao_historico['data_recebimento']}
                     importado com saldo {movimentacao_historico['saldo']}""",
                 2))
        if cursor.lastrowid:
            info = "Histórico de movimentação gravado com sucesso."
            await create_logging_nr(message=info)
        else:
            info = "Ocorreu falha ao gravar o histórico da movimentação."
            await create_logging_nr(message=info)
    except Error as e:
        info = f"Ocorreu falha ao gravar o histórico da movimentação. Erro: {e}"
        await create_logging_nr(message=info)
