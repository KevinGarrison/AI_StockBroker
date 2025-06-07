from fastapi import FastAPI
import logging
import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/delete-cache")
async def delete_cache():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://rag-chatbot:8002/delete-cached-docs", timeout=None)
        return response.json()

@app.get("/first-filter-dropdown")
async def first_filter():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://api-fetcher:8001/dropdown-values", timeout=None)
        return response.json()

@app.get("/second-filter-market-cap/{screener}/{min_cap}")
async def second_filter(screener:str, min_cap:int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://api-fetcher:8001/filter-market-cap/{screener}/{min_cap}", timeout=None)
        return response.json()


@app.get("/tickers-for-screener/{screener}")
async def first_filter_tickers(screener):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://api-fetcher:8001/tickers-for-screener/{screener}", timeout=None)
        return response.json()

@app.get("/companies")
async def companies():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://api-fetcher:8001/companies", timeout=None)
        return response.json()

@app.get("/stock-history/{ticker}")
async def stock_history(ticker: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://api-fetcher:8001/stock-history/{ticker}", timeout=None)
        return response.json()

@app.get("/company-facts/{ticker}")
async def company_facts(ticker: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://api-fetcher:8001/yfinance-company-facts/{ticker}", timeout=None)
        return response.json()

@app.get("/company-news/{ticker}")
async def company_news(ticker: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://api-fetcher:8001/company-news/{ticker}", timeout=None)
        return response.json()
    
@app.get("/stock-broker-analysis/{ticker}")
async def stock_broker_analysis(ticker: str):
    async with httpx.AsyncClient() as client:
        all_company_data = await client.get(f"http://api-fetcher:8001/company-context/{ticker}", timeout=None)
        company_json = all_company_data.json()
        logger.info(f"[AI Result 1]: {company_json.keys()}")
        
        forecast = await client.get(f"http://forecasting:8003/forecast/{ticker}", timeout=None)
        forecast_json = forecast.json()
        company_json['forecast'] = forecast_json

        logger.info(f"[AI Result 2]: {company_json.keys()}")
        response = await client.post(
            f"http://rag-chatbot:8002/relevant-sec-files/{ticker}",
            json=company_json, timeout=None)
        logger.info("[AI Result 3]")
        return response.json()

@app.get("/reference-docs")
async def get_reference_files():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://rag-chatbot:8002/reference-docs-from-analysis", timeout=None)     
        return response.json()

@app.get("/forecast/{ticker}")
async def get_forecast(ticker:str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://forecasting:8003/forecast/{ticker}", timeout=None)     
        return response.json()
