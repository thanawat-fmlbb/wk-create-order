import os
from dotenv import load_dotenv
from celery import Celery
from src.database.models import OrderInfo
from src.database.engine import create_db_and_tables

load_dotenv()
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
app = Celery("create_order_service",
             broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
             backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
             broker_connection_retry_on_startup=True)

result_collector = Celery("create_order_service",
                          broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/4",
                          backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/4",
                          broker_connection_retry_on_startup=True)

create_db_and_tables()
