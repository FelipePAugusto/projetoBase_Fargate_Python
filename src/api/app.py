from starlette.background import BackgroundTask
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.applications import Starlette
import os
import newrelic.agent

from .consolida_pagamento.tools import consolida_pagamento_job, dev_info
from .consolida_carrefour.tools import consolida_carrefour_job

newrelic.agent.initialize(os.environ.get("NEW_RELIC_CONFIG_FILE"))
newrelic.agent.register_application(timeout=10.0)

background_task = None


dev_info('api/app.py:18')


async def consolida_pagamento(request: Request) -> JSONResponse:
    global background_task

    dev_info("consolida_pagamento request start\n" + str(request))

    try:
        payload = await request.form()

        if len(payload) == 0:
            payload = None

        parameters = dict(payload.items())

        background_task = BackgroundTask(
            consolida_pagamento_job, **parameters)

        message = "Consolidação de pagamento iniciada"
    except Exception as e:
        message = str(e) + " - " + str(request)

    return JSONResponse(
        {
            "retorno": str(payload),
            "message": message,
        },
        background=background_task,
    )


async def consolida_comissao_carrefour(request) -> JSONResponse:
    global background_task
    # dev_info("consolida_pagamento request start\n" + str(request))
    # return JSONResponse({"Carrefour": "Até aqui vai"})

    try:
        payload = await request.form()

        if len(payload) == 0:
            payload = None

        parameters = dict(payload.items())

        background_task = BackgroundTask(
            consolida_carrefour_job, **parameters)

        message = 'Consolidação da Comissão do Carrefour iniciada'

    except Exception as e:
        message = str(e) + " - " + str(request)

    return JSONResponse({
        "message": message,
    }, background=background_task)


# async def consolida_comissao_carrefour(request) -> JSONResponse:
#     return JSONResponse({'alive': 'Carrefour OK'})


async def index(request) -> JSONResponse:
    return JSONResponse({'alive': 'INDEX OK'})


async def teste_redekasa(request) -> JSONResponse:
    global background_task

    dev_info("teste_redekasa request start\n" + str(request))

    try:
        payload = await request.form()

        if len(payload) == 0:
            payload = None

        parameters = dict(payload.items())

        message = "Teste_redekasa bem sucedido"
    except Exception as e:
        message = str(e) + " - " + str(request)

    return JSONResponse(
        {
            "retorno": str(payload),
            "message": message,
        },
        background=background_task,
    )


routes = [
    Route('/', endpoint=index, methods=["POST", "GET"]),
    Route("/consolida_pagamento",
          endpoint=consolida_pagamento, methods=["POST"]),
    Route("/consolida_comissao_carrefour",
          endpoint=consolida_comissao_carrefour, methods=["POST"]),
    Route('/teste_redekasa', endpoint=teste_redekasa, methods=["POST"]),
    Route('/', endpoint=index, methods=["POST"])
]

app = Starlette(debug=True, routes=routes)
