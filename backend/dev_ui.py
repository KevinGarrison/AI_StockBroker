import streamlit as st
from utils.api_data_fetcher import API_Fetcher
from utils.rag_chatbot import RAG_Chatbot
from dotenv import load_dotenv
import pandas as pd
from io import BytesIO
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
import os


load_dotenv()

fetcher = API_Fetcher()
rag_chatbot = RAG_Chatbot()
    

st.title('Dev Chatbot')

result = None
    
# Vars
docs = None
query=None
ids_row = []
company_data={}
selected_id_title = {}
filing_dfs_for_each_company = {}
company_details_and_filing_acc = {}
mapping_latest_forms_doc_index = {}
important_forms = ['10-K', '10-Q', '8-K', 'S-1', 'S-3', 'DEF 14A', '20-F', '6-K', '4', '13D', '13G']


ticker, company_ids = fetcher.get_base_data()


# Selectbox
selected_companies = st.multiselect('Choose your prefered stocks:', company_ticker['title'])


for selected in selected_companies:
    ids_row.append(company_ids[company_ids['title'] == selected])
    
if ids_row:
    filtered_comp_ids = pd.concat(ids_row, ignore_index=True)   

# Create a Mapping Dictionary of CIK and Company Title 
if selected_companies:
    for row in company_ticker[company_ticker['title'].isin(selected_companies)][['title', 'ticker']].itertuples(index=False):
        company = row.title
        ticker = row.ticker
        company_data[company] = fetcher.fetch_stock_data_yf(ticker=ticker)
    for company in selected_companies:
        inner_list = selected_id_title[company] = []
        inner_list.append(company_ticker.\
        loc[company_ticker['title'] == company, 'cik_str'].\
        astype(str).values[0].zfill(10))
        inner_list.append(company_ticker.\
        loc[company_ticker['title'] == company, 'ticker'].\
        astype(str).values[0])

# Fetch 3 Types of data of SEC with CIK ID
# 1. Type of Company, Name, Ticker, Exchange, Fiscal year
# 2. Insider transactions, Company Category e.g. Large Accelerated Filter, Adresses
# 3. Filings
# Stored in a Dictionary with Key (Company Name) Value (List[first,second,filings])
for company, id_list in selected_id_title.items():
    first, second, filings = fetcher.fetch_company_details_and_filing_accessions(id_list[0])
    company_details_and_filing_acc[company] = [first, second, filings]


# Create a Dictionary with Key (Company Name) and 
# Value Dictionary Key (all available Forms of filings) Value (index where its stored)
for company, first_second_filings in company_details_and_filing_acc.items():
    mapping_latest_forms_doc_index[company] = {}
    for form in important_forms:
        for index, row in enumerate(first_second_filings[2]['recent']['form']):
            if str(row) == form:
                mapping_latest_forms_doc_index[company][form] = index
                break

# Create the DataFrame with accession number of filings 
for company, ids in selected_id_title.items():
    cik = ids[0]
    last_accession_numbers = []
    report_dates = []
    forms = []
    primary_docs = []
    idxs = []

    for form, index in mapping_latest_forms_doc_index[company].items():
        last_accession_numbers.append(company_details_and_filing_acc[company][2]['recent']['accessionNumber'][index].replace('-', ''))
        report_dates.append(company_details_and_filing_acc[company][2]['recent']['reportDate'][index])
        forms.append(company_details_and_filing_acc[company][2]['recent']['form'][index])
        primary_docs.append(company_details_and_filing_acc[company][2]['recent']['primaryDocument'][index])
        idxs.append(index)

    df = pd.DataFrame({
        'accession_number': last_accession_numbers,
        'report_date': report_dates,
        'form': forms,
        'docs': primary_docs,
        'cik': [cik] * len(forms),
        'index': idxs
    })

    
    filing_dfs_for_each_company[company] = df.copy()
        
    count = 0
    # Fetch the identified filings from SEC.gov and store the results in a DataFrame for further processing
    with st.spinner('Documents from SEC.gov (U.S. Securities and Exchange Commission) are getting  pulled and prepared...'):
        for company, df in filing_dfs_for_each_company.items():
            all_filings = []
            for _, row in df.iterrows():
                filings_dict = fetcher.fetch_company_filings(cik=row['cik'], accession=row['accession_number'], filename=row['docs'])
                all_filings.append(filings_dict)
            if all_filings:
                st.success('Filings fetched!')
            for index, content in enumerate(all_filings):
                df.loc[index, 'content'] = content
            for index, row in df.iterrows():
                try:
                    html_stream = DocumentStream(name=f'sec_{index}', stream=BytesIO(df.at[index, 'content']))
                    converter = DocumentConverter()
                    result = converter.convert(html_stream)
                    df.loc[index, 'cleaned_docling_md'] = result.document.export_to_markdown()
                except Exception:
                    st.warning('Parsing Failed!')
                    count +=1
            st.write(count, '/', len(df), ' Docs Failed')
            count = 0  
            for index, row in df.iterrows():
                content = row['cleaned_docling_md']
                word_count = len(str(content).split()) if isinstance(content, str) else 0
                df.loc[index, 'token_count_docling_cleaned_md'] = int(int(word_count) * 0.3)
            df['Company'] = company
            for index, row in df.iterrows():
                if row.get('cleaned_docling_md'):
                    rag_chatbot.process_text_to_qdrant(
                        context_docs=str(row['cleaned_docling_md']),
                        metadata={'Company': company,
                                'Accession Number': row['accession_number'],
                                'CIK': row['cik'],
                                'Report Date':row['report_date'],
                                'Form': row['form'],
                                'Document': row['docs']}
                        )

# Load environment variables
host = os.getenv('QDRANT_HOST')
port = os.getenv('QDRANT_PORT')
collection_name = os.getenv('COLLECTION_NAME')
embedding_model = os.getenv('EMBEDDING_MODEL_OPENAI')

# Build the Qdrant client URL
url = f"http://{host}:{port}"

# Create Qdrant client
client = QdrantClient(host=host, port=int(port))  # Ensure port is int

# Chat input
query = st.chat_input('Write a query to search in the SEC docs!')

#query = 'what is the biggest risc according to the sec filings in 2024?'

if query:
    embeddings = OpenAIEmbeddings(model=embedding_model)
    
    vector_store = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=collection_name,
        url=url,
    )
    
    result = vector_store.similarity_search(query=query, k=5)
    rag_chatbot.print_results(result)
    
    combined_docs = []

    for item in result:
        doc = item[0] if isinstance(item, tuple) else item
        content = doc.page_content
        metadata = doc.metadata

        # Turn metadata into a readable string
        metadata_str = "\n".join(f"{key}: {value}" for key, value in metadata.items())

        # Combine both
        combined = f"Metadata SEC Files: {metadata_str}\n\nContent SEC:{content}"
        combined_docs.append(combined)


# if st.button('OpenAI4o-mini'):
for ticker, data in company_data.items():
    ts = data
    st.header(ts['name'] + f' ({ticker}):')
    st.line_chart(ts.get('price_history').dropna())
    #st.write(info)
    st.write(ts.get('info').get("longBusinessSummary"))
    st.write()
    st.write('Open:', ts.get('info').get('open'))
    st.write('Low:', ts.get('info').get('dayLow'))
    st.write('High:', ts.get('info').get('dayHigh'))
    st.write('Volume:', ts.get('info').get('volume'))
    st.write(ts['price_history'])
    with st.spinner('AI Assitant analyzes data!'):
        answer = rag_chatbot.gpt4o_mini(company_facts=ticker,context_y_finance=data, context_sec=combined_docs[0])
        st.write(answer)
if st.button('DeepseekR1'):
    for (company, data), ticker in zip(company_data.items(), tickers):
        ts = data
        st.header(ts['name'] + f' ({ticker}):')
        st.line_chart(ts.get('price_history').dropna())
        #st.write(info)
        st.write(ts.get('info').get("longBusinessSummary"))
        st.write()
        st.write('Open:', ts.get('info').get('open'))
        st.write('Low:', ts.get('info').get('dayLow'))
        st.write('High:', ts.get('info').get('dayHigh'))
        st.write('Volume:', ts.get('info').get('volume'))
        st.write(ts['price_history'])
        with st.spinner('AI Assitant analyzes data!'):
            answer = rag_chatbot.deepseek_r1(company_facts=ticker, context_y_finance=data, context_sec=combined_docs[0])
            st.write(answer)
    
    