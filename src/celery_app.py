import platform
from celery import Celery
from src.config import settings

celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.tasks"],
)

# Basic configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Windows-specific configuration
if platform.system() == "Windows":
    celery_app.conf.update(
        worker_pool="solo",
        worker_concurrency=1,
    )
