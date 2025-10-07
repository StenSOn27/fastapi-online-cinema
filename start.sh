#!/bin/sh

export PYTHONPATH=$PYTHONPATH:/app

python src/database/wait_for_db.py

alembic upgrade head

exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
