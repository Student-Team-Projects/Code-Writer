FROM python:3.12-slim

ENV POETRY_VERSION=1.8.4
RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root
COPY . .

CMD ["poetry", "run", "python", "src/Code-Writer/main.py"]
