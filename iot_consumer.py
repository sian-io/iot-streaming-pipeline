import json
import time
from confluent_kafka import Consumer, KafkaError
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra.query import dict_factory
from uuid import UUID

# Kafka Consumer configuration
CFG = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'iot_data_consumers',
    'auto.offset.reset': 'earliest'
}
CASSANDRA_NODES = ['localhost'] # port 9042 is default

def connect_cassandra():
    print("Connecting to Cassandra...")

    cluster = Cluster(contact_points=CASSANDRA_NODES)
    session = cluster.connect()

    session.set_keyspace('iot_data')

    # Prepared statement
    query = """
    INSERT INTO sensor_readings (sensor_id, reading_time, temperature, humidity)
    VALUES (?, ?, ?, ?)
    """
    prepared = session.prepare(query)

    print("Connected to Cassandra, statement prepared.")
    return cluster, session, prepared

def main():
    # DB connection
    cluster, session, prepared = connect_cassandra()

    # Kafka conection
    consumer = Consumer(CFG)
    consumer.subscribe(['iot_sensor_data'])

    print('Waiting for messages...')
    try:
        msg_count = 0
        cycle_start_time = time.time()

        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())
                    break
            
            # Message processing
            try:
                payload = json.loads(msg.value().decode('utf-8'))

                # Type casting
                sensor_id = UUID(payload['sensor_id'])

                # Asynchronous execution
                future = session.execute_async(
                    prepared,
                    [
                        sensor_id,
                        payload['timestamp'],
                        payload['temperature'],
                        payload['humidity']
                    ]
                )

                msg_count += 1
                
                if msg_count % 1000 == 0:
                    elapsed = time.time() - cycle_start_time
                    rate = 1000 / elapsed

                    print(f'Status: {msg_count} messages received. Rate: {rate:.2f} msgs/sec')
                    
                    cycle_start_time = time.time()
            
            except Exception as e:
                print(f'Error processing message: {e}')
    except KeyboardInterrupt:
        print('Shutting down consumer...')
    finally:
        consumer.close()
        cluster.shutdown()
        print('Consumer and Cassandra connection closed.')

if __name__ == '__main__':
    main()
                
