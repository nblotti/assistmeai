FROM python:3.12-alpine

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV ENVIRONNEMENT PROD
ENV OPENAI_API_KEY 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

RUN apk update \  && apk add  gcc python3-dev musl-dev

# install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt


# copy project
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
