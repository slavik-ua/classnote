import pika
import time
import json
import os
import logging
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

RABBIT_USER = os.getenv("RABBITMQ_USER", "guest")
RABBIT_PASS = os.getenv("RABBITMQ_PASS", "guest")
RABBIT_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBIT_PORT = os.getenv("RABBITMQ_PORT", "5672")
TASKS_QUEUE = os.getenv("TASKS_QUEUE", "tasks")
RESULTS_QUEUE = os.getenv("RESULTS_QUEUE", "results")
AUDIO_DIR = os.getenv("AUDIO_DIR", "audios")


def make_connection():
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBIT_HOST,
        port=RABBIT_PORT,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    return pika.BlockingConnection(parameters)


def main():
    from worker.summarizer import Summarizer

    summarizer = Summarizer()

    while 1:
        try:
            conn = make_connection()
            ch = conn.channel()
            ch.queue_declare(queue=TASKS_QUEUE, durable=True)
            ch.queue_declare(queue=RESULTS_QUEUE, durable=True)
            log.info("Worker listening...")

            def callback(ch, method, properties, body):
                try:
                    payload = json.loads(body)
                    file_id = payload.get("id")
                    if not file_id:
                        log.warning("Received task without id")
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        return

                    audio_path = os.path.join(AUDIO_DIR, f"{file_id}.wav")
                    log.info(f"Processing {audio_path}")
                    summary = summarizer.summarize(audio_path)
                    context = {"id": file_id, "summary": summary}
                    print(f"\n\nCONTEXT: {context}\n\n")
                    ch.basic_publish(
                        exchange="",
                        routing_key=RESULTS_QUEUE,
                        body=json.dumps(context),
                        properties=pika.BasicProperties(delivery_mode=2),
                    )
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    date = datetime.now().strftime("%Y-%m-%d")

                    with open(f"logs_{date}.log", "a") as f:
                        f.write(json.dumps(context) + "\n")
                    log.info(f"Finished task {file_id}")

                except Exception as e:
                    log.exception(f"Failed processing task: {e}")

            ch.basic_qos(prefetch_count=1)
            ch.basic_consume(
                queue=TASKS_QUEUE, on_message_callback=callback, auto_ack=False
            )
            ch.start_consuming()
        except pika.exceptions.AMQPConnection as e:
            log.exception(f"Connection to RabbitMQ failed: {e}")
            time.sleep(5)
        except Exception as e:
            log.exception(f"Unexpected worker error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
