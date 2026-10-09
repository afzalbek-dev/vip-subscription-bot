FROM python:3.12-slim-bookworm AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
COPY src/ ./src/
COPY tests/ ./tests/
COPY .env.example .

RUN pip install --no-cache-dir -e .

RUN mkdir -p /app/data /app/receipts && chmod -R 777 /app/data /app/receipts

RUN useradd -m -u 1001 botuser && chown -R botuser:botuser /app
USER botuser

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python3", "-m", "vip_bot.main"]
