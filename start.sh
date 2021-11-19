docker container stop $(docker-compose -p tp_consolida_pagamento ps -q)
docker-compose -p tp_consolida_pagamento up -d --build
docker ps
docker logs -f consolida-pagamentos-uvicorn &
