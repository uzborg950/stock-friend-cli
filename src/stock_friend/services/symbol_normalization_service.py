"""
Symbol normalization service.

Normalizes stock symbols between different gateway formats to ensure
compliance data accurately matches market data.

Critical for multi-exchange support and European market handling.
"""

import logging
import re
from typing import Dict, List, Optional

from stock_friend.models.symbol import (
    ExchangeMapping,
    MarketRegion,
    NormalizedSymbol,
    SymbolConfidence,
)

logger = logging.getLogger(__name__)


class SymbolNormalizationService:
    """
    Normalize stock symbols between different gateway formats.

    Responsibilities:
    - Remove market suffixes (.DE, .L, .F) from yfinance tickers
    - Map exchange codes between providers (yfinance ↔ Bloomberg)
    - Handle special cases (ADRs, preferred shares, dual listings)
    - Maintain audit trail of transformations
    - Score confidence of normalizations

    Design Principles:
    - Conservative: Unknown mappings marked LOW confidence, not guessed
    - Transparent: Full audit trail in transformation_notes
    - Extensible: Easy to add new exchange mappings
    - Performance: O(1) lookups via dictionaries

    Example:
        >>> service = SymbolNormalizationService()
        >>> normalized = service.normalize_for_compliance("BMW.DE")
        >>> print(normalized.base_symbol)
        'BMW'
        >>> print(normalized.exchange_code)
        'XETR'
        >>> print(normalized.confidence)
        SymbolConfidence.HIGH
    """

    # Exchange mappings: yfinance suffix → exchange information
    EXCHANGE_MAPPINGS: List[ExchangeMapping] = [
        # German Markets
        ExchangeMapping(".DE", "XETR", "Deutsche Börse Xetra", MarketRegion.EU, "DE"),
        ExchangeMapping(".F", "XFRA", "Frankfurt Stock Exchange", MarketRegion.EU, "DE"),
        ExchangeMapping(".BE", "XBER", "Berlin Stock Exchange", MarketRegion.EU, "DE"),
        ExchangeMapping(".MU", "XMUN", "Munich Stock Exchange", MarketRegion.EU, "DE"),
        ExchangeMapping(".DU", "XDUS", "Düsseldorf Stock Exchange", MarketRegion.EU, "DE"),
        ExchangeMapping(".HM", "XHAM", "Hamburg Stock Exchange", MarketRegion.EU, "DE"),
        ExchangeMapping(".HA", "XHAN", "Hanover Stock Exchange", MarketRegion.EU, "DE"),
        ExchangeMapping(".SG", "XSTU", "Stuttgart Stock Exchange", MarketRegion.EU, "DE"),
        # UK Markets
        ExchangeMapping(".L", "XLON", "London Stock Exchange", MarketRegion.UK, "GB"),
        # Euronext Markets
        ExchangeMapping(".PA", "XPAR", "Euronext Paris", MarketRegion.EU, "FR"),
        ExchangeMapping(".AS", "XAMS", "Euronext Amsterdam", MarketRegion.EU, "NL"),
        ExchangeMapping(".BR", "XBRU", "Euronext Brussels", MarketRegion.EU, "BE"),
        ExchangeMapping(".LS", "XLIS", "Euronext Lisbon", MarketRegion.EU, "PT"),
        # Italian Markets
        ExchangeMapping(".MI", "XMIL", "Borsa Italiana (Milan)", MarketRegion.EU, "IT"),
        # Swiss Markets
        ExchangeMapping(".SW", "XSWX", "SIX Swiss Exchange", MarketRegion.EU, "CH"),
        # Nordic Markets
        ExchangeMapping(".ST", "XSTO", "Nasdaq Stockholm", MarketRegion.EU, "SE"),
        ExchangeMapping(".CO", "XCSE", "Nasdaq Copenhagen", MarketRegion.EU, "DK"),
        ExchangeMapping(".HE", "XHEL", "Nasdaq Helsinki", MarketRegion.EU, "FI"),
        ExchangeMapping(".OL", "XOSL", "Oslo Stock Exchange", MarketRegion.EU, "NO"),
        # Spanish Markets
        ExchangeMapping(".MC", "XMAD", "Bolsa de Madrid", MarketRegion.EU, "ES"),
        # Austrian Markets
        ExchangeMapping(".VI", "XWBO", "Vienna Stock Exchange", MarketRegion.EU, "AT"),
        # Asian Markets
        ExchangeMapping(".HK", "XHKG", "Hong Kong Stock Exchange", MarketRegion.ASIA, "HK"),
        ExchangeMapping(".T", "XTKS", "Tokyo Stock Exchange", MarketRegion.ASIA, "JP"),
        ExchangeMapping(".KS", "XKRX", "Korea Stock Exchange", MarketRegion.ASIA, "KR"),
        ExchangeMapping(".SS", "XSHG", "Shanghai Stock Exchange", MarketRegion.ASIA, "CN"),
        ExchangeMapping(".SZ", "XSHE", "Shenzhen Stock Exchange", MarketRegion.ASIA, "CN"),
        # Australian Markets
        ExchangeMapping(".AX", "XASX", "Australian Securities Exchange", MarketRegion.OTHER, "AU"),
        # Canadian Markets
        ExchangeMapping(".TO", "XTSE", "Toronto Stock Exchange", MarketRegion.OTHER, "CA"),
        ExchangeMapping(".V", "XTSX", "TSX Venture Exchange", MarketRegion.OTHER, "CA"),
    ]

    # US exchanges have no suffix in yfinance
    US_EXCHANGE_CODES = {
        "NASDAQ": "XNGS",  # NASDAQ Global Select
        "NYSE": "XNYS",  # New York Stock Exchange
        "AMEX": "XASE",  # NYSE American (formerly AMEX)
        "NYQ": "XNYS",  # NYSE (alternative code)
        "NMS": "XNGS",  # NASDAQ (alternative code)
    }

    # Special suffixes to preserve (not exchange codes)
    PRESERVE_SUFFIXES = {
        ".A", ".B", ".C", ".D",  # Share classes (e.g., BRK.A, GOOGL.A)
        "-A", "-B", "-C", "-D",  # Preferred shares (e.g., BAC-PL)
        ".PR",  # Preferred (alternative format)
        ".U", ".UN",  # Units (trusts, SPACs)
        ".W", ".WS",  # Warrants
        ".R", ".RT",  # Rights
    }

    def __init__(self):
        """Initialize symbol normalization service."""
        # Build fast lookup dictionaries
        self._suffix_map: Dict[str, ExchangeMapping] = {
            mapping.yfinance_suffix: mapping for mapping in self.EXCHANGE_MAPPINGS
        }

        self._bloomberg_reverse_map: Dict[str, ExchangeMapping] = {
            mapping.bloomberg_code: mapping for mapping in self.EXCHANGE_MAPPINGS
        }

        logger.info(
            f"Initialized SymbolNormalizationService with {len(self._suffix_map)} exchange mappings"
        )

    def normalize_for_compliance(
        self,
        ticker: str,
        exchange: Optional[str] = None,
        source_gateway: str = "yfinance",
    ) -> NormalizedSymbol:
        """
        Normalize ticker for compliance gateway lookup.

        Args:
            ticker: Gateway-specific ticker (e.g., "BMW.DE", "AAPL")
            exchange: Exchange code from gateway (if available)
            source_gateway: Which gateway provided this symbol

        Returns:
            NormalizedSymbol with base ticker, exchange code, and confidence score

        Example:
            >>> service = SymbolNormalizationService()
            >>> result = service.normalize_for_compliance("BMW.DE")
            >>> print(result.base_symbol)
            'BMW'
            >>> print(result.confidence)
            SymbolConfidence.HIGH
        """
        ticker = ticker.strip().upper()
        notes: List[str] = []

        # Check for special suffixes to preserve
        preserved_suffix = self._get_preserved_suffix(ticker)
        if preserved_suffix:
            notes.append(f"Preserved special suffix: {preserved_suffix}")
            # Keep ticker as-is for special cases
            return NormalizedSymbol(
                base_symbol=ticker,
                original_ticker=ticker,
                exchange_code=self._infer_exchange_from_code(exchange) if exchange else None,
                market_region=MarketRegion.US if not exchange else MarketRegion.OTHER,
                confidence=SymbolConfidence.HIGH,
                transformation_notes=notes,
                source_gateway=source_gateway,
            )

        # Extract exchange suffix
        exchange_suffix = self._extract_exchange_suffix(ticker)

        if exchange_suffix:
            # Found known exchange suffix
            mapping = self._suffix_map[exchange_suffix]
            base_symbol = ticker[: -len(exchange_suffix)]
            notes.append(f"Removed {exchange_suffix} suffix → {mapping.exchange_name}")

            return NormalizedSymbol(
                base_symbol=base_symbol,
                original_ticker=ticker,
                exchange_code=mapping.bloomberg_code,
                market_region=mapping.market_region,
                confidence=SymbolConfidence.HIGH,
                transformation_notes=notes,
                source_gateway=source_gateway,
            )

        # No suffix - likely US stock or unknown format
        if exchange:
            # Try to map exchange code to Bloomberg
            bloomberg_code = self._infer_exchange_from_code(exchange)
            if bloomberg_code:
                notes.append(f"Mapped exchange code: {exchange} → {bloomberg_code}")
                confidence = SymbolConfidence.HIGH
            else:
                notes.append(f"Unknown exchange code: {exchange}")
                bloomberg_code = exchange
                confidence = SymbolConfidence.MEDIUM
        else:
            # Assume US market (most common case for no suffix)
            bloomberg_code = None
            notes.append("No suffix or exchange - assuming US market")
            confidence = SymbolConfidence.HIGH

        return NormalizedSymbol(
            base_symbol=ticker,
            original_ticker=ticker,
            exchange_code=bloomberg_code,
            market_region=MarketRegion.US if not exchange else MarketRegion.OTHER,
            confidence=confidence,
            transformation_notes=notes,
            source_gateway=source_gateway,
        )

    def extract_base_symbol(self, ticker: str) -> str:
        """
        Remove exchange suffix from ticker, preserving special suffixes.

        Args:
            ticker: Ticker symbol (e.g., "BMW.DE", "BRK.A")

        Returns:
            Base symbol (e.g., "BMW", "BRK.A")

        Example:
            >>> service = SymbolNormalizationService()
            >>> service.extract_base_symbol("BMW.DE")
            'BMW'
            >>> service.extract_base_symbol("BRK.A")  # Preserved
            'BRK.A'
        """
        ticker = ticker.strip().upper()

        # Check if has preserved suffix
        if self._get_preserved_suffix(ticker):
            return ticker

        # Remove exchange suffix if present
        exchange_suffix = self._extract_exchange_suffix(ticker)
        if exchange_suffix:
            return ticker[: -len(exchange_suffix)]

        return ticker

    def get_exchange_from_suffix(self, ticker: str) -> Optional[str]:
        """
        Extract Bloomberg exchange code from ticker suffix.

        Args:
            ticker: Ticker symbol (e.g., "BMW.DE", "AAPL")

        Returns:
            Bloomberg exchange code or None

        Example:
            >>> service = SymbolNormalizationService()
            >>> service.get_exchange_from_suffix("BMW.DE")
            'XETR'
            >>> service.get_exchange_from_suffix("AAPL")
            None
        """
        exchange_suffix = self._extract_exchange_suffix(ticker.upper())
        if exchange_suffix and exchange_suffix in self._suffix_map:
            return self._suffix_map[exchange_suffix].bloomberg_code
        return None

    def get_market_region(self, ticker: str, exchange: Optional[str] = None) -> MarketRegion:
        """
        Determine market region from ticker or exchange.

        Args:
            ticker: Ticker symbol
            exchange: Optional exchange code

        Returns:
            MarketRegion enum value
        """
        exchange_suffix = self._extract_exchange_suffix(ticker.upper())
        if exchange_suffix and exchange_suffix in self._suffix_map:
            return self._suffix_map[exchange_suffix].market_region

        if exchange and exchange.upper() in self.US_EXCHANGE_CODES.values():
            return MarketRegion.US

        # Default: assume US for no suffix
        return MarketRegion.US if not exchange_suffix else MarketRegion.OTHER

    def _extract_exchange_suffix(self, ticker: str) -> Optional[str]:
        """
        Extract exchange suffix from ticker.

        Returns:
            Exchange suffix (e.g., ".DE") or None
        """
        ticker = ticker.upper()

        # Check against known exchange suffixes (longest first to handle .WS before .W)
        sorted_suffixes = sorted(self._suffix_map.keys(), key=len, reverse=True)
        for suffix in sorted_suffixes:
            if ticker.endswith(suffix):
                return suffix

        return None

    def _get_preserved_suffix(self, ticker: str) -> Optional[str]:
        """
        Check if ticker has a special suffix that should be preserved.

        Returns:
            Preserved suffix or None
        """
        ticker = ticker.upper()

        for suffix in self.PRESERVE_SUFFIXES:
            if ticker.endswith(suffix):
                return suffix

        return None

    def _infer_exchange_from_code(self, exchange_code: str) -> Optional[str]:
        """
        Map gateway exchange code to Bloomberg code.

        Args:
            exchange_code: Exchange code from gateway

        Returns:
            Bloomberg exchange code or None
        """
        exchange_code = exchange_code.upper()

        # Direct Bloomberg code match
        if exchange_code in self._bloomberg_reverse_map:
            return exchange_code

        # US exchange code match
        if exchange_code in self.US_EXCHANGE_CODES:
            return self.US_EXCHANGE_CODES[exchange_code]

        # Partial matches (some gateways use abbreviated codes)
        for bloomberg_code, mapping in self._bloomberg_reverse_map.items():
            if exchange_code in mapping.exchange_name.upper():
                return bloomberg_code

        return None

    def get_supported_exchanges(self) -> List[ExchangeMapping]:
        """
        Get list of all supported exchange mappings.

        Returns:
            List of ExchangeMapping objects
        """
        return self.EXCHANGE_MAPPINGS.copy()

    def get_exchange_info(self, suffix_or_code: str) -> Optional[ExchangeMapping]:
        """
        Get exchange information by suffix or Bloomberg code.

        Args:
            suffix_or_code: yfinance suffix (e.g., ".DE") or Bloomberg code (e.g., "XETR")

        Returns:
            ExchangeMapping or None if not found
        """
        suffix_or_code = suffix_or_code.upper()

        # Try as suffix first
        if suffix_or_code in self._suffix_map:
            return self._suffix_map[suffix_or_code]

        # Try as Bloomberg code
        if suffix_or_code in self._bloomberg_reverse_map:
            return self._bloomberg_reverse_map[suffix_or_code]

        return None
