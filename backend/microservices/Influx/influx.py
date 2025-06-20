from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import ASYNCHRONOUS
from datetime import timedelta, datetime
from dataclasses import dataclass
from dotenv import load_dotenv
import pandas as pd
import logging
import asyncio
import httpx
import os


logger = logging.getLogger(__name__)


load_dotenv()


@dataclass
class InfluxDBHandler:
    """
    A class to handle InfluxDB operations: connecting and writing data.
    """

    async def connect_to_influx(self):
        try:
            url = os.getenv('INFLUXDB_URL')
            token = os.getenv('INFLUXDB_TOKEN')
            org = os.getenv('INFLUXDB_ORG')
            client = InfluxDBClient(url=url, token=token, org=org)
            health = client.ping()
            if health:
                logger.info(f"[Influx] Connected to org: {org}, url:{url} with token:{token[:30]}")
                return client
            else:
                logger.info(f"[Influx] Failed to connect to org: {org}, url:{url} with token:{token[:30]}")
                return
        except Exception as e:
            logger.error(f"[Influx ERROR] Connection failed: {e}")
            raise
            

    async def write_stock_data_to_influx(self, tickers: list, client: InfluxDBClient, CONCURRENCY_LIMIT=5):
        api = client.write_api(write_options=WriteOptions(write_type=ASYNCHRONOUS, batch_size=100, flush_interval=1000))
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

        async with httpx.AsyncClient() as http_client:

            async def process_ticker(ticker):
                async with semaphore:
                    try:
                        res = await http_client.get(f"http://localhost:8001/stock-history/{ticker}", timeout=None)
                        if res.status_code != 200:
                            logger.warning(f"Stock history unavailable for {ticker}: {res.status_code}")
                            return

                        price_data = res.json()
                        points = []

                        for timestamp_str, price in price_data.items():
                            try:
                                timestamp = pd.to_datetime(timestamp_str)
                                timestamp = timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")

                                if price is None:
                                    continue

                                points.append(
                                    Point("stock_price")
                                    .tag("ticker", ticker)
                                    .field("close_price_history", float(price))
                                    .time(timestamp)
                                )
                            except Exception as e:
                                logger.error(f"[ParseError] {ticker} at {timestamp_str}: {e}")

                        if points:
                            api.write(bucket=os.getenv("INFLUXDB_BUCKET"), org=os.getenv("INFLUXDB_ORG"), record=points)
                            logging.info(f'[INFLUXDB] Writing timeseries for {ticker} to database')

                    except Exception as e:
                        logger.error(f"[HTTPError] {ticker}: {e}")

            await asyncio.gather(*[process_ticker(ticker) for ticker in tickers])


    async def write_forecast_df(self, datapoint, ticker, client:InfluxDBClient):
        """
        Write forecast DataFrame to InfluxDB.
        Expected df columns: 'ds' (datetime), 'y' (float), 'ticker' (str)
        """
        try:
            api = client.write_api(write_options=WriteOptions(write_type=ASYNCHRONOUS))
            timestamp = pd.to_datetime(datapoint.ds)
            logger.info(f'[INFLUX POST] Timestamp:{timestamp}')
            if timestamp.tzinfo is None:
                timestamp = timestamp.tz_localize('UTC')
            else:
                timestamp = timestamp.tz_convert('UTC')

            y_val = datapoint.y
            logger.info(f'[INFLUX POST] Value:{y_val}')
            try:
                y_float = float(y_val)
            except (ValueError, TypeError):
                logger.error(f"Invalid forecast value {y_val} for ticker {ticker} at {timestamp}")
                return
                        
            point = (
                Point("stock_price")
                .tag("ticker", ticker)
                .field("close_price_forecast", y_float)
                .time(timestamp)
            )
            logger.info(f'[INFLUX POST] Point:{point}')
            bucket = os.getenv('INFLUXDB_BUCKET')
            org = os.getenv('INFLUXDB_ORG')
            api.write(bucket=bucket, org=org, record=point)
            logger.info(f'[INFLUXDB POST] Written fc to bucket:{bucket}, org:{org}')

        except Exception as e:
            logger.error(f"Error writing forecast data for ticker {ticker} at {timestamp}: {str(e)}")
    

    async def delete_forecast_point(self, ticker: str, timestamp: datetime, client: InfluxDBClient):
        try:
            bucket = os.getenv("INFLUXDB_BUCKET")
            org = os.getenv("INFLUXDB_ORG")
            delete_api = client.delete_api()
            if isinstance(timestamp, str):
                timestamp = pd.to_datetime(timestamp)
                timestamp = timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")

            start = timestamp - timedelta(days=1)
            stop = timestamp + timedelta(days=1)

            predicate = f'_measurement="stock_price" AND ticker="{ticker}"'

            delete_api.delete(start=start, stop=stop, bucket=bucket, org=org, predicate=predicate)

            logger.info(f"[INFLUX DELETE] Deleted forecast point for {ticker} at {timestamp.isoformat()}")

        except Exception as e:
            logger.error(f"[INFLUX DELETE ERROR] Failed to delete {ticker} at {timestamp}: {e}")


