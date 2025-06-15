from forecast_module import forecast_stock
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import logging
import json
import requests
import httpx
import pandas as pd

 
app = FastAPI()
 
@app.get("/forecast/{ticker}")
async def get_forecast(ticker: str):
    async with httpx.AsyncClient() as client:
        res_history = await client.get(f"http://api-fetcher:8001/stock-history/{ticker}", timeout=None)
        if res_history.status_code != 200:
            return JSONResponse(content={"error": "Stock history unavailable"}, status_code=500)
        price_data = res_history.json()

        res_facts = await client.get(f"http://api-fetcher:8001/yfinance-company-facts/{ticker}", timeout=None)
        if res_facts.status_code != 200:
            return JSONResponse(content={"error": "Company facts unavailable"}, status_code=500)
        facts_data = res_facts.json()

    df = pd.DataFrame(list(price_data.items()), columns=['ds', 'y'])
    df['unique_id'] = ticker
    df['recommendation'] = 1 if facts_data.get('recommendation_key', '').lower() == 'buy' else 0
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
    df['ds'] = pd.to_datetime(df['ds'], utc=True).dt.tz_localize(None)
    df['unique_id'] = df['unique_id'].astype(str)
    df['y'] = df['y'].astype('float64')

    print(df.dtypes)
    print(df.head())

    result = forecast_stock(ticker, df)
    forecast_df = result.rename(columns={'RNN': 'y'})

    history_part = df[['ds', 'y']].copy()
    forecast_part = forecast_df[['ds', 'y']].copy()

    final_result = {
        'history': history_part.to_dict(orient='records'),
        'forecast': forecast_part.to_dict(orient='records')
    }

    encoded = jsonable_encoder(final_result)
    return JSONResponse(content=encoded, status_code=200)