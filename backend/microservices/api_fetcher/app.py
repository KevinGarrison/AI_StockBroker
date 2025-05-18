from api_data_fetcher import API_Fetcher
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import logging
import json

logger = logging.getLogger(__name__)

fetcher = API_Fetcher()

app = FastAPI()

@app.get("/companies")
async def all_available_companies():
    df = await fetcher.get_available_company_data()
    encoded = jsonable_encoder(json.loads(df.to_json(orient="records")))
    return JSONResponse(content=encoded, status_code=200)

@app.get("/stock-history/{ticker}")
async def stock_history(ticker: str):
    data = await fetcher.fetch_selected_stock_data_yf(selected_ticker=ticker)
    encoded = jsonable_encoder(data['price_history'])
    return JSONResponse(content=encoded, status_code=200)

@app.get("/yfinance-company-facts/{ticker}")
async def company_facts_yf(ticker: str):
    data = await fetcher.fetch_selected_stock_data_yf(selected_ticker=ticker)
    data.pop('price_history')
    encoded = jsonable_encoder(data)
    return JSONResponse(content=encoded, status_code=200)

@app.get("/company-context/{ticker}")
async def company_context_selected_ticker(ticker: str):
    context = await fetcher.preprocess_and_pull_context_sec_yf(ticker=ticker)
    encoded = jsonable_encoder(context)
    return JSONResponse(content=encoded, status_code=200)



