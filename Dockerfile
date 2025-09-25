FROM python:3.13-slim

WORKDIR /app

ENV PYTHONBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN chmod +x start.sh
