from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models
from qdrant_client.models import Filter, FieldCondition, MatchValue
from qdrant_client.http.models import Distance, VectorParams
from langchain.text_splitter import MarkdownTextSplitter
from langchain_openai import OpenAIEmbeddings
from dataclasses import dataclass
import json
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv
import streamlit as st
from uuid import uuid4
load_dotenv()

context_yfinance = None
context_sec = None


@dataclass
class RAG_Chatbot:
    
    def process_text_to_qdrant(self, context_docs: str,
                        collection_name=None,
                        host=None,
                        port=None,
                        chunk_size=None,
                        chunk_overlap=None,
                        metadata=None):
        """
        Splits text into chunks and stores them in Qdrant vector DB.
        """
        try:
            collection_name = collection_name or os.getenv('COLLECTION_NAME')
            host = host or os.getenv('QDRANT_HOST')
            port = int(port or os.getenv('QDRANT_PORT'))
            chunk_size = int(chunk_size or os.getenv('CHUNK_SIZE', 500))
            chunk_overlap = int(chunk_overlap or os.getenv('OVERLAP_SIZE', 50))
            metadata = metadata or {}
            splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            # st.write('Metadata:', metadata)
            chunks = splitter.split_text(str(context_docs))
            documents = [Document(metadata=metadata, page_content=chunk) for chunk in chunks]
            uuids = [str(uuid4()) for _ in range(len(documents))]
            # st.write(documents)
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                raise EnvironmentError("OPENAI_API_KEY not set in environment.")

            embeddings = OpenAIEmbeddings(model=os.getenv('EMBEDDING_MODEL_OPENAI'))

            client = QdrantClient(host=host, port=port)
            existing_collections = [c.name for c in client.get_collections().collections]

            if collection_name not in existing_collections:
                st.write('No collection found. Creating one...')
                vector_size = int(os.getenv('VECTOR_SIZE', 1536))  # default for OpenAI embeddings
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=models.Distance.COSINE)
                )

            url = f"http://{host}:{port}"

            vector_store = QdrantVectorStore.from_existing_collection(
                embedding=embeddings,
                collection_name=collection_name,
                url=url,
            )

            vector_store.add_documents(documents=documents, ids=uuids)
            st.success(f"Added {len(documents)} documents to '{collection_name}' collection.")

        except Exception as e:
            st.error(f"Data processing failed: {e}")



    def print_results(self, documents):
        for i, item in enumerate(documents, 1):
            doc = item[0] if isinstance(item, tuple) else item
            st.write(f"**Result #{i}**")
            st.write(doc.page_content)
            st.write(doc.metadata)
            st.markdown("---")

            
            
    def query_qdrant(self, prompt=None,
                    collection_name=os.getenv('COLLECTION_NAME'),
                    host=os.getenv('QDRANT_HOST'),
                    port=os.getenv('QDRANT_PORT'))->list[Document]:
        if not prompt:
            print("❌ No query prompt provided.")
            return

        try:
            
            client = QdrantClient(
                host=os.getenv('QDRANT_HOST'),
                port=os.getenv('QDRANT_PORT'),
            )
            
            embeddings = OpenAIEmbeddings(model=os.getenv('EMBEDDING_MODEL_OPENAI'))

            vector_store= QdrantVectorStore.from_existing_collection(
                client=client,
                embedding=embeddings,
                collection_name=os.getenv('COLLECTION_NAME'),
                url=f"http://{host}:{port}"
            )
            
            results = vector_store.similarity_search(
                prompt, k=2
            )
            
            self.print_results(results)
            return results
        except Exception as e:
            print(f"❌ Error during Qdrant query: {e}")
    
    
    def gpt4o_mini(self, company_facts, context_y_finance, context_sec)->str:
        try:
            client = OpenAI()

            completion = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {
                        "role": "user",
                        "content": f'''You are a financial analysis assistant. Analyze the provided data and determine whether to BUY, HOLD, or SELL the asset.

                        Use the following structure for your analysis:

                        1. Technical Analysis:
                        - Analyze moving averages (e.g., 20-day vs 50-day SMA).
                        - Consider the RSI (Relative Strength Index) and what it suggests (overbought, oversold, neutral).
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

                        Respond with the company facts (company name, ..) and then a very brief structured explanation followed by the final recommendation in caps lock'''
                    }
                ]
            )
            
            result = completion.choices[0].message.content

            return result

        except Exception as e:
            return f"Unexpected error: {e}"
        


    def deepseek_r1(self, company_facts, context_y_finance, context_sec)->str:
        try:
            HEADERS = {
                'Authorization': f"Bearer {os.environ.get('DEEPSEEK_API_KEY')}",
                'Content-Type': 'application/json',
            }

            data = {
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'user', 'content': f'''You are a financial analysis assistant. Analyze the provided data and determine whether to BUY, HOLD, or SELL the asset.

                    Use the following structure for your analysis:

                    1. Technical Analysis:
                    - Analyze moving averages (e.g., 20-day vs 50-day SMA).
                    - Consider the RSI (Relative Strength Index) and what it suggests (overbought, oversold, neutral).
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

                    Respond with the company facts (company name, ..) and then a very brief structured explanation followed by the final recommendation in caps lock'''}
                ],
                'stream': False
            }

            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers=HEADERS,
                data=json.dumps(data)
            )

            response.raise_for_status()  # Raise an error for HTTP issues
            result = response.json()

            return result['choices'][0]['message']['content']

        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"

