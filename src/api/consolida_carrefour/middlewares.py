from .util import logger
from starlette.responses import JSONResponse
from starlette.requests import Request
import functools


def logging(function):
    @functools.wraps(function)
    async def wrapper(*args, **kwargs):
        request = Request(*args)
        logger.debug('>>>>> REQUEST >>>>>')
        logger.debug(f'{request.method} {request.url}')
        if request.form():
            logger.debug(request.form())

        response = await function(*args, **kwargs)
        response_log = response
        logger.debug(response_log)
        logger.debug('<<<<< RESPONSE <<<<<')
        logger.debug(response_log)

        return response
    return wrapper
