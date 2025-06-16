#!/bin/bash
set -e

INFLUX_URL="${1%/}"
PYTHON_CMD=$2
SCRIPT=$3

echo "Waiting for InfluxDB on $INFLUX_URL ..."
until curl -s "$INFLUX_URL/ping" > /dev/null; do
  echo "InfluxDB not ready yet, new tentative in 2 seconds..."
  sleep 2
done

echo "InfluxDB is ready! Launching Python script."
exec $PYTHON_CMD $SCRIPT
