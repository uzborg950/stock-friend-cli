"""
Static CSV-based compliance gateway implementation.

Loads compliance data from local CSV file for testing and offline use.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from stock_friend.gateways.compliance.base import IComplianceGateway
from stock_friend.models.compliance import ComplianceStatus

logger = logging.getLogger(__name__)


class StaticComplianceGateway(IComplianceGateway):
    """
    CSV-based compliance gateway for testing and offline use.

    Loads compliance data from CSV file with format:
        ticker,is_compliant,reasons,source,last_updated
        AAPL,True,,manual,2026-01-03
        JPM,False,Conventional bank,manual,2026-01-03

    Features:
    - No API required (offline capable)
    - Fast in-memory lookups
    - Accurate data reporting (unknown tickers return unknown status)
    - Useful for testing, development, and demos

    Design Principle:
        If ticker not found in CSV → return UNKNOWN status
        Data accuracy is paramount - we report what we know truthfully.

    Performance:
    - check_compliance: <1ms (in-memory lookup)
    - check_batch: <10ms for 100 stocks (in-memory)
    - filter_compliant: <10ms for 100 stocks

    Example:
        >>> gateway = StaticComplianceGateway()
        >>> status = gateway.check_compliance("AAPL")
        >>> print(status.is_compliant)
        True
        >>> compliant = gateway.filter_compliant(["AAPL", "JPM", "GOOGL"])
        >>> print(compliant)
        ['AAPL', 'GOOGL']
    """

    def __init__(self, data_file: Optional[Path] = None):
        """
        Initialize static compliance gateway.

        Args:
            data_file: Path to CSV file (default: data/compliance/halal_compliant_stocks.csv)

        Raises:
            FileNotFoundError: If data file doesn't exist (logged as warning, continues with empty data)
        """
        if data_file is None:
            # Default to project root / data/compliance/halal_compliant_stocks.csv
            project_root = Path(__file__).parent.parent.parent.parent.parent
            data_file = project_root / "data" / "compliance" / "halal_compliant_stocks.csv"

        self.data_file = Path(data_file)
        self._compliance_data: Dict[str, ComplianceStatus] = {}

        if self.data_file.exists():
            self._load_data()
            logger.info(
                f"Loaded {len(self._compliance_data)} stocks from {self.data_file.name}"
            )
        else:
            logger.warning(
                f"Compliance data file not found: {self.data_file}. "
                f"Operating with empty dataset (all stocks will return unknown status)."
            )

    def check_compliance(self, ticker: str) -> ComplianceStatus:
        """
        Check if single stock is halal-compliant.

        Args:
            ticker: Stock ticker symbol

        Returns:
            ComplianceStatus object with is_compliant=None if ticker not in database

        Note:
            Unknown tickers return unknown status (is_compliant=None) for data accuracy.
        """
        ticker = ticker.upper().strip()

        if not ticker:
            raise ValueError("Ticker cannot be empty")

        # Lookup in cached data
        if ticker in self._compliance_data:
            logger.debug(f"{ticker} found in static database: {self._compliance_data[ticker].is_compliant}")
            return self._compliance_data[ticker]

        # Return unknown status for tickers not in database
        logger.debug(f"{ticker} not in static database. Returning unknown status.")
        return ComplianceStatus(
            ticker=ticker,
            is_compliant=None,  # Unknown status
            reasons=["No compliance data available in database"],
            source="unknown",
            checked_at=datetime.now(),
        )

    def check_batch(self, tickers: List[str]) -> Dict[str, ComplianceStatus]:
        """
        Check multiple stocks at once (batch operation).

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping tickers to ComplianceStatus objects

        Note:
            Very fast (in-memory lookups). Unknown tickers return unknown status.
        """
        if not tickers:
            return {}

        tickers = [ticker.upper().strip() for ticker in tickers if ticker.strip()]
        results = {}

        for ticker in tickers:
            try:
                results[ticker] = self.check_compliance(ticker)
            except Exception as e:
                logger.error(f"Error checking compliance for {ticker}: {e}")
                # On error, return unknown status
                results[ticker] = ComplianceStatus(
                    ticker=ticker,
                    is_compliant=None,
                    reasons=[f"Error during check: {e}"],
                    source="unknown",
                )

        logger.debug(f"Batch check completed: {len(results)}/{len(tickers)} successful")
        return results

    def filter_compliant(self, tickers: List[str]) -> List[str]:
        """
        Filter universe to only halal-compliant stock tickers.

        Args:
            tickers: List of ticker symbols to filter

        Returns:
            List of compliant ticker symbols only (excludes non-compliant and unknown)

        Note:
            Only returns stocks with is_compliant=True. Excludes both non-compliant
            stocks (is_compliant=False) and unknown stocks (is_compliant=None).

        Example:
            >>> gateway = StaticComplianceGateway()
            >>> tickers = ["AAPL", "JPM", "GOOGL", "UNKNOWN"]
            >>> compliant = gateway.filter_compliant(tickers)
            >>> print(compliant)
            ['AAPL', 'GOOGL']  # Excludes JPM (non-compliant) and UNKNOWN (no data)
        """
        statuses = self.check_batch(tickers)

        # Only include stocks with is_compliant=True (excludes False and None)
        compliant_tickers = [
            ticker for ticker, status in statuses.items() if status.is_compliant is True
        ]

        # Count different statuses for logging
        non_compliant = sum(1 for s in statuses.values() if s.is_compliant is False)
        unknown = sum(1 for s in statuses.values() if s.is_compliant is None)

        logger.info(
            f"Filtered {len(tickers)} stocks → {len(compliant_tickers)} compliant, "
            f"{non_compliant} non-compliant, {unknown} unknown"
        )

        return compliant_tickers

    def _load_data(self) -> None:
        """
        Load compliance data from CSV file into memory.

        CSV Format:
            ticker,is_compliant,reasons,source,last_updated
            AAPL,True,,manual,2026-01-03
            JPM,False,Conventional bank,manual,2026-01-03

        Raises:
            ValueError: If CSV format is invalid (logged but continues)
        """
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Validate required columns
                required_columns = {'ticker', 'is_compliant', 'reasons', 'source'}
                if not required_columns.issubset(reader.fieldnames or []):
                    logger.error(
                        f"CSV file missing required columns. "
                        f"Expected: {required_columns}, Found: {reader.fieldnames}"
                    )
                    return

                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
                    try:
                        ticker = row['ticker'].strip().upper()
                        is_compliant_str = row['is_compliant'].strip().lower()
                        reasons_str = row.get('reasons', '').strip()
                        source = row.get('source', 'static').strip()
                        last_updated_str = row.get('last_updated', '').strip()

                        if not ticker:
                            continue  # Skip rows with empty ticker

                        # Parse is_compliant
                        is_compliant = is_compliant_str == 'true'

                        # Parse reasons (semicolon-separated)
                        reasons = []
                        if reasons_str:
                            reasons = [r.strip() for r in reasons_str.split(';') if r.strip()]

                        # Parse last_updated
                        checked_at = datetime.now()
                        if last_updated_str:
                            try:
                                checked_at = datetime.strptime(last_updated_str, '%Y-%m-%d')
                            except ValueError:
                                logger.warning(
                                    f"Invalid date format for {ticker} at row {row_num}: {last_updated_str}"
                                )

                        # Create ComplianceStatus
                        status = ComplianceStatus(
                            ticker=ticker,
                            is_compliant=is_compliant,
                            reasons=reasons,
                            source=source,
                            checked_at=checked_at,
                        )

                        self._compliance_data[ticker] = status

                    except Exception as e:
                        logger.warning(
                            f"Error parsing row {row_num} in {self.data_file.name}: {e}. Skipping row."
                        )
                        continue

        except FileNotFoundError:
            logger.error(f"CSV file not found: {self.data_file}")
            raise
        except Exception as e:
            logger.error(f"Error reading CSV file {self.data_file}: {e}")
            # Don't raise - continue with whatever data was loaded
            pass

    def get_name(self) -> str:
        """
        Return unique gateway identifier.

        Returns:
            Gateway name "static"
        """
        return "static"

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about loaded compliance data.

        Returns:
            Dictionary with statistics:
            - total: Total stocks in database
            - compliant: Number of compliant stocks
            - non_compliant: Number of non-compliant stocks

        Example:
            >>> gateway = StaticComplianceGateway()
            >>> stats = gateway.get_stats()
            >>> print(f"Loaded {stats['total']} stocks")
        """
        compliant_count = sum(
            1 for status in self._compliance_data.values() if status.is_compliant
        )
        non_compliant_count = len(self._compliance_data) - compliant_count

        return {
            "total": len(self._compliance_data),
            "compliant": compliant_count,
            "non_compliant": non_compliant_count,
        }
