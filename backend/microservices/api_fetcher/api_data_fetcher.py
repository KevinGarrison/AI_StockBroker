from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream
from dataclasses import dataclass, field
from bs4 import XMLParsedAsHTMLWarning
from urllib.parse import urlparse
from yahooquery import Screener
from typing import List, Tuple
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import yahooquery as yq
from io import BytesIO
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import warnings
import logging
import asyncio
import httpx
import json
import html
import time
import re
import os


logger = logging.getLogger(__name__)


warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


load_dotenv()


@dataclass
class API_Fetcher:
    max_concurrent: int = 10
    retry_attempts: int = 3
    retry_delay: float = 1.5
    _semaphore: asyncio.Semaphore = field(init=False)


    def __post_init__(self):
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
    

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
    
    
    def filter_stocks_screeners_sectors(self, categories: List[str]) -> List[str]:
        exclude_keywords = (
            "crypto",
            "etf",
            "mutual_fund",
            "funds",
            "options",
            "cryptocurrencies",
            "loser",
            "bond",
            "commodity",
            "forex",
            "precious",
            "metals",
            "coal",
            "uranium",
            "gold",
            "silver",
            "oil",
            "gas",
        )

        include_patterns = re.compile(
            r"""^(
            .*stocks.*|
            .*gainers.*|
            .*losers.*|
            .*actives.*|
            .*upgraded.*|
            .*undervalued.*|
            .*breakout.*|
            most_.*|
            top_.*|
            day_.*|
            analyst_.*
        )$""",
            re.IGNORECASE | re.VERBOSE,
        )

        return [
            cat for cat in categories
            if include_patterns.match(cat) and not any(ex in cat for ex in exclude_keywords)
        ]


    async def get_available_company_data(self) -> Tuple[pd.DataFrame, List]:
        screener_dict = Screener().available_screeners
        screener_ids = [
            s for s in self.filter_stocks_screeners_sectors(screener_dict)
            if isinstance(s, str) and s
        ]

        logger.info(f"[CompanyData] Found {len(screener_ids)} screener IDs from YahooQuery")

        try:
            tickers, screeners, ticker_screener = await self.get_tickers_from_screeners_async(screener_ids)
        except Exception as e:
            logger.error(f"[CompanyData] Error fetching tickers from screeners: {e}")
            return pd.DataFrame(), []

        company_ids = await self.fetch_company_cik_ticker_title()
        if company_ids.empty:
            logger.warning("[CompanyData] Company ID dataset is empty.")
            return pd.DataFrame(), []
        
        valid_tickers = company_ids["ticker"].to_list()
        common = set(valid_tickers) & set(tickers)
        subset = company_ids[company_ids["ticker"].isin(common)].copy()

        return subset, screeners, ticker_screener


    async def get_company_news(self, selected_ticker)->json:
        try:    
            if not selected_ticker:
                raise ValueError(f"Fund '{selected_ticker}' not found.")
            news = yf.Ticker(selected_ticker).get_news()
            return news        
        except Exception as e:
            print(f"Failed 'fetch_stock_data_yf': {e}")

    
    async def fetch_selected_stock_history_yq(
        self,
        selected_ticker: str,
        period: str = "10y",
        interval: str = "1mo"
    ) -> dict[str, any]:
        if not selected_ticker:
            raise ValueError("Ticker symbol must be provided.")
        
        def _worker() -> dict[str, any]:
            t = yq.Ticker(selected_ticker)
            hist_df = t.history(period=period, interval=interval)

            price_series = None
            if isinstance(hist_df, pd.DataFrame) and not hist_df.empty and "close" in hist_df.columns:
                try:
                    price_series = hist_df.loc[selected_ticker, "close"]
                except KeyError:
                    price_series = hist_df["close"]

            return {"price_history": price_series}

        try:
            return await asyncio.to_thread(_worker)
        except Exception as exc:
            logger.error("fetch_selected_stock_history_yq failed: %s", exc, exc_info=True)
            return {"error": str(exc)}


    async def fetch_selected_stock_facts_yq(self, selected_ticker: str) -> dict[str, any]:
        symbol = selected_ticker
        if not symbol:
            raise ValueError("Ticker symbol must be provided.")
        
        def _worker() -> dict[str, any]:
            t = yq.Ticker(symbol)

            # -- blocks come back as {symbol: {...}}
            prof = (t.summary_profile or {}).get(symbol, {})
            det  = (t.summary_detail  or {}).get(symbol, {})
            fin  = (t.financial_data  or {}).get(symbol, {})
            ks   = (t.key_stats       or {}).get(symbol, {})

            news_block = yf.Ticker(symbol).get_news()

            return {
                # --- identification ---
                "ticker":           symbol,
                "company_name":     prof.get("longBusinessSummary"),  
                "sector":           prof.get("sector"),
                "industry":         prof.get("industry"),
                "website":          prof.get("website"),
                "employees":        prof.get("fullTimeEmployees"),

                # --- market metrics ---
                "current_price":    fin.get("currentPrice"),
                "market_cap":       det.get("marketCap"),
                "beta":             ks.get("beta"),
                "volume":           det.get("volume"),

                # --- valuation ---
                "trailing_pe":      det.get("trailingPE"),
                "forward_pe":       ks.get("forwardPE"),
                "price_to_book":    ks.get("priceToBook"),

                # --- dividends ---
                "dividend_yield":   det.get("dividendYield"),
                "dividend_rate":    det.get("dividendRate"),
                "ex_dividend":      det.get("exDividendDate"),

                # --- performance ---
                "52w_high":         det.get("fiftyTwoWeekHigh"),
                "52w_low":          det.get("fiftyTwoWeekLow"),
                "52w_change_pct":   ks.get("52WeekChange"),

                # --- analyst targets ---
                "target_mean":      fin.get("targetMeanPrice"),
                "target_high":      fin.get("targetHighPrice"),
                "target_low":       fin.get("targetLowPrice"),
                "recommendation_mean": fin.get("recommendationMean"),

                # --- cash & leverage ---
                "total_cash":       fin.get("totalCash"),
                "total_debt":       fin.get("totalDebt"),
                "debt_to_equity":   fin.get("debtToEquity"),
                "current_ratio":    fin.get("currentRatio"),
                "quick_ratio":      fin.get("quickRatio"),

                # --- margins & returns ---
                "gross_margins":    fin.get("grossMargins"),
                "operating_margins":fin.get("operatingMargins"),
                "profit_margins":   fin.get("profitMargins"),
                "roa":              fin.get("returnOnAssets"),
                "roe":              fin.get("returnOnEquity"),
                "eps_forward":      ks.get("forwardEps") or fin.get("forwardEps"),
                "revenue_growth":   fin.get("revenueGrowth"),

                # --- news ---
                "news":             news_block,    
            }

        # run the heavy work in a thread so the coroutine stays non-blocking
        try:
            return await asyncio.to_thread(_worker)
        except Exception as exc:
            logger.error("get_yq failed: %s", exc, exc_info=True)
            return {"error": str(exc)}


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
        all_data = {}

        try:
            # Step 1: Validate & find ticker
            task_1 = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.get("http://api-gateway:8000/companies-df", timeout=None)
                all_companies = response.json()
                all_companies_df = pd.DataFrame(all_companies)
            logger.info(f"[{ticker}] Step 1 - Fetched company data ({len(all_companies_df)} rows) - {time.time() - task_1:.2f}s")
            logger.info(f"[{ticker}] - Company df ({all_companies_df.head()}")
            datapoint = all_companies_df[all_companies_df['ticker'] == ticker]

            if datapoint.empty:
                raise ValueError(f"Ticker '{ticker}' not found in company data.")

            row = datapoint.iloc[0]
            all_data['ticker'] = ticker
            all_data['cik'] = str(row["cik_str"]).zfill(10)
            all_data['company_title'] = row["title"]

            # Step 2: Yahoo Finance Data
            task_2 = time.time()
            yf_data = await self.fetch_selected_stock_facts_yq(selected_ticker=ticker)
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
 

    async def get_tickers_from_screeners_async(self, screener_ids: List[str]) -> Tuple[List[str], List[str]]:
        """
        Fetch tickers from multiple Yahoo screeners concurrently.
        Returns a tuple:
            - List of unique tickers
            - List of unique screeners (that successfully returned tickers)
        """
        logger.info(f"[ScreenerFetcher] Starting to fetch tickers for screeners: {screener_ids}")

        async def fetch(screener_id: str) -> List[str]:
            async with self._semaphore:
                for attempt in range(1, self.retry_attempts + 1):
                    try:
                        logger.info(f"[ScreenerFetcher] Fetching screener '{screener_id}' (Attempt {attempt})")
                        screener = Screener()
                        results = await asyncio.to_thread(screener.get_screeners, [screener_id])

                        if not results:
                            raise ValueError("Empty response from Yahoo Screener API")

                        key = next(iter(results))
                        quotes = results.get(key, {}).get("quotes", [])

                        tickers = [q["symbol"] for q in quotes if "symbol" in q]
                        return tickers

                    except Exception as e:
                        logger.warning(f"[ScreenerFetcher] Attempt {attempt} failed for '{screener_id}': {e}")
                        await asyncio.sleep(self.retry_delay)

                logger.info(f"[ScreenerFetcher] All attempts failed for screener '{screener_id}'")
                return []

        all_results = await asyncio.gather(*(fetch(sid) for sid in screener_ids))

        ticker_screener = [
            (screener_id, ticker)
            for screener_id, tickers in zip(screener_ids, all_results)
            for ticker in tickers
        ]

        unique_tickers = sorted(set(ticker for _, ticker in ticker_screener))
        used_screeners = sorted(set(screener for screener, _ in ticker_screener))

        logger.info(
            f"[ScreenerFetcher] Collected {len(unique_tickers)} unique tickers from {len(used_screeners)} screeners"
        )

        return unique_tickers, used_screeners, ticker_screener

 
    async def filter_tickers_by_market_cap_async(self, ticker_screener_pairs: list[tuple[str, str]], min_market_cap=1e9) -> list[str]:
        if not ticker_screener_pairs:
            return []

        tickers = list({t for _, t in ticker_screener_pairs})  

        def fetch_market_caps(tickers_batch):
            try:
                q = yq.Ticker(tickers_batch)
                logger.info(f"[YF BATCH] summary keys: {list(q.summary_detail.keys())}")
                return q.summary_detail
            except Exception as e:
                logger.warning(f"[MarketCap] Failed to fetch market caps: {e}")
                return {}

        summary_data = await asyncio.to_thread(fetch_market_caps, tickers)

        filtered = []
        for ticker in tickers:
            try:
                info = summary_data.get(ticker) or {}
                cap = info.get('marketCap')
                logger.info(f"[{ticker}] marketCap={cap}")
                if cap is not None and cap >= min_market_cap:
                    filtered.append(ticker)
            except Exception as e:
                logger.debug(f"[MarketCap] Skipping {ticker}: {e}")
                continue

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


