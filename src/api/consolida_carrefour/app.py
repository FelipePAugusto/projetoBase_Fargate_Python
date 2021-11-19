import os
#import newrelic.agent
#newrelic.agent.initialize(os.environ.get('NEW_RELIC_CONFIG_FILE'))
#newrelic.agent.register_application(timeout=10.0)

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
from starlette.background import BackgroundTask, BackgroundTasks
from dotenv import load_dotenv
import redis
from json import JSONDecodeError
from .errors import Errors
from .tools import consolida_carrefour_job
from .util import create_logging_nr, logger, check_url
import pathlib
import asyncio
from pprint import pprint
#from multiprocessing import Process

load_dotenv()

#os.environ['REDIS_HOST'] = 'mm_devdocker_mm_redis_1'
#os.environ['REDIS_PORT'] = '6379'
#os.environ['REDIS_PASSWORD'] = ''

async def index(request):
    return JSONResponse({'alive': 'true'})

async def teste():
    import time

    print('>>START<<')

    print(f"os.environ.get('DB_CONNECTION'): {os.environ.get('DB_CONNECTION')}")
    print(f"os.environ.get('DB_HOST_RO'): {os.environ.get('DB_HOST_RO')}")
    print(f"os.environ.get('DB_HOST_RW'): {os.environ.get('DB_HOST_RW')}")
    print(f"os.environ.get('DB_PORT'): {os.environ.get('DB_PORT')}")
    print(f"os.environ.get('DB_DATABASE'): {os.environ.get('DB_DATABASE')}")
    print(f"os.environ.get('DB_USERNAME'): {os.environ.get('DB_USERNAME')}")
    print(f"os.environ.get('DB_PASSWORD'): {os.environ.get('DB_PASSWORD')}")
    print(f"os.environ.get('DB_RO_CONNECTION'): {os.environ.get('DB_RO_CONNECTION')}")
    print(f"os.environ.get('DB_RO_HOST'): {os.environ.get('DB_RO_HOST')}")
    print(f"os.environ.get('DB_RO_PORT'): {os.environ.get('DB_RO_PORT')}")
    print(f"os.environ.get('DB_RO_DATABASE'): {os.environ.get('DB_RO_DATABASE')}")
    print(f"os.environ.get('DB_RO_USERNAME'): {os.environ.get('DB_RO_USERNAME')}")
    print(f"os.environ.get('DB_RO_PASSWORD'): {os.environ.get('DB_RO_PASSWORD')}")
    print(f"os.environ.get('DB_RW_CONNECTION'): {os.environ.get('DB_RW_CONNECTION')}")
    print(f"os.environ.get('DB_RW_HOST'): {os.environ.get('DB_RW_HOST')}")
    print(f"os.environ.get('DB_RW_PORT'): {os.environ.get('DB_RW_PORT')}")
    print(f"os.environ.get('DB_RW_DATABASE'): {os.environ.get('DB_RW_DATABASE')}")
    print(f"os.environ.get('DB_RW_USERNAME'): {os.environ.get('DB_RW_USERNAME')}")
    print(f"os.environ.get('DB_RW_PASSWORD'): {os.environ.get('DB_RW_PASSWORD')}")
    print(f"os.environ.get('DB_UNBUFFERED_CONNECTION'): {os.environ.get('DB_UNBUFFERED_CONNECTION')}")
    print(f"os.environ.get('DB_UNBUFFERED_HOST_RO'): {os.environ.get('DB_UNBUFFERED_HOST_RO')}")
    print(f"os.environ.get('DB_UNBUFFERED_HOST_RW'): {os.environ.get('DB_UNBUFFERED_HOST_RW')}")
    print(f"os.environ.get('DB_UNBUFFERED_PORT'): {os.environ.get('DB_UNBUFFERED_PORT')}")
    print(f"os.environ.get('DB_UNBUFFERED_DATABASE'): {os.environ.get('DB_UNBUFFERED_DATABASE')}")
    print(f"os.environ.get('DB_UNBUFFERED_USERNAME'): {os.environ.get('DB_UNBUFFERED_USERNAME')}")
    print(f"os.environ.get('DB_UNBUFFERED_PASSWORD'): {os.environ.get('DB_UNBUFFERED_PASSWORD')}")
    print(f"os.environ.get('DASHBOARD_CONNECTION'): {os.environ.get('DASHBOARD_CONNECTION')}")
    print(f"os.environ.get('DASHBOARD_HOST'): {os.environ.get('DASHBOARD_HOST')}")
    print(f"os.environ.get('DASHBOARD_PORT'): {os.environ.get('DASHBOARD_PORT')}")
    print(f"os.environ.get('DASHBOARD_DATABASE'): {os.environ.get('DASHBOARD_DATABASE')}")
    print(f"os.environ.get('DASHBOARD_USERNAME'): {os.environ.get('DASHBOARD_USERNAME')}")
    print(f"os.environ.get('DASHBOARD_PASSWORD'): {os.environ.get('DASHBOARD_PASSWORD')}")
    print(f"os.environ.get('AWS_ACCESS_KEY_ID'): {os.environ.get('AWS_ACCESS_KEY_ID')}")
    print(f"os.environ.get('AWS_SECRET_ACCESS_KEY'): {os.environ.get('AWS_SECRET_ACCESS_KEY')}")
    print(f"os.environ.get('AWS_DEFAULT_REGION'): {os.environ.get('AWS_DEFAULT_REGION')}")
    print(f"os.environ.get('AWS_BUCKET'): {os.environ.get('AWS_BUCKET')}")
    print(f"os.environ.get('AWS_PATH'): {os.environ.get('AWS_PATH')}")
    print(f"os.environ.get('AWS_URL'): {os.environ.get('AWS_URL')}")
    print(f"os.environ.get('AWS_SQS_URL'): {os.environ.get('AWS_SQS_URL')}")
    print(f"os.environ.get('AWS_SQS_NAME'): {os.environ.get('AWS_SQS_NAME')}")
    print(f"os.environ.get('AWS_SQS_KEY'): {os.environ.get('AWS_SQS_KEY')}")
    print(f"os.environ.get('AWS_SQS_SECRET'): {os.environ.get('AWS_SQS_SECRET')}")
    print(f"os.environ.get('NEW_RELIC_LICENSE_KEY'): {os.environ.get('NEW_RELIC_LICENSE_KEY')}")
    print(f"os.environ.get('NEW_RELIC_LOG_API'): {os.environ.get('NEW_RELIC_LOG_API')}")
    print(f"os.environ.get('NEW_RELIC_ENTITY_GUID'): {os.environ.get('NEW_RELIC_ENTITY_GUID')}")
    print(f"os.environ.get('NEW_RELIC_CONFIG_FILE'): {os.environ.get('NEW_RELIC_CONFIG_FILE')}")
    print(f"os.environ.get('MAIL_DRIVER'): {os.environ.get('MAIL_DRIVER')}")
    print(f"os.environ.get('MAIL_HOST'): {os.environ.get('MAIL_HOST')}")
    print(f"os.environ.get('MAIL_PORT'): {os.environ.get('MAIL_PORT')}")
    print(f"os.environ.get('MAIL_USERNAME'): {os.environ.get('MAIL_USERNAME')}")
    print(f"os.environ.get('MAIL_PASSWORD'): {os.environ.get('MAIL_PASSWORD')}")
    print(f"os.environ.get('MAIL_ENCRYPTION'): {os.environ.get('MAIL_ENCRYPTION')}")
    print(f"os.environ.get('REDIS_HOST'): {os.environ.get('REDIS_HOST')}")
    print(f"os.environ.get('REDIS_PORT'): {os.environ.get('REDIS_PORT')}")
    print(f"os.environ.get('REDIS_PASSWORD'): {os.environ.get('REDIS_PASSWORD')}")
    print(f"os.environ.get('BATCH_SIZE'): {os.environ.get('BATCH_SIZE')}")

    time.sleep(5)
    print('>>FINISH<<')

async def teste_async(request):

    task = BackgroundTask(teste)

    message = {"message":"teste"}

    return JSONResponse(message, background=task)

async def processa_carrefour(request):
    try:
        payload = await request.form()
        parameters = dict(payload.items())

        pprint(parameters)

        task = BackgroundTasks()
        task.add_task(consolida_carrefour_job, **parameters)
        # task = multiprocessing.Process(target=consolida_carrefour_job, args=[parameters,])
        # task.start()
        # task.join()

        message = {"message":"Carregou Carrefour!"}

    except Exception as e:
        message = e

    return JSONResponse({
        "message": message ,
    },background=task)

routes = [
    Route('/', endpoint=index),
    Route('/processa_carrefour', endpoint=processa_carrefour, methods=['POST']),
    Route('/teste_async', endpoint=teste_async)
]

app = Starlette(routes=routes)
