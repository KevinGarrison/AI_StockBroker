from api_data_fetcher import API_Fetcher
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.encoders import jsonable_encoder
import yfinance as yf
import logging
import json
import httpx
import tempfile
import os



logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

logger = logging.getLogger(__name__)

fetcher = API_Fetcher()

app = FastAPI()

@app.get("/dropdown-values")
async def dropdown_values_endpoint():
    values = await fetcher.get_available_dropdown_values_async()
    return JSONResponse(content=values)

@app.get("/tickers-for-screener/{screener}")
async def tickers_for_screener_endpoint(screener: str):
    tickers = await fetcher.get_tickers_for_screener_async(screener)
    return JSONResponse(content=tickers)

@app.get("/filter-market-cap/{screener}/{min_cap}")
async def filter_market_cap(screener: str, min_cap:int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://api-fetcher:8001/tickers-for-screener/{screener}", timeout=None)
        tickers = response.json()
    tickers = await fetcher.filter_tickers_by_market_cap_async(tickers=tickers, min_market_cap=min_cap)
    return JSONResponse(content=tickers)

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

@app.get("/company-news/{ticker}")
async def company_news_selected_ticker(ticker: str):
    context = await fetcher.get_company_news(ticker)
    encoded = jsonable_encoder(context)
    return JSONResponse(content=encoded, status_code=200)

@app.get("/get-logo/{ticker}")
def get_logo(ticker: str):
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    logo_path = fetcher.fetch_logo(ticker, tmp_file.name)

    if not logo_path or not os.path.exists(logo_path):
        raise HTTPException(status_code=404, detail="Logo not found or company website missing")

    return FileResponse(
        path=logo_path,
        media_type="image/png",
        filename=f"{ticker}_logo.png",
        background=lambda: os.remove(logo_path)
    )



