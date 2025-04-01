from dataclasses import dataclass
import httpx
import asyncio
import pandas as pd
from dotenv import load_dotenv
import os
from io import BytesIO
import yfinance as yf
from yahoo_fin import stock_info as si
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream
import json
import html
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
import logging
import warnings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

load_dotenv()

@dataclass
class API_Fetcher:
    
    
    async def fetch_all_major_indices(self)->set[str]:
        dow = await asyncio.to_thread(si.tickers_dow)
        nasdaq = await asyncio.to_thread(si.tickers_nasdaq)
        sp500 = await asyncio.to_thread(si.tickers_sp500)
        all_tickers =  dow + nasdaq + sp500
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
    
    
    async def get_available_company_data(self)->tuple[list, pd.DataFrame]:
        # Get all Major Tickers and Fetch a Dataframe containing all CIK ID's, Ticker, Company Titles 
        # available on sec.gov and the get union of yFinance and SEC Data
        all_tickers = await self.fetch_all_major_indices()
        company_ids = await self.fetch_company_cik_ticker_title()
        common = set(all_tickers) & set(company_ids["ticker"])
        subset_company_cik_ticker_title = company_ids[company_ids["ticker"].isin(common)]
        return subset_company_cik_ticker_title


    async def fetch_selected_stock_data_yf(self, selected_ticker:str=None, period:str="10y", interval:str="1mo") -> dict[str, any]:
        try:
            if not selected_ticker:
                raise ValueError(f"Fund '{selected_ticker}' not found.")

            def _fetch_data():    
                yf_ticker = yf.Ticker(selected_ticker)
                hist = yf_ticker.history(period=period, interval=interval)
                info = yf_ticker.info

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

            try:
                decoded = raw_content.decode("utf-8", errors="ignore")
                preprocessed = self.preclean_for_llm(decoded)

                prompt = f"""
Extract the **main readable content** from the following HTML or XML-like text, preserving logical document structure.

---

### Instructions:

1. **Ignore or summarize metadata** (e.g., headers, schema info, context tags like `<ix:header>`, `<context>`).
2. **Preserve structure** using Markdown:
    - Use `#`, `##`, `###` for titles and section headings.
    - Convert bullet and numbered lists cleanly.
    - Format any tables as **Markdown tables** with clear headers.
3. **Clean up the text**:
    - Replace escape characters (`\\n`, `\\t`, `\\r`) with real line breaks or tabs.
    - Decode HTML/XML entities (e.g., `&nbsp;`, `&amp;`).
    - Normalize spacing and remove redundant blank lines.
4. **Respond only with the extracted content.**
---

### Output Format:
**Report Type (If given)**: 
**Cleaned Content**

---

Raw content:
{preprocessed[:200000]}
"""


                headers = {
                    'Authorization': f"Bearer {os.environ.get('DEEPSEEK_API_KEY')}",
                    'Content-Type': 'application/json',
                }

                data = {
                    'model': 'deepseek-chat',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'stream': False
                }

                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        "https://api.deepseek.com/chat/completions",
                        headers=headers,
                        data=json.dumps(data)
                    )
                    response.raise_for_status()
                    result = response.json()
                    markdown = result['choices'][0]['message']['content']
                    cleaned_series.at[index] = markdown
                    print(f'[deepseek] Parsed row {index}')

            except httpx.RequestError as e:
                print(f"[deepseek] Request error at row {index}: {e}")
                cleaned_series.at[index] = None
            except Exception as e:
                print(f"[deepseek] Unexpected error at row {index}: {e}")
                cleaned_series.at[index] = None

        tasks = [process_row(index) for index in series.index]
        await asyncio.gather(*tasks)
        return cleaned_series



