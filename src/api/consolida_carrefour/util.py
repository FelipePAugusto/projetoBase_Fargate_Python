from newrelic.agent import NewRelicContextFormatter
import logging
import requests
import os
import re
import datetime
from .errors import Errors
from datetime import datetime
from .repository import *
#handler = logging.StreamHandler()
#formatter = NewRelicContextFormatter()
#handler.setFormatter(formatter)
#logger = logging.getLogger()
#logger.addHandler(handler)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

if not os.path.exists("logs/"):
    os.makedirs("logs/")
logger.addHandler(logging.FileHandler('logs/logs.txt'))


async def create_logging_nr(*,message: str = None, chaves: dict = None) -> bool:
    return True

    """ Responsável por enviar logs para o new relic
    Parâmetros:
        mensage (dict) : mensagem de rastreio
        chaves (dict) : chaves que serão necessárias para pesquisa posterior
    Retorno:
        bool indicando sucesso ou falha
    """
    try:
        response = False
        headers = {
            "Content-Type": "application/json",
            "X-License-Key": "19152807b2e07bb8f4f07bc85165b0f0b2ea7f84",
            "Accept": "*/*",
            "POST": "/log/v1 HTTP/1.1",
            "Host": "log-api.newrelic.com"
        }
        timestamp = datetime.timestamp(datetime.now()),
        payload = {
            "entity.guid": "MzE3NzAzfEFQTXxBUFBMSUNBVElPTnw2NzYyNTg1NzM",
            "debug": "False",
            "environment": "staging",
            "level":"INFO",
            "levelname": "INFO",
            "message": message,
            "service": "TIOPATINHAS-PROCESSA-PAGAMENTO",
            "service_name": "TIOPATINHAS-PROCESSA-PAGAMENTO",
            "timestamp": timestamp,
            "host": "https://conciliador.madeiramadeira.com.br"
        }
        print(payload);
        # if chaves is not None:
        #     payload.update(chaves)

        # r = requests.post(
        #     os.environ.get('NEW_RELIC_LOG_API'),
        #     json=payload,
        #     headers=headers)

        # if(r.status_code == 202):
        #     response = True

    except Exception as e:
        response = False
        Errors(f"Não foi Possível inserir log possível erro: {e}")

    return response

async def remove_accents(texto):
    import unicodedata


    nfkd_form = unicodedata.normalize('NFKD', texto)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')

    return only_ascii

async def set_consilidado_error(*,info: str = None, fonte_id: int = None, filial: str = None, data_recebimento: str = None) -> bool:
    from pymysql import Error
    from .repository import connect_database_rw
    result = False
    try:
        database = await connect_database_rw()
        if info is not None and fonte_id is not None and filial is not None and data_recebimento is not None:
            with database.cursor() as cursor:
                cursor.execute("""
                    UPDATE
                        pgtos_consolidados
                    SET
                        is_error = 1,
                        error_msg = '%s'
                    WHERE
                        fonte_id = %s ,
                        filial = '%s' ,
                        data_recebimento = %s
                    LIMIT 1

                """,(info.replace('\n', ' '), fonte_id, filial, data_recebimento)
                )
            database.commit()
            result = True
    except Error as e:
        print(e)

    return result

async def get_tags(formula,tag_init, tag_finish):
    contents = []
    start_demiliter_len = len(tag_init)
    end_delimiter_len = len(tag_finish)
    start_from = 0
    content_start = -1
    content_end = 0
    content_start = formula.find(tag_init, start_from)
    # logger.info(formula)
    while content_start == 0:
        content_start += start_demiliter_len
        content_end = formula.find(tag_finish,content_start)
        if content_end == 0:
            break
        contents.append(formula[content_start : content_end])

    return contents

async def get_dado(dado: dict, tipo: str, tag_formula: str, is_coluna_virtual: bool = False, pgtos_analitico: dict = None):
    valor = None
    corrige_dados = {}

    for key in dado:
        chave = await remove_accents(key.upper().replace(" ", "_")).decode('utf-8')
        corrige_dados[chave] = dado[key]

    if is_coluna_virtual is False:
        if tag_formula.find('=(') != -1:
            tags = await get_tags(tag_formula, '=(', ')')
            posicao = tags[0].split(",")[0]
            delimitador = tags[0].split(",")[1]
            valor = None
            condicao_operador = None
            condicao_valor = None
            if tags[0].split(",")[2] and tags[0].split("2")[3]:
                condicao_operador = tags[0].split(",")[2]
                condicao_valor = tags[0].split(",")[3]
            tag = tag_formula.split('=(')

            if posicao.upper() == 'L':
                valor = corrige_dados.get([tag[0]].split(delimitador))
                valor =  valor[-1]
            else:
                valor = corrige_dados.get([tag[0]].split(delimitador))
                if len(valor) > 1:
                    valor = valor[posicao-1]
                else:
                    valor = valor[0]
            if valor is not None and condicao_operador is not None and condicao_valor is not None:
                if await num_cond(corrige_dados, condicao_operador, condicao_valor) is False:
                    valor = corrige_dados
        else:
            if corrige_dados.get(tag_formula):
                valor = corrige_dados.get(tag_formula)
    else:
        if tag_formula.find('=(') != -1:
            tags = await get_tags(tag_formula, '=(', ')')
            posicao = tags[0].split(",")[0]
            delimitador = tags[0].split(",")[1]
            valor = None
            condicao_operador = None
            condicao_valor = None
            if tags[0].split(",")[2] and tags[0].split("2")[3]:
                condicao_operador = tags[0].split(",")[2]
                condicao_valor = tags[0].split(",")[3]
            tag = tag_formula.split('=(')

            if posicao.upper() == 'L':
                valor = corrige_dados.get([tag[0]].split(delimitador))
                valor =  valor[-1]
            else:
                valor = corrige_dados.get([tag[0]].split(delimitador))
                if len(valor) > 1:
                    valor = valor[posicao-1]
                else:
                    valor = valor[0]
            if valor is not None and condicao_operador is not None and condicao_valor is not None:
                if await num_cond(condicao_operador, '|>', 'CD'):
                    if await num_cond(corrige_dados, condicao_operador, condicao_valor, delimitador) is False:
                        valor = corrige_dados
                if await num_cond(condicao_operador, '|>', '⊇A') or num_cond(condicao_operador, '|>', '⊉A'):
                    if num_cond(valor, condicao_operador, condicao_valor, delimitador) is False:
                        valor = corrige_dados
                if await num_cond(condicao_operador, '|>', 'T'):
                    if await num_cond(valor, condicao_operador, condicao_valor, delimitador) is False:
                        valor = corrige_dados
        else:
            database = await connect_database_ro()
            with database.cursor() as cursor:
                cursor.execute("""
                    SELECT id
                        FROM campos
                    WHERE nome = %s
                    LIMIT 1
                """)
            campo_id = cursor.fetchone()
            valor = pgtos_analitico['campo_'+campo_id]

    if tipo is not None and valor is not None:
        with Switch(tipo) as case:
            if case('STRING'):
                valor = valor.strip()
            elif case('INTEGER'):
                valor = valor.replace(',', '.')
                valor = int(valor)
                if valor is not None or isinstance(valor, int) is False:
                    valor = 0
                valor = re.search(r'\d+',valor).group()
            elif case('FLOAT'):
                if valor is None:
                    valor = 0
                valor = valor.replace(",",".")
                valor = float(valor)
            elif case('DATE'):
                valor = valor.strip()
                valor = datetime.datetime.strptime(valor, '%d/%m/%Y')
    return valor


async def num_cond(var1: str, op: str, var2: str, var3: str = None):

    var1 = var1.upper()
    var2 = var2.upper()
    if var2 == '[NULO]':
        var2 = None

    with Switch(op) as case:
        if case("="):
            return var1 == var2
        elif case("!="):
            return var1 != var2
        elif case("!="):
            return var1 != var2
        elif case(">="):
            return var1 >= var2
        elif case("<="):
            return var1 <= var2
        elif case(">"):
            return var1 > var2
        elif case("<"):
            return var1 < var2
        elif case("⊇"):
            return var1.find(var2) != False
        elif case("⊉"):
            return var1.find(var2) == False
        elif case("|>"):
            return var1[0:len(var2)] == var2
        elif case(">|"):
            return var1[0:-len(var2)] == var2
        elif case("T="):
            return len(var1) == var2
        elif case("T!="):
            return len(var1) != var2
        elif case("T>="):
            return len(var1) >= var2
        elif case("T<="):
            return len(var1) <= var2
        elif case("T>"):
            return len(var1) >  var2
        elif case("T<"):
            return len(var1) <  var2
        elif case("CD="):
            return var1.split(var3) == var2
        elif case("CD!="):
            return var1.split(var3) != var2
        elif case("CD>="):
            return var1.split(var3) >= var2
        elif case("CD<="):
            return var1.split(var3) <= var2
        elif case("CD>"):
            return var1.split(var3) > var2
        elif case("CD<"):
            return var1.split(var3) < var2
        elif case("⊇A"):
            return re.search(var2, var1)
        elif case("⊉A"):
            return re.search(var2, var1)
        else:
            return False

async def verifica_condicoes(condicoes, dado):
    retorno = False
    dado_new = {}
    for key in dado:
        dado_new[remove_accents(key.upper().replace(" ", "_")).decode('utf-8')] = dado[key]

    if len(condicoes) > 2 and condicoes[2]:
        if condicoes[2]['condicao_tipo'] == 'AND' and condicoes[1]['condicao_tipo'] == 'AND':
            cond_0 = await num_cond(dado_new.get(condicoes[0]['cabecalho_nome']),condicoes[0]['sinal_tipo'], condicoes[0]['resultado_valor'])
            cond_1 = await num_cond(dado_new.get(condicoes[1]['cabecalho_nome']),condicoes[1]['sinal_tipo'], condicoes[1]['resultado_valor'])
            cond_2 = await num_cond(dado_new.get(condicoes[2]['cabecalho_nome']),condicoes[2]['sinal_tipo'], condicoes[2]['resultado_valor'])
            if cond_0 and cond_1 and cond_2:
                retorno = True

        elif condicoes[2]['condicao_tipo'] == 'AND' and condicoes[1]['condicao_tipo'] == 'OR':
            cond_0 = await num_cond(dado_new.get(condicoes[0]['cabecalho_nome']),condicoes[0]['sinal_tipo'], condicoes[0]['resultado_valor'])
            cond_1 = await num_cond(dado_new.get(condicoes[1]['cabecalho_nome']),condicoes[1]['sinal_tipo'], condicoes[1]['resultado_valor'])
            cond_2 = await num_cond(dado_new.get(condicoes[2]['cabecalho_nome']),condicoes[2]['sinal_tipo'], condicoes[2]['resultado_valor'])

            if (cond_0 or cond_1) and  cond_2:
                retorno = True

        elif condicoes[2]['condicao_tipo'] == 'OR' and condicoes[1]['condicao_tipo'] == 'AND':
            cond_0 = await num_cond(dado_new.get(condicoes[0]['cabecalho_nome']),condicoes[0]['sinal_tipo'], condicoes[0]['resultado_valor'])
            cond_1 = await num_cond(dado_new.get(condicoes[1]['cabecalho_nome']),condicoes[1]['sinal_tipo'], condicoes[1]['resultado_valor'])
            cond_2 = await num_cond(dado_new.get(condicoes[2]['cabecalho_nome']),condicoes[2]['sinal_tipo'], condicoes[2]['resultado_valor'])

            if (cond_0 and cond_1) or  cond_2:
                retorno = True

        elif condicoes[2]['condicao_tipo'] == 'OR' and condicoes[1]['condicao_tipo'] == 'OR':
            cond_0 = await num_cond(dado_new.get(condicoes[0]['cabecalho_nome']),condicoes[0]['sinal_tipo'], condicoes[0]['resultado_valor'])
            cond_1 = await num_cond(dado_new.get(condicoes[1]['cabecalho_nome']),condicoes[1]['sinal_tipo'], condicoes[1]['resultado_valor'])
            cond_2 = await num_cond(dado_new.get(condicoes[2]['cabecalho_nome']),condicoes[2]['sinal_tipo'], condicoes[2]['resultado_valor'])

            if cond_0 or cond_1 or cond_2:
                retorno = True

    else:
        if len(condicoes)>1 and condicoes[1]:
            if condicoes[1]['condicao_tipo'] == 'AND':
                cond_0 = await num_cond(dado_new.get(condicoes[0]['cabecalho_nome']),condicoes[0]['sinal_tipo'], condicoes[0]['resultado_valor'])
                cond_1 = await num_cond(dado_new.get(condicoes[1]['cabecalho_nome']),condicoes[1]['sinal_tipo'], condicoes[1]['resultado_valor'])
                if cond_0 and cond_1:
                    retorno = True
            elif condicoes[1]['condicao_tipo'] == 'OR':
                cond_0 = await num_cond(dado_new.get(condicoes[0]['cabecalho_nome']),condicoes[0]['sinal_tipo'], condicoes[0]['resultado_valor'])
                cond_1 = await num_cond(dado_new.get(condicoes[1]['cabecalho_nome']),condicoes[1]['sinal_tipo'], condicoes[1]['resultado_valor'])
                if cond_0 or cond_1:
                    retorno = False
        else:
            dado_new = {}
            for key in dado:
                dado_new[remove_accents(key.upper().replace(" ", "_")).decode('utf-8')] = dado[key]
            cond_0 = await num_cond(dado_new.get(condicoes[0]['cabecalho_nome']),condicoes[0]['sinal_tipo'], condicoes[0]['resultado_valor'])
            if cond_0:
                retorno = True

    return retorno

async def normalize_regra_api(regra, dado, array_group_by, campo):
    regra = re.sub('[{}()\[\]]','',regra)
    array_regras = regra.split("|")
    is_ok = True
    url = re.findall('(HTTPS?://\S+)', array_regras[0])[0].lower()
    method = array_regras[1]
    parametros = array_regras[2]
    valor_retornado = array_regras[3].lower()
    group_by = array_regras.replace("GROUPBY=",'')
    array_parametros = parametros.split(",")
    array_body_normalize = []

    for item in array_parametros:
        aux = item.slipt("=")
        if aux[1] not in dado:
            value = get_dado(dado, 'STRING', aux[1].upper())
            if value:
                if group_by == aux[1]:
                    if array_group_by == 0:
                        array_group_by[campo] = value
                        array_body_normalize[aux[0]] = value
                    else:
                        [k for k,v in array_group_by.items() if v == value]
                        values_group_by = k
                        if values_group_by:
                            for item_value in values_group_by:
                                if values_group_by != campo:
                                    array_group_by[campo] = value
                                    array_body_normalize[aux[0]] = value
                                else:
                                    is_ok = False
                        else:
                            array_group_by[campo] = value
                            array_body_normalize[aux[0]] = value
            else:
                is_ok = False
    return {
        "method":method,
        "url":url,
        "array_body_normalize":array_body_normalize,
        "valor_retornado":valor_retornado,
        "is_ok":is_ok
        }


async def check_url(url: str ) -> dict:
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError


    req = Request(url)
    resp = dict()
    try:
        response = urlopen(req)
        resp['message'] = "Url ok"
        resp['status_code'] = response.code
    except HTTPError as e:
        resp['message'] = 'Não foi possível acessar a URL %s' % url
        resp['status_code'] = e.code
        return resp
    except URLError as e:
        resp['message'] = ('Não foi possível acessar a URL %s pelo motivo %s') % (url, e.reason)
        resp['status_code'] = 500
        return resp
    else:
       return resp

class Switch:
    def __init__(self, value):
        self._val = value

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return False

    def __call__(self, cond, *mconds):
        return self._val in (cond,)+mconds

def proper_stract(a) -> float:

    if type(a).__name__ != "Decimal":
        a = str(a)

        a = a.replace(" ", "")
        a = a.replace("\n", "")
        a = a.replace("None", "")
        a = a.replace("[NULL]", "")
        a = a.replace("[NULO]", "")

        if a.find(".") and a.find(","):
            if a.find(".") < a.find(","):
                a = a.replace(".", "").replace(",", ".")
            else:
                a = a.replace(",", "")
        else:
            a = a.replace(",", ".")

        if a == "":
            a = 0

    # a = round(a, 2)

    a = round(float(a), 2)

    return a
