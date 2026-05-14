FROM python:3.12-slim

WORKDIR /app

COPY mcp/ .

RUN pip install --no-cache-dir -r requirements.txt

ENV DATASET_PATH=/data/legal-texts
ENV STRICT_STARTUP=true

CMD ["python", "server.py"]
