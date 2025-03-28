from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client.async_qdrant_client import AsyncQdrantClient
#from qdrant_client.models import Filter, FieldCondition, MatchValue / Mabey use in advance
from qdrant_client.http.models import VectorParams, Distance
from langchain.text_splitter import MarkdownTextSplitter
from langchain_openai import OpenAIEmbeddings
from dataclasses import dataclass
import json
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
from uuid import uuid4
import httpx

load_dotenv()


@dataclass
class RAG_Chatbot:
    
    # Connect to qdrant client
    async def connect_to_qdrant(self, host:str=None, port:str=None)->AsyncQdrantClient:
        try:
            host = str(host) or os.getenv('QDRANT_HOST')
            port = str(port) or int(os.getenv('QDRANT_PORT'))
            client = AsyncQdrantClient(host=host, port=port)
            return client
        except Exception as e:
            print(f"Error while connecting to Qdrant: {e}")
        
    async def delete_session_stored_docs(self, client:AsyncQdrantClient=None,
                                            collection_name:str=None,
                                            ):
        try:
            collection_name = str(collection_name) or os.getenv('COLLECTION_NAME')
            await client.delete_collection(collection_name=os.environ.get('COLLECTION_NAME'))
            print(f'Collection {collection_name} deleted')
        except Exception as e:
            print(f"Error {e} while deleting collection {collection_name}")
            

    async def process_text_to_qdrant(self, context_docs:str=None,
                            collection_name:str=None,
                            metadata:dict=None,
                            chunk_size:int=None,
                            chunk_overlap:int=None,
                            client:AsyncQdrantClient=None,
                            host:str=None,
                            port:str=None)->str:
        """
        Splits text into chunks and stores them in Qdrant vector DB.
        """
        try:
            client = client
            host = str(host) or os.getenv('QDRANT_HOST')
            port = int(port) or int(os.getenv('QDRANT_PORT'))
            collection_name = str(collection_name) or os.getenv('COLLECTION_NAME')
            url = f"http://{host}:{port}"
            
            chunk_size = int(chunk_size or os.getenv('CHUNK_SIZE', 500))
            chunk_overlap = int(chunk_overlap or os.getenv('OVERLAP_SIZE', 50))
            metadata = metadata or {}
            
            splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks = splitter.split_text(str(context_docs))
            documents = [Document(metadata=metadata, page_content=chunk) for chunk in chunks]
            uuids = [str(uuid4()) for _ in range(len(documents))]
            
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                raise EnvironmentError("OPENAI_API_KEY not set in environment.")

            embeddings = OpenAIEmbeddings(model=os.getenv('EMBEDDING_MODEL_OPENAI'))


            existing_collections = [c.name for c in await client.get_collections().collections]

            if collection_name not in existing_collections:
                print('No collection found. Creating one...')
                vector_size = int(os.getenv('VECTOR_SIZE', 3072)) 
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )

            
            vector_store = QdrantVectorStore.from_existing_collection(
                client=client,
                embedding=embeddings,
                collection_name=collection_name,
                url=url,
            )

            vector_store.add_documents(documents=documents, ids=uuids)
            return f"Collection {collection_name} created and {len(documents)} stored!"
        except Exception as e:
            return f"Data processing failed: {e}"


    async def query_qdrant(self, prompt:str=None,
                    collection_name:str=None,
                    client:AsyncQdrantClient=None,
                    host:str=None,
                    port:str=None)->list[Document]:
        try:
            client = client
            host = str(host) or os.getenv('QDRANT_HOST')
            port = int(port) or int(os.getenv('QDRANT_PORT'))
            collection_name = str(collection_name) or os.getenv('COLLECTION_NAME')
            url = f"http://{host}:{port}"
            
            embeddings = OpenAIEmbeddings(model=os.getenv('EMBEDDING_MODEL_OPENAI'))

            existing_collections = [c.name for c in await client.get_collections().collections]
            
            if collection_name in existing_collections:
                vector_store= QdrantVectorStore.from_existing_collection(
                    client=client,
                    embedding=embeddings,
                    collection_name=collection_name,
                    url=url
                )
                
                results = vector_store.similarity_search(
                    prompt, k=2
                )
            else:
                print(f"No collection '{collection_name}' found!")
            return results
        except Exception as e:
            return f"Error during Qdrant query: {e}"


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

            async with httpx.AsyncClient() as client:
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

