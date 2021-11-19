import logging
import os, os.path
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException


if not os.path.exists("logs/"):
    os.makedirs("logs/")

logger = logging.getLogger(__name__)
logger.addHandler(logging.FileHandler('logs/uvicorn.errors.log'))

async def Errors(message) -> HTTPException:
    return HTTPException(status_code=400,detail=message)
