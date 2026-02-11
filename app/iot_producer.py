import json
import random
import time
import uuid
import os
from confluent_kafka import Producer

KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

# Kafka Producer configuration
CFG = {
    'bootstrap.servers': KAFKA_BOOTSTRAP,
    'acks': '0',
    'linger.ms': 10,
    'compression.type': 'snappy'
}

TOPIC_NAME = 'iot_sensor_data'
SENSOR_TYPES = ['temperature', 'humidity', 'voltage', 'pressure']

def delivery_report(err, msg):
    if err is not None:
        print(f'Failed to deliver message: {err}')

def generate_sensor_reading(sensor_id):
    # Determine the sensor type based on ID
    # hash(sensor_id) returns a unique consistent integer for the string
    # % len(SENSOR_TYPES) ensures that the result is 0, 1, 2 or 3
    type_index = hash(sensor_id) % len(SENSOR_TYPES)
    sensor_type = SENSOR_TYPES[type_index]

    if sensor_type == 'temperature':
        reading = round(random.uniform(20.0, 45.0), 2) # °Celsius
    elif sensor_type == 'humidity':
        reading = round(random.uniform(30.0, 90.0), 2) # % Relative Humidity
    elif sensor_type == 'voltage':
        reading = round(random.uniform(11.5, 12.5), 2) # Volts
    elif sensor_type == 'pressure':
        reading = round(random.uniform(33775.0, 253313.0), 2) # Pascals

    data = {
        'sensor_id': sensor_id,
        'reading_time': int(time.time() * 1000), # milliseconds
        'type': sensor_type,
        'reading': reading
    }

    return data

def main():
    producer = Producer(CFG)

    # Gets the environment variable for target msg rate or defaults to 3500 msgs/sec
    target_msg_rate = int(os.getenv('PRODUCER_TARGET_RATE', '3500'))
    sleep_time = 1.0 / target_msg_rate if target_msg_rate > 0 else 0

    # Simulating 1000 different sensors
    sensor_ids = [str(uuid.uuid4()) for _ in range(1000)]

    print(f'Initiating data production at {target_msg_rate} messages per second...')
    try:
        msg_count = 0
        cycle_start_time = time.time()

        while True:
            # Randomly select a sensor and generate its reading
            sensor_id = random.choice(sensor_ids)
            data = generate_sensor_reading(sensor_id)

            payload = json.dumps(data).encode('utf-8')
            
            producer.produce(
                TOPIC_NAME,
                value=payload,
                callback=delivery_report
            )

            producer.poll(0)

            msg_count += 1

            if sleep_time > 0:
                time.sleep(sleep_time)

            # Log status every 10000 messages
            if msg_count % 10000 == 0:
                elapsed = time.time() - cycle_start_time
                rate = 10000 / elapsed
                print(f'Status: {msg_count} messages sent. Rate: {rate:.2f} msgs/sec')                
                cycle_start_time = time.time()
    
    except KeyboardInterrupt:
        print('Data production interrupted by user.')
    finally:
        producer.flush()
        print('Producer flushed and closed.')

if __name__ == '__main__':
    main()
