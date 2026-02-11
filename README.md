# IoT Real-Time Data Streaming Pipeline

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

## Data Model

As evident in `./infra/cassandra/init.cql`, the table `sensor_readings` contains the following columns:

- `sensor_id` (UUID, Partition Key): Unique identifier for each sensor device
- `reading_time` (TIMESTAMP, Clustering Key): UTC timestamp of when the reading was recorded
- `type` (TEXT): Classification of the sensor ("temperature", "humidity", "pressure", "voltage")
- `reading` (FLOAT): The actual sensor measurement value

**Sensor Type Hash Logic**: The `sensor_type` is deterministically assigned based on the `sensor_id` using a hash function. Each sensor ID is hashed to consistently map to one of the predefined sensor types. This ensures that:
- A given sensor ID always produces the same sensor type
- The hash distributes sensor types evenly across the fleet
- No explicit type mapping database is needed; the type is derived on-the-fly from the ID

Of course, this only makes sense in this simulated environment, since, in a real application, each sensor would have a predetermined type and there would be no unified "producer" script.

## Engineering Decisions & Optimizations

This project implements a few data engineering patterns:

- Optimized Partitioning Strategy: The Kafka topic iot_sensor_data is configured with 12 partitions. This number was mathematically chosen as a highly composite number, allowing for perfect load balancing across 1, 2, 3, 4, or 6 consumer instances without skewed distribution.

- Backpressure Handling: The Producer includes a dynamic throttling mechanism (configurable via environment variables) to simulate different load scenarios and test the consumers' ability to catch up (check **Configuration** section).

## Prerequisites

- Docker & Docker Compose

## Getting started

1. **Clone the repository**
    ```sh
    git clone https://github.com/sian-io/iot-streaming-pipeline.git
    ```

2. **Start the pipeline**
    (run in the project root):
    ```sh
    docker compose up
    ```

3. **Verify Data Ingestion**
    - **Kafka UI**: [http://localhost:8080](http://localhost:8080)
    - **Cassandra**: Host: `localhost`, port: `9042`, user (if needed): `cassandra`, password (if needed): `cassandra`

## Scalability

To demonstrate the system's horizontal scalability, you can increase the number of consumers on the fly with the `--scale` flag. The Kafka Consumer Group will automatically rebalance the partitions among the new instances.

For example, running `docker compose up --scale consumer=3` will create 3 containers that will each run `iot_consumer.py` to poll the `iot_sensor_data` topic and insert data into Cassandra with all of their combined processing power.

## Configuration

You can adjust certain environment variables in docker-compose.yaml to your needs:

Change the value in `PRODUCER_TARGET_RATE=3500` under the `producer` service to set the number of messages sent per second by the producer. (Change the number of consumers to account for this!)

Change the value in `KAFKA_NUM_PARTITIONS=12` under the `kafka` service to set the number of partitions of the Kafka consumer group. This number should always be at least the same as the number of consumers if you want them all to be active.

Change the values in `KAFKA_HEAP_OPTS="-Xms512M -Xmx512M"` under the `kafka` service, or the values in `MAX_HEAP_SIZE=1024M`/`HEAP_NEWSIZE=256M` under the `cassandra` service to adjust the memory allocated to each of these containers. The default values are restrictive because my PC (at the time of developing and writing this) only has 8GB.

## Monitoring

Kafka UI: Access at http://localhost:8080 to view Topic Lag and Broker status.

Containers' resource usage and load distribution: Use the command `docker stats`

Logs: Monitor the ingestion rate via `docker compose logs -f consumer`

Cassandra: Check the data that has been inserted by:
1. running `docker exec -it cassandra cqlsh`
2. connecting to the keyspace with `USE iot_data;`
3. then querying the `sensor_readings` table, e.g. `SELECT * FROM sensor_readings LIMIT 100;`
4. to exit the cqlsh CLI, run `quit`