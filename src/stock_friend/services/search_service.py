"""
Stock search service.

Provides stock search functionality using the yfinance Search API for fast,
comprehensive ticker and company name matching across all exchanges.
"""

import contextlib
import io
import logging
import sys
from datetime import timedelta
from typing import Dict, List, Optional

from stock_friend.gateways.base import IMarketDataGateway, DataProviderException
from stock_friend.gateways.compliance.base import IComplianceGateway
from stock_friend.infrastructure.cache_manager import CacheManager
from stock_friend.models.search_models import SearchResult, StockDetailedInfo, PriceInfo
from stock_friend.models.stock_data import StockData

logger = logging.getLogger(__name__)


class SearchService:
    """
    Service for stock search operations.

    Follows Single Responsibility Principle:
    - Orchestrates search across multiple strategies
    - Delegates data fetching to gateway
    - Handles caching and error recovery

    Design Pattern: Service Layer Pattern
    """

    # Exchange suffixes for direct ticker lookup (used with exchange_hint parameter)
    EXCHANGE_SUFFIXES = [
        "",      # US default (NASDAQ/NYSE)
        ".L",    # London Stock Exchange
        ".TO",   # Toronto Stock Exchange
        ".AX",   # Australian Securities Exchange
        ".PA",   # Euronext Paris
        ".DE",   # XETRA (Germany)
        ".HK",   # Hong Kong Stock Exchange
        ".T",    # Tokyo Stock Exchange
        ".SW",   # Swiss Exchange
    ]

    def __init__(
        self,
        gateway: IMarketDataGateway,
        cache_manager: Optional[CacheManager] = None,
        compliance_gateway: Optional[IComplianceGateway] = None,
    ):
        """
        Initialize search service.

        Args:
            gateway: Market data gateway for fetching stock information
            cache_manager: Optional cache manager for search result caching
            compliance_gateway: Optional compliance gateway for halal screening
        """
        self.gateway = gateway
        self.cache_manager = cache_manager
        self.compliance_gateway = compliance_gateway
        self.logger = logger

    def search(
        self,
        query: str,
        exchange_hint: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Search for stocks by ticker symbol or company name.

        Uses yfinance Search API for fast, comprehensive matching across all exchanges.
        Supports exact ticker matches, fuzzy matching, and company name searches.

        Args:
            query: Ticker symbol or company name (e.g., "AAPL", "nvidia", "NVD.DE")
            exchange_hint: Optional exchange suffix for direct lookup (e.g., "L", "TO")

        Returns:
            List of SearchResult objects (may be empty), sorted by relevance

        Example:
            >>> service.search("AAPL")
            [SearchResult(ticker="AAPL", company_name="Apple Inc.", exchange="NASDAQ")]

            >>> service.search("nvidia")
            [SearchResult(ticker="NVDA", ...), SearchResult(ticker="NVDG.F", ...)]

            >>> service.search("BARC", exchange_hint="L")
            [SearchResult(ticker="BARC.L", company_name="Barclays PLC", exchange="LSE")]
        """
        query = query.strip().upper()

        # Check cache first
        cache_key = f"search:{query}:{exchange_hint or 'auto'}"
        if self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached:
                self.logger.info(f"Cache hit for search: {query}")
                return cached

        # Perform search based on exchange hint
        if exchange_hint:
            # User specified exchange, try only that
            ticker = self._format_ticker(query, exchange_hint)
            result = self._try_ticker(ticker)
            results = [result] if result else []
        else:
            # Use gateway's search API for comprehensive matching
            # Handles exact tickers, fuzzy matching, and company names in one call
            # Works across all exchanges without requiring manual suffix expansion

            results = self._search_with_gateway(query)

        # Cache results (15 minute TTL)
        if self.cache_manager and results:
            self.cache_manager.set(cache_key, results, ttl=timedelta(minutes=15))

        return results

    def get_detailed_info(self, ticker: str) -> StockDetailedInfo:
        """
        Fetch comprehensive stock information for display.

        Args:
            ticker: Full ticker symbol (e.g., "AAPL", "BARC.L")

        Returns:
            StockDetailedInfo with all available data

        Raises:
            DataProviderException: If data fetch fails
        """
        try:
            # Fetch fundamental data
            fundamental = self.gateway.get_fundamental_data(ticker)
            if not fundamental:
                raise DataProviderException(
                    f"No fundamental data available for {ticker}"
                )

            # Fetch current price
            current_price = self.gateway.get_current_price(ticker)

            # Try to get additional price info from yfinance
            # This is a best-effort operation
            price_info = self._fetch_price_info(ticker, current_price)

            # Get description if available (from yfinance info)
            description = self._fetch_description(ticker)

            # Check compliance if gateway is available
            compliance_status = None
            if self.compliance_gateway:
                try:
                    # Extract base ticker symbol (remove exchange suffix for Zoya lookup)
                    base_ticker = self._extract_base_ticker(ticker)
                    compliance_status = self.compliance_gateway.check_compliance(base_ticker)
                    self.logger.info(
                        f"Compliance check for {ticker} ({base_ticker}): "
                        f"{compliance_status.is_compliant} (source: {compliance_status.source})"
                    )
                except Exception as e:
                    # Log error but don't fail the entire request
                    self.logger.warning(f"Compliance check failed for {ticker}: {e}")

            return StockDetailedInfo(
                ticker=ticker,
                fundamental=fundamental,
                price=price_info,
                description=description,
                compliance_status=compliance_status,
            )

        except DataProviderException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to fetch details for {ticker}: {e}")
            raise DataProviderException(f"Failed to fetch stock details: {e}")

    def _try_ticker(self, ticker: str) -> Optional[SearchResult]:
        """
        Try to fetch info for a specific ticker symbol.

        Used when exchange_hint is provided for direct ticker validation.
        Suppresses stderr to avoid showing expected 404 errors for invalid tickers.

        Args:
            ticker: Full ticker symbol (e.g., "AAPL", "BARC.L")

        Returns:
            SearchResult if ticker is valid, None otherwise
        """
        try:
            # Suppress stderr to hide expected HTTP 404 errors from yfinance
            with self._suppress_stderr():
                fundamental = self.gateway.get_fundamental_data(ticker)

            # Validate that we got meaningful data
            if fundamental and fundamental.company_name:
                # Extract exchange from yfinance info or infer from suffix
                exchange = self._extract_exchange(ticker, fundamental)

                # Try to determine quote_type (default to EQUITY for direct ticker lookups)
                quote_type = "EQUITY"  # Most common case

                return SearchResult(
                    ticker=ticker,
                    company_name=fundamental.company_name,
                    exchange=exchange,
                    sector=fundamental.sector,
                    quote_type=quote_type,
                )
        except Exception as e:
            self.logger.debug(f"Ticker {ticker} not found: {e}")

        return None

    def _search_with_gateway(self, query: str) -> List[SearchResult]:
        """
        Search for stocks using the gateway search API.

        Delegates search operation to the configured gateway (e.g., YFinance).
        Performs comprehensive search with fuzzy matching across all exchanges.
        Handles exact ticker matches, partial matches, and company name searches.

        Args:
            query: Ticker symbol, company name, or search term

        Returns:
            List of SearchResult objects, sorted by relevance
        """
        try:
            # Suppress stderr for cleaner output
            with self._suppress_stderr():
                # Delegate to gateway's search implementation
                results = self.gateway.search_stock(
                    query=query,
                    max_results=20,
                    enable_fuzzy=True,
                )

                self.logger.info(f"Found {len(results)} results for search: {query}")
                return results

        except Exception as e:
            self.logger.error(f"Search failed for '{query}': {e}")
            return []


    @staticmethod
    @contextlib.contextmanager
    def _suppress_stderr():
        """
        Context manager to temporarily suppress stderr output.

        Used during multi-exchange ticker search where we expect many
        HTTP 404 errors that would pollute the console output.
        """
        old_stderr = sys.stderr
        try:
            sys.stderr = io.StringIO()
            yield
        finally:
            sys.stderr = old_stderr

    def _extract_exchange(self, ticker: str, fundamental) -> str:
        """
        Extract exchange name from ticker suffix or fundamental data.

        Args:
            ticker: Ticker symbol
            fundamental: FundamentalData object

        Returns:
            Exchange name or code
        """
        # Try to get exchange from yfinance info first
        # (Note: This would require modifying the gateway to expose exchange info)
        # For now, infer from ticker suffix

        if "." not in ticker:
            return "US Market"

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

    def _format_ticker(self, query: str, exchange_hint: str) -> str:
        """
        Format ticker with exchange suffix.

        Args:
            query: Base ticker symbol
            exchange_hint: Exchange suffix (with or without dot)

        Returns:
            Formatted ticker (e.g., "BARC.L")
        """
        # Remove dot from exchange_hint if present
        exchange_hint = exchange_hint.lstrip(".")

        # If query already has the suffix, return as-is
        if query.endswith(f".{exchange_hint}"):
            return query

        return f"{query}.{exchange_hint}"

    def _fetch_price_info(self, ticker: str, current_price) -> PriceInfo:
        """
        Fetch comprehensive price information.

        This is a best-effort method that tries to get additional
        price data beyond just current price.

        Args:
            ticker: Ticker symbol
            current_price: Current price from gateway

        Returns:
            PriceInfo with available data
        """
        try:
            # For now, just return basic price info
            # In future, we could fetch historical data to get prev_close, day ranges, etc.
            return PriceInfo(current_price=current_price)

        except Exception as e:
            self.logger.warning(f"Failed to fetch extended price info for {ticker}: {e}")
            return PriceInfo(current_price=current_price)

    def get_price_history(
        self,
        ticker: str,
        period: str = "3mo",
    ) -> StockData:
        """
        Fetch historical OHLCV data for price charting.

        Retrieves historical price data from the gateway with caching support.
        Suitable for displaying candlestick charts and technical analysis.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL", "NVDA")
            period: Time period ("1mo", "3mo", "6mo", "1y", "2y", "5y", "max")

        Returns:
            StockData with historical OHLCV dataframe

        Raises:
            DataProviderException: If data fetch fails

        Example:
            >>> service = SearchService(gateway)
            >>> history = service.get_price_history("AAPL", period="1y")
            >>> print(f"Retrieved {len(history.data)} data points")
        """
        ticker = ticker.upper().strip()

        # Check cache first (1-hour TTL for historical data)
        cache_key = f"history:{ticker}:{period}"
        if self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached:
                self.logger.info(f"Cache hit for {ticker} price history ({period})")
                return cached

        try:
            self.logger.info(f"Fetching {period} price history for {ticker}")

            # Delegate to gateway
            stock_data = self.gateway.get_stock_data(
                ticker=ticker,
                period=period,
            )

            # Validate we got meaningful data
            if stock_data.data.empty:
                raise DataProviderException(
                    f"No historical data available for {ticker} ({period})"
                )

            # Cache for 1 hour
            if self.cache_manager:
                self.cache_manager.set(
                    cache_key, stock_data, ttl=timedelta(hours=1)
                )

            self.logger.info(
                f"Retrieved {len(stock_data.data)} data points for {ticker}"
            )
            return stock_data

        except DataProviderException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to fetch price history for {ticker}: {e}")
            raise DataProviderException(
                f"Failed to fetch price history for {ticker}: {e}"
            )

    def _fetch_description(self, ticker: str) -> Optional[str]:
        """
        Fetch company description.

        This would require extending the gateway interface or
        using yfinance directly. For now, return None.

        Args:
            ticker: Ticker symbol

        Returns:
            Company description or None
        """
        # TODO: Implement description fetching
        # This would require either:
        # 1. Adding to IMarketDataGateway interface
        # 2. Accessing yfinance.Ticker.info['longBusinessSummary'] directly
        return None

    def _extract_base_ticker(self, ticker: str) -> str:
        """
        Extract base ticker symbol by removing exchange suffix.

        Zoya API uses base symbols without exchange suffixes
        (e.g., "BMW" instead of "BMW.DE").

        Args:
            ticker: Full ticker symbol (e.g., "AAPL", "BMW.DE", "BARC.L")

        Returns:
            Base ticker symbol (e.g., "AAPL", "BMW", "BARC")

        Example:
            >>> service._extract_base_ticker("AAPL")
            'AAPL'
            >>> service._extract_base_ticker("BMW.DE")
            'BMW'
            >>> service._extract_base_ticker("BARC.L")
            'BARC'
        """
        if "." in ticker:
            return ticker.split(".")[0]
        return ticker
