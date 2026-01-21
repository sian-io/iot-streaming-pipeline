# IoT Real-Time Data Streaming Pipeline

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-3.6-blue?logo=apachekafka&logoColor=white)
![Apache Cassandra](https://img.shields.io/badge/Apache_Cassandra-4.1-blue?logo=apachecassandra&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker&logoColor=white)

A high-throughput data engineering pipeline designed to ingest, process, and store simulated IoT sensor telemetry in real-time. This project demonstrates a decoupled, fault-tolerant architecture using **Apache Kafka** for event streaming and **Apache Cassandra** for write-heavy storage.

## Architecture Overview

The system simulates a real-world IoT environment where thousands of sensors emit data simultaneously. The pipeline handles data ingestion, buffering, processing, and persistence.

- Producer: Python script generating synthetic sensor data (temperature and humidity) with configurable throughput.

- Message Broker: Apache Kafka (single node for dev) handling the data stream.

- Processing: Python Consumers operating within a Consumer Group to ensure parallel processing and message ordering guarantees per partition.

- Storage: Apache Cassandra, selected for its high write availability and linear scalability (AP system, per CAP Theorem).

- Infrastructure: Fully containerized environment using Docker Compose.

## Project Structure

```
├── app
│   ├── Dockerfile
│   ├── iot_consumer.py
│   ├── iot_producer.py
│   └── requirements.txt
├── infra
│   └── cassandra
│       └── init.cql
├── docker-compose.yaml
├── LICENSE
└── README.md
```

## Engineering Decisions & Optimizations

This project implements a few data engineering patterns:

- Optimized Partitioning Strategy: The Kafka topic iot_sensor_data is configured with 12 partitions. This number was mathematically chosen as a highly composite number, allowing for perfect load balancing across 1, 2, 3, 4, or 6 consumer instances without skewed distribution.

- JVM & Resource Tuning: The Cassandra container is tuned for a memory-constrained environment.

    - MAX_HEAP_SIZE set to 1GB to prevent OutOfMemory errors.

    - Memtable thresholds adjusted to avoid MUTATION_REQ drops during peak loads.

- Backpressure Handling: The Producer includes a dynamic throttling mechanism (configurable via environment variables) to simulate different load scenarios and test the consumers' ability to catch up (check **Configuration** section).

- Resiliency:

    - Healthchecks: Optimized Docker healthchecks with start_period to handle the slow startup time of the JVM.

    - Retry Policies: The Cassandra driver implements downgrade policies and connection retries to handle transient failures.


## Prerequisites

- Docker & Docker Compose

## Getting started

1. **Clone the repository**
    ```sh
    git clone https://github.com/username/iot-streaming-pipeline.git
    ```

2. **Start the pipeline**
    (run in the project root):
    ```sh
    docker compose up
    ```

3. **Verify Data ingestion**
    - **Kafka UI**: [http://localhost:8080](http://localhost:8080)
    - **Cassandra**: Host: `localhost`, port: `9042`, user (if needed): `cassandra`, password (if needed): `cassandra`

## Scalability

To demonstrate the system's horizontal scalability, you can increase the number of consumers on the fly. The Kafka Consumer Group will automatically rebalance the 12 partitions among the new instances.

```
docker compose up -d --scale consumer=3
```
Check the containers' resource usage and load distribution:

```
docker stats
```

## Configuration

You can adjust the load settings in docker-compose.yaml under the producer service:

```
PRODUCER_TARGET_RATE=3500
KAFKA_NUM_PARTITIONS=12
```

## Monitoring

Kafka UI: Access at http://localhost:8080 (from your pc) to view Topic Lag and Broker status.

Logs: Monitor the ingestion rate via `docker compose logs -f consumer`