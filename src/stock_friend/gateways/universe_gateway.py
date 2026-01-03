"""
Universe Gateway for loading stock universes from static data sources.

Provides access to predefined lists of stocks (S&P 500, NASDAQ-100, etc.)
"""

import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from stock_friend.models.stock_data import StockInfo


class IUniverseGateway(ABC):
    """
    Abstract interface for stock universe data providers.

    A universe is a predefined list of stocks (e.g., S&P 500, NASDAQ-100, Russell 2000).
    """

    @abstractmethod
    def get_universe(self, universe_name: str) -> List[StockInfo]:
        """
        Get list of stocks in a specific universe.

        Args:
            universe_name: Name of the universe (e.g., "sp500", "nasdaq100")

        Returns:
            List of StockInfo objects with ticker, company name, sector, industry

        Raises:
            ValueError: If universe_name is not recognized
            FileNotFoundError: If universe data file is missing
        """
        pass

    @abstractmethod
    def list_universes(self) -> List[str]:
        """
        Get list of available universe names.

        Returns:
            List of universe names that can be queried
        """
        pass


class StaticUniverseGateway(IUniverseGateway):
    """
    Universe gateway that loads data from CSV files.

    Loads universe data from CSV files in data/universes/ directory.
    Expected CSV format:
        ticker,company_name,sector,industry
        AAPL,Apple Inc.,Technology,Consumer Electronics
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize gateway.

        Args:
            data_dir: Directory containing universe CSV files
                     (defaults to project_root/data/universes/)
        """
        if data_dir is None:
            # Default to data/universes relative to project root
            # Assuming structure: src/stock_friend/gateways/universe_gateway.py
            project_root = Path(__file__).parent.parent.parent.parent
            data_dir = project_root / "data" / "universes"

        self.data_dir = Path(data_dir)

        if not self.data_dir.exists():
            raise FileNotFoundError(
                f"Universe data directory not found: {self.data_dir}"
            )

    def get_universe(self, universe_name: str) -> List[StockInfo]:
        """
        Load universe from CSV file.

        Args:
            universe_name: Name of universe (e.g., "sp500", "nasdaq100")

        Returns:
            List of StockInfo objects

        Raises:
            ValueError: If universe_name is empty or invalid
            FileNotFoundError: If CSV file for universe doesn't exist
        """
        if not universe_name or not universe_name.strip():
            raise ValueError("Universe name cannot be empty")

        universe_name = universe_name.strip().lower()

        # Build CSV file path
        csv_file = self.data_dir / f"{universe_name}_constituents.csv"

        if not csv_file.exists():
            available = ", ".join(self.list_universes())
            raise FileNotFoundError(
                f"Universe '{universe_name}' not found. "
                f"Available universes: {available}"
            )

        return self._load_csv(csv_file)

    def list_universes(self) -> List[str]:
        """
        List available universes by scanning CSV files.

        Returns:
            List of universe names (without _constituents.csv suffix)
        """
        universes = []

        for csv_file in self.data_dir.glob("*_constituents.csv"):
            # Extract universe name from filename
            # e.g., "sp500_constituents.csv" -> "sp500"
            universe_name = csv_file.stem.replace("_constituents", "")
            universes.append(universe_name)

        return sorted(universes)

    def _load_csv(self, csv_file: Path) -> List[StockInfo]:
        """
        Load stock data from CSV file.

        Args:
            csv_file: Path to CSV file

        Returns:
            List of StockInfo objects

        Raises:
            ValueError: If CSV format is invalid
        """
        stocks = []

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Validate required columns
                required_columns = {'ticker', 'company_name', 'sector', 'industry'}
                if not required_columns.issubset(reader.fieldnames or []):
                    raise ValueError(
                        f"CSV file missing required columns. "
                        f"Expected: {required_columns}, "
                        f"Found: {reader.fieldnames}"
                    )

                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
                    try:
                        ticker = row['ticker'].strip()
                        company_name = row['company_name'].strip()
                        sector = row['sector'].strip() or "Unknown"
                        industry = row['industry'].strip() or "Unknown"

                        if not ticker:
                            continue  # Skip rows with empty ticker

                        stock_info = StockInfo(
                            ticker=ticker,
                            name=company_name,
                            sector=sector,
                            industry=industry
                        )

                        stocks.append(stock_info)

                    except Exception as e:
                        # Log warning but continue processing other rows
                        print(f"Warning: Error parsing row {row_num} in {csv_file.name}: {e}")
                        continue

        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {csv_file}")
        except Exception as e:
            raise ValueError(f"Error reading CSV file {csv_file}: {e}")

        if not stocks:
            raise ValueError(f"No valid stocks found in {csv_file}")

        return stocks
