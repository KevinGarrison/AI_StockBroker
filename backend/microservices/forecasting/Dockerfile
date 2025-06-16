FROM python:3.12-slim

WORKDIR /app

COPY forecasting/requirements.txt .
RUN pip install --upgrade pip && \
    TMPDIR=/var/tmp pip install --no-cache-dir -r requirements.txt

COPY . /app
COPY ../Influx /app/Influx


CMD ["uvicorn", "forecasting.app:app", "--host", "0.0.0.0", "--port", "8003"]