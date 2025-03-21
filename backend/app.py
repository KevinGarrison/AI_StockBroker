import streamlit as st
from utils.api_data_fetcher import API_Fetcher
from utils.rag_chatbot import RAG_Chatbot
import plotly.graph_objects as go
from yahoo_fin import stock_info as si
import numpy as np
from dotenv import load_dotenv


load_dotenv()

fetcher = API_Fetcher()
rag_chatbot = RAG_Chatbot()
docs = None
company_data={}

# Retrieve tickers for major indices
dow_tickers = si.tickers_dow()
nasdaq_tickers = si.tickers_nasdaq()
sp500_tickers = si.tickers_sp500()

all_tickers = set(dow_tickers + nasdaq_tickers + sp500_tickers)
        
st.title('Dev Chatbot')

company_ticker = fetcher.fetch_company_cik_ticker_title()

common = set(all_tickers) & set(company_ticker["ticker"])

# Step 2: Filter both
tickers = [t for t in all_tickers if t in common]
company_ticker = company_ticker[company_ticker["ticker"].isin(common)]

# st.write(len(tickers))
# st.write(len(company_ticker))

# st.write(company_ticker)

selected_companies = st.multiselect('Choose your prefered stocks:', company_ticker['title'])

selected_id_title = {}
tickers = []

if selected_companies:
    for company in selected_companies:
        selected_id_title[company] = company_ticker.\
        loc[company_ticker['title'] == company, 'cik_str'].\
        astype(str).values[0].zfill(10)
        tickers.append(company_ticker.\
        loc[company_ticker['title'] == company, 'ticker'].\
        astype(str).values[0])


# st.write(tickers)
docs = fetcher.fetch_filings_accessions(selected_id_title)
company_data = fetcher.fetch_company_data(tickers)

# st.write(tickers)
# st.write(selected_id_title)

# if docs:
    # st.write(docs)


# for tick in tickers:
#     ticker = yf.Ticker(tick)

#     # Market cap and PE ratio
#     st.subheader(f"📊 {tick} Fundamentals")
#     st.write("**Market Cap:**", ticker.info.get("marketCap"))
#     st.write("**Trailing PE:**", ticker.info.get("trailingPE"))

#     # Earnings calendar
#     st.subheader("📅 Upcoming Earnings")
#     st.write(ticker.calendar)

#     # Dividends
#     st.subheader("💸 Recent Dividends")
#     st.write(ticker.dividends.tail(5))

#     # Price history
#     st.subheader("📈 Price History (1 Month)")
#     st.line_chart(ticker.history(period="1mo")["Close"])

#     # News
#     st.subheader("📰 Latest News")
#     for article in ticker.news[:3]:
#         st.write(f"**{article['content']['title']}**")
#         st.write(article['content']['summary'])


        
    # st.write(company_data)
    
if st.button('OpenAI4o-mini'):
    for ticker, data in company_data.items():
        ts = fetcher.fetch_stock_data_yf(ticker, '1y')
        st.header(ts['name'] + f' ({ticker}):')
        st.line_chart(data.get('price_history').dropna())
        #st.write(info)
        st.write(ts.get('info').get("longBusinessSummary"))
        st.write()
        st.write('Open:', ts.get('info').get('open'))
        st.write('Low:', ts.get('info').get('dayLow'))
        st.write('High:', ts.get('info').get('dayHigh'))
        st.write('Volume:', ts.get('info').get('volume'))
        st.write(ts['price_history'])
        with st.spinner('AI Assitant analyzes data!'):
            answer = rag_chatbot.gpt4o_mini(company_facts=ticker,context_y_finance=data, context_sec=None)
            st.write(answer)
if st.button('DeepseekR1'):
    for (company, data), ticker in zip(company_data.items(), tickers):
        ts = fetcher.fetch_stock_data_yf(ticker, '1y')
        st.header(ts['name'] + f' ({ticker}):')
        st.line_chart(data.get('price_history').dropna())
        #st.write(info)
        st.write(ts.get('info').get("longBusinessSummary"))
        st.write()
        st.write('Open:', ts.get('info').get('open'))
        st.write('Low:', ts.get('info').get('dayLow'))
        st.write('High:', ts.get('info').get('dayHigh'))
        st.write('Volume:', ts.get('info').get('volume'))
        st.write(ts['price_history'])
        with st.spinner('AI Assitant analyzes data!'):
            answer = rag_chatbot.deepseek_r1(company_facts=ticker, context_y_finance=data, context_sec=None)
            st.write(answer)
    
    