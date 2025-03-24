from dataclasses import dataclass
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import os
import yfinance as yf
from yahoo_fin import stock_info as si
from datetime import date
import json

load_dotenv()

@dataclass
class API_Fetcher:
    
    def fetch_all_major_indices(self):
        # Retrieve tickers for major indices
        dow_tickers = si.tickers_dow()
        nasdaq_tickers = si.tickers_nasdaq()
        sp500_tickers = si.tickers_sp500()
        all_tickers = set(dow_tickers + nasdaq_tickers + sp500_tickers)
        return all_tickers
    
    
    def fetch_company_cik_ticker_title(self)->pd.DataFrame:
        try:
            headers = {'User-Agent': os.environ.get('USER_AGENT_SEC')}
            company_tickers = requests.get(
                "https://www.sec.gov/files/company_tickers.json",
                headers=headers
            )
            company_data = pd.DataFrame(company_tickers.json()).T
            return company_data
        except Exception as e:
            print(f"Failed 'fetch_company_cik_ticker_title': {e}")    
    
    def fetch_stock_data_yf(self, ticker, period="10y", interval="1mo")->dict[str, any]:
        try:
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
        except Exception as e:
            print(f"Failed 'fetch_stock_data_yf': {e}")    
    
    def fetch_company_details_and_filing_accessions(self, cik)->tuple[dict[str, any], dict[str, any], dict[str, any]]:
        try:
            USER_AGENT_SEC = os.getenv('USER_AGENT_SEC')
            headers = {'User-Agent': USER_AGENT_SEC}
            filingMetaData = requests.get(
                f'https://data.sec.gov/submissions/CIK{cik}.json',
                headers=headers
            )
            filing_dict = filingMetaData.json()

            important_keys = [
                "name", "tickers", "exchanges", "sicDescription",
                "description", "website", "fiscalYearEnd"
            ]

            secondary_keys = [
                "stateOfIncorporation", "stateOfIncorporationDescription",
                "insiderTransactionForOwnerExists", "insiderTransactionForIssuerExists",
                "category", "addresses"
            ]
            

            # Filter dictionaries
            first_meta_data_dict = {k: (v if v else "N/A") for k, v in filing_dict.items() if k in important_keys}
            secondary_meta_data_dict = {k: (v if v else "N/A") for k, v in filing_dict.items() if k in secondary_keys}
            filings = filing_dict['filings']
            
            return first_meta_data_dict, secondary_meta_data_dict, filings
        except Exception as e:
                print(f"Failed 'fetch_company_details_and_filings_accesions': {e}")    
    
    def fetch_company_filings(self, cik, accession, filename)->bytes:
        try:
            USER_AGENT_SEC = os.getenv('USER_AGENT_SEC')
            headers = {'User-Agent': USER_AGENT_SEC}
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{filename}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.content
            return data
        except Exception as e:
            print(f"Failed 'fetch_company_filings': {e}")    
    
    
    # def fetch_company_data(self, tickers)->dict[str, any]:
        
    #     company_data = {}

    #     for tick in tickers:
    #         try:
    #             ticker = yf.Ticker(tick)
    #             info = ticker.info
    #             earnings_calendar = ticker.calendar
    #             for key, value in list(earnings_calendar.items())[:3]:
    #                 if isinstance(value, list):
    #                     earnings_calendar[key] = [v.isoformat() for v in value]
    #                 elif isinstance(value, date):
    #                     earnings_calendar[key] = value.isoformat()
    #                 else:
    #                     earnings_calendar[key] = value
    #             dividends = ticker.dividends.tail(5)
    #             price_history = ticker.history(period="1y")["Close"]
    #             news = [
    #                 {
    #                     "title":article['content']['title'],
    #                     "summary": article['content']['summary']
    #                 }
    #                 for article in ticker.news[:3]
    #             ]

    #             company_data[tick] = {
    #                 "market_cap": info.get("marketCap"),
    #                 "trailing_pe": info.get("trailingPE"),
    #                 "earnings_calendar": earnings_calendar,
    #                 "recent_dividends": dividends,
    #                 "price_history": price_history,
    #                 "news": news,
    #             }
    #         except Exception as e:
    #             print(f"⚠️ Error loading {tick}: {e}")
    #     return company_data