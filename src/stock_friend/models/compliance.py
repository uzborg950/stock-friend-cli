"""
Compliance data models for halal stock screening.

Defines data structures for representing stock compliance status.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional


@dataclass
class ComplianceStatus:
    """
    Represents halal compliance status for a stock.

    Design Principle: Data accuracy first - report what we know truthfully.
    - is_compliant=True: Stock is verified halal-compliant
    - is_compliant=False: Stock is verified non-compliant
    - is_compliant=None: Compliance status is unknown (no data available)

    Attributes:
        ticker: Stock ticker symbol
        is_compliant: Whether stock meets halal compliance criteria (None if unknown)
        compliance_score: Optional 0-100 score (provider-specific, e.g., Zoya)
        reasons: List of reasons for non-compliance or unknown status
        source: Data source ("zoya", "musaffa", "static", "unknown")
        checked_at: Timestamp when compliance was checked
        shariah_compliant: Optional explicit shariah compliance flag
        questionable_revenue_percentage: % of revenue from non-halal sources
        debt_to_market_cap_ratio: Total debt / market cap ratio

    Example:
        >>> # Compliant stock
        >>> status = ComplianceStatus(
        ...     ticker="AAPL",
        ...     is_compliant=True,
        ...     compliance_score=95.0,
        ...     reasons=[],
        ...     source="zoya"
        ... )
        >>> # Unknown stock
        >>> status = ComplianceStatus(
        ...     ticker="UNKNOWN",
        ...     is_compliant=None,
        ...     reasons=["No compliance data available"],
        ...     source="unknown"
        ... )
    """

    ticker: str
    is_compliant: Optional[bool]
    compliance_score: Optional[float] = None
    reasons: List[str] = field(default_factory=list)
    source: str = "unknown"
    checked_at: datetime = field(default_factory=datetime.now)

    # Provider-specific fields (optional)
    shariah_compliant: Optional[bool] = None
    questionable_revenue_percentage: Optional[Decimal] = None
    debt_to_market_cap_ratio: Optional[Decimal] = None

    def __post_init__(self):
        """Validate compliance status fields."""
        # Ensure ticker is uppercase
        if self.ticker:
            object.__setattr__(self, 'ticker', self.ticker.upper().strip())

        # Validate compliance score if provided
        if self.compliance_score is not None:
            if not 0 <= self.compliance_score <= 100:
                raise ValueError(
                    f"Compliance score must be between 0 and 100, got: {self.compliance_score}"
                )

        # Validate percentages
        if self.questionable_revenue_percentage is not None:
            if not 0 <= self.questionable_revenue_percentage <= 100:
                raise ValueError(
                    f"Questionable revenue percentage must be between 0 and 100, "
                    f"got: {self.questionable_revenue_percentage}"
                )

        if self.debt_to_market_cap_ratio is not None:
            if self.debt_to_market_cap_ratio < 0:
                raise ValueError(
                    f"Debt to market cap ratio cannot be negative, "
                    f"got: {self.debt_to_market_cap_ratio}"
                )

    def is_known(self) -> bool:
        """
        Check if compliance status is known.

        Returns:
            True if we have compliance data (compliant or non-compliant), False if unknown
        """
        return self.is_compliant is not None

    def is_questionable(self) -> bool:
        """
        Check if stock has questionable revenue but still compliant.

        Returns:
            True if stock is compliant but has some questionable revenue
        """
        if not self.is_compliant:
            return False

        if self.questionable_revenue_percentage is not None:
            return self.questionable_revenue_percentage > 0

        return False

    def summary(self) -> str:
        """
        Get human-readable summary of compliance status.

        Returns:
            Summary string for display
        """
        if self.is_compliant is None:
            reason_str = ", ".join(self.reasons) if self.reasons else "No data available"
            return f"❓ Unknown: {reason_str}"
        elif self.is_compliant:
            if self.compliance_score is not None:
                return f"✓ Compliant (Score: {self.compliance_score:.1f}/100)"
            return "✓ Compliant"
        else:
            reason_str = ", ".join(self.reasons) if self.reasons else "Unknown reason"
            return f"✗ Non-Compliant: {reason_str}"
