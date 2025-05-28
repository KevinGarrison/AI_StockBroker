FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV INFLUXDB_URL=http://localhost:8086/
ENV INFLUXDB_TOKEN=mySuperSecretToken123!
ENV INFLUXDB_ORG=HSAA
ENV INFLUXDB_BUCKET=25s-cd-teamb
CMD ["python", "backend/microservices/Influx/influx.py"]


