"""
Symbol normalization data models.

Provides data structures for tracking symbol transformations between
different gateway formats with full audit trail.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class SymbolConfidence(Enum):
    """
    Confidence level for symbol normalization.

    Used to track reliability of symbol transformation when mapping
    between different gateway formats.
    """

    HIGH = "HIGH"  # Known mapping, widely used exchange
    MEDIUM = "MEDIUM"  # Reasonable inference, less common exchange
    LOW = "LOW"  # Uncertain mapping, may require manual review


class MarketRegion(Enum):
    """Market region classification."""

    US = "US"  # United States
    EU = "EU"  # European Union
    UK = "UK"  # United Kingdom
    ASIA = "ASIA"  # Asian markets
    OTHER = "OTHER"  # Other markets


@dataclass(frozen=True)
class NormalizedSymbol:
    """
    Normalized symbol with full audit trail.

    Tracks transformation of gateway-specific ticker symbols to normalized
    format for compliance checking, maintaining complete audit trail for
    regulatory compliance and debugging.

    Design Principles:
    - Immutable (frozen dataclass) for audit trail integrity
    - Complete transformation history
    - Confidence scoring for uncertain mappings
    - Timestamp for troubleshooting

    Example:
        >>> normalized = NormalizedSymbol(
        ...     base_symbol="BMW",
        ...     original_ticker="BMW.DE",
        ...     exchange_code="XETR",
        ...     market_region=MarketRegion.EU,
        ...     confidence=SymbolConfidence.HIGH,
        ...     transformation_notes=["Removed .DE suffix", "Mapped to Xetra exchange"]
        ... )
        >>> normalized.is_high_confidence()
        True
    """

    base_symbol: str  # Clean ticker for compliance check (e.g., "BMW", "AAPL")
    original_ticker: str  # Original input for audit trail (e.g., "BMW.DE")
    exchange_code: Optional[str]  # Bloomberg-style code (e.g., "XETR", "XNGS")
    market_region: MarketRegion  # Geographic region
    confidence: SymbolConfidence  # Reliability of transformation
    transformation_notes: List[str] = field(default_factory=list)  # What was done
    timestamp: datetime = field(default_factory=datetime.now)  # When normalized
    source_gateway: str = "unknown"  # Which gateway provided original ticker

    def is_high_confidence(self) -> bool:
        """Check if normalization is high confidence."""
        return self.confidence == SymbolConfidence.HIGH

    def is_low_confidence(self) -> bool:
        """Check if normalization is low confidence (may need review)."""
        return self.confidence == SymbolConfidence.LOW

    def summary(self) -> str:
        """
        Get human-readable summary of normalization.

        Returns:
            String summarizing the transformation
        """
        notes_str = "; ".join(self.transformation_notes) if self.transformation_notes else "No transformation"
        exchange_str = f" [{self.exchange_code}]" if self.exchange_code else ""
        return (
            f"{self.original_ticker} → {self.base_symbol}{exchange_str} "
            f"({self.confidence.value}: {notes_str})"
        )

    def __str__(self) -> str:
        """String representation."""
        return f"NormalizedSymbol({self.original_ticker} → {self.base_symbol}, {self.confidence.value})"


@dataclass(frozen=True)
class ExchangeMapping:
    """
    Mapping between different exchange code formats.

    Tracks mappings between yfinance suffixes, Bloomberg codes, and
    human-readable exchange names.
    """

    yfinance_suffix: str  # yfinance format (e.g., ".DE", ".L")
    bloomberg_code: str  # Bloomberg format (e.g., "XETR", "XLON")
    exchange_name: str  # Human-readable name
    market_region: MarketRegion  # Geographic region
    country_code: str  # ISO country code (e.g., "DE", "US", "GB")

    def __str__(self) -> str:
        """String representation."""
        return f"{self.yfinance_suffix} → {self.bloomberg_code} ({self.exchange_name})"
