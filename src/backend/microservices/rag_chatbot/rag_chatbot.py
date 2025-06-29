from langchain.text_splitter import MarkdownTextSplitter, TokenTextSplitter
from qdrant_client.http.models import VectorParams, Distance
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, ValidationError
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from bs4 import XMLParsedAsHTMLWarning
from qdrant_client import QdrantClient
import matplotlib.ticker as mticker
from dataclasses import dataclass
from fastapi import HTTPException
import matplotlib.pyplot as plt
from openai import AsyncOpenAI
from dotenv import load_dotenv
from datetime import datetime
from typing import List
from uuid import uuid4
from io import BytesIO
from fpdf import FPDF
import pandas as pd
import tempfile
import requests
import warnings
import logging
import redis
import json
import os


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
            host = str(host or os.getenv("QDRANT_HOST"))
            port = int(port or os.getenv("QDRANT_PORT"))
            client = QdrantClient(host=host, port=port)
            logger.info(f"[Qdrant] Connected to {host}:{port}")
            return client
        except Exception as e:
            logger.error(f"[Qdrant ERROR] Connection failed: {e}")
            raise


    def connect_to_redis(
        self, host: str = None, port: int = None, db: int = 0, password: str = None
    ) -> redis.Redis:
        try:
            host = host or os.getenv("REDIS_HOST")
            port = int(port or os.getenv("REDIS_PORT", 6379))

            client = redis.Redis(host=host, port=port, db=db)
            client.ping()
            logger.info(f"[Redis] Connected to {host}:{port} (db={db})")
            return client
        except Exception as e:
            logger.error(f"[Redis ERROR] Connection failed: {e}")
            raise


    def delete_vec_docs(self, client: QdrantClient, collection_name: str = None):
        try:
            collection_name = collection_name or os.getenv("COLLECTION_NAME")
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
            collection_name = os.getenv("COLLECTION_NAME")
            chunk_size = int(os.getenv("CHUNK_SIZE", 3500))
            chunk_overlap = int(os.getenv("OVERLAP_SIZE", 200))
            markdown_splitter = MarkdownTextSplitter(chunk_size=10000, chunk_overlap=0)
            token_splitter = TokenTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )

            doc_row = None
            for form in sec_form_rank:
                filtered = context_docs[context_docs["form"] == form]
                if not filtered.empty:
                    doc_row = filtered.iloc[0]
                    break

            if doc_row is not None:
                content = doc_row.get("content")
                metadata = {
                    k: v
                    for k, v in doc_row.items()
                    if k != "content" and k != "raw_content"
                }
                documents = []
                markdown_chunks = markdown_splitter.split_text(str(content))
                for md_chunk in markdown_chunks:
                    token_chunks = token_splitter.split_text(md_chunk)
                    for chunk in token_chunks:
                        documents.append(
                            Document(page_content=chunk, metadata=metadata)
                        )

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
                        vectors_config=VectorParams(
                            size=vector_size, distance=Distance.COSINE
                        ),
                    )
                    logger.info(f"[Qdrant] Created collection '{collection_name}'")

                vector_store = QdrantVectorStore.from_existing_collection(
                    host=os.getenv("QDRANT_HOST"),
                    port=int(os.getenv("QDRANT_PORT")),
                    embedding=embeddings,
                    collection_name=collection_name,
                )
                vector_store.add_documents(documents=documents, ids=uuids)
                logger.info(
                    f"[Qdrant] Stored {len(documents)} document chunks in '{collection_name}'"
                )
                return vector_store
            else:
                logger.warning("[Qdrant] No ranked form found in docs.")
                return None

        except Exception as e:
            logger.error(f"[Qdrant ERROR] {e}")
            raise


    def query_qdrant(self, prompt: str, vector_store: QdrantVectorStore) -> Document:
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
                        "raw_content": raw_content.decode("utf-8")
                        if isinstance(raw_content, bytes)
                        else str(raw_content),
                        "cik": str(cik),
                        "accession": str(acc),
                        "form": str(filing_type),
                        "filename": str(file),
                    }
                    redis_client.rpush(filing_type, json.dumps(cached_docs))
                    logger.info(f"[REDIS] Appended doc for Filing Type '{filing_type}'")
                    forms_set.add(filing_type)
                else:
                    logger.warning(
                        f"[REDIS] Missing filing_type or content for row {idx}, skipping."
                    )

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
        forms_json = redis_client.get("available_forms")
        forms = json.loads(forms_json) if forms_json else []

        all_docs = {}
        for form in forms:
            docs = redis_client.lrange(form, 0, -1)
            docs_parsed = [json.loads(doc) for doc in docs]
            all_docs[form] = docs_parsed

        return all_docs


    def download_referenz_doc_from_redis(self, client: redis.Redis):
        ticker = client.get("ticker")
        ticker = ticker.decode("utf-8") if ticker else "UNKNOWN"

        forms_json = client.get("available_forms")
        try:
            forms = json.loads(forms_json.decode("utf-8")) if forms_json else []
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, detail="Invalid JSON in 'available_forms'"
            )

        if not forms:
            raise HTTPException(status_code=404, detail="No forms found")

        first_form = forms[0]
        docs = client.lrange(first_form, 0, -1)

        if not docs:
            raise HTTPException(
                status_code=404, detail="No documents found for first form"
            )

        doc_obj = json.loads(docs[0])
        raw_html = doc_obj.get("raw_content")

        if not raw_html:
            raise HTTPException(
                status_code=404, detail="No raw_content found in document"
            )

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".htm", mode="w", encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(raw_html)
            file_path = tmp_file.name

        return file_path, f"{ticker}_{first_form}_sec_report.htm"


    def generate_broker_analysis_pdf(self, data: dict, ticker: str) -> str:
        logo_path = None
        forecast_chart_path = None

        try:
            response = requests.get(f"http://api-gateway:8000/get-logo/{ticker}", timeout=20)
            if response.status_code == 200:
                tmp_logo = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                tmp_logo.write(response.content)
                tmp_logo.close()
                logo_path = tmp_logo.name

            response_hst = requests.get(f"http://influx-client:8004/history/{ticker}", timeout=None)
            logger.info('[RAG CHATBOT] requesting history from influx')
            history = response_hst.json()

            response_fc = requests.get(f"http://influx-client:8004/forecast/{ticker}", timeout=None)
            logger.info('[RAG CHATBOT] requesting forecast from influx')
            forecast = response_fc.json()

            if not history or not forecast:
                raise ValueError("Missing time series data for chart generation.")


            history_last_12 = history[-12:] if len(history) >= 12 else history
            history_data = [{"ds": item["ds"], "value": item["y"]} for item in history_last_12]
            forecast_data = [{"ds": item["ds"], "value": item["y"]} for item in forecast]

            combined = history_data + forecast_data
            combined.sort(key=lambda item: item["ds"])

            x_hist = []
            y_hist = []
            x_forecast = []
            y_forecast = []

            for i, item in enumerate(combined):
                try:
                    dt = datetime.fromisoformat(item["ds"])
                    if i < len(history_data):
                        x_hist.append(dt)
                        y_hist.append(item["value"])
                    else:
                        x_forecast.append(dt)
                        y_forecast.append(item["value"])
                except Exception as e:
                    logger.warning(f"Skipping invalid timestamp '{item['ds']}': {e}")

            fig, ax = plt.subplots(figsize=(5, 3))

            ax.plot(x_hist, y_hist, marker='o', label="History")

            ax.plot(x_forecast, y_forecast, marker='x', linestyle='--', label="Forecast", color='red', linewidth=2)

            ax.set_title("Forecast Stock Trend")
            ax.set_xlabel("Time")
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.2f}'))
            ax.set_ylabel("Close Price")

            ax.grid(False)

            fig.autofmt_xdate()

            ax.legend()

            fig.tight_layout()

            buf = BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_chart:
                tmp_chart.write(buf.read())
                forecast_chart_path = tmp_chart.name
                logger.info(f"[RAG CHATBOT] Chart saved at: {forecast_chart_path}")

        except Exception as e:
            logger.error(f"[PDF Generation] Chart/logo fetch or generation failed for {ticker}: {e}")

        class PDF(FPDF):
            def __init__(self):
                super().__init__()
                self.logo_inserted = False

            def header(self):
                self.set_y(10)
                self.set_text_color(0, 0, 0)
                self.set_font("Times", "B", 24)
                self.cell(0, 14, f"{data.get('company_name', 'Company')} - Broker Analysis", ln=True, align="C")
                self.ln(5)
            
            def footer(self):
                self.set_y(-15)
                self.set_font("Times", "I", 9)
                self.set_text_color(100)
                self.cell(0, 10, f"Page {self.page_no()}", align="C")

            def chapter_title(self, title):
                if not self.logo_inserted and logo_path and os.path.exists(logo_path):
                    logo_width = 20
                    x_center = (self.w - logo_width) / 2
                    self.image(logo_path, x=x_center, y=self.get_y(), w=logo_width)
                    self.ln(30)
                    self.logo_inserted = True

                self.set_fill_color(230, 230, 250)
                self.set_text_color(0, 0, 0)
                self.set_font("Times", "B", 14)
                self.ln(4)
                self.cell(0, 8, title, ln=True, fill=True)

            def chapter_body(self, text):
                self.set_font("Times", "", 11)
                self.set_text_color(50, 50, 50)
                self.multi_cell(0, 6, text or "")  
                self.ln(2)

        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        sections = {
            "Forecast Chart": forecast_chart_path,
            "Technical Analysis": (data.get("technical_analysis") or "").strip(),
            "Fundamental Analysis": (data.get("fundamental_analysis") or "").strip(),
            "Sentiment Analysis": (data.get("sentiment_analysis") or "").strip(),
            "Risks (SEC Files)": (data.get("risks_sec_files") or "").strip(),
            "Final Recommendation": f"{(data.get('final_recommendation') or '').strip()} - {(data.get('justification') or '').strip()}",
        }

        sec_meta = data.get("sec_metadata", [])
        if sec_meta:
            meta_text = ", ".join(
                f"File: {meta.get('file_name')}, Date: {meta.get('file_date')}, Type: {meta.get('file_type')}"
                for meta in sec_meta
            )
            sections["SEC Metadata"] = meta_text

        new_page_triggered = False

        for title, content in sections.items():
            if title == "Sentiment Analysis" and not new_page_triggered:
                pdf.add_page()
                new_page_triggered = True

            pdf.chapter_title(title)

            if title == "Forecast Chart" and content and os.path.exists(content):
                pdf.image(content, x=10, w=180)
                pdf.ln(10)
            else:
                pdf.chapter_body(content or "")


        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(tmp_file.name)
        tmp_file.close()

        if logo_path and os.path.exists(logo_path):
            os.remove(logo_path)
        if forecast_chart_path and os.path.exists(forecast_chart_path):
            os.remove(forecast_chart_path)

        return tmp_file.name


    async def gpt4o_broker_analysis(
        self,
        context_y_finance: str = None,
        context_sec: str = None,
        forecast_yf: str = None,
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
            openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.2,  # low temp for deterministic output
                max_tokens=1024,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content

            # If the model returns a markdown block, strip it
            if content.strip().startswith("```json"):
                content = (
                    content.strip().removeprefix("```json").removesuffix("```").strip()
                )
            elif content.strip().startswith("```"):
                content = (
                    content.strip().removeprefix("```").removesuffix("```").strip()
                )

            parsed = parser.parse(content)

            return parsed

        except ValidationError as ve:
            logger.error(f"[gpt4o_broker_analysis PARSING ERROR] {ve}")
            raise
        except Exception as e:
            logger.error(f"[gpt4o_broker_analysis ERROR] {e}")
            raise
