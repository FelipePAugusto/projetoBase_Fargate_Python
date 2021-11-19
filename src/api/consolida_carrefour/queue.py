import os
import base64
import json
import boto3
import requests
from botocore.exceptions import ClientError
from .util import *
from .repository import *


async def create_message_sqs(message: str, fonte_id: None, filial: None, data_recebimento: None, data_enviado: None, item_pos: None, item_tot: None):

    print('create_message_sqs')

    try:
        sqs = boto3.client(
            'sqs',
            aws_access_key_id=os.environ.get('AWS_SQS_KEY'),
            aws_secret_access_key=os.environ.get('AWS_SQS_SECRET')
         )

        queue_url = os.environ.get('AWS_SQS_URL')

        response = sqs.send_message(
            QueueUrl=queue_url,
            DelaySeconds=1,
            MessageAttributes={
                'Author': {
                    'StringValue': 'ProcessaPagamentoTioPatinhas',
                    'DataType': 'String'
                }
            },
            MessageBody=message
        )

        if response is not None and response['MessageId'] is not None and fonte_id is not None and filial is not None and data_recebimento is not None:
            if item_pos == item_tot:
                print(f"[{fonte_id}:{filial}:{data_recebimento}] Envio Finalizado!")

            # print(f">>>>>>>>>>>> ENVIANDO LINHA: {processaPagamentos_PB_Tot} / {item_tot}")

            print(f"[{fonte_id}:{filial}:{data_recebimento}][{item_pos}/{item_tot}] Item inserido na fila com sucesso MessageID: {response['MessageId']}")
            # await create_logging_nr(message=f"Item inserido na fila com sucesso MessageID: {response['MessageId']}")

        return response['MessageId']

    except ClientError as e:
        print(e)
        # logger.info(f"Erro: {e}")
