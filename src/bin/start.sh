#!/usr/bin/env bash
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "PWD: ${GREEN}${PWD}${NC}"

echo -e "${GREEN}Iniciando o ambiente de desenvolvimento do Consolida pagamento${NC}"

echo -e "${GREEN}Verificando configurações de ambiente${NC}"
if [ ! -f ".env" ]; then
    echo "${GREEN}Criando arquivo de configuração de ambiente${NC}"
    ln -s ./src/environments/development.env .env
fi

echo -e "${GREEN}Removendo containers Docker (docker rm consolida-pagamentos-nginx consolida-pagamentos-uvicorn)${NC}"
docker container rm -f consolida-pagamentos-nginx consolida-pagamentos-uvicorn

echo -e "${GREEN}Construindo Docker (docker-compose -p tp_consolida_pagamento up -d --build)${NC}"
docker-compose -p tp_consolida_pagamento up -d --build

echo -e "${GREEN}Docker logs!${NC}"
docker logs -f --tail 50 consolida-pagamentos-uvicorn &

echo -e "${GREEN}Finalizado${NC}"