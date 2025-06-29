from dateutil.relativedelta import relativedelta
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from influx import InfluxDBHandler
from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import List
import logging
import httpx
import os


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


logger = logging.getLogger(__name__)


class HistoryEntry(BaseModel):
    ds: str
    y: float


class ForecastPayload(BaseModel):
    history: List[HistoryEntry]


influx_db = {}


handler = InfluxDBHandler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    influx_db['client'] = await handler.connect_to_influx()
    influx_db['forecast_ids'] = []
    try:
        yield
    finally:
        influx_db["client"].close()
        influx_db.clear()


app = FastAPI(lifespan=lifespan)


@app.get("/collect-stock-history-from-yfinance")
async def collect_stock_history():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://api-gateway:8000/companies-for-dropdown", timeout=None)
        if response.status_code != 200:
            return {"error": "Failed to fetch companies"}
        companies = response.json()
        tickers = companies
    client = influx_db['client']
    await handler.write_stock_data_to_influx(tickers, client)


@app.post("/write-forecast-to-influx/{ticker}")
async def write_forecast(ticker:str,
                         context: ForecastPayload = Body(...)):
    try:
        client = influx_db['client']
        logger.info(f'[InfluxDB POST] Client connected to {client}')
        timeseries = context
        logger.info(f'[InfluxDB POST] Timeseries to write to influx: {timeseries}') 
        for datapoint_forecast in timeseries.history:
            influx_db['forecast_ids'].append((ticker, datapoint_forecast.ds))
            logging.info(f'[InfluxDB POST] Writing {datapoint_forecast.ds}:{datapoint_forecast.y} to DB')
            await handler.write_forecast_df(datapoint=datapoint_forecast,ticker=ticker, client=client)

        return {"status": "success", "data_points": len(context.history)}
    except Exception as e:
        logger.error(f'[Influx Error] {e} Failed to write forecast for {ticker} to db!')


@app.get("/history/{ticker}")
def get_timeseries(ticker: str):
    query = f'''
    from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
      |> range(start: -10y)
      |> filter(fn: (r) => r["_measurement"] == "stock_price")
      |> filter(fn: (r) => r["_field"] == "close_price_history")
      |> filter(fn: (r) => r["ticker"] == "{ticker}")
      |> sort(columns: ["_time"])
    '''
    client = influx_db["client"]
    result = client.query_api().query(query=query)

    data = []
    for table in result:
        for record in table.records:
            data.append({
                "ds": record.get_time().isoformat(),
                "y": record.get_value()
            })

    return data


@app.get("/forecast/{ticker}")
def get_forecast(ticker: str):
    bucket = os.getenv("INFLUXDB_BUCKET")
    client = influx_db["client"]
    query_api = client.query_api()

    history_query = f'''
    from(bucket: "{bucket}")
      |> range(start: -10y)
      |> filter(fn: (r) => r["_measurement"] == "stock_price")
      |> filter(fn: (r) => r["_field"] == "close_price_history")
      |> filter(fn: (r) => r["ticker"] == "{ticker}")
      |> sort(columns: ["_time"], desc: true)
      |> limit(n:1)
    '''
    history_result = query_api.query(query=history_query)
    last_history = []
    for table in history_result:
        for record in table.records:
            last_history.append({
                "ds": record.get_time().isoformat(),
                "y": record.get_value()
            })
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    stop = (datetime.now(timezone.utc) + relativedelta(months=5)).isoformat()

    forecast_query = f'''
    from(bucket: "{bucket}")
      |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
      |> filter(fn: (r) => r["_measurement"] == "stock_price")
      |> filter(fn: (r) => r["_field"] == "close_price_forecast")
      |> filter(fn: (r) => r["ticker"] == "{ticker}")
      |> sort(columns: ["_time"])
    '''
    forecast_result = query_api.query(query=forecast_query)
    forecast = []
    for table in forecast_result:
        for record in table.records:
            forecast.append({
                "ds": record.get_time().isoformat(),
                "y": record.get_value()
            })

    return last_history + forecast

    
@app.get("/delete-forecasts")
async def delete_fc():
    for ticker, timestamp in influx_db.get("forecast_ids", []):
        await handler.delete_forecast_point(ticker, timestamp, client=influx_db['client'])


