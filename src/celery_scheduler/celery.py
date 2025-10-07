import os
from celery import Celery
from celery.schedules import crontab
from src.celery_scheduler.tasks import celery_delete_expired_tokens


celery = Celery(
    __name__,
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
)

celery.autodiscover_tasks(["src.tasks"])

celery.conf.beat_schedule = {
    'delete-expired-tokens-every-hour': {
        'task': 'src.celery_scheduler.tasks.celery_delete_expired_tokens',
        'schedule': crontab(hour="*/1"),
    },
}
