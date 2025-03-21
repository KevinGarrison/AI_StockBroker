from dataclasses import dataclass
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import os
import yfinance as yf
from datetime import date

load_dotenv()

@dataclass
class API_Fetcher:
    def fetch_company_cik_ticker_title(self):
        
        headers = {'User-Agent': os.environ.get('USER_AGENT_SEC')}
        company_tickers = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=headers
        )
        company_data = pd.DataFrame(company_tickers.json()).T
        return company_data
    
    def fetch_stock_data_yf(self, ticker, period="10y", interval="1mo"):
        if not ticker:
            raise ValueError(f"Fund '{ticker}' not found.")
        
        yf_ticker = yf.Ticker(ticker)
        hist = yf_ticker.history(period=period, interval=interval)
        info = yf_ticker.info
        return {
            "ticker": ticker,
            "name": info.get("longName", ticker),
            "expense_ratio": info.get("expenseRatio"),
            "price_history": hist.get("Close"),
            "info":info
        }
    
    def fetch_filings_accessions(self, companies:dict):
        
        docs = {}
        headers = {'User-Agent': os.environ.get('USER_AGENT_SEC')}
        for company, cik in companies.items():
            filingMetaData = requests.get(
                f'https://data.sec.gov/submissions/CIK{cik}.json',
                headers=headers
            )
            filing_dict = filingMetaData.json()
            recent_filings = pd.DataFrame(filing_dict['filings']['recent'])
            cols = ['accessionNumber', 'reportDate', 'form', 'cik']
            
            important_forms = ['10-K', '10-Q', '8-K', 'S-1', 'S-3', 'DEF 14A', '20-F', '6-K', '4', '13D', '13G']
            
            docs[company] = {}
            for form_type in important_forms:
                filtered = recent_filings[recent_filings['core_type'] == form_type]
                if not filtered.empty:
                    filtered = filtered.copy()
                    filtered['cik'] = cik
                    filing = filtered[cols].reset_index(drop=True).head(1)
                    
                    docs[company][form_type] = filing
        return docs
    
    def fetch_company_data(self, tickers):
        
        company_data = {}

        for tick in tickers:
            try:
                ticker = yf.Ticker(tick)
                info = ticker.info
                earnings_calendar = ticker.calendar
                for key, value in list(earnings_calendar.items())[:3]:
                    if isinstance(value, list):
                        earnings_calendar[key] = [v.isoformat() for v in value]
                    elif isinstance(value, date):
                        earnings_calendar[key] = value.isoformat()
                    else:
                        earnings_calendar[key] = value
                dividends = ticker.dividends.tail(5)
                price_history = ticker.history(period="1y")["Close"]
                news = [
                    {
                        "title":article['content']['title'],
                        "summary": article['content']['summary']
                    }
                    for article in ticker.news[:3]
                ]

                company_data[tick] = {
                    "market_cap": info.get("marketCap"),
                    "trailing_pe": info.get("trailingPE"),
                    "earnings_calendar": earnings_calendar,
                    "recent_dividends": dividends,
                    "price_history": price_history,
                    "news": news,
                }
            except Exception as e:
                print(f"⚠️ Error loading {tick}: {e}")
        return company_data