FROM python:3.10-slim

WORKDIR /app

ENV POETRY_HOME="/opt/poetry"
ENV PATH="${POETRY_HOME}/bin:${PATH}"
ENV POETRY_VERSION="2.1.2"

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=$POETRY_HOME python3 - --version $POETRY_VERSION \
    && chmod a+x /opt/poetry/bin/poetry \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

COPY backend/pyproject.toml ./

RUN poetry config virtualenvs.create false \
    && poetry update --no-interaction --no-ansi

COPY backend /app/backend

EXPOSE 8000

CMD ["poetry","run","uvicorn", "backend.api.fastapi_backend:app", "--host", "0.0.0.0", "--port", "8000"]