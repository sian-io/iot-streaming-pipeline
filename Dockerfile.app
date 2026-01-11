FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install confluent-kafka cassandra-driver

COPY iot_producer.py .
COPY iot_consumer.py .