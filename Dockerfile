FROM python:3.12-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    PORT=8000

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && playwright install --with-deps chromium

COPY . .
RUN mkdir -p /app/data/thumbs

EXPOSE 8000

CMD ["sh","-c","uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
