from rag_chatbot import RAG_Chatbot
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from contextlib import asynccontextmanager
from pathlib import Path
import logging
import asyncio
import time
import pandas as pd

logger = logging.getLogger(__name__)

rag_bot = RAG_Chatbot()

redis_db = {}
vector_db = {}

class ContextData(BaseModel):
    yf_stock_data: dict
    sec_details_1: dict

@asynccontextmanager
async def lifespan(app: FastAPI):
    vector_db["client"] = rag_bot.connect_to_qdrant()
    redis_db["client"] = rag_bot.connect_to_redis()

    try:
        yield
    finally:
        rag_bot.delete_vec_docs(client=vector_db["client"])
        rag_bot.delete_cached_docs(client=redis_db["client"])
        vector_db["client"].close()
        redis_db["client"].close()
        vector_db.clear()
        redis_db.clear()

app = FastAPI(lifespan=lifespan)


@app.post("/relevant-sec-files/{ticker}")
async def process_and_get_most_relevant_files(
    ticker: str,
    context: ContextData = Body(...)
):
    prompt = f"""Find the most important recent SEC filings for {ticker}
    focusing on documents relevant to stock research such as:
    10-K (annual report),
    10-Q (quarterly report),
    8-K (material events),
    S-1 (if applicable),
    and DEF 14A (proxy statements).
    """
    context_dict = context.dict()

    context_df = pd.DataFrame([{
        "raw_content": "...",   # ← required field
        "content": "...",       # ← required field
        "cik": context_dict['sec_details_1'].get("cik", ""),
        "accession_number": context_dict['sec_details_1'].get("accession_number", ""),
        "docs": context_dict['sec_details_1'].get("docs", ""),
        "form": context_dict['sec_details_1'].get("form", "")
    }])

    task_7 = time.time()
    vector_store = await asyncio.to_thread(
        rag_bot.process_text_to_qdrant,
        context_docs=context_df,  
        client=vector_db["client"],
        redis=redis_db["client"]
    )
    logger.info(f"[{ticker}] Step 7 - Store SEC documents in vector db - {time.time() - task_7:.2f}s")

    task_8 = time.time()
    vdb_result = await asyncio.to_thread(
        rag_bot.query_qdrant,
        prompt=prompt,
        vector_store=vector_store
    )
    logger.info(f"[{ticker}] Step 8 - Query SEC documents in vector db - {time.time() - task_8:.2f}s")

    sec_result_formatted = [
        {
            "content": doc.page_content,
            "metadata": doc.metadata
        }
        for doc in vdb_result
    ]

    context_yf = str(context.yf_stock_data)
    company_facts = str(context.sec_details_1)

    task_9 = time.time()
    final_broker_analysis = await rag_bot.deepseek_r1_broker_analysis(
        company_facts=company_facts,
        context_y_finance=context_yf,
        context_sec=str(sec_result_formatted)
    )
    logger.info(f"[{ticker}] Step 9 - Final AI Broker Analysis - {time.time() - task_9:.2f}s")

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

    return JSONResponse(content=jsonable_encoder(result_json), status_code=200)

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

        output_path = temp_dir / f"{form}_{file_name}"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return JSONResponse(content=jsonable_encoder(decoded_doc_data), status_code=200)

    except Exception as e:
        logger.error(f"[REDIS ERROR] Failed to fetch {accession}/{filename} - {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document from Redis.")
