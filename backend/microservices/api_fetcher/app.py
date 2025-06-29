from fastapi.responses import JSONResponse, FileResponse
from fastapi import FastAPI, Query, HTTPException
from fastapi.encoders import jsonable_encoder
from api_data_fetcher import API_Fetcher
import logging
import tempfile
import os


logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)


logger = logging.getLogger(__name__)


fetcher = API_Fetcher()


app = FastAPI()


@app.get("/filter-market-cap/")
async def filter_market_cap(screeners: list[str] = Query(...), min_cap: int = 1_000_000_000):
    logger.info(f"[API FETCHER] screeners: [{screeners}]")
    all_tickers = await fetcher.get_tickers_from_screeners_async(screeners)
    logger.info(f"[API FETCHER] filtered tickers [{all_tickers}]")
    filtered = await fetcher.filter_tickers_by_market_cap_async(all_tickers[2], min_market_cap=min_cap)

    return JSONResponse(content=filtered)


@app.get("/companies")
async def all_available_companies():
    companies, screeners, ticker_screener = await fetcher.get_available_company_data()

    if companies.empty:
        return JSONResponse(content={"tickers": {}, "screeners": []}, status_code=204)

    screeners = sorted(screeners)

    companies = companies.to_dict(orient="records") 
    content = jsonable_encoder({
        "companies": companies,
        "screeners": screeners,
        "ticker_screener": ticker_screener
    })

    return JSONResponse(content=content, status_code=200)


@app.get("/stock-history/{ticker}")
async def stock_history(ticker: str):
    data = await fetcher.fetch_selected_stock_history_yq(selected_ticker=ticker)
    encoded = jsonable_encoder(data['price_history'])
    return JSONResponse(content=encoded, status_code=200)


@app.get("/yfinance-company-facts/{ticker}")
async def company_facts_yf(ticker: str):
    data = await fetcher.fetch_selected_stock_facts_yq(selected_ticker=ticker)
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



