"""
Compliance checking service with symbol normalization.

Orchestrates compliance checking across different gateways with automatic
symbol format normalization for data integrity.
"""

import logging
from typing import Dict, List

from stock_friend.gateways.compliance.base import IComplianceGateway
from stock_friend.models.compliance import ComplianceStatus
from stock_friend.models.stock_data import StockData
from stock_friend.models.symbol import NormalizedSymbol, SymbolConfidence
from stock_friend.services.symbol_normalization_service import (
    SymbolNormalizationService,
)

logger = logging.getLogger(__name__)


class ComplianceService:
    """
    Orchestrates compliance checking with symbol normalization.

    Responsibilities:
    - Normalize stock symbols between gateway formats
    - Check compliance using appropriate gateway
    - Maintain audit trail of symbol transformations
    - Handle low-confidence mappings conservatively
    - Provide batch operations

    Design Principles:
    - Data Integrity: Symbol normalization ensures compliance data matches market data
    - Conservative Screening: Low-confidence mappings logged for review
    - Transparency: Full audit trail attached to compliance status
    - Gateway Abstraction: Works with any IComplianceGateway implementation

    Example:
        >>> gateway = ZoyaComplianceGateway(api_key="...")
        >>> normalizer = SymbolNormalizationService()
        >>> service = ComplianceService(gateway, normalizer)
        >>>
        >>> stock = StockData(ticker="BMW.DE", exchange="FRA", ...)
        >>> status = service.check_stock_compliance(stock)
        >>> print(status.is_compliant)
        True
    """

    def __init__(
        self,
        compliance_gateway: IComplianceGateway,
        normalization_service: SymbolNormalizationService,
        log_low_confidence: bool = True,
    ):
        """
        Initialize compliance service.

        Args:
            compliance_gateway: Gateway for compliance checking
            normalization_service: Service for symbol normalization
            log_low_confidence: Whether to log warnings for low-confidence mappings
        """
        self.gateway = compliance_gateway
        self.normalizer = normalization_service
        self.log_low_confidence = log_low_confidence

        logger.info(
            f"Initialized ComplianceService with {self.gateway.get_name()} gateway"
        )

    def check_stock_compliance(self, stock: StockData) -> ComplianceStatus:
        """
        Check compliance for a stock with automatic symbol normalization.

        Handles:
        - Symbol format conversion (BMW.DE → BMW)
        - Exchange code mapping (FRA → XETR)
        - Audit trail logging
        - Low-confidence mapping warnings

        Args:
            stock: StockData object from universe gateway

        Returns:
            ComplianceStatus with compliance details

        Example:
            >>> stock = StockData(ticker="BMW.DE", exchange="FRA", ...)
            >>> status = service.check_stock_compliance(stock)
            >>> print(status.is_compliant)
            True
        """
        # Normalize symbol for compliance gateway
        normalized = self.normalizer.normalize_for_compliance(
            stock.ticker,
            stock.exchange,
            source_gateway="universe",
        )

        # Log transformation for audit trail
        logger.info(
            f"Symbol normalization: {stock.ticker} → {normalized.base_symbol} "
            f"[{normalized.exchange_code or 'N/A'}] "
            f"(confidence: {normalized.confidence.value})"
        )

        # Warn on low-confidence mappings
        if self.log_low_confidence and normalized.is_low_confidence():
            logger.warning(
                f"LOW CONFIDENCE symbol mapping for {stock.ticker}: "
                f"{'; '.join(normalized.transformation_notes)}"
            )

        # Check compliance with normalized symbol
        status = self.gateway.check_compliance(normalized.base_symbol)

        # Attach normalization metadata to status for audit trail
        # (Store as attribute for debugging/logging)
        status.normalized_from = normalized

        logger.info(
            f"Compliance check: {stock.ticker} ({normalized.base_symbol}) → "
            f"{status.is_compliant} (source: {status.source})"
        )

        return status

    def check_batch_compliance(
        self, stocks: List[StockData]
    ) -> Dict[str, ComplianceStatus]:
        """
        Check compliance for multiple stocks with normalization.

        Args:
            stocks: List of StockData objects

        Returns:
            Dictionary mapping original tickers to ComplianceStatus

        Note:
            Uses gateway's batch operation if available, otherwise loops.
        """
        if not stocks:
            return {}

        logger.info(f"Checking compliance for {len(stocks)} stocks (batch)")

        # Normalize all symbols first
        normalized_map: Dict[str, NormalizedSymbol] = {}
        for stock in stocks:
            normalized = self.normalizer.normalize_for_compliance(
                stock.ticker,
                stock.exchange,
            )
            normalized_map[stock.ticker] = normalized

            if self.log_low_confidence and normalized.is_low_confidence():
                logger.warning(
                    f"LOW CONFIDENCE mapping: {stock.ticker} → {normalized.base_symbol}"
                )

        # Build list of normalized base symbols for batch check
        base_symbols = [norm.base_symbol for norm in normalized_map.values()]

        # Check compliance (uses gateway's batch implementation)
        base_statuses = self.gateway.check_batch(base_symbols)

        # Map results back to original tickers
        results: Dict[str, ComplianceStatus] = {}
        for stock in stocks:
            normalized = normalized_map[stock.ticker]
            status = base_statuses.get(normalized.base_symbol)

            if status:
                # Attach normalization info
                status.normalized_from = normalized
                results[stock.ticker] = status
            else:
                # Shouldn't happen, but handle gracefully
                logger.error(f"No compliance result for {stock.ticker}")
                results[stock.ticker] = ComplianceStatus(
                    ticker=stock.ticker,
                    is_compliant=None,
                    reasons=["Internal error: no compliance result"],
                    source="error",
                )

        logger.info(
            f"Batch compliance check completed: {len(results)}/{len(stocks)} successful"
        )

        return results

    def filter_compliant_stocks(
        self, stocks: List[StockData], conservative: bool = True
    ) -> List[StockData]:
        """
        Filter to only halal-compliant stocks.

        Args:
            stocks: List of StockData objects
            conservative: If True, exclude unknowns (default); if False, include unknowns

        Returns:
            List of compliant StockData objects

        Note:
            Conservative mode (default) excludes unknown stocks to maintain
            zero false positives guarantee.
        """
        if not stocks:
            return []

        # Check compliance for all stocks
        statuses = self.check_batch_compliance(stocks)

        # Filter based on compliance status
        compliant_stocks = []
        for stock in stocks:
            status = statuses.get(stock.ticker)
            if not status:
                continue

            # Conservative: only include verified compliant
            if conservative:
                if status.is_compliant is True:
                    compliant_stocks.append(stock)
            else:
                # Non-conservative: include compliant and unknown
                if status.is_compliant is not False:
                    compliant_stocks.append(stock)

        # Log filtering results
        compliant_count = sum(
            1 for s in statuses.values() if s.is_compliant is True
        )
        non_compliant_count = sum(
            1 for s in statuses.values() if s.is_compliant is False
        )
        unknown_count = sum(
            1 for s in statuses.values() if s.is_compliant is None
        )

        logger.info(
            f"Filtered {len(stocks)} stocks → {len(compliant_stocks)} compliant "
            f"({compliant_count} verified, {non_compliant_count} non-compliant, "
            f"{unknown_count} unknown, conservative={conservative})"
        )

        return compliant_stocks

    def get_compliance_summary(
        self, stocks: List[StockData]
    ) -> Dict[str, int]:
        """
        Get summary statistics of compliance for a list of stocks.

        Args:
            stocks: List of StockData objects

        Returns:
            Dictionary with counts:
            - total: Total stocks checked
            - compliant: Verified compliant
            - non_compliant: Verified non-compliant
            - unknown: Unknown status

        Example:
            >>> summary = service.get_compliance_summary(stocks)
            >>> print(f"Compliant: {summary['compliant']}/{summary['total']}")
        """
        if not stocks:
            return {
                "total": 0,
                "compliant": 0,
                "non_compliant": 0,
                "unknown": 0,
            }

        statuses = self.check_batch_compliance(stocks)

        return {
            "total": len(statuses),
            "compliant": sum(1 for s in statuses.values() if s.is_compliant is True),
            "non_compliant": sum(
                1 for s in statuses.values() if s.is_compliant is False
            ),
            "unknown": sum(1 for s in statuses.values() if s.is_compliant is None),
        }
