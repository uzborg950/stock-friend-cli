"""
Stock data models.

Defines the core data structures for stock market data, fundamental data,
and compliance status.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class StockInfo:
    """
    Basic stock information (ticker, name, sector, industry).

    Lightweight model for universe/screener results before fetching full data.

    Attributes:
        ticker: Stock ticker symbol
        name: Company name
        sector: Business sector (GICS or similar classification)
        industry: Industry classification (GICS sub-industry)
    """

    ticker: str
    name: str
    sector: str = "Unknown"
    industry: str = "Unknown"


@dataclass(frozen=True)
class StockData:
    """
    Stock OHLCV data container.

    Attributes:
        ticker: Stock ticker symbol
        data: DataFrame with OHLCV data
        fetched_at: Timestamp when data was fetched
        source: Data source (e.g., "YAHOO_FINANCE", "ALPHA_VANTAGE")
    """

    ticker: str
    data: pd.DataFrame
    fetched_at: datetime
    source: str

    def __post_init__(self) -> None:
        """Validate data structure."""
        required_cols = ["date", "open", "high", "low", "close", "volume"]
        missing = [col for col in required_cols if col not in self.data.columns]

        if missing:
            raise ValueError(
                f"Missing required columns for {self.ticker}: {missing}. "
                f"Available: {list(self.data.columns)}"
            )

    @property
    def period_count(self) -> int:
        """Return number of data periods."""
        return len(self.data)

    @property
    def latest_close(self) -> Decimal:
        """Return most recent closing price."""
        return Decimal(str(self.data["close"].iloc[-1]))

    @property
    def date_range(self) -> tuple[datetime, datetime]:
        """Return (start_date, end_date) of data."""
        return (
            self.data["date"].iloc[0],
            self.data["date"].iloc[-1],
        )


@dataclass(frozen=True)
class FundamentalData:
    """
    Fundamental financial metrics for a stock.

    Attributes:
        ticker: Stock ticker symbol
        company_name: Company name
        sector: Business sector
        industry: Industry classification
        market_cap: Market capitalization
        pe_ratio: Price-to-earnings ratio
        pb_ratio: Price-to-book ratio
        ps_ratio: Price-to-sales ratio
        peg_ratio: PEG ratio
        eps: Earnings per share
        eps_growth_yoy: YoY EPS growth rate
        book_value_per_share: Book value per share
        revenue: Total revenue
        revenue_growth_yoy: YoY revenue growth rate
        net_income: Net income
        profit_margin: Profit margin percentage
        roe: Return on equity
        total_debt: Total debt
        total_cash: Total cash and cash equivalents
        debt_to_equity: Debt-to-equity ratio
        last_updated: When data was last updated
    """

    ticker: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[Decimal] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    eps: Optional[Decimal] = None
    eps_growth_yoy: Optional[float] = None
    book_value_per_share: Optional[Decimal] = None
    revenue: Optional[Decimal] = None
    revenue_growth_yoy: Optional[float] = None
    net_income: Optional[Decimal] = None
    profit_margin: Optional[float] = None
    roe: Optional[float] = None
    total_debt: Optional[Decimal] = None
    total_cash: Optional[Decimal] = None
    debt_to_equity: Optional[float] = None
    last_updated: Optional[datetime] = None


class ComplianceResult(Enum):
    """Halal compliance check result."""

    COMPLIANT = "compliant"
    EXCLUDED = "excluded"
    UNVERIFIED = "unverified"


@dataclass(frozen=True)
class ComplianceStatus:
    """
    Halal compliance status for a stock.

    Attributes:
        ticker: Stock ticker symbol
        result: Compliance result
        exclusion_reason: Reason for exclusion (if excluded)
        exclusion_detail: Detailed explanation
        verified_at: Timestamp of verification
        data_source: Source of compliance data
    """

    ticker: str
    result: ComplianceResult
    exclusion_reason: Optional[str] = None
    exclusion_detail: Optional[str] = None
    verified_at: Optional[datetime] = None
    data_source: Optional[str] = None

    @property
    def is_compliant(self) -> bool:
        """Check if stock is compliant."""
        return self.result == ComplianceResult.COMPLIANT

    @classmethod
    def compliant(
        cls, ticker: str, verified_at: datetime, source: str
    ) -> "ComplianceStatus":
        """Create compliant status."""
        return cls(
            ticker=ticker,
            result=ComplianceResult.COMPLIANT,
            verified_at=verified_at,
            data_source=source,
        )

    @classmethod
    def excluded(
        cls, ticker: str, reason: str, detail: str, source: str
    ) -> "ComplianceStatus":
        """Create excluded status."""
        return cls(
            ticker=ticker,
            result=ComplianceResult.EXCLUDED,
            exclusion_reason=reason,
            exclusion_detail=detail,
            verified_at=datetime.now(),
            data_source=source,
        )
