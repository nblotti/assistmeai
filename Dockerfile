FROM python:3.12-alpine

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
#RUN apk update \  && apk add postgresql-dev gcc python3-dev musl-dev

RUN mkdir "/app/transcripts/"

RUN apk update \  && apk add  gcc python3-dev musl-dev
RUN apk add ffmpeg

# install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt


# copy project
COPY . .

RUN pwd
RUN ls -la .
ENTRYPOINT ["sh", "entrypoint.sh"]
