from celery import shared_task
from src.database.session_sqlite import SessionLocal
from src.crud import delete_expired_tokens


@shared_task
def celery_delete_expired_tokens():
    with SessionLocal() as db:
        delete_expired_tokens(db)

