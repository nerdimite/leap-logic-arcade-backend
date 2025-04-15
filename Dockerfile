FROM python:3.12-slim

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir poetry

WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock README.md ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Copy application code
COPY . .

# Run tests
# RUN poetry run pytest

RUN poetry install

# Expose port
EXPOSE 8080

# Start the application
CMD ["poetry", "run", "start"]
