from backend.utils.rag_chatbot import RAG_Chatbot
from contextlib import asynccontextmanager
from fastapi import FastAPI

app = FastAPI()

vector_db = {}
timeseries_db = {}
rag_bot = RAG_Chatbot()

@asynccontextmanager
async def lifespan(app: FastAPI):
    vector_db["client"] = await rag_bot.connect_to_qdrant()
    # timeseries_db["client"] = await timeseries.connect_to_influx()
    yield
    await vector_db['client'].close()
    # await timeseries_db["client"].close()
    
    vector_db.clear()
    timeseries_db.clear()


app = FastAPI(lifespan=lifespan)

@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}

@app.get("/stock_broker_analysis/{ticker}")
async def read_filings(ticker: str):
    return {"ticker": ticker}
