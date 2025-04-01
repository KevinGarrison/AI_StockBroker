from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
#from qdrant_client.models import Filter, FieldCondition, MatchValue / Mabey use in advance
from qdrant_client.http.models import VectorParams, Distance
from langchain.text_splitter import MarkdownTextSplitter, TokenTextSplitter
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
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


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

load_dotenv()


@dataclass
class RAG_Chatbot:
    
    def connect_to_qdrant(self, host: str = None, port: str = None) -> QdrantClient:
        try:
            host = str(host or os.getenv('QDRANT_HOST'))
            port = int(port or os.getenv('QDRANT_PORT'))
            client = QdrantClient(host=host, port=port)
            logging.info(f"[Qdrant] Connected to {host}:{port}")
            return client
        except Exception as e:
            logging.error(f"[Qdrant ERROR] Connection failed: {e}")
            raise
        
    def connect_to_redis(self, host: str = None, port: int = None, db: int = 0, password: str = None) -> redis.Redis:
        try:
            host = host or os.getenv('REDIS_HOST', 'localhost')
            port = int(port or os.getenv('REDIS_PORT', 6379))
            password = password or os.getenv('REDIS_PASSWORD', None)

            client = redis.Redis(host=host, port=port, db=db)
            client.ping()  # Verbindungsprüfung
            logging.info(f"[Redis] Connected to {host}:{port} (db={db})")
            return client
        except Exception as e:
            logging.error(f"[Redis ERROR] Connection failed: {e}")
            raise

    def delete_session_stored_docs(self, client: QdrantClient, collection_name: str = None):
        try:
            collection_name = collection_name or os.getenv('COLLECTION_NAME')
            client.delete_collection(collection_name=collection_name)
            logging.info(f"[Qdrant] Deleted collection '{collection_name}'")
        except Exception as e:
            logging.error(f"[Qdrant ERROR] Couldn't delete collection: {e}")

    def process_text_to_qdrant(self, context_docs: pd.DataFrame, client: QdrantClient, redis: redis.Redis) -> QdrantVectorStore:
        try:
            
            collection_name = os.getenv('COLLECTION_NAME')
            chunk_size = int(os.getenv('CHUNK_SIZE', 3500))  # now in tokens
            chunk_overlap = int(os.getenv('OVERLAP_SIZE', 200))

            markdown_splitter = MarkdownTextSplitter(chunk_size=10000, chunk_overlap=0)
            token_splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

            documents = []

            for _, row in context_docs.iterrows():
                content = row.get("content")
                cik = row.get("cik")
                acc = row.get("accession_number")
                file = row.get("docs")
                form = row.get("form")
                if not content:
                    continue
                
                cached_docs = {
                    "content":content,
                    "cik":cik,
                    "accession":acc,
                    "form":form,
                    "filename":file
                }
                
                redis.hset(name=f"{cik}",key=f"{acc}/{file}", mapping=cached_docs)
                
                metadata = {k: v for k, v in row.items() if k != "content"}

                # Step 1: Markdown structure chunks
                markdown_chunks = markdown_splitter.split_text(str(content))

                # Step 2: Token-limited chunks per markdown section
                for md_chunk in markdown_chunks:
                    token_chunks = token_splitter.split_text(md_chunk)
                    for chunk in token_chunks:
                        documents.append(Document(page_content=chunk, metadata=metadata))

            uuids = [str(uuid4()) for _ in documents]

            embeddings = OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL_OPENAI"))

            existing = client.get_collections().collections
            existing_names = [c.name for c in existing]

            if collection_name not in existing_names:
                vector_size = int(os.getenv("VECTOR_SIZE", 3072))
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                logging.info(f"[Qdrant] Created collection '{collection_name}'")

            vector_store = QdrantVectorStore.from_existing_collection(
                host=os.getenv("QDRANT_HOST"),
                port=int(os.getenv("QDRANT_PORT")),
                embedding=embeddings,
                collection_name=collection_name
            )


            if not documents:
                logging.warning("[Qdrant] No documents to add — skipping.")
                return None

            vector_store.add_documents(documents=documents, ids=uuids)
            logging.info(f"[Qdrant] Stored {len(documents)} document chunks in '{collection_name}'")
            return vector_store

        except Exception as e:
            logging.error(f"[Qdrant ERROR] {e}")
            raise

    def query_qdrant(self, prompt: str, client: QdrantClient, collection_name: str = None) -> list[Document]:
        try:
            collection_name = collection_name or os.getenv('COLLECTION_NAME')
            embeddings = OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL_OPENAI"))

            existing = client.get_collections().collections
            existing_names = [c.name for c in existing]

            if collection_name not in existing_names:
                logging.warning(f"[Qdrant] No collection '{collection_name}' found")
                return []

            vector_store = QdrantVectorStore.from_existing_collection(
                host=os.getenv("QDRANT_HOST"),
                port=int(os.getenv("QDRANT_PORT")),
                embedding=embeddings,
                collection_name=collection_name
            )


            return vector_store.similarity_search(prompt, k=2)

        except Exception as e:
            logging.error(f"[Qdrant ERROR] {e}")
            return []



    async def gpt4o_mini(self, company_facts:str=None, context_y_finance:str=None, context_sec:str=None)->str:
        try:
            client = AsyncOpenAI()

            completion = await client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {
                        "role": "user",
                        "content": f'''You are a financial analysis assistant.
                        Analyze the provided data and determine whether to BUY, HOLD, or SELL the asset.

                        Use the following structure for your analysis:

                        1. Technical Analysis:
                        - Analyze moving averages (e.g., 20-day vs 50-day SMA).
                        - Consider the RSI (Relative Strength Index) and what it suggests:
                        (overbought, oversold, neutral).
                        - Mention any trend or signal (bullish, bearish, etc.).

                        2. Fundamental Analysis:
                        - Evaluate key metrics such as P/E ratio, ROE, and EPS.
                        - Mention if valuation is high/low, earnings performance, and profitability outlook.

                        3. Sentiment Analysis:
                        - Consider the provided sentiment summary (from news, social media, etc.).
                        - State whether the market sentiment is positive, negative, or neutral.

                        4. Final Recommendation:
                        - Clearly state a one-word recommendation: BUY, HOLD, or SELL.
                        - Briefly justify the decision based on the analysis above.
                        
                        5. Meta Data SEC Files:
                        - List here only the Metadata of the SEC Files not the Content.

                        Here are the company facts:
                        {company_facts}
                        
                        Here is the data from yahoo finance:
                        {context_y_finance}

                        Here are the key facts from SEC filings:
                        {context_sec}

                        Respond with the company facts (company name, ..) and then a very brief,
                        structured explanation followed by the final recommendation in caps lock'''
                    }
                ]
            )
            
            result = completion.choices[0].message.content

            return result

        except Exception as e:
            return f"Unexpected error: {e}"        


    async def deepseek_r1(self, company_facts:str=None, context_y_finance:str=None, context_sec:str=None)->str:
        try:
            HEADERS = {
                'Authorization': f"Bearer {os.environ.get('DEEPSEEK_API_KEY')}",
                'Content-Type': 'application/json',
            }

            data = {
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'user', 'content': f'''You are a financial analysis assistant.
                    Analyze the provided data and determine whether to BUY, HOLD, or SELL the asset.

                    Use the following structure for your analysis:

                    1. Technical Analysis:
                    - Analyze moving averages (e.g., 20-day vs 50-day SMA).
                    - Consider the RSI (Relative Strength Index) and what it suggests: 
                    (overbought, oversold, neutral).
                    - Mention any trend or signal (bullish, bearish, etc.).

                    2. Fundamental Analysis:
                    - Evaluate key metrics such as P/E ratio, ROE, and EPS.
                    - Mention if valuation is high/low, earnings performance, and profitability outlook.

                    3. Sentiment Analysis:
                    - Consider the provided sentiment summary (from news, social media, etc.).
                    - State whether the market sentiment is positive, negative, or neutral.

                    4. Final Recommendation:
                    - Clearly state a one-word recommendation: BUY, HOLD, or SELL.
                    - Briefly justify the decision based on the analysis above.
                    
                    5. Meta Data SEC Files:
                        - List here only the Metadata of the SEC Files not the Content.
                    
                    Here are the company facts:
                    {company_facts}
                    
                    Here is the data from yahoo finance:
                    {context_y_finance}

                    Here are the key facts from SEC filings:
                    {context_sec}

                    Respond with the company facts (company name, ..) and then a very brief,
                    structured explanation followed by the final recommendation in caps lock'''}
                ],
                'stream': False
            }
            logging.debug(json.dumps(data, indent=2))
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.deepseek.com/chat/completions",
                    headers=HEADERS,
                    data=json.dumps(data)
                )
                response.raise_for_status()
                result = response.json()

            return result['choices'][0]['message']['content']

        except httpx.RequestError as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"

