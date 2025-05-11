from fastapi import FastAPI
import logging
import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
async def companies():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8001/companies")
        return response.json()

@app.get("/stock-history/{ticker}")
async def stock_history(ticker: str = None):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8001/stock-history/{ticker}")
        return response.json()

@app.get("/company-facts/{ticker}")
async def company_facts(ticker: str = None):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8001/yfinance-company-facts/{ticker}")
        return response.json()
    
@app.get("/stock-broker-analysis/{ticker}")
async def stock_broker_analysis(ticker: str = None):
    async with httpx.AsyncClient() as client:
        all_company_data = await client.get(f"http://localhost:8001/company-context/{ticker}")
        response = await client.post(f"http://localhost:8002/relevant-sec-files//{ticker}", json=all_company_data, timeout=120.0)      
        return response.json()

@app.get("/reference-doc/{accession}/{filename}")
async def get_reference_files(accession: str, filename: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/reference-doc-from-analysis/{accession}/{filename}")      
        return response.json()
    