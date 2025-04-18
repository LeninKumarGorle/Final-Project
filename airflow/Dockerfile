FROM apache/airflow:2.10.4

USER root

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Poetry globally
ENV POETRY_HOME="/opt/poetry"
ENV PATH="${POETRY_HOME}/bin:${PATH}"
ENV POETRY_VERSION="2.1.2"

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=$POETRY_HOME python3 - --version $POETRY_VERSION \
    && chmod a+x /opt/poetry/bin/poetry \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# WORKDIR before install
WORKDIR /opt/airflow

# Make sure scripts is recognized as a module
ENV PYTHONPATH="${PYTHONPATH}:/opt/airflow"

# Copy dependency files only
COPY pyproject.toml poetry.lock ./
COPY pinecone-sdk /opt/airflow/pinecone-sdk

# Run poetry install BEFORE switching to airflow user
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Now switch to airflow user (safe, clean env)
USER airflow

# Copy code
COPY --chown=airflow:root ./scripts /opt/airflow/scripts
COPY --chown=airflow:root ./dags /opt/airflow/dags
COPY --chown=airflow:root ./dbt /opt/airflow/dbt