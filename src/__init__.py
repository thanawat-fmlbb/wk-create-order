import os

from celery import Celery
from src.database.engine import create_db_and_tables

create_db_and_tables()
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", "6381")
app = Celery("create_order_service",
             broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
             backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
             broker_connection_retry_on_startup=True)