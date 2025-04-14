from utils.rag_chatbot import RAG_Chatbot
from utils.api_data_fetcher import API_Fetcher
from contextlib import asynccontextmanager
from fastapi import HTTPException
from fastapi import FastAPI
import json
from bs4 import XMLParsedAsHTMLWarning
import logging
import warnings
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

load_dotenv()

app = FastAPI()

redis_db = {}
vector_db = {}
timeseries_db = {}
rag_bot = RAG_Chatbot()
fetcher = API_Fetcher()

@asynccontextmanager
async def lifespan(app: FastAPI):
    vector_db["client"] = rag_bot.connect_to_qdrant()
    redis_db["client"] = rag_bot.connect_to_redis()
    
    try:
        yield
    finally:
        rag_bot.delete_session_stored_docs(client=vector_db["client"])
        vector_db["client"].close()
        redis_db["client"].close()
        vector_db.clear()
        redis_db.clear()


app = FastAPI(lifespan=lifespan)

# Vars
result = None
docs = None
query=None

@app.get("/")
async def read_root():
    available_companies = await fetcher.get_available_company_data()
    return available_companies.to_json(orient="records")

@app.get("/stock-history/{ticker}")
async def stock_history_of_selected_ticker(ticker:str=None):
    data = await fetcher.fetch_selected_stock_data_yf(selected_ticker=ticker)
    history_timeseries = {str(key): value for key, value in data['price_history'].items()}
    return json.dumps(history_timeseries)
    
@app.get("/stock-broker-analysis/{ticker}")
async def pull_and_analyze(ticker: str = None):
    start_time = time.time()
    all_data = {}

    # Step 1: Validate & find ticker
    task_1 = time.time()
    all_companies_df = await fetcher.get_available_company_data()
    logger.info(f"[{ticker}] Step 1 - Fetched company data ({len(all_companies_df)} rows) - {time.time() - task_1:.2f}s")
    datapoint = all_companies_df[all_companies_df['ticker'] == ticker]

    if datapoint.empty:
        raise HTTPException(status_code=404, detail=f"No company found for ticker '{ticker}'")

    row = datapoint.iloc[0]
    all_data['ticker'] = ticker
    all_data['cik'] = str(row["cik_str"]).zfill(10)
    all_data['company_title'] = row["title"]
    
    # Step 2: Yahoo Finance Data
    task_2 = time.time()
    all_data['yf_stock_data'] = await fetcher.fetch_selected_stock_data_yf(selected_ticker=ticker)
    logger.info(f"[{ticker}] Step 2 - Fetched Yahoo Finance data - {time.time() - task_2:.2f}s")

    # Step 3: SEC Data
    task_3 = time.time()
    details_1, details_2, filing_accessions = await fetcher.fetch_selected_company_details_and_filing_accessions(
        selected_cik=all_data['cik']
    )
    logger.info(f"[{ticker}] Step 3 - Fetched SEC filings - {time.time() - task_3:.2f}s")
    all_data['sec_details_1'] = details_1
    all_data['sec_details_2'] = details_2
    all_data['filing_accessions'] = filing_accessions
    task_4 = time.time()
    all_data['mapping_latest_docs'] = fetcher.get_latest_filings_index(filings=all_data['filing_accessions'])
    logger.info(f"[{ticker}] Step 4 - Get SEC documents index- {time.time() - task_4:.2f}s")

    all_data['base_sec_df'] = fetcher.create_base_df_for_sec_company_data(mapping_latest_docs=all_data['mapping_latest_docs'],
                                                                        filings=all_data['filing_accessions'],
                                                                        cik=all_data['cik'])
    
    task_5 = time.time()
    docs_content_series = await fetcher.fetch_all_filings(base_sec_df=all_data['base_sec_df'])
    logger.info(f"[{ticker}] Step 5 - Fetch SEC documents - {time.time() - task_5:.2f}s")
    task_6 = time.time()
    docs_content_series_1 = await fetcher.preprocess_docs_content(series=docs_content_series)
    logger.info(f"[{ticker}] Step 6 - Preprocess SEC documents - {time.time() - task_6:.2f}s")
    temp_df = all_data['base_sec_df'].copy()
    temp_df['raw_content'] = docs_content_series
    temp_df['content'] = docs_content_series_1
    all_data['final_sec_df'] = temp_df
    
    task_7 = time.time()
    vector_store = await asyncio.to_thread(
        rag_bot.process_text_to_qdrant,
        context_docs=all_data['final_sec_df'],
        client=vector_db["client"],
        redis=redis_db["client"]
    )
    logger.info(f"[{ticker}] Step 7 - Store SEC documents in vector db - {time.time() - task_7:.2f}s")

    query = 'what is the biggest risc according to the sec filings in 2024?'
    task_8 = time.time()
    result = vector_store.similarity_search(query=query, k=1)
    logger.info(f"[{ticker}] Step 8 - Find most related SEC documents - {time.time() - task_8:.2f}s")
    sec_result_formatted = [
        {
            "content": doc.page_content,
            "metadata": doc.metadata
        }
        for doc in result
    ]
    
    context_yf = str(all_data['yf_stock_data'])
    company_facts = str(all_data['sec_details_1'])
    task_9 = time.time() 
    final_broker_analysis = await rag_bot.deepseek_r1_broker_analysis(company_facts=company_facts,
                                                context_y_finance=context_yf,
                                                context_sec=str(sec_result_formatted))
    logger.info(f"[{ticker}] Step 9 - Final AI Broker Analysis - {time.time() - task_9:.2f}s")
    end_time = time.time()
    elapsed = end_time - start_time
    
    logger.info(f"[{ticker}] Task completed in {elapsed:.2f} seconds")
    
    result_json = {
        "broker_analysis": final_broker_analysis,
        "reference_file_metadata": [
            {
                "cik": doc["metadata"].get("cik"),
                "accession_number": doc["metadata"].get("accession_number"),
                "filename": doc["metadata"].get("docs")
            }
            for doc in sec_result_formatted
        ]
    }

    return json.dumps(result_json)


@app.get("/reference-doc-from-analysis/{accession}/{filename}")
async def get_reference_files(accession: str, filename: str):
    if not redis_db.get("client"):
        raise HTTPException(status_code=500, detail="Redis client not available.")

    try:
        redis = redis_db["client"]
        key = f"{accession}/{filename}"
        doc_data = await asyncio.to_thread(redis.hgetall, key)

        if not doc_data:
            raise HTTPException(status_code=404, detail="Document not found in Redis.")

        decoded_doc_data = {k.decode(): v.decode() for k, v in doc_data.items()}
        
        html_content = decoded_doc_data.get("raw_content")

        form = decoded_doc_data.get("form")
        file_name = decoded_doc_data.get("filename")
        
        
        temp_dir = Path("temp_sec_files")
        temp_dir.mkdir(exist_ok=True)

        # Save the HTML
        output_path = temp_dir / f"{form}_{file_name}"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return decoded_doc_data

    except Exception as e:
        logger.error(f"[REDIS ERROR] Failed to fetch {accession}/{filename} - {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document from Redis.")
