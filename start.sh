#!/bin/sh

export PYTHONPATH=$PYTHONPATH:/app

# Чекаємо на базу
python src/database/wait_for_db.py

# Запускаємо всі міграції
alembic upgrade head

# Запускаємо FastAPI як основний процес контейнера
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
