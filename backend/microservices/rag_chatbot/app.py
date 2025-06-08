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
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)

rag_bot = RAG_Chatbot()

redis_db = {}
vector_db = {}

SEC_FORM_RANK = [
    "10-K", "10-Q", "8-K", "S-1", "DEF 14A", "20-F", "6-K", "13D/13G", "4", "S-8"
]


class ContextData(BaseModel):
    yf_stock_data: dict
    base_sec_df: dict
    forecast: dict


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
    prompt = """Find the highest risk according to the 10k form"""
    context_dict = context.dict()
    
    yf_stock_data = context_dict['yf_stock_data']
    context_df = pd.DataFrame.from_dict(context_dict['base_sec_df'])
    forecast = context_dict['forecast']
    
    await asyncio.to_thread(rag_bot.store_docs_by_filing_type_list,    
                            context_docs=context_df, redis_client=redis_db["client"])

        
    form, doc = await asyncio.to_thread(
        rag_bot.get_first_available_form_content, 
        redis_client=redis_db["client"], 
        form_rank=SEC_FORM_RANK
    )

    vec_db = await asyncio.to_thread(
        rag_bot.process_most_important_form_to_qdrant,
        context_docs=context_df,
        qdrant_client=vector_db["client"],
        sec_form_rank=SEC_FORM_RANK
    )

    vec_db_results = await asyncio.to_thread(
        rag_bot.query_qdrant,
        prompt=prompt,
        vector_store=vec_db
    )

    if form and doc:
        sec_result_formatted = {
            "Form": form,
            "content": vec_db_results,
            "metadata": {
                "cik": doc.get("cik"),
                "accession": doc.get("accession"),
                "filename": doc.get("filename"),
                "form": doc.get("form")
            }
        }
    else:
        sec_result_formatted = {}


    context_yf = str(yf_stock_data)
    

    final_broker_analysis = await rag_bot.gpt4o_broker_analysis(
        context_y_finance=str(context_yf),
        context_sec=str(sec_result_formatted)[:10000],
        forecast_yf = str(forecast)
    )

    encoded = jsonable_encoder(final_broker_analysis)
    return JSONResponse(content=encoded, status_code=200)


@app.get("/reference-docs-from-analysis")
async def get_reference_files():
    if not redis_db.get("client"):
        raise HTTPException(status_code=500, detail="Redis client not available.")

    try:
        redis = redis_db["client"]
        all_docs = await asyncio.to_thread(rag_bot.get_all_docs_from_redis, redis)
        return JSONResponse(content=jsonable_encoder(all_docs), status_code=200)

    except Exception as e:
        logger.error(f"[REDIS ERROR] Failed to fetch reference docs - {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents from Redis.")

    
@app.get("/delete-cached-docs")
async def delete_docs():
    rag_bot.delete_vec_docs(client=vector_db["client"])
    rag_bot.delete_cached_docs(client=redis_db["client"])

    return JSONResponse(content={"message": "Cache successfully deleted"}, status_code=200)


