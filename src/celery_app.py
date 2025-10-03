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

celery_app.conf.update(
    worker_pool='threads',  # Use threads instead of solo to allow concurrency
    worker_concurrency=4,   # Allow up to 4 concurrent tasks
)

celery_app.conf.beat_schedule = {
    'cleanup-celery-meta-ten-minutes': {
        'task': 'src.tasks.cleanup_celery_meta',
        'schedule': 600,
    },
}
