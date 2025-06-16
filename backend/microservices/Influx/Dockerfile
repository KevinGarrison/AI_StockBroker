FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl

WORKDIR /app

RUN mkdir -p /app/api_fetcher

COPY Influx/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api_fetcher/api_data_fetcher.py /app/api_fetcher/api_data_fetcher.py
COPY Influx/ /app/


RUN chmod +x /app/wait-for-influx.sh

CMD ["./wait-for-influx.sh", "http://influxdb:8086", "python", "influx.py"]
