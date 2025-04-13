FROM apache/airflow:2.10.4

USER root

# Install system dependencies and Google Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget unzip curl gnupg2 ca-certificates git python3-pip \
    fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libcups2 libdbus-1-3 libgdk-pixbuf2.0-0 libnspr4 libnss3 libx11-xcb1 \
    libxcomposite1 libxdamage1 libxrandr2 xdg-utils \
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb || true \
    && apt-get -f install -y \
    && rm google-chrome-stable_current_amd64.deb \
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

# Copy dependency files only
COPY pyproject.toml poetry.lock ./

# Run poetry install BEFORE switching to airflow user
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Now switch to airflow user
USER airflow

# Copy code
COPY --chown=airflow:root ./scripts /opt/airflow/scripts
COPY --chown=airflow:root ./dags /opt/airflow/dags
COPY --chown=airflow:root ./dbt /opt/airflow/dbt
