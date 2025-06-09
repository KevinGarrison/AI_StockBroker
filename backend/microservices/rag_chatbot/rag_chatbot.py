from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client.http.models import VectorParams, Distance
from langchain.text_splitter import MarkdownTextSplitter, TokenTextSplitter
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from langchain.output_parsers import PydanticOutputParser
from dataclasses import dataclass
import json
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
from uuid import uuid4
import httpx
from bs4 import XMLParsedAsHTMLWarning
import logging
import warnings
import pandas as pd
import redis
from pydantic import BaseModel, ValidationError
from typing import List, Optional
import tempfile
from fastapi import HTTPException


logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

load_dotenv()

class SecMetaData(BaseModel):
    file_name: str
    file_date: str
    file_type: str

class BrokerAnalysisOutput(BaseModel):
    company_name: str
    technical_analysis: str
    fundamental_analysis: str
    sentiment_analysis: str
    risks_sec_files: str
    final_recommendation: str
    justification: str
    sec_metadata: List[SecMetaData]

@dataclass
class RAG_Chatbot:
    
    def connect_to_qdrant(self, host: str = None, port: str = None) -> QdrantClient:
        try:
            host = str(host or os.getenv('QDRANT_HOST'))
            port = int(port or os.getenv('QDRANT_PORT'))
            client = QdrantClient(host=host, port=port)
            logger.info(f"[Qdrant] Connected to {host}:{port}")
            return client
        except Exception as e:
            logger.error(f"[Qdrant ERROR] Connection failed: {e}")
            raise


    def connect_to_redis(self, host: str = None, port: int = None, db: int = 0, password: str = None) -> redis.Redis:
        try:
            host = host or os.getenv('REDIS_HOST')
            port = int(port or os.getenv('REDIS_PORT', 6379))

            client = redis.Redis(host=host, port=port, db=db)
            client.ping() 
            logger.info(f"[Redis] Connected to {host}:{port} (db={db})")
            return client
        except Exception as e:
            logger.error(f"[Redis ERROR] Connection failed: {e}")
            raise


    def delete_vec_docs(self, client: QdrantClient, collection_name: str = None):
        try:
            collection_name = collection_name or os.getenv('COLLECTION_NAME')
            client.delete_collection(collection_name=collection_name)
            logger.info(f"[Qdrant] Deleted collection '{collection_name}'")
        except Exception as e:
            logger.error(f"[Qdrant ERROR] Couldn't delete collection: {e}")
    

    def delete_cached_docs(self, client: redis.Redis):
        try:
            client.flushdb()
            logger.info("[Redis] Deleted cache")
        except Exception as e:
            logger.error(f"[Redis ERROR] Couldn't delete collection: {e}")
    

    def process_most_important_form_to_qdrant(
        self,
        context_docs: pd.DataFrame,
        qdrant_client: QdrantClient,
        sec_form_rank: list,
    ) -> QdrantVectorStore:
        """
        Only store the single most important doc (by sec_form_rank) in Qdrant.
        """
        try:
            collection_name = os.getenv('COLLECTION_NAME')
            chunk_size = int(os.getenv('CHUNK_SIZE', 3500))
            chunk_overlap = int(os.getenv('OVERLAP_SIZE', 200))
            markdown_splitter = MarkdownTextSplitter(chunk_size=10000, chunk_overlap=0)
            token_splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

            doc_row = None
            for form in sec_form_rank:
                filtered = context_docs[context_docs['form'] == form]
                if not filtered.empty:
                    doc_row = filtered.iloc[0]
                    break

            if doc_row is not None:
                content = doc_row.get("content")
                metadata = {k: v for k, v in doc_row.items() if k != "content" and k != "raw_content"}
                documents = []
                markdown_chunks = markdown_splitter.split_text(str(content))
                for md_chunk in markdown_chunks:
                    token_chunks = token_splitter.split_text(md_chunk)
                    for chunk in token_chunks:
                        documents.append(Document(page_content=chunk, metadata=metadata))

                if not documents:
                    logger.warning("[Qdrant] No documents to add — skipping.")
                    return None

                uuids = [str(uuid4()) for _ in documents]
                embeddings = OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL_OPENAI"))
                existing = qdrant_client.get_collections().collections
                existing_names = [c.name for c in existing]

                if collection_name not in existing_names:
                    vector_size = int(os.getenv("VECTOR_SIZE", 3072))
                    qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                    )
                    logger.info(f"[Qdrant] Created collection '{collection_name}'")

                vector_store = QdrantVectorStore.from_existing_collection(
                    host=os.getenv("QDRANT_HOST"),
                    port=int(os.getenv("QDRANT_PORT")),
                    embedding=embeddings,
                    collection_name=collection_name
                )
                vector_store.add_documents(documents=documents, ids=uuids)
                logger.info(f"[Qdrant] Stored {len(documents)} document chunks in '{collection_name}'")
                return vector_store
            else:
                logger.warning("[Qdrant] No ranked form found in docs.")
                return None

        except Exception as e:
            logger.error(f"[Qdrant ERROR] {e}")
            raise

    
    def query_qdrant(self, prompt: str, vector_store:QdrantVectorStore) -> Document:
        try:
            return vector_store.similarity_search(prompt, k=4)
        except Exception as e:
            logger.error(f"[Qdrant ERROR] {e}")
            return [] 


    def store_docs_by_filing_type_list(
        self, context_docs: pd.DataFrame, redis_client: redis.Redis
    ) -> None:
        """
        Stores each document (with meta) in a Redis list keyed by Filing Type (form).
        Each Redis key is the filing type, and its value is a list of JSON objects.
        """
        try:
            forms_set = set()
            for idx, row in context_docs.iterrows():
                filing_type = row.get("form")
                raw_content = row.get("raw_content")
                cik = row.get("cik")
                acc = row.get("accession_number")
                file = row.get("docs")
                if filing_type and raw_content:
                    cached_docs = {
                        "raw_content": raw_content.decode("utf-8") if isinstance(raw_content, bytes) else str(raw_content),
                        "cik": str(cik),
                        "accession": str(acc),
                        "form": str(filing_type),
                        "filename": str(file)
                    }
                    redis_client.rpush(filing_type, json.dumps(cached_docs))
                    logger.info(f"[REDIS] Appended doc for Filing Type '{filing_type}'")
                    forms_set.add(filing_type)
                else:
                    logger.warning(f"[REDIS] Missing filing_type or content for row {idx}, skipping.")

            redis_client.set("available_forms", json.dumps(sorted(forms_set)))
            logger.info(f"[REDIS] Stored all available forms: {sorted(forms_set)}")
        except Exception as e:
            logger.error(f"[REDIS ERROR] {e}")
            raise


    def get_first_available_form_content(
        self, redis_client: redis.Redis, form_rank: list
    ) -> tuple:
        """
        Returns (form, doc_dict) for the highest-priority form available in Redis.
        Only returns the first (oldest) document stored for that form.
        If no form is found, returns (None, None).
        """
        for form in form_rank:
            docs_json = redis_client.lrange(form, 0, 0)  
            if docs_json:
                item = docs_json[0]
                try:
                    if isinstance(item, bytes):
                        item = item.decode("utf-8")
                    doc = json.loads(item)
                except Exception as e:
                    logger.warning(f"[REDIS] Could not decode item for {form}: {e}")
                    doc = {"raw_content": item}
                return form, doc
        return None, None
        

    def get_all_docs_from_redis(self, redis_client):
        forms_json = redis_client.get('available_forms')
        forms = json.loads(forms_json) if forms_json else []
        
        all_docs = {}
        for form in forms:
            docs = redis_client.lrange(form, 0, -1)
            docs_parsed = [json.loads(doc) for doc in docs]
            all_docs[form] = docs_parsed

        return all_docs


    def download_referenz_doc_from_redis(self, client: redis.Redis):
        forms_json = client.get('available_forms')
        forms = json.loads(forms_json) if forms_json else []
        
        if not forms:
            raise HTTPException(status_code=404, detail="No forms found")
        
        first_form = forms[0] 
        docs = client.lrange(first_form, 0, -1)
        
        if not docs:
            raise HTTPException(status_code=404, detail="No documents found for first form")
        
        doc_json = docs[0]  
        doc_obj = json.loads(doc_json)
        raw_html = doc_obj.get("raw_content")
        
        if not raw_html:
            raise HTTPException(status_code=404, detail="No raw_content found in document")
        
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".htm", mode="w", encoding="utf-8")
        tmp_file.write(raw_html)
        tmp_file.close()
        
        return tmp_file.name, f"{first_form}_0.htm"


    async def gpt4o_broker_analysis(
            self,
            context_y_finance: str = None,
            context_sec: str = None,
            forecast_yf: str = None
        ) -> BrokerAnalysisOutput:
            try:
                parser = PydanticOutputParser(pydantic_object=BrokerAnalysisOutput)
                format_instructions = parser.get_format_instructions()

                user_prompt = f"""
    You are a financial analysis assistant.
    Analyze the provided data and determine whether to BUY, HOLD, or SELL the asset.

    Your response MUST follow this format:
    {format_instructions}

    Here are the company facts:
    {context_y_finance}

    Here are the key facts from SEC filing:
    {context_sec}

    Here is a forecast of the stock:
    {forecast_yf}

    Instructions:
    1. Use the SEC files for risk analysis. 
    2. Use the forecast for your decisison.
    3. Use news in the facts about the company for your sentiment analysis.
    4. Identify if there are some risks according to the Form of the SEC filing. 
    5. Mention all your decisions from the instructions in the analysis.
    """
                openai_client = AsyncOpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
                response = await openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,  # low temp for deterministic output
                    max_tokens=1024,
                    response_format={"type": "json_object"},
                )

                content = response.choices[0].message.content

                # If the model returns a markdown block, strip it
                if content.strip().startswith("```json"):
                    content = content.strip().removeprefix("```json").removesuffix("```").strip()
                elif content.strip().startswith("```"):
                    content = content.strip().removeprefix("```").removesuffix("```").strip()

                parsed = parser.parse(content)

                return parsed

            except ValidationError as ve:
                logger.error(f"[gpt4o_broker_analysis PARSING ERROR] {ve}")
                raise
            except Exception as e:
                logger.error(f"[gpt4o_broker_analysis ERROR] {e}")
                raise

        