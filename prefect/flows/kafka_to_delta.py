# prefect/flows/kafka_to_delta.py
from pathlib import Path
import json, os, subprocess, time

from prefect import flow, task
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import pandas as pd
from datetime import datetime

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_CONNECT_RETRIES = int(os.getenv("KAFKA_CONNECT_RETRIES", "3"))
KAFKA_CONNECT_RETRY_DELAY_SECONDS = float(os.getenv("KAFKA_CONNECT_RETRY_DELAY_SECONDS", "2"))
PIPELINE_MODE = os.getenv("PIPELINE_MODE", "local").strip().lower()
RUNNING_IN_PREFECT_CONTAINER = os.getenv("PREFECT_RUN_CONTAINERIZED") == "1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DOCKER_COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"
DELTA_LAKE_PATH = os.getenv(
    "DELTA_LAKE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "delta-lake", "raw"),
)

@task
def consume_and_process():
    """Consume data from Kafka topic"""
    return consume_and_process_impl()


def consume_and_process_impl():
    consumer = None
    last_error = None
    for attempt in range(1, KAFKA_CONNECT_RETRIES + 1):
        try:
            consumer = KafkaConsumer(
                "data.raw",
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset="earliest",
                consumer_timeout_ms=5000,
                value_deserializer=lambda m: json.loads(m.decode()),
            )
            break
        except NoBrokersAvailable as exc:
            last_error = exc
            if attempt < KAFKA_CONNECT_RETRIES:
                print(
                    f"Kafka broker not ready at {KAFKA_BOOTSTRAP_SERVERS}; "
                    f"retrying {attempt}/{KAFKA_CONNECT_RETRIES}..."
                )
                time.sleep(KAFKA_CONNECT_RETRY_DELAY_SECONDS)
            else:
                print(
                    f"Kafka broker not available at {KAFKA_BOOTSTRAP_SERVERS}; "
                    "skipping this batch."
                )
                return []

    if consumer is None:
        print(f"Kafka connection failed: {last_error}")
        return []

    records = []
    for msg in consumer:
        records.append(msg.value)

    print(f"Consumed {len(records)} records from Kafka")
    return records

@task
def save_to_delta(records):
    """Save records to Delta Lake (parquet format)"""
    return save_to_delta_impl(records)


def save_to_delta_impl(records):
    if not records:
        print("No records to save")
        return

    df = pd.DataFrame(records)
    os.makedirs(DELTA_LAKE_PATH, exist_ok=True)
    df.to_parquet(
        os.path.join(DELTA_LAKE_PATH, f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet")
    )
    print(f"Saved {len(df)} records to Delta Lake")


def run_pipeline():
    records = consume_and_process_impl()
    save_to_delta_impl(records)


def deploy_flow():
    kafka_to_delta_flow.deploy(
        name=os.getenv("PREFECT_DEPLOYMENT_NAME", "kafka-to-delta"),
        work_pool_name=os.getenv("PREFECT_WORK_POOL_NAME", "docker"),
        image=os.getenv("PREFECT_IMAGE", "day28-prefect-worker:latest"),
    )


def run_prefect_flow_in_container():
    command = [
        "docker",
        "compose",
        "-f",
        str(DOCKER_COMPOSE_FILE),
        "run",
        "--rm",
        "-e",
        "PIPELINE_MODE=prefect-run",
        "-e",
        "PREFECT_RUN_CONTAINERIZED=1",
        "prefect-worker",
        "python",
        "/opt/prefect/flows/kafka_to_delta.py",
    ]
    subprocess.run(command, cwd=REPO_ROOT, check=True)

@flow(name="Kafka to Delta Pipeline")
def kafka_to_delta_flow():
    """Main flow: consume from Kafka and save to Delta Lake"""
    records = consume_and_process()
    save_to_delta(records)


def main():
    if os.getenv("PREFECT_DEPLOY") == "1" or PIPELINE_MODE in {"deploy", "prefect-deploy"}:
        deploy_flow()
    elif PIPELINE_MODE in {"prefect", "prefect-run", "flow"}:
        if RUNNING_IN_PREFECT_CONTAINER:
            kafka_to_delta_flow()
        else:
            run_prefect_flow_in_container()
    else:
        run_pipeline()

if __name__ == "__main__":
    main()
