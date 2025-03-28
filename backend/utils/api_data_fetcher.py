from dataclasses import dataclass
import httpx
import asyncio
import pandas as pd
from dotenv import load_dotenv
import os
import yfinance as yf
from yahoo_fin import stock_info as si

load_dotenv()

@dataclass
class API_Fetcher:
    
    
    async def fetch_all_major_indices(self):
        dow = await asyncio.to_thread(si.tickers_dow)
        nasdaq = await asyncio.to_thread(si.tickers_nasdaq)
        sp500 = await asyncio.to_thread(si.tickers_sp500)
        all_tickers =  set(dow + nasdaq + sp500)
        return all_tickers
    
        
    async def fetch_company_cik_ticker_title(self)->pd.DataFrame:
        try:
            headers = {'User-Agent': os.environ.get('USER_AGENT_SEC')}
            
            async with httpx.AsyncClient() as client:
                company_tickers = await client.get(
                    "https://www.sec.gov/files/company_tickers.json",
                    headers=headers
                )
                company_tickers.raise_for_status()
                company_data = pd.DataFrame(company_tickers.json()).T
                return company_data
        except httpx.HTTPStatusError as e:
            print(f"HTTP error while fetching SEC data: {e}")
        except httpx.RequestError as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Failed 'fetch_company_cik_ticker_title': {e}")    
    
    async def get_available_company_data(self, selected_ticker:str=None):
        # Get all Major Tickers and Fetch a Dataframe containing all CIK ID's, Ticker, Company Titles 
        # available on sec.gov and the get union of yFinance and SEC Data
        all_tickers = await self.fetch_all_major_indices()
        company_ids = await self.fetch_company_cik_ticker_title()
        common = set(all_tickers) & set(company_ids["ticker"])
        subset_tickers = [t for t in all_tickers if t in common]
        subset_company_cik_ticker_title = company_ids[company_ids["ticker"].isin(common)]
        return subset_tickers, subset_company_cik_ticker_title


    async def fetch_selected_stock_data_yf(self, selected_ticker:str=None, period:str="10y", interval:str="1mo") -> dict[str, any]:
        try:
            if not ticker:
                raise ValueError(f"Fund '{selected_ticker}' not found.")

            def _fetch_data():
                yf_ticker = yf.Ticker(selected_ticker)
                hist = yf_ticker.history(period=period, interval=interval)
                info = yf_ticker.info
                return {
                    "ticker": selected_ticker,
                    "name": info.get("longName", selected_ticker),
                    "expense_ratio": info.get("expenseRatio"),
                    "price_history": hist.get("Close"),
                    "info": info
                }

            return await asyncio.to_thread(_fetch_data)

        except Exception as e:
            print(f"Failed 'fetch_stock_data_yf': {e}")


    async def fetch_selected_company_details_and_filing_accessions(self, selected_cik)->tuple[dict[str, any], dict[str, any], dict[str, any]]:
        try:
            USER_AGENT_SEC = os.getenv('USER_AGENT_SEC', 'default-agent')
            headers = {'User-Agent': USER_AGENT_SEC}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'https://data.sec.gov/submissions/CIK{selected_cik}.json',
                    headers=headers,
                    timeout=15.0  # optional timeout
                )
                response.raise_for_status()
                filing_dict = await response.json()

            if filing_dict:
                important_keys = [
                    "name", "tickers", "exchanges", "sicDescription",
                    "description", "website", "fiscalYearEnd"
                ]

                secondary_keys = [
                    "stateOfIncorporation", "stateOfIncorporationDescription",
                    "insiderTransactionForOwnerExists", "insiderTransactionForIssuerExists",
                    "category", "addresses"
                ]

                first_meta_data_dict = {k: (v if v else "N/A") for k, v in filing_dict.items() if k in important_keys}
                secondary_meta_data_dict = {k: (v if v else "N/A") for k, v in filing_dict.items() if k in secondary_keys}
                filings = filing_dict.get('filings', {})

                return first_meta_data_dict, secondary_meta_data_dict, filings

        except Exception as e:
            print(f"Failed 'fetch_company_details_and_filing_accessions': {e}")
            return {}, {}, {}



    async def fetch_selected_company_filings(self, cik, accession, filename) -> bytes:
        try:
            USER_AGENT_SEC = os.getenv('USER_AGENT_SEC', 'default-agent')
            headers = {'User-Agent': USER_AGENT_SEC}
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{filename}"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=20.0)
                response.raise_for_status()
                return response.content

        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e}")
        except httpx.RequestError as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Unexpected error in 'fetch_company_filings': {e}")

        return b""
    
    