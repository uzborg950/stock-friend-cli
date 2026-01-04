"""
Abstract interface for halal compliance gateways.

Defines the contract that all compliance data providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from stock_friend.models.compliance import ComplianceStatus


class IComplianceGateway(ABC):
    """
    Abstract interface for halal compliance checking.

    Design Principles:
    - Dependency Inversion: Services depend on this interface, not implementations
    - Data Accuracy: Report what we know truthfully (use is_compliant=None for unknown)
    - Batch Operations: Optimize for screening large universes
    - Caching: Compliance data rarely changes (30-day TTL recommended)
    - Fail Gracefully: Log errors but don't stop screening

    Implementation Guidelines:
    - Handle retries and error recovery internally
    - Return standardized ComplianceStatus objects
    - Use cache manager when provided (30-day TTL)
    - Use rate limiter when provided
    - Log all errors and API failures
    - Return unknown status (is_compliant=None) when data is unavailable

    Example:
        >>> gateway = ZoyaComplianceGateway(api_key="...", environment="sandbox")
        >>> status = gateway.check_compliance("AAPL")
        >>> print(f"{status.ticker}: {status.is_compliant}")
    """

    @abstractmethod
    def check_compliance(self, ticker: str) -> ComplianceStatus:
        """
        Check if single stock is halal-compliant.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")

        Returns:
            ComplianceStatus object with compliance details:
            - is_compliant=True: Stock is verified compliant
            - is_compliant=False: Stock is verified non-compliant
            - is_compliant=None: Compliance status unknown (no data)

        Raises:
            ComplianceException: If check cannot be performed (rare)

        Note:
            Should return unknown status (is_compliant=None) when data
            is unavailable rather than making assumptions.

        Performance Target:
            <2 seconds per request (with caching: <100ms)
        """
        pass

    @abstractmethod
    def check_batch(self, tickers: List[str]) -> Dict[str, ComplianceStatus]:
        """
        Check multiple stocks at once (optimized for API efficiency).

        Batch operations are preferred over sequential calls for:
        - Reduced API requests
        - Faster screening of large universes
        - Better rate limit utilization

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping tickers to ComplianceStatus objects

        Note:
            Failures for individual stocks should be logged but not stop
            the entire batch. Return partial results. Unknown tickers
            should return unknown status (is_compliant=None).

        Performance Target:
            <30 seconds for 100 stocks (with caching and batch API)
        """
        pass

    @abstractmethod
    def filter_compliant(self, tickers: List[str]) -> List[str]:
        """
        Filter universe to only halal-compliant stock tickers.

        Convenience method that performs batch check and filters results.
        This is the primary method used by ScreeningService.

        Args:
            tickers: List of ticker symbols to filter

        Returns:
            List of compliant ticker symbols only (excludes non-compliant and unknown)

        Note:
            Only returns stocks with is_compliant=True. Stocks with unknown status
            (is_compliant=None) are excluded for conservative screening.

        Example:
            >>> sp500_tickers = ["AAPL", "JPM", "GOOGL", "UNKNOWN", ...]
            >>> compliant = gateway.filter_compliant(sp500_tickers)
            >>> # Returns only ["AAPL", "GOOGL"] - excludes JPM (non-compliant) and UNKNOWN

        Performance Target:
            <60 seconds for 500 stocks (S&P 500 screening)
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Return unique gateway identifier.

        Returns:
            Gateway name (e.g., "zoya_sandbox", "zoya_live", "musaffa", "static")

        Example:
            >>> gateway.get_name()
            'zoya_sandbox'
        """
        pass


class ComplianceException(Exception):
    """
    Raised when compliance check encounters an unrecoverable error.

    This exception indicates a critical failure in the compliance provider
    (authentication error, network error, invalid API response, etc.).

    Note:
        Most errors should be handled gracefully by defaulting to compliant.
        This exception should only be raised for critical infrastructure failures.
    """

    pass


class ComplianceDataNotFoundError(Exception):
    """
    Raised when compliance data is not available for a ticker.

    This is informational only. Implementations should catch this internally
    and default to compliant (zero false negatives principle).
    """

    pass
