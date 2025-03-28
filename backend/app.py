from utils.rag_chatbot import RAG_Chatbot
from utils.api_data_fetcher import API_Fetcher
from contextlib import asynccontextmanager
from fastapi import HTTPException
from fastapi import FastAPI
import json

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
    available_companies = await fetcher.get_available_company_data()
    return available_companies.to_json(orient="records")

@app.get("/history-timeseries-stock/{ticker}")
async def stock_history_of_selected_ticker(ticker:str=None):
    data = await fetcher.fetch_selected_stock_data_yf(selected_ticker=ticker)
    history_timeseries = {str(key): value for key, value in data['price_history'].items()}
    return json.dumps(history_timeseries)
    
@app.get("/stock-broker-analysis/{ticker}")
async def pull_and_analyze(ticker: str = None):
    all_data = {}

    # Step 1: Validate & find ticker
    all_companies_df = await fetcher.get_available_company_data()
    datapoint = all_companies_df[all_companies_df['ticker'] == ticker]

    if datapoint.empty:
        raise HTTPException(status_code=404, detail=f"No company found for ticker '{ticker}'")

    row = datapoint.iloc[0]
    all_data['cik'] = str(row["cik_str"]).zfill(10)
    all_data['company_title'] = row["title"]

    # Step 2: Yahoo Finance Data
    all_data['yf_stock_data'] = await fetcher.fetch_selected_stock_data_yf(selected_ticker=ticker)
    all_data['yf_stock_data']#.pop('price_history', None)  # Safe pop just in case it's missing

    # Step 3: SEC Data
    details_1, details_2, filing_accessions = await fetcher.fetch_selected_company_details_and_filing_accessions(
        selected_cik=all_data['cik']
    )
    all_data['sec_details_1'] = details_1
    all_data['sec_details_2'] = details_2
    all_data['filing_accessions'] = filing_accessions
    all_data['mapping_latest_docs'] = fetcher.get_latest_filings_index(filings=all_data['filing_accessions'])
    all_data['base_sec_df'] = fetcher.create_base_df_for_sec_company_data(mapping_latest_docs=all_data['mapping_latest_docs'],
                                                                        filings=all_data['filing_accessions'],
                                                                        cik=all_data['cik'])
    
    return all_data['base_sec_df']
