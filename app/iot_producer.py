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

def delivery_report(err, msg):
    if err is not None:
        print(f'Failed to deliver message: {err}')

def generate_sensor_reading(sensor_id):
    return {
        'sensor_id': sensor_id,
        'timestamp': int(time.time() * 1000),
        'temperature': round(random.uniform(20.0, 45.0), 2),
        'humidity': round(random.uniform(30.0, 90.0), 2),
        'voltage': round(random.uniform(11.5, 12.5), 2)
    }

def main():
    producer = Producer(CFG)

    # Simulating 100 different sensors
    sensor_ids = [str(uuid.uuid4()) for _ in range(100)]

    print('Initiating data production...')
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

            # Small throttle to control hardware usage
            time.sleep(.000285)

            # Log status every 1000 messages
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
