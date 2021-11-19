FROM python:3.8.1
LABEL maintainer="Humberto Oliveira <humberto.oliveira@madeiramadeira.com.br>"

<<<<<<< HEAD
ARG CONTAINER_PORT=80
=======
ARG CONTAINER_PORT=84
>>>>>>> develop
ENV SERVICE_PORT=$CONTAINER_PORT \
    POETRY_VERSION=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE ${SERVICE_PORT}

# Update/upgrade packages and install Poetry
RUN apt-get update -yy && apt-get upgrade -yy
RUN pip install --upgrade pip && pip install "poetry==$POETRY_VERSION"

# Change working directory
<<<<<<< HEAD
# VOLUME /app
=======
VOLUME /app
>>>>>>> develop
WORKDIR /app

# Install project dependencies
COPY ./src/poetry.lock ./src/pyproject.toml ./
RUN poetry install

# Copy project files
COPY ./src ./

<<<<<<< HEAD
#funciona localmente
# CMD poetry run uvicorn --reload --workers=2 --host 0.0.0.0 --port $SERVICE_PORT api:app

#default:
CMD poetry run uvicorn --workers=8 --host 0.0.0.0 --port $SERVICE_PORT --loop asyncio api:app
=======
# CMD poetry run uvicorn --workers=8 --host 0.0.0.0 --port $SERVICE_PORT --loop asyncio consolida_carrefour:app
# CMD poetry run uvicorn --reload --workers=2 --host 0.0.0.0 --port $SERVICE_PORT api:app

CMD poetry run uvicorn --reload --workers=2 --host 0.0.0.0 --port $SERVICE_PORT api:app
>>>>>>> develop
