from rag_chatbot import RAG_Chatbot
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from contextlib import asynccontextmanager
from pathlib import Path
import logging
import asyncio
import time
import pandas as pd
import json
import os
import io
from weasyprint import HTML


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

    analysis_json = json.dumps(encoded)
    redis_client = redis_db["client"]
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, redis_client.set, "broker_analysis", analysis_json)
    await loop.run_in_executor(None, redis_client.set, "ticker", ticker)

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

@app.get("/reference-doc-pdf")
def reference_doc_pdf():
    client = redis_db["client"]

    html_file_path, base_filename = rag_bot.download_referenz_doc_from_redis(client)
    
    pdf_io = io.BytesIO()
    HTML(filename=html_file_path).write_pdf(pdf_io)
    pdf_io.seek(0)

    pdf_filename = base_filename.replace('.htm', '.pdf')
    return StreamingResponse(
        pdf_io,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
    )

@app.get("/download-refdoc-redis")
def download_refdoc_endpoint():
    client = redis_db["client"]
    file_path, filename = rag_bot.download_referenz_doc_from_redis(client)

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="text/html",
        background=lambda: os.remove(file_path) 
    )

@app.get("/download-broker-pdf/{ticker}")
def download_broker_pdf(ticker:str):
    redis_client = redis_db["client"]
    json_str = redis_client.get("broker_analysis")
    if not json_str:
        raise HTTPException(status_code=404, detail="No broker analysis found in Redis")

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid JSON format in Redis")

    pdf_path = rag_bot.generate_broker_analysis_pdf(data=data, ticker=ticker)

    return FileResponse(
        path=pdf_path,
        filename="broker_analysis.pdf",
        media_type="application/pdf",
        background=lambda: os.remove(pdf_path)
    )

    
@app.get("/delete-cached-docs")
async def delete_docs():
    rag_bot.delete_vec_docs(client=vector_db["client"])
    rag_bot.delete_cached_docs(client=redis_db["client"])

    return JSONResponse(content={"message": "Cache successfully deleted"}, status_code=200)


