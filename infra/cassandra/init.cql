CREATE KEYSPACE IF NOT EXISTS iot_data
WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE iot_data;

CREATE TABLE IF NOT EXISTS sensor_readings (
    sensor_id UUID,
    type TEXT,
    reading_time TIMESTAMP,
    reading FLOAT,

    -- PRIMARY KEY:
    PRIMARY KEY ((sensor_id), reading_time)
)

WITH CLUSTERING ORDER BY (reading_time DESC);