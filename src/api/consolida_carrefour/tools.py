import os
from typing import List
from .queue import create_message_sqs
from .errors import Errors
from pprint import pprint
from starlette.background import BackgroundTask
from starlette.responses import JSONResponse
import redis
from datetime import datetime
import logging

# from .repository import connect_database_ro, connect_database_rw, upload_to_s3, check_registros_anteriores
# from .util import create_logging_nr, remove_accents, set_consolidado_error, logger, proper_stract

from .repository import connect_database_ro, connect_database_rw, upload_to_s3, check_registros_anteriores
from .util import create_logging_nr, remove_accents, set_consilidado_error, logger, proper_stract

# from .sqsqueue import create_message_sqs

_fonte_id = None
_filial = None
_data_recebimento = None
_parcela = None
_comissao_perc = None

sql_db_ro_conn = None
sql_db_ro_cursor = None

sql_db_rw_conn = None
sql_db_rw_cursor = None

sql_qry_select = None
sql_qry_update = None

_array_consolidado = {}
_dados_nro = 0

async def consolida_carrefour_job(**kwargs) -> List:
    """ Retorna uma lista de informações do arquivo(carrefour) que será processado
    Parâmetros:
        fonte_id (int) id da fonte de pagamento
        data_recebimento (str) data de recebimento do arquivo
        data_enviado: (str) data de envio do arquivo
        file_path: (str) caminho do arquivo
        file_name: (str) nome do arquivo
        file_ext: (str) extensão do arquivo
        file_hash: (str) hash do arquivo
    Retorno: List de dados
    """

    fonte_id = kwargs["fonte_id"]
    data_recebimento = kwargs["data_recebimento"]
    filial = kwargs["filial"]
    parcela = kwargs["parcela"]

    global _fonte_id
    global _filial
    global _data_recebimento
    global _parcela
    global _comissao_perc

    global sql_db_ro_conn
    global sql_db_ro_cursor

    global sql_db_rw_conn
    global sql_db_rw_cursor

    global array_consolidado
    global dados_nro

    _fonte_id = fonte_id
    _data_recebimento = data_recebimento
    _filial = filial
    _parcela = parcela

    _comissao_perc = os.getenv('COMISSAO_PERC')

    print("Fonte -> " + _fonte_id)
    print("Data -> " + _data_recebimento)
    print("Filial -> " + _filial)
    print("Parcela -> " + str(_parcela))

    sql_db_ro_conn = await connect_database_ro()
    sql_db_rw_conn = await connect_database_rw()
    
    if _fonte_id is not None and _filial is not None and _data_recebimento is not None:
        r = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=int(os.getenv('REDIS_PORT')) or 6379,
            password=os.getenv('REDIS_PASSWORD')
        )

        await create_logging_nr(message=f"""[ConsolidaComissaoCarrefour]==========> Iniciando processo""")        
                                
        r.set( str(_fonte_id) + ':' + str(_filial) + ':' + str(_data_recebimento) + ':ConsolidaComissao', '1' )
        
    print(f"[ConsolidaComissaoCarrefour]==========> Iniciando processos")

    MapeiaCampos = buscaMapeiaCampos(_fonte_id, _parcela) #chama aqui primeiro e conectar no banco e traz os valores com sucesso
    
    # print("MapeiaCampos -> " + str(MapeiaCampos))
    
    if MapeiaCampos == False:
        msg_log = ""
        msg_log += "Comissão Principal não informada. " if comissao else ""
        msg_log += "Valor Principal não informado. " if valor else ""
        msg_log += "Fonte ID " + _fonte_id + " - Filial " + _filial

        print(f"> {msg_log}")
        await create_logging_nr(message=f"""{msg_log}""")
    else:
        PagamentosAnaliticos = getPagamentosAnaliticos(MapeiaCampos, _fonte_id, _parcela) #chama aqui outra funcao que utiliza do banco tbm mas ai da aquele problema
        
        if len(PagamentosAnaliticos):

            array_consolidado = {}
            for pagamento in PagamentosAnaliticos:
                comissao = valor = id_pgto = 0
                id_pgto = int(pagamento["id"])  #762
                pedido = str(proper_stract(pagamento["pedido"]))
                comissao = proper_stract(pagamento["comissao"])
                valor = proper_stract(pagamento["valor"])
                
                pedido = pedido.replace(".", "")
                pedido = pedido.replace(",", "")

                if comissao > 0:
                    id_pgto_array = []
                    id_pgto_array.append(int(id_pgto))
                    array_consolidado[str(pedido)] = {
                        "id": id_pgto_array,
                        "comissao": comissao,
                        "valor": 0.0
                    }

                if valor > 0:
                    array_consolidado[str(pedido)] = {
                        "valor": str(valor)
                    }
                    
                    aux = array_consolidado[str(pedido)].get('valor')

                    if aux is None or aux == 0:
                        valor = float(valor) + float(aux)
                                        
                    if comissao > 0:
                        id_pgto_array = []
                        id_pgto_array.append(int(id_pgto))
                        array_consolidado[str(pedido)] = {
                            "id": id_pgto_array,
                            "comissao": comissao,
                            "valor": valor
                        }
                    else:
                        array_consolidado[str(pedido)] = {
                            "valor": valor
                        }

            try:
                dados_nro = dados_tot = 0
                dados_tot = len(array_consolidado)

                # calcula % comissao e salva valores consolidados
                for x, y in array_consolidado.items():

                    # Enquanto não é o último item, seta o progresso
                    runJob = r.get(str(fonte_id) + ':' + str(filial) + ':' + str(data_recebimento) + ':ConsolidaComissao') or 0

                    # Setamos também o "ConsolidaComissao_PB_Tot" e "ConsolidaComissao_PB_Val" apenas para registro de chave no Redis
                    if int(runJob) == 1:
                        if proper_stract(y.get('valor')) > 0 and proper_stract(y.get('comissao')) > 0:
                            dados_nro += 1

                            r.set( str(fonte_id) + ':' + str(filial) + ':' + str(data_recebimento) + ':ConsolidaComissao_PB_Tot', dados_tot )
                            r.set( str(fonte_id) + ':' + str(filial) + ':' + str(data_recebimento) + ':ConsolidaComissao_PB_Val', dados_nro )
                            
                            array_consolidado[str(x)] = {
                                "id": y.get('id'),
                                "comissao": y.get('comissao'),
                                "valor": y.get('valor'),
                                "comissao_perc": round( ((proper_stract(y.get('comissao'))/proper_stract(y.get('valor'))) * 100), 2)
                            }

                            for key in array_consolidado[str(x)].get('id'):
                                pagamentoAnalitico = getInformacaoPagamentoAnalitico(key)
                                if(pagamentoAnalitico):
                                    try:
                                        alteraComissao = setAlteraComissao(array_consolidado[str(x)].get('comissao_perc'), key)
                                        if(alteraComissao):
                                            print(f"> Registros consolidados com sucesso! {array_consolidado[str(x)]}")
                                            await create_logging_nr(message=f"""Registros consolidados com sucesso! {array_consolidado[str(x)]}""")
                                    except Exception as e:
                                        print(f"> Ocorreu falha ao consolidar os registros. Erro: {str(e)}")
                                        await create_logging_nr(message=f"""Ocorreu falha ao consolidar os registros. Erro: {str(e)}""")
                                else:
                                    print(f"> Registro não localizado.") 
                                    await create_logging_nr(message=f"""Registro não localizado.""")        

                runJob = r.get(str(fonte_id) + ':' + str(filial) + ':' + str(data_recebimento) + ':ConsolidaComissao_PB_Tot') or 0
                if int(runJob) != 0:
                    r.delete( str(fonte_id) + ':' + str(filial) + ':' + str(data_recebimento) + ':ConsolidaComissao_PB_Tot' )
                    print(f"> Removendo: {str(fonte_id) + ':' + str(filial) + ':' + str(data_recebimento) + ':ConsolidaComissao_PB_Tot'}")

                runJob = r.get(str(fonte_id) + ':' + str(filial) + ':' + str(data_recebimento) + ':ConsolidaComissao_PB_Val') or 0
                if int(runJob) != 0:
                    r.delete( str(fonte_id) + ':' + str(filial) + ':' + str(data_recebimento) + ':ConsolidaComissao_PB_Val' )
                    print(f"> Removendo: {str(fonte_id) + ':' + str(filial) + ':' + str(data_recebimento) + ':ConsolidaComissao_PB_Val'}")
                    
            except Exception as e:
                print(f"> Ocorreu falha ao consolidar os registros. Erro: {str(e)}")
                await create_logging_nr(message=f"""Ocorreu falha ao consolidar os registros. Erro: {str(e)}""")
        else:
            print(f"> Nenhum registro de Comissão Carrefour foi encontrado.")
            await create_logging_nr(message=f"""Nenhum registro de Comissão Carrefour foi encontrado.""")

    r.delete( str(fonte_id) + ':' + str(filial) + ':' + str(data_recebimento) + ':ConsolidaComissao' )
    print(f"> Removendo: {str(fonte_id) + ':' + str(filial) + ':' + str(data_recebimento) + ':ConsolidaComissao'}")

    print(f"[ConsolidaComissaoCarrefour]==========> Finalizando processos")
    print(f">>>>>>>>>>>>>>>file_hash Carrefour <<<<<<<<<<< ")


def buscaMapeiaCampos(fonte_id, parcela):
    global sql_qry_select

    qry_map_campos = """\
                        SELECT
                            campo_id
                        FROM
                            fonte_campos
                        WHERE
                            fonte_id=%s
                            AND {campo}_principal=1\
                        """

    # [nome do campo, cod campo, query sql, buscar ou nao?]
    campos = [
        ["pedido", None, None, True],
        ["valor", None, None, True],
        ["comissao", None, None, True],
    ]

    qry_campos = ""

    valida = None

    for campo in campos:
        if campo[3]:
            # substitui o nome do campo aqui pois ao jogá-lo no cursor pela função do mysql.connector, este coloca entre aspas para evitar injection, dando erro na lógica.
            qry_map_campo = qry_map_campos.format(campo=campo[0])

            with sql_db_ro_conn.cursor() as cursor:     
                cursor.execute(qry_map_campo, (fonte_id,))
                cod_campo_results = cursor.fetchall()
                cursor.close()
                
                if cod_campo_results == None:
                    valida = False
                else:
                    cod_campo = cod_campo_results[0]["campo_id"]
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
                    valida = True         
                    
    if valida == True:
        qry_campos = qry_campos[0 : len(qry_campos) - 2]
        qry_campos += "      1 as numero"

        sql_qry_select = """\
                    SELECT
                        pgto_tbl.id,
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
                        pgto_tbl.parcela""".format(
            campos=qry_campos
        )
        
        return sql_qry_select
    else:
        return valida


def getPagamentosAnaliticos(MapeiaCampos, fonte_id, parcela) -> List:
    """ Retorna os itens que não foram consolidados"""

    with sql_db_ro_conn.cursor() as cursor:   
        cursor.execute(MapeiaCampos, (fonte_id, _filial, _data_recebimento, parcela,))
        itensAnaliticos = cursor.fetchall()
        cursor.close()

    return itensAnaliticos

def getInformacaoPagamentoAnalitico(id_pagto) -> List:
    """ Retorna todas as informações de cada pagamento analitico"""
    
    with sql_db_ro_conn.cursor() as cursor:  
        cursor.execute("SELECT * FROM pgtos_analiticos WHERE id = %s", (id_pagto,))
        pagamentoAnalitico = cursor.fetchall()
        cursor.close()

    return pagamentoAnalitico

def setAlteraComissao(comissao, id_pagto) -> List:
    """ Altera a informação de Comissão nos Pagamentos Analiticos(campo_9)"""
    from pymysql import Error
    result = False

    try:
        with sql_db_rw_conn.cursor() as cursor: 
            cursor.execute("UPDATE pgtos_analiticos SET campo_%s = '%s' WHERE id = %s", (int(_comissao_perc), comissao, id_pagto,))
        sql_db_rw_conn.commit()
        result = True
    except Error as e:
        print(e)

    return result
