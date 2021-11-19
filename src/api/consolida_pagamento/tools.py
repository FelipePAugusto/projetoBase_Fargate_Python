import os
from datetime import datetime

from typing import List
from .repository import (
    connect_database_ro,
    connect_database_rw,
)
from .util import (
    logger,
    proper_stract,
)


_fonte_ids = None
_datas_recebimento = None
_filial = None
_parcela = None

sql_db_ro_conn = None
sql_db_ro_cursor = None

sql_db_rw_conn = None
sql_db_rw_cursor = None

sql_vars = None

sql_qry_select = ""
sql_qry_select_base = """\
SELECT
    pgto_tbl.fonte_id,
    fonte_tbl.nome as fonte_nome,
    pgto_tbl.filial as filial,
    pgto_tbl.data_recebimento as data_recebimento,
    pgto_tbl.parcela as parcela,
    COUNT(1) as registros,
{campos}
FROM
    pgtos_analiticos as pgto_tbl
    INNER JOIN fontes as fonte_tbl
        ON pgto_tbl.fonte_id = fonte_tbl.id
WHERE
    pgto_tbl.fonte_id = %s AND
    pgto_tbl.filial = %s AND
    pgto_tbl.data_recebimento = %s AND
    pgto_tbl.parcela = %s
GROUP BY
    pgto_tbl.fonte_id,
    pgto_tbl.filial,
    pgto_tbl.data_recebimento,
    pgto_tbl.parcela"""

sql_qry_select_id_base = """SELECT
    id
FROM
    pgtos_consolidados
WHERE
    fonte_id=%s
    AND filial =%s
    AND data_recebimento = %s
    AND parcela = %s"""

sql_qry_update_base = """\
UPDATE
    pgtos_consolidados pc
{set}
WHERE
    id = %s"""

qry_map_campos_base = """\
SELECT
    campo_id
FROM
    fonte_campos
WHERE
    fonte_id=%s
    AND {campo}_principal=1
"""


async def consolida_pagamento_job(**kwargs) -> List:
    """Retorna uma lista de informações do pagamento que será consolidado
    Parâmetros:
        fonte_id (int/list) id da fonte de pagamento
        filial (int) id da filial
        data_recebimento (str/list) data de recebimento do arquivo
        parcela (int) numero da parcela a ser conolidada

    Retorno: List de dados
    """

    fonte_id = kwargs["fonte_id"]
    data_recebimento = kwargs["data_recebimento"]
    filial = kwargs["filial"]
    parcela = kwargs["parcela"]

    global sql_vars

    global _fonte_ids
    global _filial
    global _datas_recebimento
    global _parcela

    global sql_qry_select

    global sql_db_ro_conn
    global sql_db_rw_conn
    # global dic_campos_sql

    _fonte_ids = fonte_id if type(fonte_id) is list else [fonte_id]
    _datas_recebimento = (
        data_recebimento if type(data_recebimento) is list else [
            data_recebimento]
    )
    _filial = filial
    _parcela = parcela

    sql_db_ro_conn = connect_database_ro()

    sql_db_rw_conn = connect_database_rw()
    sql_db_rw_cursor = sql_db_rw_conn.cursor()

    for _fonte_id in _fonte_ids:
        mapear_campos(_fonte_id)

        for _data_recebimento in _datas_recebimento:
            sql_vars = (_fonte_id, _filial, _data_recebimento, _parcela)

            sql_db_ro_cursor = sql_db_ro_conn.cursor()
            sql_db_ro_cursor.execute(sql_qry_select, sql_vars)
            pagamentos = sql_db_ro_cursor.fetchall()
            sql_db_ro_cursor.close()

            if len(pagamentos):
                for pagamento in pagamentos:

                    total = estorno = chargeback = comissao = valor = registro = 0.0

                    estorno = proper_stract(pagamento["estorno"])
                    chargeback = proper_stract(pagamento["chargeback"])
                    comissao = proper_stract(pagamento["comissao"])
                    valor = proper_stract(pagamento["valor"])
                    registros = int(pagamento["registros"])

                    total = valor

                    if estorno:
                        total = total - abs(estorno)
                    if chargeback:
                        total = total - abs(chargeback)
                    if comissao:
                        total = total - abs(comissao)

                    total = round(total, 2)

                    sql_db_ro_cursor = sql_db_ro_conn.cursor()
                    sql_db_ro_cursor.execute(sql_qry_select_id_base, sql_vars)
                    consolidado_id_result = sql_db_ro_cursor.fetchone()
                    sql_db_ro_cursor.close()

                    consolidado_id = consolidado_id_result["id"]
                    pgtosConsolidados = {}

                    pgtosConsolidados["id"] = consolidado_id
                    pgtosConsolidados["registros"] = registros
                    pgtosConsolidados["recnos_pendentes"] = registros
                    pgtosConsolidados["valor"] = round(valor, 2)
                    pgtosConsolidados["estorno"] = round(estorno, 2)
                    pgtosConsolidados["chargeback"] = round(chargeback, 2)
                    pgtosConsolidados["comissao"] = round(comissao, 2)
                    pgtosConsolidados["total"] = round(total, 2)
                    pgtosConsolidados["saldo"] = round(valor, 2)
                    pgtosConsolidados["saldo_protheus"] = round(valor, 2)

                    if estorno:
                        pgtosConsolidados["estorno_divergencia"] = "true"
                    if chargeback:
                        pgtosConsolidados["chargeback_divergencia"] = "true"

                    sql_qry_update_set = """SET"""

                    sql_qry_update_vars = []

                    for key, value in pgtosConsolidados.items():
                        if key != "id":
                            sql_qry_update_set = (
                                sql_qry_update_set + "\n    " +
                                str(key) + " = %s ,"
                            )
                            sql_qry_update_vars.append(str(value))

                    sql_qry_update_set = sql_qry_update_set[
                        0: len(sql_qry_update_set) - 2
                    ]

                    sql_qry_update_vars.extend([consolidado_id])

                    sql_qry_update_vars = tuple(sql_qry_update_vars)

                    sql_qry_update = sql_qry_update_base.format(
                        set=sql_qry_update_set)

                    vars_rau_set_timeline = ""
                    if estorno == 0 and chargeback == 0:
                        vars_rau_set_timeline = (
                            "ESTORNOS_CHARGEBACK",
                            _fonte_id,
                            _filial,
                            _data_recebimento,
                            _parcela,
                        )

                    try:
                        dev_info(
                            "vars_rau_set_timeline:\n" +
                            str(vars_rau_set_timeline)
                        )  # Chamar a função rau_settimeline após o refactoring dela, com os parametros definidos aqui

                        sql_db_rw_cursor.execute(
                            sql_qry_update, sql_qry_update_vars)
                        # print(cursor.statement)

                        if sql_db_rw_cursor.rowcount:
                            sql_db_rw_conn.commit()

                        # Adiciona histórico da movimentação
                        "\App\Traits\Funcoes::addMovimentacaoHistorico(["
                        vars_add_movimentacao_historico = {}
                        vars_add_movimentacao_historico["origem_id"] = (
                            pgtosConsolidados["id"],
                        )
                        vars_add_movimentacao_historico["origem_analitico"] = False
                        vars_add_movimentacao_historico["origem_consolidado"] = True
                        vars_add_movimentacao_historico["origem_titulo"] = False
                        vars_add_movimentacao_historico["destino_id"] = None
                        vars_add_movimentacao_historico["destino_analitico"] = None
                        vars_add_movimentacao_historico["destino_consolidado"] = None
                        vars_add_movimentacao_historico["destino_titulo"] = None
                        vars_add_movimentacao_historico[
                            "movimento_valor"
                        ] = pgtosConsolidados["saldo_protheus"]
                        vars_add_movimentacao_historico[
                            "movimento_data"
                        ] = datetime.now()

                        vars_add_movimentacao_historico["movimento_historico"] = (
                            'Consolidado ID "'
                            + str(pgtosConsolidados["id"])
                            + '", Fonte ID "'
                            + str(_fonte_id)
                            + '", Filial "'
                            + str(_filial)
                            + '", na data de recebimento "'
                            + str(_data_recebimento)
                            + '", parcela "'
                            + str(_parcela)
                            + '", importado com saldo "'
                            + str(pgtosConsolidados["saldo_protheus"])
                            + '"'
                        )
                        vars_add_movimentacao_historico["usuario_id"] = 2

                        dev_info("vars_add_movimentacao_historico: " +
                                 str(vars_add_movimentacao_historico))

                        info = "Registros consolidados com sucesso!"
                        dev_info(info)
                        vars_log = (
                            2,
                            "url()->current()",
                            info,
                            "cmd.consolida_pagamento_job.ok",  # "cmd." + self.__class__.__name__ + ".ok",
                        )
                        dev_info(vars_log)

                        info = (
                            '[ConsolidadoPagamentos] Fonte de pagamento ID "'
                            + str(_fonte_id)
                            + '", filial "'
                            + str(_filial)
                            + '", na data "'
                            + str(_data_recebimento)
                            + '", parcela "'
                            + str(_parcela)
                            + '", processado.'
                        )
                        dev_info(info)

                        var_notifica = info
                        dev_info(var_notifica)

                        rau_set_timeline = (
                            "TOTAIS_CALCULADOS",
                            _fonte_id,
                            _filial,
                            _data_recebimento,
                            _parcela,
                        )
                        dev_info(rau_set_timeline)

                        info = " Adicionando pedidos à fila a job AtualizaPedidosMMJob"
                        dev_info(info)

                        vars_log = (
                            2,
                            "url.current",
                            info,
                            # "cmd." + self.__class__.__name__ + ".info",
                            "cmd.consolida_pagamento_job.info",
                        )
                        dev_info(vars_log)

                        vars_atualiza_pedidos_mm_job_dispatch = {
                            "fonte_id": _fonte_id,
                            "filial": _filial,
                            "data_recebimento": _data_recebimento,
                            "parcela": _parcela,
                        }
                        # ->onConnection('redis')
                        # //->onQueue(( (count($arr_Queues) > 0 && array_keys($arr_Queues, min($arr_Queues))[0]) ? array_keys($arr_Queues, min($arr_Queues))[0] : 'cron_atualiza_pedidos_mm_1' ));
                        # ->onQueue(( (count($arr_Queues) > 0 && array_keys($arr_Queues, min($arr_Queues))[0]) ? array_keys($arr_Queues, min($arr_Queues))[0] : 'cron_processar_pagamentos_1' ));
                        #  unset($arr_Queues);
                        dev_info("consolida_pagamento_job executado sem erros")

                    except Exception as e:
                        breakpoint()
                        sql_db_rw_conn.rollback()

                        info = (
                            'Ocorreu falha ao consolidar os registros para a Fonte ID "'
                            + _fonte_id
                            + '", Filial "'
                            + _filial
                            + '", na data de recebimento "'
                            + _data_recebimento
                            + '", parcela "'
                            + _parcela
                            + '". Excessao: '
                            + str(e)
                        )
                        dev_info(info)

                        vars_log = (
                            2,
                            "url.current",
                            info,
                            # "cmd." + self.__class__.__name__ + ".erro",
                            "cmd.consolida_pagamento_job.erro",
                        )
                        dev_info(vars_log)

                        var_notifica = info
                        dev_info(var_notifica)

                        dev_info("Erro: " + str(e.__dict__.items()))
    dev_info('consolida_pagamento_job concluído')


def dev_info(msg=None):
    skip = False

    if skip:
        return None

    if msg is None:
        msg = 10 * "\n"

    txt = str(
        "\n\033[0;32m"
        + 10 * "-"
        + "  %s  "
        + 10 * "-"
        + "\n%s\n"
        + 50 * "-"
        + "\033[0m"
    ) % (
        str(datetime.now()),
        str(msg),
    )
    logger.info(txt)
    print(txt)


def mapear_campos(fonte_id):
    global sql_qry_select
    global sql_db_ro_conn

    # [nome do campo, cod campo, query sql, buscar ou nao?]
    campos = [
        ["pedido", None, None, False],
        ["valor", None, None, True],
        ["estorno", None, None, True],
        ["chargeback", None, None, True],
        ["parcela", None, None, False],
        ["comissao", None, None, True],
    ]

    qry_campos = ""
    for campo in campos:
        if campo[3]:
            # substitui o nome do campo aqui pois ao jogá-lo no cursor pela função do mysql.connector, este coloca entre aspas para evitar injection, dando erro na lógica.
            sql_db_ro_cursor = sql_db_ro_conn.cursor()
            qry_map_campo = qry_map_campos_base.format(campo=campo[0])
            sql_db_ro_cursor.execute(qry_map_campo, (fonte_id,))

            cod_campo_result = sql_db_ro_cursor.fetchone()
            sql_db_ro_cursor.close()

            cod_campo = cod_campo_result["campo_id"]
            campo[1] = cod_campo
            campo[2] = (
                "    SUM( CAST( replace( pgto_tbl.campo_"
                + str(campo[1])
                + ", ',', '.') as DECIMAL(18,2) ) ) as "
                + campo[0]
                + """,
"""
            )
            qry_campos += campo[2]
    qry_campos = qry_campos[0: len(qry_campos) - 2]
    sql_qry_select = sql_qry_select_base.format(campos=qry_campos)
    return
