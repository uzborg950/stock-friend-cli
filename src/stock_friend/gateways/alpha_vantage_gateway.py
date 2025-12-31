"""
Alpha Vantage gateway implementation using alpha_vantage library.

Primary data source for stock market data (OHLCV, fundamentals, current prices).
More reliable than yfinance with official API support.
"""

import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
from typing import Dict, List, Optional

import pandas as pd
from alpha_vantage.fundamentaldata import FundamentalData as AVFundamentalData
from alpha_vantage.timeseries import TimeSeries

from stock_friend.gateways.base import DataProviderException, IMarketDataGateway
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
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )

            raise last_exception

        return wrapper

    return decorator


class AlphaVantageGateway(IMarketDataGateway):
    """
    Gateway for Alpha Vantage API using alpha_vantage library.

    Features:
    - Official API with better reliability than yfinance
    - OHLCV historical data (TIME_SERIES_DAILY_ADJUSTED)
    - Current price retrieval (GLOBAL_QUOTE)
    - Fundamental metrics (OVERVIEW)
    - Automatic retries with exponential backoff
    - Caching support
    - Rate limiting support (5 requests/minute, 500/day)
    - Batch operations with rate limiting

    API Limits:
    - Free tier: 5 requests per minute, 500 requests per day
    - Premium tiers: Higher limits available

    Note:
        Requires API key from https://www.alphavantage.co/support/#api-key
    """

    def __init__(
        self,
        api_key: str,
        cache_manager: Optional[CacheManager] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        """
        Initialize Alpha Vantage gateway.

        Args:
            api_key: Alpha Vantage API key
            cache_manager: Optional cache manager for caching responses
            rate_limiter: Optional rate limiter for API throttling
        """
        if not api_key:
            raise ValueError("Alpha Vantage API key is required")

        self.api_key = api_key
        self.cache_manager = cache_manager
        self.rate_limiter = rate_limiter

        # Initialize Alpha Vantage clients
        self.ts_client = TimeSeries(key=self.api_key, output_format="pandas")
        self.fundamental_client = AVFundamentalData(key=self.api_key, output_format="pandas")

        if self.rate_limiter:
            # Configure rate limiter: 5 requests/minute (300 requests/hour)
            # Using conservative limit to avoid hitting daily limit
            self.rate_limiter.configure("alpha_vantage", requests_per_hour=300)

        logger.info("Initialized AlphaVantageGateway")

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
            start_date: Start date for data (optional, will filter)
            end_date: End date for data (optional, will filter)
            period: Period string (used to determine outputsize)

        Returns:
            StockData object with OHLCV DataFrame

        Raises:
            ValueError: If ticker invalid
            DataProviderException: If data cannot be retrieved

        Note:
            Alpha Vantage returns full historical data by default.
            We filter by dates after retrieval if specified.
        """
        ticker = ticker.upper().strip()

        # Check cache first
        if self.cache_manager:
            cache_key = f"stock:{ticker}:ohlcv:full"
            cached_data = self.cache_manager.get(cache_key)

            if cached_data is not None:
                logger.debug(f"Cache hit for {ticker} OHLCV data")
                # Filter by dates if specified
                return self._filter_by_dates(cached_data, start_date, end_date)

        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire("alpha_vantage")

        try:
            # Fetch daily adjusted data from Alpha Vantage
            # outputsize='full' gets 20+ years of data
            # outputsize='compact' gets last 100 data points
            outputsize = "compact" if period in ["1d", "5d", "1mo"] else "full"

            logger.info(f"Fetching {ticker} data from Alpha Vantage (outputsize={outputsize})")
            df, meta_data = self.ts_client.get_daily_adjusted(
                symbol=ticker, outputsize=outputsize
            )

            if df.empty:
                raise ValueError(f"No data returned for ticker: {ticker}")

            # Standardize column names
            # Alpha Vantage returns: 1. open, 2. high, 3. low, 4. close, 5. adjusted close, 6. volume
            df = df.reset_index()
            df.columns = [col.lower().replace(". ", "_") for col in df.columns]

            # Rename columns to match our standard format
            column_mapping = {
                "date": "date",
                "1_open": "open",
                "2_high": "high",
                "3_low": "low",
                "4_close": "close",
                "5_adjusted_close": "adjusted_close",
                "6_volume": "volume",
            }
            df = df.rename(columns=column_mapping)

            # Ensure required columns exist
            required_cols = ["date", "open", "high", "low", "close", "volume"]
            missing = [col for col in required_cols if col not in df.columns]

            if missing:
                raise DataProviderException(
                    f"Missing required columns for {ticker}: {missing}"
                )

            # Convert date column to datetime
            df["date"] = pd.to_datetime(df["date"])

            # Sort by date (ascending)
            df = df.sort_values("date").reset_index(drop=True)

            # Create StockData object
            stock_data = StockData(
                ticker=ticker,
                data=df,
                fetched_at=datetime.now(),
                source="ALPHA_VANTAGE",
            )

            # Cache the data (TTL: 1 hour for recent data, 24 hours for full data)
            if self.cache_manager:
                ttl = timedelta(hours=1) if outputsize == "compact" else timedelta(hours=24)
                self.cache_manager.set(cache_key, stock_data, ttl=ttl)

            logger.info(f"Retrieved {len(df)} data points for {ticker}")

            # Filter by dates if specified
            return self._filter_by_dates(stock_data, start_date, end_date)

        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            raise DataProviderException(f"Alpha Vantage error for {ticker}: {e}")

    def _filter_by_dates(
        self,
        stock_data: StockData,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> StockData:
        """
        Filter stock data by date range.

        Args:
            stock_data: StockData object to filter
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            New StockData object with filtered data
        """
        df = stock_data.data.copy()

        if start_date:
            df = df[df["date"] >= start_date]

        if end_date:
            df = df[df["date"] <= end_date]

        return StockData(
            ticker=stock_data.ticker,
            data=df.reset_index(drop=True),
            fetched_at=stock_data.fetched_at,
            source=stock_data.source,
        )

    def get_batch_stock_data(
        self,
        tickers: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "1y",
    ) -> Dict[str, StockData]:
        """
        Retrieve OHLCV data for multiple stocks (batch operation).

        Args:
            tickers: List of ticker symbols
            start_date: Start date for data
            end_date: End date for data
            period: Period string

        Returns:
            Dictionary mapping tickers to StockData objects

        Note:
            Processes tickers sequentially with rate limiting (5 req/min).
            For 100 stocks, this will take ~20 minutes due to API limits.
        """
        results = {}
        errors = []

        for i, ticker in enumerate(tickers):
            try:
                stock_data = self.get_stock_data(ticker, start_date, end_date, period)
                results[ticker] = stock_data

                # Progress logging
                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {i + 1}/{len(tickers)} stocks fetched")

            except Exception as e:
                logger.warning(f"Skipping {ticker} due to error: {e}")
                errors.append((ticker, str(e)))

        if errors:
            logger.warning(
                f"Batch fetch completed with {len(errors)} errors out of {len(tickers)} stocks"
            )

        return results

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

        # Check cache (short TTL for current prices: 15 minutes)
        if self.cache_manager:
            cache_key = f"stock:{ticker}:current_price"
            cached_price = self.cache_manager.get(cache_key)

            if cached_price is not None:
                logger.debug(f"Cache hit for {ticker} current price")
                return cached_price

        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire("alpha_vantage")

        try:
            # Use GLOBAL_QUOTE endpoint for current price
            df, meta_data = self.ts_client.get_quote_endpoint(symbol=ticker)

            if df.empty:
                raise DataProviderException(f"No quote data available for {ticker}")

            # Extract price (column name: '05. price')
            price_str = df["05. price"].iloc[0]
            price_decimal = Decimal(str(price_str))

            # Cache for 15 minutes
            if self.cache_manager:
                self.cache_manager.set(
                    cache_key, price_decimal, ttl=timedelta(minutes=15)
                )

            logger.debug(f"Current price for {ticker}: ${price_decimal}")

            return price_decimal

        except Exception as e:
            logger.error(f"Failed to fetch current price for {ticker}: {e}")
            raise DataProviderException(f"Price retrieval error for {ticker}: {e}")

    def get_batch_current_prices(self, tickers: List[str]) -> Dict[str, Decimal]:
        """
        Get current prices for multiple stocks (batch operation).

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping tickers to current prices

        Note:
            Subject to same rate limits as other operations (5 req/min).
        """
        results = {}

        for ticker in tickers:
            try:
                price = self.get_current_price(ticker)
                results[ticker] = price
            except Exception as e:
                logger.warning(f"Skipping price for {ticker}: {e}")

        return results

    @retry_on_failure(max_attempts=3, backoff_factor=2.0)
    def get_fundamental_data(self, ticker: str) -> Optional[FundamentalData]:
        """
        Retrieve fundamental data for a stock.

        Args:
            ticker: Stock ticker symbol

        Returns:
            FundamentalData object or None if not available

        Note:
            Returns None on error rather than raising exception,
            as fundamental data is optional.
        """
        ticker = ticker.upper().strip()

        # Check cache (TTL: 24 hours for fundamental data)
        if self.cache_manager:
            cache_key = f"stock:{ticker}:fundamental"
            cached_data = self.cache_manager.get(cache_key)

            if cached_data is not None:
                logger.debug(f"Cache hit for {ticker} fundamental data")
                return cached_data

        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire("alpha_vantage")

        try:
            # Get company overview (fundamentals)
            df, meta_data = self.fundamental_client.get_company_overview(symbol=ticker)

            if df.empty:
                logger.warning(f"No fundamental data available for {ticker}")
                return None

            # Alpha Vantage returns fundamentals as a single-row DataFrame
            info = df.iloc[0].to_dict()

            # Extract and convert fundamental metrics
            def safe_decimal(value):
                try:
                    return Decimal(str(value)) if value and value != "None" else None
                except:
                    return None

            def safe_float(value):
                try:
                    return float(value) if value and value != "None" else None
                except:
                    return None

            fundamental = FundamentalData(
                ticker=ticker,
                company_name=info.get("Name"),
                sector=info.get("Sector"),
                industry=info.get("Industry"),
                market_cap=safe_decimal(info.get("MarketCapitalization")),
                pe_ratio=safe_float(info.get("PERatio")),
                pb_ratio=safe_float(info.get("PriceToBookRatio")),
                ps_ratio=safe_float(info.get("PriceToSalesRatioTTM")),
                peg_ratio=safe_float(info.get("PEGRatio")),
                eps=safe_decimal(info.get("EPS")),
                eps_growth_yoy=safe_float(info.get("QuarterlyEarningsGrowthYOY")),
                book_value_per_share=safe_decimal(info.get("BookValue")),
                revenue=safe_decimal(info.get("RevenueTTM")),
                revenue_growth_yoy=safe_float(info.get("QuarterlyRevenueGrowthYOY")),
                net_income=None,  # Not directly available in overview
                profit_margin=safe_float(info.get("ProfitMargin")),
                roe=safe_float(info.get("ReturnOnEquityTTM")),
                total_debt=None,  # Would need balance sheet endpoint
                total_cash=None,  # Would need balance sheet endpoint
                debt_to_equity=safe_float(info.get("DebtToEquity")),
                last_updated=datetime.now(),
            )

            # Cache for 24 hours
            if self.cache_manager:
                self.cache_manager.set(
                    cache_key, fundamental, ttl=timedelta(hours=24)
                )

            logger.info(f"Retrieved fundamental data for {ticker}")

            return fundamental

        except Exception as e:
            logger.error(f"Failed to fetch fundamental data for {ticker}: {e}")
            # Return None instead of raising, as fundamental data is optional
            return None

    def search_stock(
        self,
        query: str,
        max_results: int = 20,
        enable_fuzzy: bool = True,
    ) -> List[SearchResult]:
        """
        Search for stocks by ticker symbol or company name.

        Note: Alpha Vantage SYMBOL_SEARCH endpoint implementation pending.
        """
        raise NotImplementedError(
            "Search functionality not yet implemented for Alpha Vantage gateway. "
            "Use YFinance gateway for stock search."
        )

    def get_name(self) -> str:
        """Return unique gateway identifier."""
        return "alpha_vantage"
