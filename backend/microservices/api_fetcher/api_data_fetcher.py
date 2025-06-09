from dataclasses import dataclass
import httpx
import asyncio
import pandas as pd
from dotenv import load_dotenv
import os
from io import BytesIO
import yfinance as yf
from yahoo_fin import stock_info as si
import yahooquery as yq
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream
import json
import html
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
import logging
import warnings
import time
import numpy as np
from urllib.parse import urlparse
import requests


logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

load_dotenv()

@dataclass
class API_Fetcher:
    
    
    async def fetch_all_major_indices(self)->set[str]:
        dow = await asyncio.to_thread(si.tickers_dow)
        nasdaq = await asyncio.to_thread(si.tickers_nasdaq)
        sp500 = await asyncio.to_thread(si.tickers_sp500)
        all_tickers =  dow + nasdaq + sp500
        logger.info("[Tickers Y Finance] %s", all_tickers[:5])
        return all_tickers

        
    async def fetch_company_cik_ticker_title(self)->pd.DataFrame:
        try:
            headers = {'User-Agent': os.environ.get('USER_AGENT_SEC')}
            logger.info(f"[Header_SEC]: {headers}")
            async with httpx.AsyncClient() as client:
                company_tickers = await client.get(
                    "https://www.sec.gov/files/company_tickers.json",
                    headers=headers,
                    timeout = None
                )
                logger.info(f"SEC response status code: {company_tickers.status_code}")
                logger.info(f"Response headers: {company_tickers.headers}")
                
                if company_tickers.status_code != 200:
                    logger.warning(f"Unexpected status from SEC: {company_tickers.status_code}")
                    logger.debug(f"Response content: {company_tickers.text[:300]}")
                    
                company_tickers.raise_for_status()
                company_data = pd.DataFrame(company_tickers.json()).T
                return company_data
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while fetching SEC data: {e}")
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
        except Exception as e:
            logger.exception(f"Failed 'fetch_company_cik_ticker_title': {e}")    
    
    
    async def get_available_company_data(self)->tuple[list, pd.DataFrame]:
        all_tickers = await self.fetch_all_major_indices()
        company_ids = await self.fetch_company_cik_ticker_title()
        common = set(all_tickers) & set(company_ids["ticker"])
        subset_company_cik_ticker_title = company_ids[company_ids["ticker"].isin(common)]
        logger.info("[Union Ticker]: %s", subset_company_cik_ticker_title[:3])
        return subset_company_cik_ticker_title
    
    async def get_company_news(self, selected_ticker)->json:
        try:    
            if not selected_ticker:
                raise ValueError(f"Fund '{selected_ticker}' not found.")
            news = yf.Ticker(selected_ticker).get_news()
            return news        
        except Exception as e:
            print(f"Failed 'fetch_stock_data_yf': {e}")
    
    async def fetch_selected_stock_data_yf(self, selected_ticker:str=None, period:str="10y", interval:str="1mo") -> dict[str, any]:
        try:
            if not selected_ticker:
                raise ValueError(f"Fund '{selected_ticker}' not found.")

            def _fetch_data():    
                yf_ticker = yf.Ticker(selected_ticker)
                hist = yf_ticker.history(period=period, interval=interval)
                info = yf_ticker.info
                news = yf_ticker.get_news()

                return {
                    "ticker": selected_ticker,
                    "name": info.get("longName"),
                    "expense_ratio": info.get("expenseRatio"),
                    "price_history": hist.get('Close'),
                    
                    # Core Profile
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "website": info.get("website"),
                    "fullTimeEmployees": info.get("fullTimeEmployees"),

                    # Market Metrics
                    "current_price": info.get("currentPrice"),
                    "market_cap": info.get("marketCap"),
                    "volume": info.get("volume"),
                    "beta": info.get("beta"),

                    # Valuation
                    "trailing_pe": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "price_to_book": info.get("priceToBook"),
                    "peg_ratio": info.get("trailingPegRatio"),
                    "price_to_sales": info.get("priceToSalesTrailing12Months"),

                    # Earnings
                    "eps_trailing": info.get("epsTrailingTwelveMonths"),
                    "eps_forward": info.get("epsForward"),
                    "earnings_growth": info.get("earningsGrowth"),
                    "revenue_growth": info.get("revenueGrowth"),
                    "revenue": info.get("totalRevenue"),
                    "net_income": info.get("netIncomeToCommon"),

                    # Dividends
                    "dividend_yield": info.get("dividendYield"),
                    "dividend_rate": info.get("dividendRate"),
                    "payout_ratio": info.get("payoutRatio"),
                    "ex_dividend_date": info.get("exDividendDate"),

                    # Performance
                    "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                    "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                    "fifty_two_week_change_percent": info.get("fiftyTwoWeekChangePercent"),
                    "average_volume": info.get("averageVolume"),

                    # Analyst Sentiment
                    "recommendation_mean": info.get("recommendationMean"),
                    "recommendation_key": info.get("recommendationKey"),
                    "target_mean_price": info.get("targetMeanPrice"),
                    "target_high_price": info.get("targetHighPrice"),
                    "target_low_price": info.get("targetLowPrice"),

                    # Balance Sheet / Risk
                    "total_cash": info.get("totalCash"),
                    "total_debt": info.get("totalDebt"),
                    "current_ratio": info.get("currentRatio"),
                    "quick_ratio": info.get("quickRatio"),
                    "debt_to_equity": info.get("debtToEquity"),

                    # Margins & Returns
                    "gross_margins": info.get("grossMargins"),
                    "operating_margins": info.get("operatingMargins"),
                    "profit_margins": info.get("profitMargins"),
                    "return_on_assets": info.get("returnOnAssets"),
                    "return_on_equity": info.get("returnOnEquity"),

                    # News
                    "news": news
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
                    timeout = None
                )
                response.raise_for_status()
                filing_dict = response.json()

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


    def get_latest_filings_index(self, filings:dict=None)->dict:
        mapping_latest_forms_doc_index = {}
        important_forms = ['10-K', '10-Q', '8-K', 'S-1', 'S-3', 'DEF 14A', '20-F', '6-K', '4', '13D', '13G']
        for form in important_forms:
            for index, row in enumerate(filings['recent']['form']):
                if str(row) == form:
                    mapping_latest_forms_doc_index[form] = index
                    break
        return mapping_latest_forms_doc_index
    
    
    def create_base_df_for_sec_company_data(self,mapping_latest_docs:dict=None,
                                            filings:dict=None, cik:str=None)->pd.DataFrame:
        last_accession_numbers = []
        report_dates = []
        forms = []
        primary_docs = []
        idxs = []

        for form, index in mapping_latest_docs.items():
            last_accession_numbers.append(filings['recent']['accessionNumber'][index].replace('-', ''))
            report_dates.append(filings['recent']['reportDate'][index])
            forms.append(filings['recent']['form'][index])
            primary_docs.append(filings['recent']['primaryDocument'][index])
            idxs.append(index)

        base_sec_df = pd.DataFrame({
            'accession_number': last_accession_numbers,
            'report_date': report_dates,
            'form': forms,
            'docs': primary_docs,
            'cik': [cik] * len(forms),
            'index': str(idxs)
        })
        return base_sec_df
        
        
    async def _fetch_selected_company_filings(self, cik, accession, filename) -> bytes:
        try:
            USER_AGENT_SEC = os.getenv('USER_AGENT_SEC', 'default-agent')
            headers = {'User-Agent': USER_AGENT_SEC}
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{filename}"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=None)
                response.raise_for_status()
                return response.content

        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e}")
        except httpx.RequestError as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Unexpected error in 'fetch_company_filings': {e}")

        return b""
    
    async def fetch_all_filings(self, base_sec_df: pd.DataFrame=None) -> pd.Series:
        all_filings = []
        for _, row in base_sec_df.iterrows():
            filings_dict = await self._fetch_selected_company_filings(cik=str(int(row['cik'])), accession=row['accession_number'], filename=row['docs'])
            all_filings.append(filings_dict)
        if all_filings:
            print('Files successfully fetched from SEC.gov')

        return pd.Series(all_filings)
                

    def preclean_for_llm(self, text: str = None) -> str:
        if text is None:
            return ""

        soup = BeautifulSoup(text, "lxml")

        for tag in soup.find_all(["ix", "xbrli", "link", "xlink"]):
            tag.decompose()

        for tag in soup.find_all(["dei", "us-gaap"]):
            tag.unwrap() 

        cleaned_text = soup.get_text()

        cleaned_text = html.unescape(cleaned_text)

        cleaned_text = cleaned_text.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "")

        return cleaned_text.strip()


    async def preprocess_docs_content(self, series: pd.Series) -> pd.Series:
        series = series.copy()
        cleaned_series = pd.Series(index=series.index, dtype=object)

        async def process_row(index):
            raw_content = series.at[index]

            try:
                html_stream = DocumentStream(name=f'sec_{index}', stream=BytesIO(raw_content))
                converter = DocumentConverter()
                result = converter.convert(html_stream)
                cleaned_series.at[index] = result.document.export_to_markdown()
                print(f'[docling] Parsed row {index}')
                return
            except Exception as e:
                print(f'[docling] Failed at row {index}: {e}')
                return

        tasks = [process_row(index) for index in series.index]
        await asyncio.gather(*tasks)
        
        return cleaned_series


    async def preprocess_and_pull_context_sec_yf(self, ticker: str = None):
        start_time = time.time()
        all_data = {}

        try:
            # Step 1: Validate & find ticker
            task_1 = time.time()
            all_companies_df = await self.get_available_company_data()
            logger.info(f"[{ticker}] Step 1 - Fetched company data ({len(all_companies_df)} rows) - {time.time() - task_1:.2f}s")
            datapoint = all_companies_df[all_companies_df['ticker'] == ticker]

            if datapoint.empty:
                raise ValueError(f"Ticker '{ticker}' not found in company data.")

            row = datapoint.iloc[0]
            all_data['ticker'] = ticker
            all_data['cik'] = str(row["cik_str"]).zfill(10)
            all_data['company_title'] = row["title"]

            # Step 2: Yahoo Finance Data
            task_2 = time.time()
            yf_data = await self.fetch_selected_stock_data_yf(selected_ticker=ticker)
            yf_data.pop('price_history', None)
            all_data['yf_stock_data'] = yf_data
            logger.info(f"[{ticker}] Step 2 - Fetched Yahoo Finance data - {time.time() - task_2:.2f}s")

            # Step 3: SEC Data
            task_3 = time.time()
            details_1, details_2, filing_accessions = await self.fetch_selected_company_details_and_filing_accessions(
                selected_cik=all_data['cik']
            )
            logger.info(f"[{ticker}] Step 3 - Fetched SEC filings - {time.time() - task_3:.2f}s")
            all_data['sec_details_1'] = details_1
            all_data['sec_details_2'] = details_2
            all_data['filing_accessions'] = filing_accessions

            # Step 4: Map latest documents
            task_4 = time.time()
            all_data['mapping_latest_docs'] = self.get_latest_filings_index(filings=all_data['filing_accessions'])
            logger.info(f"[{ticker}] Step 4 - Get SEC documents index - {time.time() - task_4:.2f}s")

            all_data['base_sec_df'] = self.create_base_df_for_sec_company_data(
                mapping_latest_docs=all_data['mapping_latest_docs'],
                filings=all_data['filing_accessions'],
                cik=all_data['cik']
            )

            # Step 5: Fetch filings
            task_5 = time.time()
            docs_content_series = await self.fetch_all_filings(base_sec_df=all_data['base_sec_df'])
            logger.info(f"[{ticker}] Step 5 - Fetch SEC documents - {time.time() - task_5:.2f}s")

            # Step 6: Preprocess documents
            task_6 = time.time()
            docs_content_series_1 = await self.preprocess_docs_content(series=docs_content_series)
            logger.info(f"[{ticker}] Step 6 - Preprocess SEC documents - {time.time() - task_6:.2f}s")

            all_data['base_sec_df']['raw_content'] = docs_content_series
            all_data['base_sec_df']['content'] = docs_content_series_1
            all_data['base_sec_df'] = all_data['base_sec_df'].replace({np.nan: None, np.inf: None, -np.inf: None})

            final_dict = {}

            final_dict['yf_stock_data'] = all_data["yf_stock_data"]
            final_dict['base_sec_df'] = all_data["base_sec_df"]

            return final_dict

        except Exception as e:
            logger.error(f"[{ticker}] ERROR in preprocess_and_pull_context_sec_yf: {e}", exc_info=True)
            raise

    
    def is_relevant_screener(self, scr):
        EXCLUDE_KEYWORDS = [
            "etf", "fund", "mutual", "bond", "commodity", "crypto",
            "currency", "option", "futures", "yield", "day_losers",
            "day_losers_br", "day_losers_de", "day_losers_dji", "day_losers_es",
            "day_losers_fr","day_losers_gb", "day_losers_hk", "day_losers_it",
            "day_losers_ndx", "day_losers_nz", "day_losers_sg"
        ]
        REGION_KEYWORDS = [
            "europe", "asia", "latam", "china", "japan", "brazil", "africa", "au", "in", "ca"
        ]
        if isinstance(scr, dict):
            fields = [
                scr.get('id', ''), scr.get('title', ''),
                scr.get('description', ''), scr.get('canonicalName', '')
            ]
            for f in fields:
                if any(k in f.lower() for k in EXCLUDE_KEYWORDS + REGION_KEYWORDS):
                    return False
            qtype = scr.get('criteriaMeta', {}).get('quoteType', '').lower()
            if qtype != "equity":
                return False
            for crit in scr.get('criteriaMeta', {}).get('criteria', []):
                if crit['field'] == 'exchange':
                    values = crit.get('dependentValues', [])
                    if not any(x in values for x in ['NMS', 'NYQ']):
                        return False
            return True
        else:
            return not any(k in scr.lower() for k in EXCLUDE_KEYWORDS + REGION_KEYWORDS)

    async def get_available_dropdown_values_async(self):
        def fetch_screeners():
            s = yq.Screener()
            try:
                screeners = s.available_screeners
            except Exception as e:
                print(f"Error fetching available_screeners: {e}")
                return []
            if hasattr(screeners, "get"):
                return screeners.get("data", [])
            else:
                return screeners

        screener_list = await asyncio.to_thread(fetch_screeners)

        filtered_screeners = []
        if screener_list and isinstance(screener_list[0], dict):
            for scr in screener_list:
                if self.is_relevant_screener(scr):
                    filtered_screeners.append(scr.get('title', scr.get('id')))
        else:
            for scr in screener_list:
                if self.is_relevant_screener(scr):
                    filtered_screeners.append(scr)
        return filtered_screeners
    
    def get_tickers_for_screener_sync(self, screener_id_or_title):
        s = yq.Screener()
        try:
            results = s.get_screeners([screener_id_or_title])
        except Exception as e:
            print(f"Error fetching screener '{screener_id_or_title}': {e}")
            return []
        tickers = []
        try:
            key = next(iter(results))
            data = results[key]
            for item in data['quotes']:
                if 'symbol' in item:
                    tickers.append(item['symbol'])
        except Exception as e:
            print(f"Error parsing tickers: {e}")
        return tickers

    async def get_tickers_for_screener_async(self, screener_id_or_title):
        return await asyncio.to_thread(self.get_tickers_for_screener_sync, screener_id_or_title)

 
    
    async def filter_tickers_by_market_cap_async(
            self, tickers, min_market_cap=1e9
    ):
        if not tickers:
            return []
        filtered = []
        for i in range(0, len(tickers), 50):
            batch = tickers[i:i+50]
            def fetch_summary_detail():
                q = yq.Ticker(batch)
                return q.summary_detail
            data = await asyncio.to_thread(fetch_summary_detail)
            for symbol in batch:
                cap = None
                try:
                    cap = data[symbol]['marketCap']
                except Exception:
                    continue
                if cap is None:
                    continue
                if cap >= min_market_cap:
                    filtered.append(symbol)
        return filtered


    def fetch_logo(self, ticker_symbol: str, save_path: str = "logo.png"):
        ticker = yf.Ticker(ticker_symbol)
        website = ticker.info.get("website")
        if not website:
            return None

        domain = urlparse(website).netloc
        logo_url = f"https://logo.clearbit.com/{domain}"


        response = requests.get(logo_url, timeout=20)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            return save_path
        return None


