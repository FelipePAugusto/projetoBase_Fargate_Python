import asyncio
from consolida_pagamento.tools import consolida_pagamento_job
import socket
import os
COLOR = "\033[93m"
NC = "\033[0m"  # No Color


os.system("pip install newrelic pymysql boto3 starlette")

hn = socket.gethostname()
fq = socket.getfqdn()
ip1 = socket.gethostbyname(hn)
ip2 = socket.gethostbyname(fq)

print(
    "Hostname: {hn}\nFQDN: {fq}\nIP:'{ip1}' ou '{ip2}'".format(
        hn=hn, fq=fq, ip1=ip1, ip2=ip2
    )
)

# print(chr(27) + "[2J")

# #Get
# import urllib.request

# urlGet = "http://consolidapagamentos.local:5000/consolida"
# x = urllib.request.urlopen(urlGet).read()
# x = str(x)
# print("\n\n" + x + "\n\n")

data_ = {
    "fonte_id": 16,
    "filial": "010101",
    "data_recebimento": "2020-07-14",
    "parcela": 1,
}

# Post

# import requests
# import os

# os.system("cls" if os.name == "nt" else "clear")

# urlPost = "http://consolidapagamentos.local:5000/consolida-pagamentos"
# x = requests.post(urlPost, data=data_)
# print("\n" + COLOR + x.text + NC)


# direct


async def consolida_teste():

    await consolida_pagamento_job(**data_)

asyncio.run(consolida_teste())
