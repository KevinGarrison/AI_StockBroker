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
        # Preis-Historie abrufen
        res_history = await client.get("http://api-fetcher:8001/stock-history/{ticker}", timeout=None)
        if res_history.status_code != 200:
            return JSONResponse(content={"error": "Stock history unavailable"}, status_code=500)
        price_data = res_history.json()

        # Unternehmensdaten abrufen
        res_facts = await client.get(f"http://api-fetcher:8001/yfinance-company-facts/{ticker}", timeout=None)
        if res_facts.status_code != 200:
            return JSONResponse(content={"error": "Company facts unavailable"}, status_code=500)
        facts_data = res_facts.json()
    
    # Preis-Daten in DataFrame laden
    # In DataFrame umwandeln
    df = pd.DataFrame(list(price_data.items()), columns=['ds', 'y'])
    df['unique_id'] = ticker

    # Notwendige Features in DataFrame einfügen
    #df['recommendation_key'] = facts_data.get('recommendation_key', 'hold')
    #df['recommendation'] = 1 if features.get('recommendation_key') == 'buy' else 0
    df['recommendation'] = 1 if facts_data.get('recommendation_key', '').lower() == 'buy' else 0
    df['eps_forward'] = facts_data.get('eps_forward', 0.0)
    df['revenue_growth'] = facts_data.get('revenue_growth', 0.0)
    df['recommendation_mean'] = facts_data.get('recommendation_mean', 0.0)
    df['gross_margins'] = facts_data.get('gross_margins', 0.0)
    df['dividend_yield'] = facts_data.get('dividend_yield', 0.0)
    df['debt_to_equity'] = facts_data.get('debt_to_equity', 0.0)

    # Forecast berechnen
    result = forecast_stock(ticker, df)

    # Ergebnis zurückgeben
    #return JSONResponse(content=jsonable_encoder(result), status_code=200)
    return JSONResponse(content=result, status_code=200)
