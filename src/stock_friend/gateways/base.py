"""
Base gateway interface for market data access.

Defines the abstract interface that all market data gateways must implement.
This ensures pluggability and allows easy switching between data providers.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from stock_friend.models.stock_data import FundamentalData, StockData
from stock_friend.models.search_models import SearchResult


class IMarketDataGateway(ABC):
    """
    Abstract interface for market data gateways.

    Design Principles:
    - Dependency Inversion: Services depend on this interface, not implementations
    - Strategy Pattern: Different providers are interchangeable
    - Single Responsibility: Only responsible for data fetching
    - Open/Closed: New providers can be added without modifying consumers

    Implementation Guidelines:
    - Handle retries and error recovery internally
    - Return standardized data structures (StockData, FundamentalData)
    - Use cache manager and rate limiter when provided
    - Log all errors and failures
    - Fail gracefully with clear error messages
    """

    @abstractmethod
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
            ValueError: If ticker is invalid or parameters are incompatible
            DataProviderException: If data cannot be retrieved

        Performance Target:
            <5 seconds for 1 year of daily data (95% of cases)
        """
        pass

    @abstractmethod
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
            period: Period string if dates not specified

        Returns:
            Dictionary mapping tickers to StockData objects

        Note:
            Failures for individual stocks should be logged but not stop
            the entire batch. Return partial results.

        Performance Target:
            <120 seconds for 100 stocks (parallel processing)
        """
        pass

    @abstractmethod
    def get_current_price(self, ticker: str) -> Decimal:
        """
        Get current/latest price for a stock.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Current price as Decimal

        Raises:
            DataProviderException: If price cannot be retrieved

        Performance Target:
            <1 second for 95% of requests
        """
        pass

    @abstractmethod
    def get_batch_current_prices(self, tickers: List[str]) -> Dict[str, Decimal]:
        """
        Get current prices for multiple stocks (batch operation).

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping tickers to current prices

        Note:
            Failures for individual stocks should be logged but not stop
            the entire batch.

        Performance Target:
            <10 seconds for 50 stocks
        """
        pass

    @abstractmethod
    def get_fundamental_data(self, ticker: str) -> Optional[FundamentalData]:
        """
        Retrieve fundamental data for a stock.

        Args:
            ticker: Stock ticker symbol

        Returns:
            FundamentalData object or None if not available

        Note:
            Fundamental data is optional. Return None if unavailable
            rather than raising an exception.

        Performance Target:
            <2 seconds per request
        """
        pass

    @abstractmethod
    def search_stock(
        self,
        query: str,
        max_results: int = 20,
        enable_fuzzy: bool = True,
    ) -> List[SearchResult]:
        """
        Search for stocks by ticker symbol or company name.

        Handles exact ticker matches, partial matches, and company name searches
        across all exchanges without requiring manual suffix expansion.

        Args:
            query: Ticker symbol, company name, or search term
            max_results: Maximum number of results to return
            enable_fuzzy: Enable fuzzy matching for typos

        Returns:
            List of SearchResult objects sorted by relevance (empty if no matches)
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Return unique gateway identifier.

        Returns:
            Gateway name (e.g., "yahoo_finance", "alpha_vantage")
        """
        pass


class DataProviderException(Exception):
    """
    Raised when data provider encounters an error.

    This exception indicates a failure in the external data provider
    (network error, API limit, invalid response, etc.).
    """

    pass


class InsufficientDataError(Exception):
    """
    Raised when insufficient historical data is available.

    This exception indicates that the data source doesn't have enough
    historical data to satisfy the request (e.g., newly listed stock).
    """

    pass
