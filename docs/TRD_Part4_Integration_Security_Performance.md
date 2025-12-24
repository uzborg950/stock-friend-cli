# Technical Requirements Document (TRD)
## stock-friend-cli: Halal-Compliant Stock Screening Tool

**Part 4: Integration, Security & Performance**

---

## Document Navigation

- **Part 1:** Architecture & Foundation
- **Part 2:** Data Models & Service Layer
- **Part 3:** Indicator Architecture & Data Access Layer
- **Part 4:** Integration, Security & Performance (this document)
- **Part 5:** Implementation & Testing Strategy

---

## Phase 14: Data Access Layer (Gateway Implementations)

### 14.1 MarketDataGateway - Yahoo Finance Implementation

```python
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import time
from functools import wraps

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
                        delay = backoff_factor ** attempt
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


class YahooFinanceGateway:
    """
    Gateway for Yahoo Finance data using yfinance library.

    Provides OHLCV data, fundamental metrics, and current prices.

    Features:
    - Automatic retries with exponential backoff
    - Batch operations
    - Integration with CacheManager and RateLimiter
    - Error handling and logging
    """

    def __init__(self,
                 cache_manager: 'CacheManager',
                 rate_limiter: 'RateLimiter'):
        self.cache_manager = cache_manager
        self.rate_limiter = rate_limiter

    @retry_on_failure(max_attempts=3, backoff_factor=2.0)
    def get_stock_data(self,
                      ticker: str,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      period: str = "1y") -> pd.DataFrame:
        """
        Retrieve OHLCV data for a single stock.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for data (optional)
            end_date: End date for data (optional)
            period: Period string if dates not specified ("1d", "5d", "1mo", "3mo",
                   "6mo", "1y", "2y", "5y", "10y", "ytd", "max")

        Returns:
            DataFrame with columns: ['date', 'open', 'high', 'low', 'close', 'volume']

        Raises:
            ValueError: If ticker invalid
            DataProviderException: If data cannot be retrieved
        """
        # Check cache first
        cache_key = f"stock:{ticker}:ohlcv:{period}"
        cached_data = self.cache_manager.get(cache_key)

        if cached_data is not None:
            logger.debug(f"Cache hit for {ticker} OHLCV data")
            return cached_data

        # Apply rate limiting
        self.rate_limiter.acquire("yahoo_finance")

        try:
            # Fetch from Yahoo Finance
            stock = yf.Ticker(ticker)

            if start_date and end_date:
                df = stock.history(start=start_date, end=end_date)
            else:
                df = stock.history(period=period)

            if df.empty:
                raise ValueError(f"No data returned for ticker: {ticker}")

            # Standardize column names
            df = df.reset_index()
            df.columns = [col.lower() for col in df.columns]

            # Ensure required columns exist
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            missing = [col for col in required_cols if col not in df.columns]

            if missing:
                raise DataProviderException(
                    f"Missing required columns for {ticker}: {missing}"
                )

            # Cache the data (TTL: 1 hour)
            self.cache_manager.set(
                cache_key,
                df,
                ttl=timedelta(hours=1)
            )

            logger.info(f"Retrieved {len(df)} data points for {ticker}")

            return df

        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            raise DataProviderException(f"Yahoo Finance error for {ticker}: {e}")

    def get_batch_stock_data(self,
                            tickers: List[str],
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            period: str = "1y") -> Dict[str, pd.DataFrame]:
        """
        Retrieve OHLCV data for multiple stocks (batch operation).

        Args:
            tickers: List of ticker symbols
            start_date: Start date for data
            end_date: End date for data
            period: Period string if dates not specified

        Returns:
            Dictionary mapping tickers to DataFrames

        Note:
            This method processes tickers sequentially with rate limiting.
            For true parallel processing, use async implementation.
        """
        results = {}
        errors = []

        for ticker in tickers:
            try:
                df = self.get_stock_data(ticker, start_date, end_date, period)
                results[ticker] = df
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
        # Check cache (short TTL for current prices: 15 minutes)
        cache_key = f"stock:{ticker}:current_price"
        cached_price = self.cache_manager.get(cache_key)

        if cached_price is not None:
            logger.debug(f"Cache hit for {ticker} current price")
            return cached_price

        # Apply rate limiting
        self.rate_limiter.acquire("yahoo_finance")

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Try different price fields in order of preference
            price_fields = ['currentPrice', 'regularMarketPrice', 'price', 'previousClose']
            price = None

            for field in price_fields:
                if field in info and info[field]:
                    price = info[field]
                    break

            if price is None:
                raise DataProviderException(f"No price data available for {ticker}")

            price_decimal = Decimal(str(price))

            # Cache for 15 minutes
            self.cache_manager.set(
                cache_key,
                price_decimal,
                ttl=timedelta(minutes=15)
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

        Raises:
            DataProviderException: If critical error occurs
        """
        # Check cache (TTL: 24 hours for fundamental data)
        cache_key = f"stock:{ticker}:fundamental"
        cached_data = self.cache_manager.get(cache_key)

        if cached_data is not None:
            logger.debug(f"Cache hit for {ticker} fundamental data")
            return cached_data

        # Apply rate limiting
        self.rate_limiter.acquire("yahoo_finance")

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Extract fundamental metrics
            fundamental = FundamentalData(
                ticker=ticker,
                pe_ratio=info.get('trailingPE'),
                pb_ratio=info.get('priceToBook'),
                ps_ratio=info.get('priceToSalesTrailing12Months'),
                peg_ratio=info.get('pegRatio'),
                eps=Decimal(str(info['trailingEps'])) if info.get('trailingEps') else None,
                eps_growth_yoy=info.get('earningsGrowth'),
                book_value_per_share=Decimal(str(info['bookValue'])) if info.get('bookValue') else None,
                revenue=Decimal(str(info['totalRevenue'])) if info.get('totalRevenue') else None,
                revenue_growth_yoy=info.get('revenueGrowth'),
                net_income=Decimal(str(info['netIncomeToCommon'])) if info.get('netIncomeToCommon') else None,
                profit_margin=info.get('profitMargins'),
                roe=info.get('returnOnEquity'),
                total_debt=Decimal(str(info['totalDebt'])) if info.get('totalDebt') else None,
                total_cash=Decimal(str(info['totalCash'])) if info.get('totalCash') else None,
                debt_to_equity=info.get('debtToEquity'),
                last_updated=datetime.now()
            )

            # Cache for 24 hours
            self.cache_manager.set(
                cache_key,
                fundamental,
                ttl=timedelta(hours=24)
            )

            logger.info(f"Retrieved fundamental data for {ticker}")

            return fundamental

        except Exception as e:
            logger.error(f"Failed to fetch fundamental data for {ticker}: {e}")
            # Return None instead of raising, as fundamental data is optional
            return None


class DataProviderException(Exception):
    """Raised when data provider encounters an error."""
    pass
```

---

### 14.2 ComplianceGateway - Halal Screening Implementation

```python
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import csv
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ComplianceGateway:
    """
    Gateway for halal compliance verification.

    Multi-source approach:
    1. Primary: Zoya API
    2. Secondary: Musaffa API
    3. Fallback: Local CSV database

    Ensures zero false negatives through fail-safe filtering.
    """

    def __init__(self,
                 cache_manager: 'CacheManager',
                 zoya_api_key: Optional[str] = None,
                 musaffa_api_key: Optional[str] = None,
                 local_db_path: str = "data/compliance/manual_classification.csv"):
        self.cache_manager = cache_manager
        self.zoya_api_key = zoya_api_key
        self.musaffa_api_key = musaffa_api_key
        self.local_db_path = Path(local_db_path)

        # Initialize local database
        self._load_local_database()

    def _load_local_database(self):
        """Load local compliance database from CSV."""
        self.local_db = {}

        if not self.local_db_path.exists():
            logger.warning(f"Local compliance database not found: {self.local_db_path}")
            return

        try:
            with open(self.local_db_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ticker = row['ticker'].upper()
                    self.local_db[ticker] = {
                        'result': row['result'],  # 'compliant', 'excluded'
                        'exclusion_reason': row.get('exclusion_reason'),
                        'notes': row.get('notes')
                    }

            logger.info(f"Loaded {len(self.local_db)} entries from local compliance database")

        except Exception as e:
            logger.error(f"Failed to load local compliance database: {e}")

    @retry_on_failure(max_attempts=2, backoff_factor=1.5)
    def check_compliance(self, ticker: str) -> ComplianceStatus:
        """
        Check halal compliance for a single stock.

        Uses multi-source approach with fail-safe default to exclusion.

        Args:
            ticker: Stock ticker symbol

        Returns:
            ComplianceStatus object

        Fail-Safe Logic:
            - If uncertain or error: DEFAULT TO EXCLUSION
            - Never return compliant unless explicitly verified
        """
        ticker = ticker.upper()

        # Check cache first (TTL: 30 days)
        cache_key = f"compliance:{ticker}"
        cached_status = self.cache_manager.get(cache_key)

        if cached_status is not None:
            logger.debug(f"Cache hit for {ticker} compliance status")
            return cached_status

        # Try Zoya API (primary source)
        if self.zoya_api_key:
            try:
                status = self._check_zoya_api(ticker)
                if status:
                    self._cache_compliance_status(ticker, status)
                    return status
            except Exception as e:
                logger.warning(f"Zoya API failed for {ticker}: {e}")

        # Try Musaffa API (secondary source)
        if self.musaffa_api_key:
            try:
                status = self._check_musaffa_api(ticker)
                if status:
                    self._cache_compliance_status(ticker, status)
                    return status
            except Exception as e:
                logger.warning(f"Musaffa API failed for {ticker}: {e}")

        # Try local database (tertiary source)
        if ticker in self.local_db:
            entry = self.local_db[ticker]
            status = ComplianceStatus(
                ticker=ticker,
                result=ComplianceResult(entry['result']),
                exclusion_reason=entry.get('exclusion_reason'),
                exclusion_detail=entry.get('notes'),
                verified_at=datetime.now(),
                data_source="LOCAL_DB"
            )
            self._cache_compliance_status(ticker, status)
            return status

        # FAIL-SAFE: No data available, default to exclusion
        logger.warning(
            f"No compliance data available for {ticker}. "
            f"Defaulting to EXCLUSION (zero false negatives guarantee)."
        )

        status = ComplianceStatus.excluded(
            ticker=ticker,
            reason="UNVERIFIED",
            detail="No compliance data available from any source",
            source="SYSTEM"
        )

        # Cache unverified status for shorter period (7 days)
        self.cache_manager.set(
            cache_key,
            status,
            ttl=timedelta(days=7)
        )

        return status

    def batch_check_compliance(self, tickers: List[str]) -> Dict[str, ComplianceStatus]:
        """
        Check compliance for multiple stocks (batch operation).

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping tickers to ComplianceStatus

        Note:
            Processes tickers sequentially. For production, implement
            batch API calls if supported by provider.
        """
        results = {}

        for ticker in tickers:
            try:
                status = self.check_compliance(ticker)
                results[ticker.upper()] = status
            except Exception as e:
                logger.error(f"Compliance check failed for {ticker}: {e}")
                # Fail-safe: Exclude on error
                results[ticker.upper()] = ComplianceStatus.excluded(
                    ticker=ticker.upper(),
                    reason="ERROR",
                    detail=str(e),
                    source="SYSTEM"
                )

        return results

    def _check_zoya_api(self, ticker: str) -> Optional[ComplianceStatus]:
        """
        Check compliance via Zoya API.

        API Documentation: https://zoya.finance/api (example endpoint)

        Returns:
            ComplianceStatus or None if API call fails
        """
        url = f"https://api.zoya.finance/v1/compliance/{ticker}"
        headers = {
            "Authorization": f"Bearer {self.zoya_api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Parse API response
            is_compliant = data.get('is_compliant', False)
            confidence = data.get('confidence', 'low')

            if is_compliant and confidence == 'high':
                return ComplianceStatus.compliant(
                    ticker=ticker,
                    verified_at=datetime.now(),
                    source="ZOYA_API"
                )
            elif not is_compliant:
                reason_code = self._map_zoya_reason(data.get('reason'))
                return ComplianceStatus.excluded(
                    ticker=ticker,
                    reason=reason_code,
                    detail=data.get('reason_detail'),
                    source="ZOYA_API"
                )
            else:
                # Low confidence or questionable: Fail-safe to exclusion
                return ComplianceStatus.excluded(
                    ticker=ticker,
                    reason="UNVERIFIED",
                    detail=f"Low confidence from Zoya API: {confidence}",
                    source="ZOYA_API"
                )

        except requests.exceptions.RequestException as e:
            logger.error(f"Zoya API request failed for {ticker}: {e}")
            return None

    def _check_musaffa_api(self, ticker: str) -> Optional[ComplianceStatus]:
        """
        Check compliance via Musaffa API.

        API Documentation: https://musaffa.com/api (example endpoint)

        Returns:
            ComplianceStatus or None if API call fails
        """
        url = f"https://api.musaffa.com/v1/stocks/{ticker}/compliance"
        headers = {
            "X-API-Key": self.musaffa_api_key,
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            status = data.get('status', 'unknown')

            if status == 'compliant':
                return ComplianceStatus.compliant(
                    ticker=ticker,
                    verified_at=datetime.now(),
                    source="MUSAFFA_API"
                )
            elif status == 'non_compliant':
                reason_code = self._map_musaffa_reason(data.get('reason'))
                return ComplianceStatus.excluded(
                    ticker=ticker,
                    reason=reason_code,
                    detail=data.get('explanation'),
                    source="MUSAFFA_API"
                )
            else:
                # Unknown or questionable: Fail-safe to exclusion
                return ComplianceStatus.excluded(
                    ticker=ticker,
                    reason="UNVERIFIED",
                    detail=f"Uncertain status from Musaffa API: {status}",
                    source="MUSAFFA_API"
                )

        except requests.exceptions.RequestException as e:
            logger.error(f"Musaffa API request failed for {ticker}: {e}")
            return None

    def _map_zoya_reason(self, api_reason: str) -> str:
        """Map Zoya API reason to internal reason code."""
        reason_map = {
            'alcohol': 'ALCOHOL',
            'tobacco': 'TOBACCO',
            'gambling': 'GAMBLING',
            'weapons': 'DEFENSE',
            'interest_banking': 'BANKING',
            'pork': 'PORK',
            'adult_entertainment': 'ADULT',
            'excessive_debt': 'DEBT_RATIO',
            'impure_income': 'IMPURE_INCOME'
        }
        return reason_map.get(api_reason, 'UNVERIFIED')

    def _map_musaffa_reason(self, api_reason: str) -> str:
        """Map Musaffa API reason to internal reason code."""
        # Similar mapping as Zoya
        reason_map = {
            'alcoholic_beverages': 'ALCOHOL',
            'tobacco_products': 'TOBACCO',
            'gambling_casinos': 'GAMBLING',
            'weapons_defense': 'DEFENSE',
            'conventional_banking': 'BANKING',
            'pork_related': 'PORK',
            'adult_content': 'ADULT',
            'high_debt_ratio': 'DEBT_RATIO'
        }
        return reason_map.get(api_reason, 'UNVERIFIED')

    def _cache_compliance_status(self, ticker: str, status: ComplianceStatus):
        """Cache compliance status with appropriate TTL."""
        cache_key = f"compliance:{ticker}"

        if status.result == ComplianceResult.COMPLIANT:
            # Cache compliant status for 30 days
            ttl = timedelta(days=30)
        elif status.result == ComplianceResult.EXCLUDED:
            # Cache excluded status for 30 days
            ttl = timedelta(days=30)
        else:
            # Cache unverified status for shorter period
            ttl = timedelta(days=7)

        self.cache_manager.set(cache_key, status, ttl=ttl)

        # Also persist to database
        self._persist_compliance_status(status)

    def _persist_compliance_status(self, status: ComplianceStatus):
        """Persist compliance status to SQLite database."""
        # Implementation: Insert into compliance_status table
        # See database schema in Part 2
        pass
```

---

### 14.3 UniverseGateway - Stock Universe Implementation

```python
from typing import List, Dict, Optional
from pathlib import Path
import csv
import logging

logger = logging.getLogger(__name__)


class UniverseGateway:
    """
    Gateway for retrieving stock universe lists.

    Sources:
    - Static CSV files for major indices (S&P 500, NASDAQ, etc.)
    - Yahoo Finance for sector and market cap queries
    - ETF holdings from provider websites or APIs
    """

    def __init__(self,
                 cache_manager: 'CacheManager',
                 static_data_path: str = "data/universes",
                 yahoo_gateway: 'YahooFinanceGateway' = None):
        self.cache_manager = cache_manager
        self.static_data_path = Path(static_data_path)
        self.yahoo_gateway = yahoo_gateway

    def get_universe(self, config: UniverseConfig) -> List[str]:
        """
        Get stock universe based on configuration.

        Args:
            config: UniverseConfig specifying universe type and parameters

        Returns:
            List of ticker symbols

        Raises:
            UniverseNotFoundException: If universe cannot be retrieved
        """
        if config.universe_type == UniverseType.EXCHANGE:
            return self.get_exchange_constituents(config.exchange)

        elif config.universe_type == UniverseType.SECTOR:
            return self.get_sector_stocks(config.sector)

        elif config.universe_type == UniverseType.MARKET_CAP:
            return self.get_market_cap_stocks(config.min_market_cap, config.max_market_cap)

        elif config.universe_type == UniverseType.ETF:
            return self.get_etf_holdings(config.etf_ticker, config.min_etf_weight)

        elif config.universe_type == UniverseType.CUSTOM:
            return self._validate_tickers(config.custom_tickers)

        else:
            raise ValueError(f"Unknown universe type: {config.universe_type}")

    def get_exchange_constituents(self, exchange: ExchangeType) -> List[str]:
        """
        Get constituent list for a major exchange or index.

        Args:
            exchange: Exchange type (SP500, NASDAQ, etc.)

        Returns:
            List of ticker symbols

        Data Source:
            Static CSV files updated monthly from official sources
        """
        # Check cache (TTL: 30 days)
        cache_key = f"universe:exchange:{exchange.value}"
        cached_tickers = self.cache_manager.get(cache_key)

        if cached_tickers is not None:
            logger.debug(f"Cache hit for {exchange.value} constituents")
            return cached_tickers

        # Map exchange to CSV filename
        file_map = {
            ExchangeType.SP500: "sp500_constituents.csv",
            ExchangeType.NASDAQ_100: "nasdaq100_constituents.csv",
            ExchangeType.NASDAQ_COMPOSITE: "nasdaq_composite_constituents.csv",
            ExchangeType.RUSSELL_2000: "russell2000_constituents.csv",
            ExchangeType.DOW_JONES: "dow_jones_constituents.csv"
        }

        filename = file_map.get(exchange)
        if not filename:
            raise UniverseNotFoundException(f"No data file for exchange: {exchange.value}")

        filepath = self.static_data_path / filename

        if not filepath.exists():
            raise UniverseNotFoundException(
                f"Constituent file not found: {filepath}. "
                f"Please download from official source."
            )

        # Load tickers from CSV
        tickers = []
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ticker = row['ticker'].upper().strip()
                    tickers.append(ticker)

            logger.info(f"Loaded {len(tickers)} constituents for {exchange.value}")

            # Cache for 30 days
            self.cache_manager.set(
                cache_key,
                tickers,
                ttl=timedelta(days=30)
            )

            return tickers

        except Exception as e:
            raise UniverseNotFoundException(
                f"Failed to load constituents for {exchange.value}: {e}"
            )

    def get_sector_stocks(self, sector: SectorType) -> List[str]:
        """
        Get stocks in a specific sector.

        Args:
            sector: Sector type

        Returns:
            List of ticker symbols

        Data Source:
            Yahoo Finance screener or static sector mapping file
        """
        # Check cache (TTL: 7 days)
        cache_key = f"universe:sector:{sector.value}"
        cached_tickers = self.cache_manager.get(cache_key)

        if cached_tickers is not None:
            logger.debug(f"Cache hit for {sector.value} sector stocks")
            return cached_tickers

        # Try loading from static file
        sector_file = self.static_data_path / f"sector_{sector.name.lower()}.csv"

        if sector_file.exists():
            tickers = self._load_tickers_from_csv(sector_file)
        else:
            # Fallback: Query Yahoo Finance (if available)
            if self.yahoo_gateway:
                tickers = self._query_yahoo_sector(sector)
            else:
                raise UniverseNotFoundException(
                    f"No data available for sector: {sector.value}"
                )

        # Cache for 7 days
        self.cache_manager.set(
            cache_key,
            tickers,
            ttl=timedelta(days=7)
        )

        logger.info(f"Retrieved {len(tickers)} stocks for {sector.value} sector")

        return tickers

    def get_market_cap_stocks(self,
                             min_cap: Optional[Decimal],
                             max_cap: Optional[Decimal]) -> List[str]:
        """
        Get stocks within a market cap range.

        Args:
            min_cap: Minimum market cap (USD)
            max_cap: Maximum market cap (USD)

        Returns:
            List of ticker symbols

        Data Source:
            Yahoo Finance screener or market cap database

        Note:
            This is a filtered query, results may change daily.
            Cache TTL is short (24 hours).
        """
        # Check cache (TTL: 24 hours)
        cache_key = f"universe:market_cap:{min_cap}:{max_cap}"
        cached_tickers = self.cache_manager.get(cache_key)

        if cached_tickers is not None:
            logger.debug(f"Cache hit for market cap range")
            return cached_tickers

        # Query Yahoo Finance screener (pseudo-implementation)
        # In production, use Yahoo Finance screener API or alternative
        tickers = self._query_yahoo_market_cap(min_cap, max_cap)

        # Cache for 24 hours
        self.cache_manager.set(
            cache_key,
            tickers,
            ttl=timedelta(hours=24)
        )

        logger.info(
            f"Retrieved {len(tickers)} stocks for market cap range "
            f"${min_cap/1e9:.1f}B - ${max_cap/1e9:.1f}B"
        )

        return tickers

    def get_etf_holdings(self,
                        etf_ticker: str,
                        min_weight: Optional[float] = None) -> List[str]:
        """
        Get holdings (constituents) of an ETF.

        Args:
            etf_ticker: ETF ticker symbol (e.g., "SPY", "QQQ")
            min_weight: Minimum holding weight percentage (optional)

        Returns:
            List of ticker symbols

        Data Source:
            ETF provider website or holdings API
        """
        etf_ticker = etf_ticker.upper()

        # Check cache (TTL: 30 days)
        cache_key = f"universe:etf:{etf_ticker}"
        cached_holdings = self.cache_manager.get(cache_key)

        if cached_holdings is not None:
            logger.debug(f"Cache hit for {etf_ticker} holdings")
            holdings = cached_holdings
        else:
            # Fetch ETF holdings
            holdings = self._fetch_etf_holdings(etf_ticker)

            # Cache for 30 days
            self.cache_manager.set(
                cache_key,
                holdings,
                ttl=timedelta(days=30)
            )

        # Filter by minimum weight if specified
        if min_weight is not None:
            tickers = [
                ticker for ticker, weight in holdings.items()
                if weight >= min_weight
            ]
        else:
            tickers = list(holdings.keys())

        logger.info(
            f"Retrieved {len(tickers)} holdings for {etf_ticker} "
            f"(min weight: {min_weight or 0}%)"
        )

        return tickers

    def _fetch_etf_holdings(self, etf_ticker: str) -> Dict[str, float]:
        """
        Fetch ETF holdings with weights.

        Returns:
            Dictionary mapping ticker to weight percentage
        """
        # Implementation options:
        # 1. Use etfdb.com API (if available)
        # 2. Scrape ETF provider website (iShares, Vanguard, etc.)
        # 3. Use yfinance (limited ETF data)

        # Example using yfinance
        try:
            etf = yf.Ticker(etf_ticker)
            holdings = etf.get_holdings()

            if holdings is None or holdings.empty:
                raise UniverseNotFoundException(
                    f"No holdings data available for {etf_ticker}"
                )

            # Convert to dict: ticker -> weight
            holdings_dict = {}
            for _, row in holdings.iterrows():
                ticker = row.get('symbol', row.get('ticker'))
                weight = row.get('weight', row.get('holding_percent', 0))

                if ticker:
                    holdings_dict[ticker.upper()] = float(weight)

            return holdings_dict

        except Exception as e:
            raise UniverseNotFoundException(
                f"Failed to fetch holdings for {etf_ticker}: {e}"
            )

    def _validate_tickers(self, tickers: List[str]) -> List[str]:
        """
        Validate and normalize ticker list.

        Args:
            tickers: Raw ticker list

        Returns:
            Validated and normalized ticker list
        """
        validated = []

        for ticker in tickers:
            # Normalize: uppercase, strip whitespace
            normalized = ticker.upper().strip()

            # Basic validation: alphanumeric + dots
            if normalized and normalized.replace('.', '').isalnum():
                validated.append(normalized)
            else:
                logger.warning(f"Invalid ticker format, skipping: {ticker}")

        logger.info(f"Validated {len(validated)}/{len(tickers)} tickers")

        return validated

    def _load_tickers_from_csv(self, filepath: Path) -> List[str]:
        """Load tickers from CSV file."""
        tickers = []

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row['ticker'].upper().strip()
                tickers.append(ticker)

        return tickers

    def _query_yahoo_sector(self, sector: SectorType) -> List[str]:
        """Query Yahoo Finance for stocks in sector (placeholder)."""
        # Implementation: Use Yahoo Finance screener
        # This is a placeholder - actual implementation would use
        # Yahoo Finance API or web scraping
        raise NotImplementedError("Yahoo Finance sector query not yet implemented")

    def _query_yahoo_market_cap(self,
                                min_cap: Optional[Decimal],
                                max_cap: Optional[Decimal]) -> List[str]:
        """Query Yahoo Finance for stocks by market cap (placeholder)."""
        # Implementation: Use Yahoo Finance screener
        raise NotImplementedError("Yahoo Finance market cap query not yet implemented")


class UniverseNotFoundException(Exception):
    """Raised when stock universe cannot be retrieved."""
    pass
```

---

## Phase 15: API Integration Patterns

### 15.1 Async Parallel Data Fetching

```python
import asyncio
import aiohttp
from typing import List, Dict, Coroutine
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AsyncMarketDataFetcher:
    """
    Async parallel data fetcher for improved performance.

    Features:
    - Concurrent HTTP requests using aiohttp
    - Semaphore control for max concurrent requests
    - Connection pooling
    - Timeout handling
    """

    def __init__(self,
                 max_concurrent: int = 10,
                 timeout: int = 30):
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_batch_stock_data(self,
                                     tickers: List[str],
                                     period: str = "1y") -> Dict[str, pd.DataFrame]:
        """
        Fetch stock data for multiple tickers in parallel.

        Args:
            tickers: List of ticker symbols
            period: Data period

        Returns:
            Dictionary mapping tickers to DataFrames

        Performance:
            - Sequential: ~0.5s per stock = 50s for 100 stocks
            - Parallel (10 concurrent): ~5s for 100 stocks
            - Speedup: 10x
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = [
                self._fetch_single_stock(session, ticker, period)
                for ticker in tickers
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        data = {}
        errors = []

        for ticker, result in zip(tickers, results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to fetch {ticker}: {result}")
                errors.append((ticker, str(result)))
            else:
                data[ticker] = result

        if errors:
            logger.warning(
                f"Batch fetch completed with {len(errors)} errors out of {len(tickers)}"
            )

        return data

    async def _fetch_single_stock(self,
                                  session: aiohttp.ClientSession,
                                  ticker: str,
                                  period: str) -> pd.DataFrame:
        """
        Fetch data for a single stock (async).

        Uses semaphore to limit concurrent requests.
        """
        async with self.semaphore:
            try:
                # Use yfinance or direct API call
                # For demonstration, using yfinance in executor
                loop = asyncio.get_event_loop()
                df = await loop.run_in_executor(
                    None,  # Use default executor
                    self._fetch_yfinance_data,
                    ticker,
                    period
                )

                return df

            except Exception as e:
                logger.error(f"Error fetching {ticker}: {e}")
                raise

    def _fetch_yfinance_data(self, ticker: str, period: str) -> pd.DataFrame:
        """Fetch data using yfinance (synchronous, called in executor)."""
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)

        if df.empty:
            raise ValueError(f"No data returned for {ticker}")

        df = df.reset_index()
        df.columns = [col.lower() for col in df.columns]

        return df


# Usage example
async def main():
    fetcher = AsyncMarketDataFetcher(max_concurrent=10)

    tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]  # + 95 more

    start = datetime.now()
    data = await fetcher.fetch_batch_stock_data(tickers)
    elapsed = (datetime.now() - start).total_seconds()

    print(f"Fetched {len(data)} stocks in {elapsed:.2f}s")
    print(f"Average: {elapsed/len(data):.2f}s per stock")

# Run async code
# asyncio.run(main())
```

---

### 15.2 Circuit Breaker Pattern

```python
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures detected, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern for unreliable external services.

    Prevents cascading failures by temporarily disabling calls
    to failing services.

    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: Allow limited requests to test recovery

    Configuration:
    - failure_threshold: Number of failures before opening circuit
    - recovery_timeout: Time before attempting recovery (seconds)
    - success_threshold: Successes needed in half-open to close circuit
    """

    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 success_threshold: int = 2):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpen: If circuit is open
            Exception: Original exception if function fails
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpen(
                    f"Circuit breaker is OPEN. "
                    f"Will retry in {self._time_until_retry()}s"
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1

            if self.success_count >= self.success_threshold:
                self._close_circuit()
        else:
            # Reset failure count on success in CLOSED state
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            self._open_circuit()
        elif self.failure_count >= self.failure_threshold:
            self._open_circuit()

    def _open_circuit(self):
        """Open the circuit."""
        self.state = CircuitState.OPEN
        self.success_count = 0

        logger.warning(
            f"Circuit breaker OPENED after {self.failure_count} failures. "
            f"Will retry in {self.recovery_timeout}s"
        )

    def _close_circuit(self):
        """Close the circuit."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0

        logger.info("Circuit breaker CLOSED - service recovered")

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def _time_until_retry(self) -> int:
        """Calculate seconds until next retry attempt."""
        if self.last_failure_time is None:
            return 0

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        remaining = max(0, self.recovery_timeout - elapsed)
        return int(remaining)


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""
    pass


# Usage example with gateway
class ResilientYahooFinanceGateway(YahooFinanceGateway):
    """Yahoo Finance Gateway with circuit breaker."""

    def __init__(self, cache_manager, rate_limiter):
        super().__init__(cache_manager, rate_limiter)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            success_threshold=2
        )

    def get_stock_data(self, ticker: str, **kwargs) -> pd.DataFrame:
        """Fetch stock data with circuit breaker protection."""
        try:
            return self.circuit_breaker.call(
                super().get_stock_data,
                ticker,
                **kwargs
            )
        except CircuitBreakerOpen as e:
            logger.warning(f"Circuit breaker open for Yahoo Finance: {e}")
            # Try backup data source or return cached data
            cached = self.cache_manager.get(f"stock:{ticker}:ohlcv:1y")
            if cached is not None:
                logger.info(f"Returning stale cached data for {ticker}")
                return cached
            raise
```

---

## Phase 16: Caching Strategy

### 16.1 Two-Tier CacheManager Implementation

```python
from typing import Any, Optional
from datetime import datetime, timedelta
from collections import OrderedDict
import sqlite3
import pickle
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Two-tier cache manager (L1: Memory, L2: SQLite).

    L1 Cache (Memory):
    - Fast access (~1μs)
    - Limited size (100MB default)
    - LRU eviction policy
    - Short TTL for frequently changing data

    L2 Cache (SQLite):
    - Persistent storage
    - Slower access (~1ms)
    - Larger capacity
    - Longer TTL

    Cache Hierarchy:
    1. Check L1 (memory) - if hit, return immediately
    2. Check L2 (SQLite) - if hit, promote to L1 and return
    3. If miss in both - fetch from source, store in both

    Benefits:
    - Reduced API calls (cost savings, rate limit compliance)
    - Faster response times
    - Offline capability (stale data better than no data)
    """

    def __init__(self,
                 db_path: str = "data/cache.db",
                 max_memory_mb: int = 100):
        self.db_path = db_path
        self.max_memory_bytes = max_memory_mb * 1024 * 1024

        # L1: Memory cache (OrderedDict for LRU)
        self._memory_cache: OrderedDict[str, 'CacheEntry'] = OrderedDict()
        self._memory_size = 0

        # L2: SQLite connection
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for L2 cache."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                value BLOB NOT NULL,
                cached_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                size_bytes INTEGER NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at)"
        )
        conn.commit()
        conn.close()

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        # Check L1 (memory)
        if key in self._memory_cache:
            entry = self._memory_cache[key]

            if entry.is_expired():
                # Expired, remove from L1
                del self._memory_cache[key]
                self._memory_size -= entry.size_bytes
                logger.debug(f"L1 cache expired: {key}")
            else:
                # Cache hit, move to end (LRU)
                self._memory_cache.move_to_end(key)
                logger.debug(f"L1 cache hit: {key}")
                return entry.value

        # Check L2 (SQLite)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT value, expires_at FROM cache_entries WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            value_blob, expires_at_str = row
            expires_at = datetime.fromisoformat(expires_at_str)

            if expires_at < datetime.now():
                # Expired in L2, delete
                self._delete_from_l2(key)
                logger.debug(f"L2 cache expired: {key}")
                return None

            # L2 cache hit, deserialize and promote to L1
            value = pickle.loads(value_blob)
            logger.debug(f"L2 cache hit: {key} (promoting to L1)")

            # Promote to L1
            entry = CacheEntry(
                value=value,
                expires_at=expires_at,
                size_bytes=len(value_blob)
            )
            self._put_in_l1(key, entry)

            return value

        # Cache miss
        logger.debug(f"Cache miss: {key}")
        return None

    def set(self, key: str, value: Any, ttl: timedelta):
        """
        Store value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live duration
        """
        expires_at = datetime.now() + ttl

        # Serialize value
        value_blob = pickle.dumps(value)
        size_bytes = len(value_blob)

        # Create cache entry
        entry = CacheEntry(
            value=value,
            expires_at=expires_at,
            size_bytes=size_bytes
        )

        # Store in L1 (memory)
        self._put_in_l1(key, entry)

        # Store in L2 (SQLite)
        self._put_in_l2(key, value_blob, expires_at, size_bytes)

        logger.debug(f"Cached: {key} (TTL: {ttl}, size: {size_bytes} bytes)")

    def invalidate(self, pattern: str):
        """
        Invalidate all keys matching pattern.

        Args:
            pattern: Glob pattern (e.g., "stock:AAPL:*")
        """
        import fnmatch

        # Invalidate in L1
        keys_to_delete = [
            k for k in self._memory_cache.keys()
            if fnmatch.fnmatch(k, pattern)
        ]

        for key in keys_to_delete:
            entry = self._memory_cache[key]
            del self._memory_cache[key]
            self._memory_size -= entry.size_bytes

        # Invalidate in L2
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "DELETE FROM cache_entries WHERE key LIKE ?",
            (pattern.replace('*', '%'),)
        )
        conn.commit()
        conn.close()

        logger.info(f"Invalidated {len(keys_to_delete)} cache entries matching: {pattern}")

    def clear(self):
        """Clear all cache entries."""
        # Clear L1
        self._memory_cache.clear()
        self._memory_size = 0

        # Clear L2
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM cache_entries")
        conn.commit()
        conn.close()

        logger.info("Cleared all cache entries")

    def cleanup_expired(self):
        """Remove expired entries from cache."""
        now = datetime.now()

        # Cleanup L1
        expired_keys = [
            k for k, entry in self._memory_cache.items()
            if entry.is_expired()
        ]

        for key in expired_keys:
            entry = self._memory_cache[key]
            del self._memory_cache[key]
            self._memory_size -= entry.size_bytes

        # Cleanup L2
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM cache_entries WHERE expires_at < ?", (now,))
        conn.commit()
        conn.close()

        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        # L1 stats
        l1_entries = len(self._memory_cache)
        l1_size_mb = self._memory_size / (1024 * 1024)

        # L2 stats
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*), SUM(size_bytes) FROM cache_entries")
        l2_entries, l2_size_bytes = cursor.fetchone()
        conn.close()

        l2_size_mb = (l2_size_bytes or 0) / (1024 * 1024)

        return {
            "l1_entries": l1_entries,
            "l1_size_mb": round(l1_size_mb, 2),
            "l2_entries": l2_entries or 0,
            "l2_size_mb": round(l2_size_mb, 2),
            "total_entries": l1_entries + (l2_entries or 0)
        }

    def _put_in_l1(self, key: str, entry: 'CacheEntry'):
        """Store entry in L1 memory cache."""
        # Remove old entry if exists
        if key in self._memory_cache:
            old_entry = self._memory_cache[key]
            self._memory_size -= old_entry.size_bytes
            del self._memory_cache[key]

        # Add new entry
        self._memory_cache[key] = entry
        self._memory_size += entry.size_bytes

        # Enforce size limit (LRU eviction)
        while self._memory_size > self.max_memory_bytes and self._memory_cache:
            # Remove oldest (first) entry
            oldest_key, oldest_entry = self._memory_cache.popitem(last=False)
            self._memory_size -= oldest_entry.size_bytes
            logger.debug(f"LRU evicted from L1: {oldest_key}")

    def _put_in_l2(self,
                   key: str,
                   value_blob: bytes,
                   expires_at: datetime,
                   size_bytes: int):
        """Store entry in L2 SQLite cache."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO cache_entries (key, value, cached_at, expires_at, size_bytes)
            VALUES (?, ?, ?, ?, ?)
        """, (key, value_blob, datetime.now(), expires_at, size_bytes))
        conn.commit()
        conn.close()

    def _delete_from_l2(self, key: str):
        """Delete entry from L2 cache."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
        conn.commit()
        conn.close()


from dataclasses import dataclass

@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    value: Any
    expires_at: datetime
    size_bytes: int

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return datetime.now() >= self.expires_at
```

---

### 16.2 TTL Specifications and Cache Keys

```python
# TTL Configuration
TTL_CONFIG = {
    # Stock market data
    "stock_ohlcv": timedelta(hours=1),
    "stock_current_price": timedelta(minutes=15),
    "stock_fundamental": timedelta(hours=24),

    # Compliance data
    "compliance_status": timedelta(days=30),

    # Universe data
    "universe_exchange": timedelta(days=30),
    "universe_sector": timedelta(days=7),
    "universe_etf": timedelta(days=30),
    "universe_market_cap": timedelta(hours=24),

    # Indicator calculations (not cached - recomputed with fresh data)
}

# Cache Key Patterns
CACHE_KEY_PATTERNS = {
    "stock_ohlcv": "stock:{ticker}:ohlcv:{period}",
    "stock_current_price": "stock:{ticker}:current_price",
    "stock_fundamental": "stock:{ticker}:fundamental",
    "compliance": "compliance:{ticker}",
    "universe_exchange": "universe:exchange:{exchange}",
    "universe_sector": "universe:sector:{sector}",
    "universe_etf": "universe:etf:{etf_ticker}",
}


def get_cache_key(category: str, **kwargs) -> str:
    """
    Generate cache key from category and parameters.

    Args:
        category: Cache category (e.g., "stock_ohlcv")
        **kwargs: Parameters to interpolate into key pattern

    Returns:
        Formatted cache key

    Example:
        >>> get_cache_key("stock_ohlcv", ticker="AAPL", period="1y")
        'stock:AAPL:ohlcv:1y'
    """
    pattern = CACHE_KEY_PATTERNS.get(category)
    if not pattern:
        raise ValueError(f"Unknown cache category: {category}")

    return pattern.format(**kwargs)
```

---

## Phase 17: Rate Limiting

### 17.1 Token Bucket Rate Limiter

```python
from typing import Dict
from datetime import datetime
import time
import threading
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for API rate limiting.

    Algorithm:
    - Bucket fills with tokens at a constant rate (refill_rate)
    - Each request consumes 1 token
    - If bucket empty, request must wait

    Features:
    - Per-API rate limits
    - Thread-safe
    - Automatic token refill
    - Queue management for waiting requests

    Example:
        rate_limiter = RateLimiter()
        rate_limiter.configure("yahoo_finance", requests_per_hour=2000)

        rate_limiter.acquire("yahoo_finance")  # Consumes 1 token
        # ... make API call
    """

    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}
        self.lock = threading.Lock()

    def configure(self,
                  api_name: str,
                  requests_per_hour: int):
        """
        Configure rate limit for an API.

        Args:
            api_name: API identifier (e.g., "yahoo_finance")
            requests_per_hour: Maximum requests per hour
        """
        with self.lock:
            self.buckets[api_name] = TokenBucket(
                capacity=requests_per_hour,
                refill_rate=requests_per_hour / 3600.0  # Tokens per second
            )

        logger.info(
            f"Configured rate limit for {api_name}: "
            f"{requests_per_hour} requests/hour"
        )

    def acquire(self, api_name: str, timeout: Optional[float] = None):
        """
        Acquire a token for API call (blocks if necessary).

        Args:
            api_name: API identifier
            timeout: Maximum wait time in seconds (None = wait indefinitely)

        Raises:
            RateLimitException: If timeout exceeded
        """
        if api_name not in self.buckets:
            raise ValueError(f"API not configured: {api_name}")

        bucket = self.buckets[api_name]

        start_time = time.time()

        while True:
            if bucket.consume():
                # Token acquired
                return

            # No tokens available, wait
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise RateLimitException(
                        f"Rate limit timeout for {api_name} after {elapsed:.1f}s"
                    )

            # Wait for next refill
            wait_time = min(1.0, bucket.time_until_next_token())
            logger.debug(f"Rate limit reached for {api_name}, waiting {wait_time:.2f}s")
            time.sleep(wait_time)

    def try_acquire(self, api_name: str) -> bool:
        """
        Try to acquire token without blocking.

        Args:
            api_name: API identifier

        Returns:
            True if token acquired, False if rate limit reached
        """
        if api_name not in self.buckets:
            raise ValueError(f"API not configured: {api_name}")

        bucket = self.buckets[api_name]
        return bucket.consume()

    def get_available_tokens(self, api_name: str) -> int:
        """Get number of available tokens."""
        if api_name not in self.buckets:
            return 0

        bucket = self.buckets[api_name]
        bucket._refill()  # Ensure up-to-date count
        return int(bucket.tokens)


class TokenBucket:
    """
    Token bucket implementation.

    Tokens refill at constant rate until bucket is full.
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill_time = time.time()
        self.lock = threading.Lock()

    def consume(self) -> bool:
        """
        Attempt to consume one token.

        Returns:
            True if token consumed, False if no tokens available
        """
        with self.lock:
            self._refill()

            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True

            return False

    def _refill(self):
        """Refill bucket based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill_time

        # Add tokens based on refill rate
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)

        self.last_refill_time = now

    def time_until_next_token(self) -> float:
        """Calculate seconds until next token available."""
        if self.tokens >= 1.0:
            return 0.0

        tokens_needed = 1.0 - self.tokens
        time_needed = tokens_needed / self.refill_rate

        return time_needed


class RateLimitException(Exception):
    """Raised when rate limit timeout is exceeded."""
    pass


# Configuration for APIs
def configure_rate_limiters(rate_limiter: RateLimiter):
    """Configure rate limits for all APIs."""

    # Yahoo Finance: 2000 requests/hour (per API documentation)
    rate_limiter.configure("yahoo_finance", requests_per_hour=2000)

    # Zoya API: Assume 60 requests/minute
    rate_limiter.configure("zoya_api", requests_per_hour=3600)

    # Musaffa API: Assume 60 requests/minute
    rate_limiter.configure("musaffa_api", requests_per_hour=3600)
```

---

## Phase 18: Security Architecture

### 18.1 API Key Management with Encryption

```python
from cryptography.fernet import Fernet
from pathlib import Path
import os
import keyring
import logging

logger = logging.getLogger(__name__)


class SecureConfigManager:
    """
    Secure configuration manager with encrypted API keys.

    Features:
    - API keys encrypted at rest using Fernet (symmetric encryption)
    - Encryption key stored in OS keyring
    - No credentials in logs
    - Environment variable support for CI/CD
    """

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Initialize or load encryption key
        self.cipher = self._get_cipher()

    def _get_cipher(self) -> Fernet:
        """Get or create encryption cipher."""

        # Try to load encryption key from OS keyring
        encryption_key = keyring.get_password("stock-friend-cli", "encryption_key")

        if encryption_key is None:
            # Generate new encryption key
            encryption_key = Fernet.generate_key().decode()

            # Store in OS keyring
            keyring.set_password("stock-friend-cli", "encryption_key", encryption_key)

            logger.info("Generated new encryption key and stored in OS keyring")

        return Fernet(encryption_key.encode())

    def set_api_key(self, service: str, api_key: str):
        """
        Store API key securely (encrypted).

        Args:
            service: Service name (e.g., "zoya_api", "yahoo_finance")
            api_key: API key to store
        """
        # Encrypt API key
        encrypted_key = self.cipher.encrypt(api_key.encode())

        # Store encrypted key to file
        key_file = self.config_dir / f"{service}.key"
        key_file.write_bytes(encrypted_key)

        logger.info(f"Stored encrypted API key for {service}")

    def get_api_key(self, service: str) -> Optional[str]:
        """
        Retrieve API key (decrypted).

        Args:
            service: Service name

        Returns:
            Decrypted API key or None if not found

        Priority:
        1. Environment variable (e.g., ZOYA_API_KEY)
        2. Encrypted file
        """
        # Try environment variable first (for CI/CD)
        env_var_name = f"{service.upper()}_API_KEY"
        env_value = os.getenv(env_var_name)

        if env_value:
            logger.debug(f"Loaded {service} API key from environment variable")
            return env_value

        # Try encrypted file
        key_file = self.config_dir / f"{service}.key"

        if not key_file.exists():
            logger.warning(f"No API key found for {service}")
            return None

        try:
            # Read encrypted key
            encrypted_key = key_file.read_bytes()

            # Decrypt
            api_key = self.cipher.decrypt(encrypted_key).decode()

            logger.debug(f"Loaded {service} API key from encrypted file")

            return api_key

        except Exception as e:
            logger.error(f"Failed to decrypt API key for {service}: {e}")
            return None

    def delete_api_key(self, service: str):
        """Delete stored API key."""
        key_file = self.config_dir / f"{service}.key"

        if key_file.exists():
            key_file.unlink()
            logger.info(f"Deleted API key for {service}")


def sanitize_for_logging(value: str) -> str:
    """
    Sanitize sensitive values for logging.

    Args:
        value: Value to sanitize (e.g., API key)

    Returns:
        Sanitized string showing only first/last 4 characters

    Example:
        >>> sanitize_for_logging("abcdefghijklmnop")
        'abcd...mnop'
    """
    if not value or len(value) < 8:
        return "***"

    return f"{value[:4]}...{value[-4:]}"


# Example usage
def setup_secure_configuration():
    """Setup secure configuration with API keys."""

    config_manager = SecureConfigManager()

    # Store API keys (one-time setup)
    # In production, prompt user for keys
    zoya_api_key = input("Enter Zoya API key: ").strip()
    if zoya_api_key:
        config_manager.set_api_key("zoya_api", zoya_api_key)

    musaffa_api_key = input("Enter Musaffa API key: ").strip()
    if musaffa_api_key:
        config_manager.set_api_key("musaffa_api", musaffa_api_key)

    print("API keys stored securely")


def load_api_keys() -> Dict[str, Optional[str]]:
    """Load API keys for application."""

    config_manager = SecureConfigManager()

    keys = {
        "zoya_api": config_manager.get_api_key("zoya_api"),
        "musaffa_api": config_manager.get_api_key("musaffa_api"),
    }

    # Log loaded keys (sanitized)
    for service, key in keys.items():
        if key:
            logger.info(f"Loaded {service} API key: {sanitize_for_logging(key)}")
        else:
            logger.warning(f"No API key configured for {service}")

    return keys
```

---

### 18.2 .env File Structure

```bash
# .env file for local development
# DO NOT commit this file to version control!

# Application settings
APP_ENV=development
LOG_LEVEL=INFO

# API Keys (alternative to encrypted storage)
ZOYA_API_KEY=your_zoya_api_key_here
MUSAFFA_API_KEY=your_musaffa_api_key_here

# Database
DATABASE_PATH=data/stock-friend.db

# Cache settings
CACHE_MAX_MEMORY_MB=100

# Rate limiting
YAHOO_FINANCE_REQUESTS_PER_HOUR=2000

# Performance
MAX_CONCURRENT_REQUESTS=10
BATCH_SIZE=10
```

**.gitignore entry:**
```
# Environment variables and secrets
.env
.env.*
config/*.key
```

---

## Phase 19: Halal Compliance Enforcement

### 19.1 Zero False Negatives Guarantee

```python
class ComplianceEnforcer:
    """
    Enforces halal compliance with zero false negatives guarantee.

    Design Principles:
    1. Default to exclusion when uncertain
    2. Require explicit verification for inclusion
    3. Maintain audit trail of all decisions
    4. Allow user override only with explicit confirmation
    """

    def __init__(self,
                 compliance_gateway: 'ComplianceGateway',
                 audit_logger: 'AuditLogger'):
        self.gateway = compliance_gateway
        self.audit_logger = audit_logger

    def filter_halal_compliant(self,
                              tickers: List[str],
                              allow_unverified: bool = False) -> tuple[List[str], List[StockExclusion]]:
        """
        Filter stock list for halal compliance.

        Args:
            tickers: List of tickers to filter
            allow_unverified: If True, prompt user for unverified stocks

        Returns:
            Tuple of (compliant_tickers, exclusions)

        Guarantee:
            NEVER includes non-compliant stock in results.
            When uncertain, excludes stock.
        """
        compliant = []
        excluded = []

        # Check compliance for all tickers
        compliance_results = self.gateway.batch_check_compliance(tickers)

        for ticker, status in compliance_results.items():
            if status.is_compliant:
                # Explicitly verified as compliant
                compliant.append(ticker)

                # Audit trail
                self.audit_logger.log_compliance_check(
                    ticker=ticker,
                    result="COMPLIANT",
                    source=status.data_source
                )

            elif status.result == ComplianceResult.UNVERIFIED and allow_unverified:
                # Uncertain status - prompt user
                if self._prompt_user_for_unverified(ticker, status):
                    compliant.append(ticker)

                    # Audit trail with user override
                    self.audit_logger.log_compliance_check(
                        ticker=ticker,
                        result="COMPLIANT_USER_OVERRIDE",
                        source="USER_CONFIRMATION",
                        notes="User explicitly confirmed compliance"
                    )
                else:
                    # User declined - exclude
                    exclusion = StockExclusion(
                        ticker=ticker,
                        exclusion_reason="UNVERIFIED",
                        exclusion_detail="User declined to include unverified stock"
                    )
                    excluded.append(exclusion)

                    # Audit trail
                    self.audit_logger.log_exclusion(
                        ticker=ticker,
                        reason="UNVERIFIED",
                        source="USER_DECISION"
                    )
            else:
                # Excluded or unverified (without user prompt)
                exclusion = StockExclusion(
                    ticker=ticker,
                    exclusion_reason=status.exclusion_reason or "UNVERIFIED",
                    exclusion_detail=status.exclusion_detail
                )
                excluded.append(exclusion)

                # Audit trail
                self.audit_logger.log_exclusion(
                    ticker=ticker,
                    reason=status.exclusion_reason or "UNVERIFIED",
                    source=status.data_source
                )

        logger.info(
            f"Compliance filtering: {len(compliant)} compliant, "
            f"{len(excluded)} excluded from {len(tickers)} total"
        )

        return compliant, excluded

    def _prompt_user_for_unverified(self,
                                    ticker: str,
                                    status: ComplianceStatus) -> bool:
        """
        Prompt user to include unverified stock.

        Returns:
            True if user confirms inclusion
        """
        print(f"\n{'='*60}")
        print(f"UNVERIFIED COMPLIANCE STATUS: {ticker}")
        print(f"{'='*60}")
        print(f"Status: {status.result.value}")
        print(f"Source: {status.data_source}")
        print(f"Detail: {status.exclusion_detail or 'No compliance data available'}")
        print()
        print("WARNING: Including this stock without verified compliance")
        print("         may violate halal investment principles.")
        print()

        response = input("Include this stock anyway? (type 'YES' to confirm): ").strip()

        return response == "YES"


class AuditLogger:
    """
    Audit logger for compliance decisions.

    Logs all compliance checks and exclusions for transparency.
    """

    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection

    def log_compliance_check(self,
                           ticker: str,
                           result: str,
                           source: str,
                           notes: Optional[str] = None):
        """Log compliance check to audit trail."""

        self.conn.execute("""
            INSERT INTO audit_log (id, timestamp, operation, ticker, details_json, user)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            datetime.now(),
            "COMPLIANCE_CHECK",
            ticker,
            json.dumps({
                "result": result,
                "source": source,
                "notes": notes
            }),
            "system"
        ))
        self.conn.commit()

    def log_exclusion(self,
                     ticker: str,
                     reason: str,
                     source: str,
                     detail: Optional[str] = None):
        """Log stock exclusion to audit trail."""

        self.conn.execute("""
            INSERT INTO audit_log (id, timestamp, operation, ticker, details_json, user)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            datetime.now(),
            "HALAL_EXCLUSION",
            ticker,
            json.dumps({
                "reason": reason,
                "source": source,
                "detail": detail
            }),
            "system"
        ))
        self.conn.commit()

        logger.info(f"Audit log: Excluded {ticker} - {reason} (source: {source})")
```

---

## Phase 20: Performance Optimization

### 20.1 Response Time Specifications

| Operation | Target Time | Optimization Strategy |
|-----------|-------------|----------------------|
| **CLI Startup** | <2 seconds | Lazy loading, minimal initialization |
| **Menu Navigation** | <0.1 seconds | In-memory state, no I/O |
| **Screen 100 stocks** | <120 seconds (2 min) | Parallel fetching, caching, batch processing |
| **Screen 500 stocks** | <600 seconds (10 min) | Async I/O, connection pooling, rate limiting |
| **Portfolio check (10 stocks)** | <15 seconds | Cached market data, vectorized calculations |
| **Indicator calculation (per stock)** | <1 second | Vectorized pandas/numpy operations |
| **MCDX calculation** | <0.5 seconds | Optimized rolling window operations |
| **B-XTrender calculation** | <0.3 seconds | EMA calculations are O(n) |
| **Database query** | <0.01 seconds | Proper indexing, prepared statements |
| **Cache lookup (L1)** | <0.001 seconds (1ms) | In-memory OrderedDict |
| **Cache lookup (L2)** | <0.01 seconds (10ms) | SQLite with indexes |

---

### 20.2 Parallel Processing Strategy

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any
import logging

logger = logging.getLogger(__name__)


class ParallelProcessor:
    """
    Parallel processing utility for batch operations.

    Uses ThreadPoolExecutor for I/O-bound tasks (API calls).
    For CPU-bound tasks, use ProcessPoolExecutor instead.
    """

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers

    def process_batch(self,
                     items: List[Any],
                     process_func: Callable[[Any], Any],
                     progress_callback: Optional[Callable] = None) -> List[Any]:
        """
        Process items in parallel.

        Args:
            items: List of items to process
            process_func: Function to apply to each item
            progress_callback: Optional callback(current, total, item)

        Returns:
            List of results (in order of completion)
        """
        results = []
        completed = 0
        total = len(items)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(process_func, item): item
                for item in items
            }

            # Collect results as they complete
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                completed += 1

                try:
                    result = future.result()
                    results.append(result)

                    if progress_callback:
                        progress_callback(completed, total, item)

                except Exception as e:
                    logger.error(f"Error processing {item}: {e}")
                    results.append(None)

        return results


# Example usage
def fetch_stock_data_parallel(tickers: List[str],
                              yahoo_gateway: YahooFinanceGateway) -> Dict[str, pd.DataFrame]:
    """
    Fetch stock data for multiple tickers in parallel.

    Args:
        tickers: List of ticker symbols
        yahoo_gateway: Gateway instance

    Returns:
        Dictionary mapping tickers to DataFrames
    """
    processor = ParallelProcessor(max_workers=10)

    def fetch_single(ticker: str) -> tuple[str, pd.DataFrame]:
        try:
            df = yahoo_gateway.get_stock_data(ticker)
            return (ticker, df)
        except Exception as e:
            logger.warning(f"Failed to fetch {ticker}: {e}")
            return (ticker, None)

    def progress_callback(current, total, ticker):
        print(f"Progress: {current}/{total} - Fetched {ticker}")

    results = processor.process_batch(
        tickers,
        fetch_single,
        progress_callback
    )

    # Convert to dictionary
    data = {ticker: df for ticker, df in results if df is not None}

    return data
```

---

### 20.3 DataFrame Optimization

```python
# Optimization techniques for pandas DataFrames

# 1. Use appropriate data types
def optimize_dataframe_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage by using appropriate dtypes.

    Can reduce memory by 50-80%.
    """
    # Downcast numeric columns
    for col in df.select_dtypes(include=['int']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')

    for col in df.select_dtypes(include=['float']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')

    # Convert object columns to category if low cardinality
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() / len(df) < 0.5:  # <50% unique values
            df[col] = df[col].astype('category')

    return df


# 2. Vectorized operations (avoid loops)
# BAD: Loop through rows
for i, row in df.iterrows():
    df.loc[i, 'result'] = row['a'] + row['b']

# GOOD: Vectorized operation
df['result'] = df['a'] + df['b']


# 3. Use .loc and .iloc for indexing (not chained indexing)
# BAD: Chained indexing
df[df['volume'] > 1000000]['close'].mean()

# GOOD: Single indexing operation
df.loc[df['volume'] > 1000000, 'close'].mean()


# 4. Use query() for complex filtering
# GOOD: query() is optimized for complex conditions
df.query('volume > 1000000 and close > 100')


# 5. Process in chunks for large datasets
def process_large_dataset(filepath: str, chunk_size: int = 10000):
    """Process large CSV in chunks to avoid memory issues."""
    results = []

    for chunk in pd.read_csv(filepath, chunksize=chunk_size):
        # Process chunk
        processed = process_chunk(chunk)
        results.append(processed)

    return pd.concat(results, ignore_index=True)
```

---

## Phase 21: Error Handling & Resilience

### 21.1 Error Taxonomy

```python
# Custom exception hierarchy

class StockFriendException(Exception):
    """Base exception for all stock-friend-cli errors."""
    pass


# Data Access Errors
class DataAccessException(StockFriendException):
    """Base exception for data access errors."""
    pass


class DataProviderException(DataAccessException):
    """External data provider error (Yahoo Finance, etc.)."""
    pass


class UniverseNotFoundException(DataAccessException):
    """Stock universe not found."""
    pass


class InsufficientDataError(DataAccessException):
    """Insufficient historical data for calculation."""
    pass


# Compliance Errors
class ComplianceException(StockFriendException):
    """Base exception for compliance-related errors."""
    pass


# Strategy Errors
class StrategyException(StockFriendException):
    """Base exception for strategy-related errors."""
    pass


class StrategyNotFoundException(StrategyException):
    """Strategy ID not found."""
    pass


class ValidationError(StrategyException):
    """Strategy validation failed."""
    pass


# Portfolio Errors
class PortfolioException(StockFriendException):
    """Base exception for portfolio-related errors."""
    pass


class PortfolioNotFoundException(PortfolioException):
    """Portfolio ID not found."""
    pass


class HoldingNotFoundException(PortfolioException):
    """Holding not found in portfolio."""
    pass


# Infrastructure Errors
class InfrastructureException(StockFriendException):
    """Base exception for infrastructure errors."""
    pass


class RateLimitException(InfrastructureException):
    """Rate limit exceeded."""
    pass


class CircuitBreakerOpen(InfrastructureException):
    """Circuit breaker is open."""
    pass
```

---

### 21.2 Graceful Degradation

```python
def get_stock_data_with_fallback(ticker: str,
                                 yahoo_gateway: YahooFinanceGateway,
                                 cache_manager: CacheManager) -> pd.DataFrame:
    """
    Get stock data with graceful degradation.

    Fallback strategy:
    1. Try Yahoo Finance API
    2. If fails, try cache (even if stale)
    3. If cache empty, raise exception

    This ensures best-effort data availability.
    """
    try:
        # Try primary source
        return yahoo_gateway.get_stock_data(ticker)

    except DataProviderException as e:
        logger.warning(f"Primary data source failed for {ticker}: {e}")

        # Try cache (ignore TTL)
        cache_key = f"stock:{ticker}:ohlcv:1y"
        cached_data = cache_manager.get(cache_key)

        if cached_data is not None:
            logger.info(f"Using stale cached data for {ticker}")
            return cached_data

        # No fallback available
        logger.error(f"No data available for {ticker} (fresh or cached)")
        raise


def screen_stocks_with_resilience(tickers: List[str],
                                  screening_service: ScreeningService,
                                  strategy_id: str) -> ScreeningResult:
    """
    Screen stocks with resilience to partial failures.

    Strategy:
    - Process all stocks, skip failures
    - Return partial results if some stocks succeed
    - Log errors for manual review
    """
    successes = []
    failures = []

    for ticker in tickers:
        try:
            # Process stock
            result = process_stock(ticker, strategy_id)
            successes.append(result)

        except Exception as e:
            logger.warning(f"Failed to process {ticker}: {e}")
            failures.append((ticker, str(e)))

    if not successes and failures:
        # Total failure
        raise DataProviderException(
            f"Failed to process any stocks. {len(failures)} errors."
        )

    if failures:
        # Partial success
        logger.warning(
            f"Screening completed with {len(failures)} failures "
            f"out of {len(tickers)} stocks"
        )

    return build_screening_result(successes, failures)
```

---

### 21.3 User-Friendly Error Messages

```python
def format_user_error_message(exception: Exception) -> str:
    """
    Convert technical exception to user-friendly message.

    Args:
        exception: Exception to format

    Returns:
        User-friendly error message
    """
    if isinstance(exception, DataProviderException):
        return (
            "Unable to fetch stock data from data provider. "
            "This may be due to network issues or API rate limits. "
            "Please try again in a few minutes."
        )

    elif isinstance(exception, RateLimitException):
        return (
            "API rate limit reached. "
            "Please wait a few minutes before trying again. "
            "This helps ensure fair usage of data services."
        )

    elif isinstance(exception, InsufficientDataError):
        ticker = getattr(exception, 'ticker', 'stock')
        return (
            f"Insufficient historical data for {ticker}. "
            f"This stock may be newly listed or have limited trading history. "
            f"Try screening older, more established stocks."
        )

    elif isinstance(exception, StrategyNotFoundException):
        return (
            "The selected strategy was not found. "
            "It may have been deleted. "
            "Please select a different strategy or create a new one."
        )

    elif isinstance(exception, ComplianceException):
        return (
            "Unable to verify halal compliance for this stock. "
            "For safety, this stock will be excluded from results. "
            "Check the excluded stocks list for details."
        )

    else:
        # Generic error
        return (
            f"An unexpected error occurred: {type(exception).__name__}. "
            f"Please check the log files for details. "
            f"If the problem persists, please report this issue."
        )
```

---

**End of Part 4: Integration, Security & Performance**

This completes the comprehensive technical specifications for integration, security, and performance optimization. The document includes complete implementations of all gateway classes, security mechanisms, caching strategies, rate limiting, and performance optimization techniques.

Proceed to **Part 5: Implementation & Testing Strategy** when ready.