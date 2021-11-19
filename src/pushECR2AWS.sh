#!/bin/bash

aws ecr create-repository --repository-name tp-consolida-pagamentos --profile default
aws ecr describe-repositories --repository-name tp-consolida-pagamentos --profile default
docker build --tag tp-consolida-pagamentos -f Dockerfile	.
aws ecr get-login-password --region us-east-2  --profile default | docker login -u AWS --password-stdin 683720833731.dkr.ecr.us-east-2.amazonaws.com/tp-consolida-pagamentos
docker tag tp-consolida-pagamentos:latest 683720833731.dkr.ecr.us-east-2.amazonaws.com/tp-consolida-pagamentos:latest
docker push 683720833731.dkr.ecr.us-east-2.amazonaws.com/tio-patinhas-consolida-pagamentos:latest