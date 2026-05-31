FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY pyproject.toml README.md ./
COPY api ./api
COPY schemasage ./schemasage
COPY static ./static
COPY data/training ./data/training
COPY scripts/serve.sh ./scripts/serve.sh

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

EXPOSE 8000

CMD ["sh", "scripts/serve.sh"]
