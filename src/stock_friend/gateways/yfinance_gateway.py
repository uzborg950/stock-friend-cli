"""
YFinance gateway implementation using yfinance library.

Primary data source for stock market data with no API key required.
Superior batch performance with yf.download() for parallel fetching.
"""

import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf

from stock_friend.gateways.base import DataProviderException, IMarketDataGateway, InsufficientDataError
from stock_friend.infrastructure.cache_manager import CacheManager
from stock_friend.infrastructure.rate_limiter import RateLimiter
from stock_friend.models.stock_data import FundamentalData, StockData
from stock_friend.models.search_models import SearchResult

logger = logging.getLogger(__name__)


def retry_on_failure(max_attempts: int = 3, backoff_factor: float = 2.0):
    """
    Decorator for retry logic with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Multiplier for backoff delay
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    last_exception = e

                    if attempt < max_attempts:
                        delay = backoff_factor**attempt
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")

            raise last_exception

        return wrapper

    return decorator


class YFinanceGateway(IMarketDataGateway):
    """
    Gateway for Yahoo Finance API using yfinance library.

    Features:
    - No API key required
    - Superior batch performance with yf.download() parallel fetching
    - Aggressive caching (24h TTL for OHLCV, 15min for current prices)
    - Automatic retries with exponential backoff
    - Rate limiting support (conservative 2000 req/hour)
    - Batch operations optimized with threads=True

    Performance:
    - Single stock fetch: <2s (95th percentile)
    - 100 stock batch: <60s (with parallel download)

    Note:
        YFinance uses web scraping, so it may be less stable than official APIs.
        Use comprehensive error handling and retries.
    """

    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        rate_limiter: Optional[RateLimiter] = None,
        requests_per_hour: int = 2000,
    ):
        """
        Initialize YFinance gateway.

        Args:
            cache_manager: Optional cache manager for caching responses
            rate_limiter: Optional rate limiter for API throttling
            requests_per_hour: Rate limit for YFinance (default: 2000/hour)
        """
        self.cache_manager = cache_manager
        self.rate_limiter = rate_limiter
        self.requests_per_hour = requests_per_hour

        if self.rate_limiter:
            # Configure rate limiter: conservative limit to avoid IP throttling
            self.rate_limiter.configure("yfinance", requests_per_hour=self.requests_per_hour)

        logger.info("Initialized YFinanceGateway (no API key required)")

    @retry_on_failure(max_attempts=3, backoff_factor=2.0)
    def get_stock_data(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "1y",
    ) -> StockData:
        """
        Retrieve OHLCV data for a single stock.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for data (optional)
            end_date: End date for data (optional)
            period: Period string if dates not specified
                   ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")

        Returns:
            StockData object with OHLCV DataFrame

        Raises:
            ValueError: If ticker invalid or parameters incompatible
            DataProviderException: If data cannot be retrieved
        """
        ticker = ticker.upper().strip()

        # Check cache first
        if self.cache_manager:
            cache_key = f"stock:{ticker}:ohlcv:{period}"
            cached_data = self.cache_manager.get(cache_key)

            if cached_data is not None:
                logger.debug(f"Cache hit for {ticker} OHLCV data (period={period})")
                return cached_data

        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire("yfinance")

        try:
            logger.info(f"Fetching {ticker} data from YFinance (period={period})")

            # Create yfinance Ticker object
            stock = yf.Ticker(ticker)

            # Fetch historical data
            if start_date and end_date:
                df = stock.history(start=start_date, end=end_date)
            else:
                df = stock.history(period=period)

            if df.empty:
                raise InsufficientDataError(f"No data returned for ticker: {ticker}")

            # Standardize column names
            # YFinance returns: Date (index), Open, High, Low, Close, Volume, Dividends, Stock Splits
            df = df.reset_index()
            df.columns = [col.lower().replace(" ", "_") for col in df.columns]

            # Ensure required columns exist
            required_cols = ["date", "open", "high", "low", "close", "volume"]
            missing = [col for col in required_cols if col not in df.columns]

            if missing:
                raise DataProviderException(
                    f"Missing required columns for {ticker}: {missing}"
                )

            # Convert date column to datetime (remove timezone if present)
            df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

            # Sort by date (ascending)
            df = df.sort_values("date").reset_index(drop=True)

            # Select only required columns
            df = df[required_cols]

            # Create StockData object
            stock_data = StockData(
                ticker=ticker,
                data=df,
                fetched_at=datetime.now(),
                source="YFINANCE",
            )

            # Cache the data (TTL: 24 hours - aggressive caching for YFinance)
            if self.cache_manager:
                ttl = timedelta(hours=24)
                self.cache_manager.set(cache_key, stock_data, ttl=ttl)

            logger.info(f"Retrieved {len(df)} data points for {ticker}")
            return stock_data

        except InsufficientDataError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            raise DataProviderException(f"YFinance error for {ticker}: {e}")

    @retry_on_failure(max_attempts=3, backoff_factor=2.0)
    def get_batch_stock_data(
        self,
        tickers: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "1y",
    ) -> Dict[str, StockData]:
        """
        Retrieve OHLCV data for multiple stocks (batch operation).

        Uses yf.download() with threads=True for parallel fetching.
        This is significantly faster than sequential requests.

        Args:
            tickers: List of ticker symbols
            start_date: Start date for data
            end_date: End date for data
            period: Period string if dates not specified

        Returns:
            Dictionary mapping tickers to StockData objects

        Note:
            Failures for individual stocks are logged but don't stop
            the entire batch. Returns partial results.
        """
        if not tickers:
            return {}

        tickers = [ticker.upper().strip() for ticker in tickers]
        results = {}

        # Check cache for all tickers
        uncached_tickers = []
        if self.cache_manager:
            for ticker in tickers:
                cache_key = f"stock:{ticker}:ohlcv:{period}"
                cached_data = self.cache_manager.get(cache_key)
                if cached_data is not None:
                    logger.debug(f"Cache hit for {ticker} OHLCV data")
                    results[ticker] = cached_data
                else:
                    uncached_tickers.append(ticker)
        else:
            uncached_tickers = tickers

        if not uncached_tickers:
            logger.info(f"All {len(tickers)} tickers found in cache")
            return results

        # Apply rate limiting for batch operation
        if self.rate_limiter:
            # Acquire one token for the entire batch operation
            self.rate_limiter.acquire("yfinance")

        try:
            logger.info(
                f"Fetching batch data for {len(uncached_tickers)} tickers from YFinance "
                f"(period={period})"
            )

            # Use yf.download() for parallel fetching (much faster than sequential)
            if start_date and end_date:
                batch_df = yf.download(
                    uncached_tickers,
                    start=start_date,
                    end=end_date,
                    group_by="ticker",
                    threads=True,
                    progress=False,
                )
            else:
                batch_df = yf.download(
                    uncached_tickers,
                    period=period,
                    group_by="ticker",
                    threads=True,
                    progress=False,
                )

            # Process each ticker from batch result
            for ticker in uncached_tickers:
                try:
                    # Extract data for this ticker
                    if len(uncached_tickers) == 1:
                        # yf.download returns a simple DataFrame for single ticker
                        ticker_df = batch_df
                    else:
                        # For multiple tickers, data is multi-indexed
                        ticker_df = batch_df[ticker]

                    if ticker_df.empty:
                        logger.warning(f"No data returned for ticker: {ticker}")
                        continue

                    # Standardize format
                    ticker_df = ticker_df.reset_index()
                    ticker_df.columns = [col.lower().replace(" ", "_") for col in ticker_df.columns]

                    # Ensure required columns exist
                    required_cols = ["date", "open", "high", "low", "close", "volume"]
                    if not all(col in ticker_df.columns for col in required_cols):
                        logger.warning(f"Missing required columns for {ticker}")
                        continue

                    # Convert date column to datetime (remove timezone if present)
                    ticker_df["date"] = pd.to_datetime(ticker_df["date"]).dt.tz_localize(None)

                    # Sort by date
                    ticker_df = ticker_df.sort_values("date").reset_index(drop=True)

                    # Select only required columns
                    ticker_df = ticker_df[required_cols]

                    # Create StockData object
                    stock_data = StockData(
                        ticker=ticker,
                        data=ticker_df,
                        fetched_at=datetime.now(),
                        source="YFINANCE",
                    )

                    # Cache the data
                    if self.cache_manager:
                        cache_key = f"stock:{ticker}:ohlcv:{period}"
                        ttl = timedelta(hours=24)
                        self.cache_manager.set(cache_key, stock_data, ttl=ttl)

                    results[ticker] = stock_data
                    logger.debug(f"Successfully processed {ticker}")

                except Exception as e:
                    logger.error(f"Failed to process {ticker} in batch: {e}")
                    continue

            logger.info(
                f"Batch fetch completed: {len(results)}/{len(uncached_tickers)} successful"
            )
            return results

        except Exception as e:
            logger.error(f"Batch fetch failed: {e}")
            raise DataProviderException(f"YFinance batch error: {e}")

    @retry_on_failure(max_attempts=3, backoff_factor=2.0)
    def get_current_price(self, ticker: str) -> Decimal:
        """
        Get current/latest price for a stock.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Current price as Decimal

        Raises:
            DataProviderException: If price cannot be retrieved
        """
        ticker = ticker.upper().strip()

        # Check cache first
        if self.cache_manager:
            cache_key = f"stock:{ticker}:current_price"
            cached_price = self.cache_manager.get(cache_key)

            if cached_price is not None:
                logger.debug(f"Cache hit for {ticker} current price")
                return cached_price

        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire("yfinance")

        try:
            logger.info(f"Fetching current price for {ticker} from YFinance")

            stock = yf.Ticker(ticker)
            info = stock.info

            # Try different price fields
            price = None
            price_fields = ["currentPrice", "regularMarketPrice", "previousClose"]

            for field in price_fields:
                if field in info and info[field] is not None:
                    price = Decimal(str(info[field]))
                    break

            if price is None:
                raise DataProviderException(f"No price data available for {ticker}")

            # Cache the price (TTL: 15 minutes for current prices)
            if self.cache_manager:
                ttl = timedelta(minutes=15)
                self.cache_manager.set(cache_key, price, ttl=ttl)

            logger.info(f"Current price for {ticker}: ${price}")
            return price

        except Exception as e:
            logger.error(f"Failed to fetch current price for {ticker}: {e}")
            raise DataProviderException(f"YFinance error for {ticker}: {e}")

    def get_batch_current_prices(self, tickers: List[str]) -> Dict[str, Decimal]:
        """
        Get current prices for multiple stocks (batch operation).

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping tickers to current prices

        Note:
            Failures for individual stocks are logged but don't stop
            the entire batch.
        """
        if not tickers:
            return {}

        tickers = [ticker.upper().strip() for ticker in tickers]
        results = {}

        # Process each ticker (YFinance doesn't have a true batch current price API)
        for ticker in tickers:
            try:
                price = self.get_current_price(ticker)
                results[ticker] = price
            except Exception as e:
                logger.error(f"Failed to get current price for {ticker}: {e}")
                continue

        logger.info(f"Batch price fetch completed: {len(results)}/{len(tickers)} successful")
        return results

    @retry_on_failure(max_attempts=3, backoff_factor=2.0)
    def get_fundamental_data(self, ticker: str) -> Optional[FundamentalData]:
        """
        Retrieve fundamental data for a stock.

        Args:
            ticker: Stock ticker symbol

        Returns:
            FundamentalData object or None if not available
        """
        ticker = ticker.upper().strip()

        # Check cache first
        if self.cache_manager:
            cache_key = f"stock:{ticker}:fundamental"
            cached_data = self.cache_manager.get(cache_key)

            if cached_data is not None:
                logger.debug(f"Cache hit for {ticker} fundamental data")
                return cached_data

        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire("yfinance")

        try:
            logger.info(f"Fetching fundamental data for {ticker} from YFinance")

            stock = yf.Ticker(ticker)
            info = stock.info

            if not info:
                logger.warning(f"No fundamental data available for {ticker}")
                return None

            # Map YFinance info to FundamentalData
            fundamental_data = FundamentalData(
                ticker=ticker,
                company_name=info.get("longName"),
                sector=info.get("sector"),
                industry=info.get("industry"),
                market_cap=Decimal(str(info["marketCap"])) if "marketCap" in info and info["marketCap"] else None,
                pe_ratio=info.get("trailingPE"),
                pb_ratio=info.get("priceToBook"),
                ps_ratio=info.get("priceToSalesTrailing12Months"),
                peg_ratio=info.get("pegRatio"),
                eps=Decimal(str(info["trailingEps"])) if "trailingEps" in info and info["trailingEps"] else None,
                eps_growth_yoy=info.get("earningsGrowth"),
                book_value_per_share=Decimal(str(info["bookValue"])) if "bookValue" in info and info["bookValue"] else None,
                revenue=Decimal(str(info["totalRevenue"])) if "totalRevenue" in info and info["totalRevenue"] else None,
                revenue_growth_yoy=info.get("revenueGrowth"),
                net_income=Decimal(str(info["netIncomeToCommon"])) if "netIncomeToCommon" in info and info["netIncomeToCommon"] else None,
                profit_margin=info.get("profitMargins"),
                roe=info.get("returnOnEquity"),
                total_debt=Decimal(str(info["totalDebt"])) if "totalDebt" in info and info["totalDebt"] else None,
                total_cash=Decimal(str(info["totalCash"])) if "totalCash" in info and info["totalCash"] else None,
                debt_to_equity=info.get("debtToEquity"),
                last_updated=datetime.now(),
            )

            # Cache the data (TTL: 24 hours for fundamentals)
            if self.cache_manager:
                ttl = timedelta(hours=24)
                self.cache_manager.set(cache_key, fundamental_data, ttl=ttl)

            logger.info(f"Retrieved fundamental data for {ticker}")
            return fundamental_data

        except Exception as e:
            logger.error(f"Failed to fetch fundamental data for {ticker}: {e}")
            # Return None instead of raising exception (fundamentals are optional)
            return None

    @retry_on_failure(max_attempts=2, backoff_factor=1.5)
    def search_stock(
        self,
        query: str,
        max_results: int = 20,
        enable_fuzzy: bool = True,
    ) -> List[SearchResult]:
        """
        Search for stocks using yfinance Search API.

        Performs comprehensive search with fuzzy matching across all exchanges.
        Handles exact ticker matches, partial matches, and company name searches.

        Args:
            query: Ticker symbol, company name, or search term
            max_results: Maximum number of results to return
            enable_fuzzy: Enable fuzzy matching for typos

        Returns:
            List of SearchResult objects sorted by relevance (empty if no matches)
        """
        query = query.strip().upper()

        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire("yfinance")

        try:
            logger.info(f"Searching for '{query}' using YFinance Search API")

            # Use yfinance Search API
            search = yf.Search(
                query,
                max_results=max_results,
                enable_fuzzy_query=enable_fuzzy,
            )

            quotes = search.quotes or []
            results = []
            seen_tickers = set()

            for quote in quotes:
                ticker = quote.get("symbol", "").strip()
                company_name = quote.get("shortname") or quote.get("longname", "")
                quote_type = quote.get("quoteType", "")

                if not ticker or not company_name:
                    continue

                if ticker in seen_tickers:
                    continue

                # Extract exchange name
                exchange_name = self._extract_exchange_from_quote(quote)

                # Normalize quote_type
                if quote_type:
                    quote_type = quote_type.upper()

                result = SearchResult(
                    ticker=ticker,
                    company_name=company_name,
                    exchange=exchange_name,
                    sector=quote.get("sector"),
                    quote_type=quote_type if quote_type else "OTHER",
                )

                results.append(result)
                seen_tickers.add(ticker)

            logger.info(f"Found {len(results)} results for '{query}'")
            return results

        except Exception as e:
            logger.error(f"Search failed for '{query}': {e}")
            # Return empty list on error (search is not critical)
            return []

    def _extract_exchange_from_quote(self, quote: dict) -> str:
        """
        Extract exchange name from yfinance search quote.

        Args:
            quote: Quote dictionary from yfinance.Search

        Returns:
            Exchange name
        """
        exchange_code = quote.get("exchange", "")
        if exchange_code:
            exchange_map = {
                "NMS": "NASDAQ",
                "NYQ": "NYSE",
                "NGM": "NASDAQ Global Market",
                "NCM": "NASDAQ Capital Market",
                "LSE": "London Stock Exchange",
                "FRA": "Frankfurt Stock Exchange",
                "ETR": "XETRA",
                "PAR": "Euronext Paris",
                "AMS": "Euronext Amsterdam",
                "BRU": "Euronext Brussels",
                "TOR": "Toronto Stock Exchange",
                "ASX": "Australian Securities Exchange",
                "HKG": "Hong Kong Stock Exchange",
                "JPX": "Tokyo Stock Exchange",
            }
            return exchange_map.get(exchange_code, exchange_code)

        # Fallback: infer from ticker suffix
        ticker = quote.get("symbol", "")
        if "." in ticker:
            suffix = ticker.split(".")[-1]
            exchange_map = {
                "L": "LSE",
                "TO": "TSX",
                "AX": "ASX",
                "PA": "EPA",
                "DE": "XETRA",
                "HK": "HKEX",
                "T": "TSE",
                "SW": "SWX",
            }
            return exchange_map.get(suffix, f"{suffix} Exchange")

        return "US Market"

    def get_name(self) -> str:
        """
        Return unique gateway identifier.

        Returns:
            Gateway name "yfinance"
        """
        return "yfinance"
