FROM python:3.12-alpine
#FROM python:3.8.7-slim-buster

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV ENVIRONNEMENT PROD
ENV OPENAI_API_KEY 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
#ENV DB_USER postgres
ENV DB_PASSWORD postgres

# install dependencies
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip
RUN apk update && \
 apk add --no-cache python3 postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc python3-dev musl-dev postgresql-dev && \
 python3 -m pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps




# copy project
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
