FROM python:3.12

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=1.8.4
RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root
COPY . .