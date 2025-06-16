import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api_fetcher.api_data_fetcher import API_Fetcher

import asyncio
import yfinance as yf
import pandas as pd
import logging
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Import the function or variable that provides the forecast DataFrame
from forecasting.utils import get_forecast_only



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("Influx code is running now - this step is only to test if influx run automatic...")


class DataCollector:
    """
    A class to collect data from Yahoo Finance
    """

    async def fetch_stock_data_yf(self, ticker: str, period: str = "1y", interval: str = "1d") -> dict:
        def _fetch():
            yf_ticker = yf.Ticker(ticker)
            history = yf_ticker.history(period=period, interval=interval)
            info = yf_ticker.info
            price_history = history['Close'].to_dict()
            return {
                "ticker": ticker,
                "name": info.get("longName"),
                "price_history": price_history,
                "current_price": info.get("currentPrice"),
                "market_cap": info.get("marketCap"),
                "sector": info.get("sector"),
                "industry": info.get("industry")
            }
        return await asyncio.to_thread(_fetch)


class InfluxDBHandler:
    """
    A class to handle InfluxDB operations: connecting and writing data.
    """

    def __init__(self):
        self.url = os.getenv("INFLUXDB_URL", "http://localhost:8086/")
        self.token = os.getenv("INFLUXDB_TOKEN", "mySuperSecretToken123!")
        self.org = os.getenv("INFLUXDB_ORG", "HSAA")
        self.bucket = os.getenv("INFLUXDB_BUCKET", "25s-cd-teamb")
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def write_stock_data(self, stock_data: dict):
        ticker = stock_data.get("ticker")
        now = pd.Timestamp.now(tz='UTC')

        for timestamp, price in stock_data.get("price_history", {}).items():
            try:
                timestamp = pd.to_datetime(timestamp)
                if timestamp.tzinfo is None:
                    timestamp = timestamp.tz_localize('UTC')
                else:
                    timestamp = timestamp.tz_convert('UTC')

                #if timestamp > now:
                    #logger.warning(f"Skipping future date for {ticker} at {timestamp}")
                    #continue

                if price is None:
                    continue

                try:
                    price_float = float(price)
                except (ValueError, TypeError):
                    logger.error(f"Invalid price value for {ticker} at {timestamp}: {price}")
                    continue

                point = (
                    Point("stock_prices_ILEF")
                    .tag("ticker", ticker)
                    .field("close_price", price_float)
                    .time(timestamp)
                )
                self.write_api.write(bucket=self.bucket, org=self.org, record=point)

            except Exception as e:
                logger.error(f"Error writing stock data for {ticker} at {timestamp}: {str(e)}")

    def write_forecast_df(self, df: pd.DataFrame):
        """
        Write forecast DataFrame to InfluxDB.
        Expected df columns: 'ds' (datetime), 'y' (float), 'ticker' (str)
        """
        now = pd.Timestamp.now(tz='UTC')

        for _, row in df.iterrows():
            try:
                timestamp = pd.to_datetime(row['ds'])
                if timestamp.tzinfo is None:
                    timestamp = timestamp.tz_localize('UTC')
                else:
                    timestamp = timestamp.tz_convert('UTC')

                #if timestamp > now:
                    #logger.warning(f"Skipping future date {timestamp} for ticker {row.get('ticker')}")
                    #continue

                y_val = row.get('y')
                if y_val is None:
                    continue

                try:
                    y_float = float(y_val)
                except (ValueError, TypeError):
                    logger.error(f"Invalid forecast value {y_val} for ticker {row.get('ticker')} at {timestamp}")
                    continue

                ticker = str(row.get('ticker', 'unknown'))

               
                point = (
                    Point("forecast_prices_PARDIS")
                    .tag("ticker", ticker)
                    .tag("type", "forecast456")
                    .field("price", y_float)
                    .time(timestamp)
                )
                self.write_api.write(bucket=self.bucket, org=self.org, record=point)

            except Exception as e:
                logger.error(f"Error writing forecast data for ticker {row.get('ticker')} at {row.get('ds')}: {str(e)}")


    def close(self):
        self.client.close()


# Optional: limit concurrency (e.g., to 10 parallel tasks)
semaphore = asyncio.Semaphore(10)


async def process_ticker(ticker, collector, influx_handler):
    async with semaphore:
        try:
            logger.info(f"Fetching stock data for {ticker}...")
            stock_data = await collector.fetch_stock_data_yf(ticker)
            logger.debug(f"Stock Data for {ticker}: {stock_data}")

            logger.info(f"Writing stock data for {ticker} to InfluxDB...")
            influx_handler.write_stock_data(stock_data)

            logger.info(f"Writing forecasting data for {ticker} to InfluxDB...")
            # Get the forecast DataFrame for the ticker from forecasting/app.py
            forecast_df = await get_forecast_only(ticker)  # Make sure get_forecast_df returns the correct DataFrame
            await asyncio.to_thread(influx_handler.write_forecast_df, forecast_df)

            #logger.info(f"Writing forecasting data for {ticker} to InfluxDB...")
            #await asyncio.to_thread(influx_handler.write_forecast_df, pd.DataFrame(stock_data['price_history'].items(), columns=['ds', 'y']).assign(ticker=ticker))

        except Exception as e:
            logger.error(f"Error processing {ticker}: {str(e)}")


async def main():
    collector = DataCollector()
    influx_handler = InfluxDBHandler()
    fetcher = API_Fetcher()

    logger.info("Fetching list of all major stock indices...")
    tickers = await fetcher.fetch_all_major_indices()
    logger.info(f"Fetched {len(tickers)} tickers.")

    tasks = [
        process_ticker(ticker, collector, influx_handler)
        for ticker in tickers
    ]
    await asyncio.gather(*tasks)

    influx_handler.close()
    logger.info("Process completed.")


if __name__ == "__main__":
    asyncio.run(main())
