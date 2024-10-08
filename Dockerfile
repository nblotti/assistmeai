FROM python:3.12-alpine
#FROM python:3.8.7-slim-buster

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV ENVIRONNEMENT PROD


# install dependencies
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && pip install "psycopg[binary,pool]" && apk update &&  \
    apk add --no-cache python3 postgresql-libs postgresql-client && \
    apk add --no-cache --virtual .build-deps gcc python3-dev musl-dev postgresql-dev && \
    python3 -m pip install -r requirements.txt --no-cache-dir && apk --purge del .build-deps && \
    apk add openjdk17-jre-headless && apk  add --no-cache libreoffice && \
    apk add --no-cache msttcorefonts-installer fontconfig && update-ms-fonts



# copy project
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
