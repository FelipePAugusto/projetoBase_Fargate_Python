import os
import pymysql

from consolida_pagamento.tools import consolida_pagamento_job
import asyncio


sql_db_ro_conn = None
sql_db_rw_conn = None


def connect_database_ro() -> pymysql.connections.Connection:
    """Retorna uma conexão com o banco de dados de leitura.

    >>> database = connect_database_ro()
    ... with database.cursor() as cursor:
    ...     pass

    Retorno:
        pymysql.connections.Connection: Objeto de conexão com o MySQL.
    """
    global sql_db_ro_conn
    if sql_db_ro_conn is None:
        sql_db_ro_conn = pymysql.connect(
            host=os.environ.get("DB_RO_HOST"),
            user=os.environ.get("DB_RO_USERNAME"),
            password=os.environ.get("DB_RO_PASSWORD"),
            database=os.environ.get("DB_RO_DATABASE"),
            port=int(os.environ.get("DB_RO_PORT")),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
    return sql_db_ro_conn


def connect_database_rw() -> pymysql.connections.Connection:
    """Retorna uma conexão com o banco de dados de escrita.

    >>> database = connect_database_rw()
    ... with database.cursor() as cursor:
    ...     pass

    Retorno:
        pymysql.connections.Connection: Objeto de conexão com o MySQL.
    """
    global sql_db_rw_conn
    if sql_db_rw_conn is None:
        sql_db_rw_conn = pymysql.connect(
            host=os.environ.get("DB_RW_HOST"),
            user=os.environ.get("DB_RW_USERNAME"),
            password=os.environ.get("DB_RW_PASSWORD"),
            database=os.environ.get("DB_RW_DATABASE"),
            port=int(os.environ.get("DB_RW_PORT")),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
    return sql_db_rw_conn


async def consolida(data_):
    global i
    print("Consolida(Data)" + str(i + 1) + ":\n" + str(data))
    await consolida_pagamento_job(**data_)
    i += 1


sql_db_ro_conn = connect_database_ro()
sql_db_rw_conn = connect_database_rw()


date_begin = "2020-09-15"
date_end = "2020-09-20"
num_testes = 5

sql_qry_slct_rand_ids = """SELECT
    id
FROM 
    (SELECT
        id,
        RAND() as aleat 
    FROM
        tiopatinhas.pgtos_consolidados
    WHERE
        data_recebimento
            BETWEEN '{date_begin}' AND '{date_end}'
    ORDER BY 
        aleat 
    LIMIT     
        {num_testes}) as a
ORDER BY 
    id""".format(
    date_begin=date_begin, date_end=date_end, num_testes=num_testes
)

sql_qry_slct = """SELECT
    data_recebimento,
    fonte_id,
    parcela,
    filial,
    consolidado,
    id,
    recnos_pendentes,
    valor,
    estorno,
    chargeback,
    comissao,
    total,
    saldo,
    saldo_protheus,
    estorno_divergencia,
    chargeback_divergencia
FROM 
    tiopatinhas.pgtos_consolidados
WHERE
    id IN (%s)
ORDER BY 
    id"""

sql_qry_updt_desconsolida = """UPDATE
    tiopatinhas.pgtos_consolidados
SET
    consolidado=0
WHERE
    id IN (%s)"""

sql_db_ro_cursor = sql_db_ro_conn.cursor()
sql_db_rw_cursor = sql_db_rw_conn.cursor()

sql_db_ro_cursor.execute(sql_qry_slct_rand_ids)
selected_ids = sql_db_ro_cursor.fetchall()

rand_ids = ""
for id_ in selected_ids:
    rand_ids += str(id_["id"]) + ", "

rand_ids = rand_ids[0: len(rand_ids) - 2]

print("IDs Avaliados: (" + rand_ids + ")")

sql_qry_slct = sql_qry_slct % rand_ids

sql_db_ro_cursor.execute(sql_qry_slct)
linhas_originais = sql_db_ro_cursor.fetchall()

print("Valores iniciais:\n" + str(linhas_originais))


sql_qry_updt_desconsolida = sql_qry_updt_desconsolida % rand_ids
sql_db_rw_cursor.execute(sql_qry_updt_desconsolida)
sql_db_rw_conn.commit()

print("DESCONSOLIDADOS: " + rand_ids)

i = 0
orig = {}
for linha in linhas_originais:
    data = {
        "fonte_id": int(linha["fonte_id"]),
        "filial": str(linha["filial"]),
        "data_recebimento": str(linha["data_recebimento"]),
        "parcela": int(linha["parcela"]),
    }
    orig[str(linha["id"])] = linha

    asyncio.run(consolida(data))

print("Orig:\n" + str(orig))


sql_db_ro_cursor.execute(sql_qry_slct)
linhas_desconsolidadas = sql_db_ro_cursor.fetchall()

print("Valores desconsolidados:\n" + str(linhas_desconsolidadas))

desc = {}
for linha in linhas_desconsolidadas:
    desc[str(linha["id"])] = linha
print("Desc:\n" + str(desc))


sql_db_ro_cursor.execute(sql_qry_slct)
linhas_recalculadas = sql_db_ro_cursor.fetchall()

recalc = {}
for linha in linhas_originais:
    recalc[str(linha["id"])] = linha

print("Recalc:\n")
print(str(recalc))

for id_, linha in orig.items():
    print(
        "--- id: "
        + str(id_)
        + 20 * " "
        + "Original"
        + 4 * " "
        + "Desconsolidado"
        + 2 * " "
        + "Reconsolidado"
    )

    for col, valor in linha.items():
        igual = (
            "\033[1;32m[IGUAL]\033[0m"
            if str(valor) == str(recalc[id_][col])
            else "\033[1;31m[DIFERENTE]\033[0m"
        )
        print(
            "  - Col: "
            + str(col)
            + (23 - len(str(col))) * " "
            + str(valor)
            + (10 - len(str(valor))) * " "
            + " - "
            + str(desc[id_][col])
            + (14 - len(str(desc[id_][col]))) * " "
            + " - "
            + str(recalc[id_][col])
            + (12 - len(str(recalc[id_][col]))) * " "
            + " - "
            + str(igual)
        )
    # breakpoint()
    print("\n")


# breakpoint()

sql_db_ro_cursor.close()
sql_db_ro_conn.close()

sql_db_rw_cursor.close()
sql_db_rw_conn.close()
