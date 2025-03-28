from backend.utils.rag_chatbot import RAG_Chatbot
from backend.utils.api_data_fetcher import API_Fetcher
from contextlib import asynccontextmanager
from fastapi import FastAPI

app = FastAPI()

vector_db = {}
timeseries_db = {}
rag_bot = RAG_Chatbot()
fetcher = API_Fetcher()

@asynccontextmanager
async def lifespan(app: FastAPI):
    vector_db["client"] = await rag_bot.connect_to_qdrant()
    # timeseries_db["client"] = await timeseries.connect_to_influx()
    yield
    await rag_bot.delete_session_stored_docs(client=vector_db['client'])
    await vector_db['client'].close()
    # await timeseries_db["client"].close()
    
    vector_db.clear()
    timeseries_db.clear()


app = FastAPI(lifespan=lifespan)

result = None
    
# Vars
docs = None
query=None
ids_row = []
company_data={}
selected_id_title = {}
company_details_and_filing_acc = {}
mapping_latest_forms_doc_index = {}
important_forms = ['10-K', '10-Q', '8-K', 'S-1', 'S-3', 'DEF 14A', '20-F', '6-K', '4', '13D', '13G']

@app.get("/")
async def read_root():
    
    return {"message": "Hello, FastAPI!"}


@app.get("/stock_broker_analysis/{ticker}/")
async def pull_and_analyze(ticker:str):
    investment_recommendation = None
    ticker, company_id = await fetcher.get_base_data(selected_ticker=ticker)
    
    
    
    
    
    return {"investment_recommendation": f"{investment_recommendation}"}
