from fastapi import FastAPI
import logging
import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
##############################################################################################
# For Dev change hostname of the requests to localhost & for prod (Container) to containername
##############################################################################################
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/companies")
async def companies():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://api-fetcher:8001/companies")
        return response.json()

@app.get("/stock-history/{ticker}")
async def stock_history(ticker: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://api-fetcher:8001/stock-history/{ticker}")
        return response.json()

@app.get("/company-facts/{ticker}")
async def company_facts(ticker: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://api-fetcher:8001/yfinance-company-facts/{ticker}")
        return response.json()

@app.get("/company-news/{ticker}")
async def company_news(ticker: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://api-fetcher:8001/company-news/{ticker}")
        return response.json()
    
@app.get("/stock-broker-analysis/{ticker}")
async def stock_broker_analysis(ticker: str):
    async with httpx.AsyncClient() as client:
        all_company_data = await client.get(f"http://api-fetcher:8001/company-context/{ticker}", timeout=300.0)
        logger.info("[AI Result 1]", all_company_data)
        context_data = all_company_data.json()
        logger.info("[AI Result 2]", context_data)
        response = await client.post(f"http://rag-chatbot:8002/relevant-sec-files/{ticker}", json=context_data, timeout=120.0)      
        logger.info("[AI Result 3]", response)
        return response.json()

@app.get("/reference-doc/{accession}/{filename}")
async def get_reference_files(accession: str, filename: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://rag-chatbot:8002/reference-doc-from-analysis/{accession}/{filename}")     
        return response.json()

@app.get("/forecast/{ticker}")
async def get_forecast(ticker:str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://forecasting:8003/forecast/{ticker}")     
        return response.json()
