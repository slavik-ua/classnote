import json
import logging
import time
from typing import Dict, Any
import pika
import pika.exceptions
from threading import Thread, Event
from dotenv import load_dotenv
import os

load_dotenv()
log = logging.getLogger(__name__)

RABBIT_USER = str(os.getenv("RABBITMQ_USER", "guest"))
RABBIT_PASS = str(os.getenv("RABBITMQ_PASS", "guest"))
RABBIT_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBIT_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
TASKS_QUEUE = os.getenv("TASKS_QUEUE", "tasks")
RESULTS_QUEUE = os.getenv("RESULTS_QUEUE", "results")

RESULTS: Dict[str, Dict[str, Any]] = {}


class RabbitClient:
    def __init__(self):
        self._stop_event = Event()
        self._connect()

    def _connect(self):
        attempts = 0
        while 1:
            try:
                credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
                params = pika.ConnectionParameters(
                    host=RABBIT_HOST,
                    port=RABBIT_PORT,
                    credentials=credentials,
                    heartbeat=600,
                )
                self._pub_conn = pika.BlockingConnection(params)
                self._pub_channel = self._pub_conn.channel()
                self._pub_channel.queue_declare(queue=TASKS_QUEUE, durable=True)
                self._pub_channel.confirm_delivery()
                log.info("Publisher connected to RabbitMQ")
                break
            except Exception as e:
                attempts += 1
                sleep = min(30, 2**attempts)
                log.warning(
                    f"Publisher failed connect failed {e}. Retrying in {sleep}."
                )
                time.sleep(sleep)

    def publish_task(self, message: Dict):
        body = json.dumps(message)
        props = pika.BasicProperties(delivery_mode=2)  # Makes it persistent
        try:
            self._pub_channel.basic_publish(
                exchange="", routing_key=TASKS_QUEUE, body=body, properties=props
            )
        except (pika.exceptions.StreamLostError, pika.exceptions.ConnectionClosed) as e:
            log.exception(f"Publish failed: {e}")
            self.__connect()
            self._pub_channel.basic_publish(
                exchange="", routing_key=TASKS_QUEUE, body=body, properties=props
            )

    def start_result_consumer(self):
        def consume():
            while not self._stop_event.is_set():
                try:
                    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
                    params = pika.ConnectionParameters(
                        host=RABBIT_HOST,
                        port=RABBIT_PORT,
                        credentials=credentials,
                        heartbeat=600,
                        blocked_connection_timeout=300,
                    )
                    conn = pika.BlockingConnection(params)
                    channel = conn.channel()
                    channel.queue_declare(queue=RESULTS_QUEUE, durable=True)

                    def callback(ch, method, properties, body):
                        message = json.loads(body)
                        file_id = message.get("id")
                        if file_id:
                            RESULTS[file_id] = message
                            print(RESULTS)
                            log.info(f"Received result for {file_id}")
                        ch.basic_ack(delivery_tag=method.delivery_tag)

                    channel.basic_consume(
                        queue=RESULTS_QUEUE,
                        on_message_callback=callback,
                        auto_ack=False,
                    )
                    log.info("Started consuming")
                    channel.start_consuming()
                except pika.exceptions.AMQPConnectionError as e:
                    log.warning(f"Consumer connection lost: {e}, retrying in 5 s")
                    time.sleep(5)

        t = Thread(target=consume, daemon=True)
        t.start()
        log.info("Result consumer thread started")

    def stop(self):
        self._stop_event.set()
        if self._pub_conn and self._pub_conn.is_open:
            self._pub_conn.close()
