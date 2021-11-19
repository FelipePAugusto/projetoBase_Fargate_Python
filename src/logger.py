from datetime import datetime
from pytz import timezone
import os
import json
import requests

def log(info, level='info'):
    """Escreve uma mensagem de log. Futuramente
    alterar a implementação desse método de forma a salvar
    os logs no newRelic"""

    now = datetime.now()
    fuso = timezone('America/Recife')
    datahoraBR = now.astimezone(fuso)
    timestamp = datahoraBR.strftime('%Y-%m-%d %H:%M:%S')
    print('[' + str(timestamp) + ']' + '[' + level.upper() + ']', str(info))

    """
    if level.upper() == "ERRO":
        if os.getenv('ENV') == 'prd':
            webhook_url = "https://hooks.slack.com/services/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"
        elif os.getenv('ENV') == 'stg':
            webhook_url = "https://hooks.slack.com/services/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"
        else:
            webhook_url = "https://hooks.slack.com/services/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"

        slack_data = {'text': "> " + str(timestamp) + "\n> *APP:* " + os.getenv('APP_NAME') + "\n> *ENV:* " + os.getenv('ENV') + "\n> *INFO:* " + str(info)}
        response = requests.post(
            webhook_url, json.dumps(slack_data),
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code != 200:
            raise ValueError(
                'Request to slack returned an error %s, the response is:\n%s'
                % (response.status_code, response.text)
        )
    """
