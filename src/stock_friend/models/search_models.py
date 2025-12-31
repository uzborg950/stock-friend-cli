"""
Search-related data models.

Defines data structures for stock search operations, including search results
and detailed stock information for display.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from stock_friend.models.stock_data import FundamentalData


@dataclass(frozen=True)
class SearchResult:
    """
    Lightweight search result for displaying in search results list.

    Attributes:
        ticker: Full ticker symbol including exchange suffix (e.g., "AAPL", "BARC.L")
        company_name: Company or asset name
        exchange: Exchange name or code
        sector: Business sector (optional)
        quote_type: Security type (EQUITY, ETF, MUTUALFUND, etc.)
    """

    ticker: str
    company_name: str
    exchange: str
    sector: Optional[str] = None
    quote_type: Optional[str] = None


@dataclass(frozen=True)
class PriceInfo:
    """
    Current price information for a stock.

    Attributes:
        current_price: Current trading price
        previous_close: Previous closing price
        day_low: Intraday low price
        day_high: Intraday high price
        fifty_two_week_low: 52-week low price
        fifty_two_week_high: 52-week high price
        volume: Trading volume
    """

    current_price: Decimal
    previous_close: Optional[Decimal] = None
    day_low: Optional[Decimal] = None
    day_high: Optional[Decimal] = None
    fifty_two_week_low: Optional[Decimal] = None
    fifty_two_week_high: Optional[Decimal] = None
    volume: Optional[int] = None

    @property
    def price_change(self) -> Optional[Decimal]:
        """Calculate price change from previous close."""
        if self.previous_close and self.current_price:
            return self.current_price - self.previous_close
        return None

    @property
    def price_change_pct(self) -> Optional[float]:
        """Calculate percentage price change from previous close."""
        if self.previous_close and self.price_change:
            return float(self.price_change / self.previous_close)
        return None


@dataclass(frozen=True)
class StockDetailedInfo:
    """
    Comprehensive stock information for detailed display.

    Combines fundamental data with current price information for
    presentation in the search results detailed view.

    Attributes:
        ticker: Full ticker symbol
        fundamental: Fundamental financial metrics
        price: Current price information
        description: Company business description (optional)
    """

    ticker: str
    fundamental: FundamentalData
    price: PriceInfo
    description: Optional[str] = None

    @property
    def company_name(self) -> str:
        """Get company name from fundamentals."""
        return self.fundamental.company_name or "N/A"

    @property
    def exchange(self) -> str:
        """Get exchange from ticker suffix or return 'Unknown'."""
        # Extract exchange from ticker suffix
        if "." in self.ticker:
            suffix = self.ticker.split(".")[-1]
            return self._map_exchange_suffix(suffix)
        return "US Market"

    @staticmethod
    def _map_exchange_suffix(suffix: str) -> str:
        """Map exchange suffix to friendly name."""
        exchange_map = {
            "L": "London Stock Exchange (LSE)",
            "TO": "Toronto Stock Exchange (TSX)",
            "AX": "Australian Securities Exchange (ASX)",
            "PA": "Euronext Paris",
            "DE": "XETRA (Frankfurt)",
            "HK": "Hong Kong Stock Exchange",
            "T": "Tokyo Stock Exchange",
            "SW": "Swiss Exchange",
            "AS": "Euronext Amsterdam",
            "BR": "Euronext Brussels",
            "MC": "Madrid Stock Exchange",
            "MI": "Milan Stock Exchange",
            "OL": "Oslo Stock Exchange",
            "ST": "Stockholm Stock Exchange",
            "CO": "Copenhagen Stock Exchange",
            "HE": "Helsinki Stock Exchange",
            "IC": "Iceland Stock Exchange",
            "VI": "Vienna Stock Exchange",
            "LS": "Lisbon Stock Exchange",
        }
        return exchange_map.get(suffix.upper(), f"{suffix.upper()} Exchange")
