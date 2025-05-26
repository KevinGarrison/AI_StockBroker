from fastapi import FastAPI

from inf_data_collector import DataCollector, InfluxDBHandler
import asyncio

app = FastAPI()

@app.get("/collect")
async def collect_data(ticker: str):
    collector = DataCollector()
    influx_handler = InfluxDBHandler()
    stock_data = await collector.fetch_stock_data_yf(ticker)
    influx_handler.write_stock_data(stock_data)
    influx_handler.close()
    return {"status": "success", "ticker": ticker}

