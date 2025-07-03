######### Author: Pardis Ebrahimi ##########

from neuralforecast import NeuralForecast
from neuralforecast.models import RNN
import pandas as pd
import logging
import httpx


logger = logging.getLogger(__name__)


async def prepare_forecast_data(ticker: str) -> pd.DataFrame:
    try:
        async with httpx.AsyncClient() as client:
            res_history = await client.get(f"http://influx-client:8004/history/{ticker}", timeout=None)
            if res_history.status_code != 200:
                raise Exception("Stock history unavailable")
            price_data = res_history.json()
            res_facts = await client.get(f"http://api-fetcher:8001/yfinance-company-facts/{ticker}", timeout=None)

            if res_facts.status_code != 200:
                raise Exception("Company facts unavailable")
            facts_data = res_facts.json()

        df = pd.DataFrame(price_data)
        logger.info(f'[FORECAST] prepared history data for {ticker}:{df}')
        logger.info(f'[FORECAST] facts keys: {facts_data}')
        df['unique_id'] = ticker
        df['eps_forward'] = facts_data.get('eps_forward', 0.0)
        df['revenue_growth'] = facts_data.get('revenue_growth', 0.0)
        df['recommendation_mean'] = facts_data.get('recommendation_mean', 0.0)
        df['gross_margins'] = facts_data.get('gross_margins', 0.0)
        df['dividend_yield'] = facts_data.get('dividend_yield', 0.0)
        df['debt_to_equity'] = facts_data.get('debt_to_equity', 0.0)

        float_cols = [
            'eps_forward', 'revenue_growth', 'recommendation_mean',
            'gross_margins', 'dividend_yield', 'debt_to_equity', 'recommendation'
        ]
        for col in float_cols:
            if col in df.columns:
                df[col] = df[col].astype('float64').fillna(0.0)

        df['ds'] = pd.to_datetime(df['ds']).dt.tz_localize(None)
        df['unique_id'] = df['unique_id'].astype(str)
        df['y'] = df['y'].astype('float64')
        logger.info(f'[FORECAST] payload df {df}')

        return df
    except Exception as e:
        logger.exception(f"[FORECAST] Failed to prepare forecast data for {ticker}")
        raise


def forecast_stock(ticker: str, df: pd.DataFrame) -> dict:
    try:
        logger.info(f"[FORECAST] Starting forecast for {ticker}")

        df['ds'] = pd.to_datetime(df['ds'])
        df['ds'] = df['ds'].dt.tz_localize(None)    
        df['unique_id'] = df['unique_id'].astype(str)
        df['y'] = df['y'].astype('float64')

        feature_columns = [
            'recommendation', 'eps_forward', 'revenue_growth',
            'recommendation_mean', 'gross_margins',
            'dividend_yield', 'debt_to_equity'
        ]

        for col in feature_columns:
            if col in df.columns:
                df[col] = df[col].astype('float64').fillna(0.0)

        logger.info(f"[FORECAST] Data prepared with shape {df.shape}")
        logger.debug(f"[FORECAST] Data preview:\n{df.head(3)}")

        model = RNN(h=5, input_size=12, max_steps=100)
        nf = NeuralForecast(models=[model], freq='ME')

        nf.fit(df=df)

        logger.info("[FORECAST] Predicting future prices...")
        forecast = nf.predict()
        logger.info("[FORECAST] Forecast complete")

        return forecast

    except Exception as e:
        logger.exception(f"[FORECAST] Forecasting failed for {ticker}: {e}")
        raise
