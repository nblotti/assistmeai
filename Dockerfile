FROM python:alpine3.21
#FROM python:3.8.7-slim-buster

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV ENVIRONNEMENT PROD


# install dependencies
COPY requirements.txt /app/requirements.txt

RUN apk add --no-cache g++ clang linux-headers \
    && pip install --upgrade pip \
    && pip install "psycopg[binary,pool]" \
    && apk update \
    && apk add --no-cache python3 postgresql-libs postgresql-client \
    && apk add --no-cache --virtual .build-deps build-base python3-dev postgresql-dev \
    && python3 -m pip install -r requirements.txt --no-cache-dir \
    && apk --purge del .build-deps


# copy project
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
