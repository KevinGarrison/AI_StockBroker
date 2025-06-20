from fastapi.responses import Response, JSONResponse
from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
import logging
import httpx


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


logger = logging.getLogger(__name__)


union_tickers = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        logger.info("[API-GATEWAY] Lifespan starting")
        response = await client.get("http://api-fetcher:8001/companies", timeout=None)

        logger.info("[API-GATEWAY] Startup task: building union of tickers for second filter")

        if response.status_code == 200:
            result = response.json()
            companies = result.get("companies", [])
            screeners = result.get("screeners", [])
            ticker_screeners = result.get("ticker_screener")

            tickers = [entry.get("ticker") for entry in companies if "ticker" in entry]

            union_tickers["tickers"] = sorted(set(tickers))
            union_tickers["screeners"] = sorted(set(screeners))
            union_tickers["ticker_screener"] = ticker_screeners
            union_tickers["companies"] = companies

        else:
            logger.warning(f"[API-GATEWAY] Failed to fetch companies: {response.status_code}")
            union_tickers["tickers"] = []
            union_tickers["screeners"] = []
            union_tickers["ticker_screener"] = []
            union_tickers["companies"] = []

    yield

    union_tickers.clear()


app = FastAPI(lifespan=lifespan)


@app.get("/data-ingest-yf-to-influx")
async def ingest_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://influx-client:8004/collect-stock-history-from-yfinance", timeout=None)
        if response.status_code == 200:
            logger.info('[API-GATEWAY] Request Yahoo Finance data collection')
            return {'Status': 'Ingested data successfully'}
        else:
            logger.error('[API-GATEWAY] Failed request Yahoo Finance data collection')
            return {'Status': 'Failed'}


@app.get("/companies-for-dropdown")
async def companies():
    return union_tickers["tickers"]


@app.get("/screeners")
async def screeners():
    return union_tickers["screeners"]


@app.get("/filter-ticker-from-screener/")
async def ticker_screener(screeners: list[str] = Query(...)):
    filtered_data = [
        (s, t) for s, t in union_tickers["ticker_screener"]
        if s in screeners
    ]
    return JSONResponse(content={"filtered": filtered_data})


@app.get("/second-filter-market-cap/")
async def second_filter(
    screeners: list[str] = Query(...),
    min_cap: int = 1_000_000_000
):
    params = [("screeners", s) for s in screeners]
    params.append(("min_cap", str(min_cap)))

    async with httpx.AsyncClient() as client:
        try:
            logger.info(
                "[API-GATEWAY] Forwarding to /filter-market-cap/ → screeners=%s, min_cap=%s",
                screeners, min_cap
            )

            response = await client.get(
                "http://api-fetcher:8001/filter-market-cap/",
                params=params,
                timeout=None
            )
            response.raise_for_status()
            return JSONResponse(content=response.json())

        except httpx.RequestError as e:
            logger.error("[API-GATEWAY] Network error: %s", e)
            return JSONResponse(status_code=502, content={"error": "downstream unreachable"})

        except httpx.HTTPStatusError as e:
            logger.error("[API-GATEWAY] Downstream returned status %s", e.response.status_code)
            return JSONResponse(status_code=502, content={"error": "downstream error"})

        except Exception as e:
            logger.exception("[API-GATEWAY] Unexpected error: %s", e)
            return JSONResponse(status_code=500, content={"error": "internal error"})


@app.get("/companies-df")
async def companies_df():
    return union_tickers["companies"]


@app.get("/company-facts/{ticker}")
async def company_facts(ticker: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://api-fetcher:8001/yfinance-company-facts/{ticker}", timeout=None)
        logger.info('[API-GATEWAY] requesting company facts from yahoo finance')
        return response.json()


@app.get("/company-news/{ticker}") 
async def company_news(ticker: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://api-fetcher:8001/company-news/{ticker}", timeout=None)
        logger.info('[API-GATEWAY] requesting yahoo finance news')
        return response.json()


@app.get("/stock-history/{ticker}")
async def stock_history(ticker: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://influx-client:8004/history/{ticker}", timeout=None)
        logger.info('[API-GATEWAY] requesting yahoo finance stock-history from influx')
        return response.json()


@app.get("/delete-cache")
async def delete_cache():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://rag-chatbot:8002/delete-cached-docs", timeout=None)
        logger.info('[API-GATEWAY] deleting cached docs')
        return response.json()


@app.get("/stock-broker-analysis/{ticker}")
async def stock_broker_analysis(ticker: str):
    async with httpx.AsyncClient() as client:
        # Step 1: SEC Data
        all_company_data = await client.get(f"http://api-fetcher:8001/company-context/{ticker}", timeout=None)
        company_json = all_company_data.json()
        logger.info("[AI Result 1]: SEC files pulled")

        forecast_json = {}
        try:
            forecast = await client.get(f"http://forecasting:8003/forecast/{ticker}", timeout=None)
            if forecast.status_code == 200:
                forecast_json = forecast.json()
                forecast_data = forecast_json.get('forecast', [])
                company_json['forecast'] = {
                    "forecast": forecast_json.get("forecast", []),  
                    "history": forecast_json.get("history", [])     
                }
                logger.info(f"[AI Result 2]: Forecast [{forecast_data}]")

                influx_post = await client.post(
                    f"http://influx-client:8004/write-forecast-to-influx/{ticker}",
                    json={"history": forecast_data},
                    timeout=None
                )
                if influx_post.status_code != 200:
                    logger.warning(f"Failed to post forecast to Influx for {ticker}: {influx_post.text}")
            else:
                logger.warning(f"Forecast API returned {forecast.status_code} for {ticker}")
                company_json['forecast'] = []
        except Exception as e:
            logger.exception(f"Exception while fetching or posting forecast for {ticker}")
            company_json['forecast'] = []

        try:
            response = await client.post(
                f"http://rag-chatbot:8002/relevant-sec-files/{ticker}",
                json=company_json,
                timeout=None
            )
            analysis = response.json()
            logger.info(f"[AI Result 3] Final recommendation of gpt4o broker [{analysis.get('final_recommendation')}]")
            return analysis

        except Exception as e:
            logger.exception(f"Failed to analyze SEC files for {ticker}")
            return JSONResponse(status_code=500, content={"error": "SEC analysis failed"})


@app.get("/forecast/{ticker}")
async def get_forecast(ticker:str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://influx-client:8004/forecast/{ticker}", timeout=None)
        logger.info('[API-GATEWAY] requesting forecast of Neural Network predictor')
        return response.json()


@app.get("/reference-docs")
async def get_reference_files():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://rag-chatbot:8002/reference-docs-from-analysis", timeout=None)
        logger.info('[API-GATEWAY] requesting reference docs')
        return response.json()


@app.get("/download-reference-doc")
async def download_reference_doc():
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://rag-chatbot:8002/download-refdoc-redis", timeout=None)
        logger.info('[API-GATEWAY] downloading reference docs from redis cache')
        headers = {
            "Content-Disposition": resp.headers.get("content-disposition", "attachment; filename=reference.htm"),
            "Content-Type": resp.headers.get("content-type", "text/html"),
        }
        return Response(content=resp.content, headers=headers, media_type=headers["Content-Type"])


@app.get("/download-broker-pdf/{ticker}")
async def download_broker_pdf(ticker:str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://rag-chatbot:8002/download-broker-pdf/{ticker}", timeout=None)

        if resp.status_code != 200:
            return Response(content=resp.text, status_code=resp.status_code)
        logger.info('[API-GATEWAY] downloading broker pdf')
        headers = {
            "Content-Disposition": resp.headers.get("content-disposition", "attachment; filename=broker_analysis.pdf"),
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
        logger.info('[API-GATEWAY] requesting company logo png')

        return Response(
            content=response.content,
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename={ticker}_logo.png"}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch logo: {str(e)}")


@app.get("/delete-forecasts")
async def delete_forecast():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://influx-client:8004/delete-forecasts", timeout=None)
        logger.info('[API-GATEWAY] deleting forecast in influxDB')
        return response.json()
