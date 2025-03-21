from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_huggingface import HuggingFaceEmbeddings
from dataclasses import dataclass
import json
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv

load_dotenv()

context_yfinance = None
context_sec = None


@dataclass
class RAG_Chatbot:
    def process_text_to_qdrant(self, context_docs: str,
                               collection_name=os.getenv('COLLECTION_NAME'), 
                               host=os.getenv('QDRANT_HOST'),
                               port=os.getenv('QDRANT_PORT'), 
                               chunk_size=os.getenv('CHUNK_SIZE'),
                               chunk_overlap=os.getenv('OVERLAP_SIZE')):
        """
        Splits text into chunks and stores them in Qdrant vector DB.
        
        Parameters:
            context_docs (str): The full raw text to chunk and embed.
            collection_name (str): Qdrant collection name.
            host (str): Qdrant host.
            port (int): Qdrant port.
            chunk_size (int): Max characters per chunk.
            chunk_overlap (int): Overlap between chunks.
        """
        try:
            # Split text into chunks
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
            )
            chunks = splitter.split_text(context_docs)
            documents = [Document(page_content=chunk) for chunk in chunks]
            
            embeddings = HuggingFaceEmbeddings(model_name=os.getenv('EMBEDDING_MODEL_NAME'))

            client = QdrantClient(
                host=os.getenv('QDRANT_HOST'),
                port=os.getenv('QDRANT_PORT'),
            )

            # Check if collection exists
            if collection_name not in client.get_collections().collections:
                # Create collection if it doesn't exist
                client.create_collection(
                    collection_name=os.getenv('COLLECTION_NAME'),
                    vectors_config=VectorParams(size=os.getenv('VECTOR_SIZE'), distance=Distance.COSINE)
                )

            # Store documents in Qdrant
            vector_store = QdrantVectorStore.from_documents(
                documents=documents,
                embedding=embeddings,
                collection_name=os.getenv('COLLECTION_NAME'),
                url=f"http://{host}:{port}"
            )
            
            print(f"Stored {len(documents)} chunks in Qdrant collection: '{os.getenv('COLLECTION_NAME')}'")
            return vector_store
        except Exception as e:
            print('Data processing failed!', e)
            
    def print_results(self, documents):
        for i, doc in enumerate(documents, 1):
            print(f"\n📄 Result #{i}")
            print("-" * 40)
            print("🔑 Metadata:")
            for key, value in doc.metadata.items():
                print(f"   {key}: {value}")
            print("\n📄 Content:")
            print(doc.page_content.strip())
            
    def query_qdrant(self, prompt=None, collection_name=os.getenv('COLLECTION_NAME'), host=os.getenv('QDRANT_HOST'), port=os.getenv('QDRANT_PORT')):
        if not prompt:
            print("❌ No query prompt provided.")
            return

        try:
            
            client = QdrantClient(
                host=os.getenv('QDRANT_HOST'),
                port=os.getenv('QDRANT_PORT'),
            )
            
            embeddings = HuggingFaceEmbeddings(model_name=os.getenv('EMBEDDING_MODEL_NAME'))

            vector_store = QdrantVectorStore(
                client=client,
                collection_name=os.getenv('COLLECTION_NAME'),
                embedding=embeddings,
            )
            
            results = vector_store.similarity_search(
                query, k=2
            )
            
            self.print_results(results)
        except Exception as e:
            print(f"❌ Error during Qdrant query: {e}")
    
    def gpt4o_mini(self, company_facts, context_y_finance, context_sec):
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

                        Here are the company facts:
                        {company_facts}
                        
                        Here is the data from yahoo finance:
                        {context_y_finance}

                        Here are the key facts from sec filings:
                        {context_sec}

                        Respond with the company facts (company name, ..) and then a very brief structured explanation followed by the final recommendation in caps lock'''
                    }
                ]
            )
            
            result = completion.choices[0].message.content

            return result

        except Exception as e:
            return f"Unexpected error: {e}"
        


    def deepseek_r1(self, company_facts, context_y_finance, context_sec):
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
                    
                    Here are the company facts:
                    {company_facts}
                    
                    Here is the data from yahoo finance:
                    {context_y_finance}

                    Here are the key facts from sec filings:
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



        

if __name__ == "__main__":
    chatbot = RAG_Chatbot()
    example_text = """
    DeepSeek is an open-source initiative focused on building high-performance large language models (LLMs). 
    Its models are designed to support reasoning, coding, and advanced natural language understanding.

    Qdrant is a vector database optimized for storing and searching high-dimensional embeddings. 
    It enables semantic search and real-time AI applications by providing fast and accurate similarity queries.

    LangChain is a framework that allows developers to build applications with language models. 
    It supports document retrieval, agents, tools, and memory features, making it ideal for RAG-based workflows.
    """
    chatbot.process_text_to_qdrant(context_docs=example_text)
    query = "What is Qdrant used for?"
    chatbot.query_qdrant(prompt=query)
