import requests
import os
import time


COLOR = "\033[93m"
NC = "\033[0m"  # No Color

os.system("cls" if os.name == "nt" else "clear")

data_ = {
    "fonte_id": 17,
    "filial": "010101",
    "data_recebimento": "2020-12-20",
    "parcela": 1,
}
data_ = {
    "fonte_id": 16,
    "filial": "010101",
    "data_recebimento": "2020-07-14",
    "parcela": 1,
}

print('Início do Teste:')
t = ''
for key, value in data_.items():
    t = input('Informe {key} [default:{value}]:'.format(key=key, value=value))

    # breakpoint()
    if t != "":
        # if type(value).__name__ == 'int':
        #     t = int(t)
        data_[key] = t

    print(str(key) + "["+type(data_[key]).__name__+"]: " + str(data_[key]))

print()

opt = url = porta = ''

opt = input(
    'Digite \'1\' para teste local (consolidapagamentos.local) ou \'2\' para teste no servidor (tp-consolida-pagamentos.redekasa.com):\n    ')

if (opt == ""):
    url = 'consolidapagamentos.local'
elif (int(opt[0:1]) == 1):
    url = 'consolidapagamentos.local'
else:
    url = 'tp-consolida-pagamentos.redekasa.com'


opt = input(
    'Deseja fazer o teste em qual porta?[default: 80]:\n    ')

if (int(opt == "")):
    porta = '80'
else:
    porta = str(int(opt))

url = "http://{url}:{porta}/".format(url=url, porta=porta)

urlPost = (url, url+"teste_redekasa", url+"consolida_pagamento",
           url+"consolida_comissao_carrefour")

for u in urlPost:
    print('Iniciando teste da URL "%s"' % u)
    x = requests.post(u, data=data_)
    print("Resposta do teste da URL '"+u+"': " +
          COLOR + str(x.text).replace("\\n", "\n") + NC + "\n")
    time.sleep(2)
