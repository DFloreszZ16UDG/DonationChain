FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app

RUN useradd --create-home --uid 10001 donationchain \
    && mkdir -p /data/receipts \
    && chown -R donationchain:donationchain /app /data

USER donationchain
EXPOSE 8000

CMD ["sh", "-c", "alembic -c alembic.ini upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-2}"]
