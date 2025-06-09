from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
import httpx
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


@app.get("/download-reference-doc")
async def download_reference_doc():
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "http://rag-chatbot:8002/download-refdoc-redis", timeout=None
        )

        headers = {
            "Content-Disposition": resp.headers.get("content-disposition", "attachment; filename=reference.htm"),
            "Content-Type": resp.headers.get("content-type", "text/html"),
        }
        return Response(content=resp.content, headers=headers, media_type=headers["Content-Type"])


@app.get("/download-reference-doc-pdf")
async def download_reference_doc_pdf():
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "http://rag-chatbot:8002/reference-doc-pdf", timeout=None
        )
        headers = {
            "Content-Disposition": resp.headers.get(
                "content-disposition", "attachment; filename=reference.pdf"
            ),
            "Content-Type": resp.headers.get("content-type", "application/pdf"),
        }
        return Response(content=resp.content, headers=headers, media_type=headers["Content-Type"])


@app.get("/download-broker-pdf/{ticker}")
async def download_broker_pdf(ticker:str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"http://rag-chatbot:8002/download-broker-pdf/{ticker}", timeout=None
        )

        if resp.status_code != 200:
            return Response(content=resp.text, status_code=resp.status_code)

        headers = {
            "Content-Disposition": resp.headers.get(
                "content-disposition", "attachment; filename=broker_analysis.pdf"
            ),
            "Content-Type": resp.headers.get("content-type", "application/pdf"),
        }

        return Response(content=resp.content, headers=headers, media_type=headers["Content-Type"])


@app.get("/get-logo/{ticker}")
async def proxy_logo(ticker: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://api-fetcher:8001/get-logo/{ticker}", timeout=20)

        if response.status_code != 200:
            try:
                detail = response.json().get("detail", "Logo not found")
            except Exception:
                detail = response.text or "Logo not found"
            raise HTTPException(status_code=response.status_code, detail=detail)

        return Response(
            content=response.content,
            media_type="image/png",
            headers={
                "Content-Disposition": f"inline; filename={ticker}_logo.png"
            }
        )
    except HTTPException as e:
        raise e 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch logo: {str(e)}")




@app.get("/forecast/{ticker}")
async def get_forecast(ticker:str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://forecasting:8003/forecast/{ticker}", timeout=None)     
        return response.json()
