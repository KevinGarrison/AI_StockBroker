from fastapi import FastAPI
from fastapi import FastAPI, Response
import json
from influx import DataCollector, InfluxDBHandler
import asyncio

app = FastAPI()

# Endpoint to collect stock data and write to InfluxDB
@app.get("/collect")
async def collect_data(ticker: str):
    collector = DataCollector()
    influx_handler = InfluxDBHandler()
    stock_data = await collector.fetch_stock_data_yf(ticker)
    influx_handler.write_stock_data(stock_data)
    influx_handler.close()
    #return {"status": "success", "ticker": ticker}



# Endpoint to fetch Grafana dashboard JSON
@app.get("/grafana-dashboard")
def get_grafana_dashboard():
    with open("Grafana.json", "r") as f:
        dashboard_json = json.load(f)
    return dashboard_json

