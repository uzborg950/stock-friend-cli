"""
Unit tests for Universe Gateway.

Tests the StaticUniverseGateway with mocked CSV files.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from stock_friend.gateways.universe_gateway import StaticUniverseGateway
from stock_friend.models.stock_data import StockInfo


@pytest.fixture
def mock_data_dir(tmp_path):
    """Create temporary directory with mock CSV files."""
    data_dir = tmp_path / "universes"
    data_dir.mkdir()

    # Create sp500 CSV
    sp500_csv = data_dir / "sp500_constituents.csv"
    sp500_csv.write_text(
        "ticker,company_name,sector,industry\n"
        "AAPL,Apple Inc.,Technology,Consumer Electronics\n"
        "MSFT,Microsoft Corporation,Technology,Software\n"
        "GOOGL,Alphabet Inc.,Technology,Internet Services\n"
    )

    # Create nasdaq100 CSV
    nasdaq_csv = data_dir / "nasdaq100_constituents.csv"
    nasdaq_csv.write_text(
        "ticker,company_name,sector,industry\n"
        "TSLA,Tesla Inc.,Automotive,Electric Vehicles\n"
        "NVDA,NVIDIA Corporation,Technology,Semiconductors\n"
    )

    return data_dir


@pytest.fixture
def gateway(mock_data_dir):
    """Create gateway with mock data directory."""
    return StaticUniverseGateway(data_dir=mock_data_dir)


class TestStaticUniverseGatewayInit:
    """Test gateway initialization."""

    def test_init_with_custom_data_dir(self, mock_data_dir):
        """Should initialize with custom data directory."""
        gateway = StaticUniverseGateway(data_dir=mock_data_dir)
        assert gateway.data_dir == mock_data_dir

    def test_init_without_data_dir_uses_default(self):
        """Should use default data directory when none provided."""
        gateway = StaticUniverseGateway()
        # Should resolve to project_root/data/universes
        assert gateway.data_dir.name == "universes"
        assert gateway.data_dir.parent.name == "data"

    def test_init_raises_error_if_data_dir_not_exists(self, tmp_path):
        """Should raise FileNotFoundError if data directory doesn't exist."""
        non_existent = tmp_path / "does_not_exist"
        with pytest.raises(FileNotFoundError, match="Universe data directory not found"):
            StaticUniverseGateway(data_dir=non_existent)


class TestListUniverses:
    """Test listing available universes."""

    def test_list_universes_returns_available_names(self, gateway):
        """Should return list of universe names from CSV files."""
        universes = gateway.list_universes()
        assert len(universes) == 2
        assert "sp500" in universes
        assert "nasdaq100" in universes

    def test_list_universes_returns_sorted_list(self, gateway):
        """Should return universes in alphabetical order."""
        universes = gateway.list_universes()
        assert universes == sorted(universes)

    def test_list_universes_excludes_non_constituent_files(self, mock_data_dir):
        """Should only include files with _constituents.csv suffix."""
        # Create non-constituent file
        (mock_data_dir / "other_file.csv").write_text("data")

        gateway = StaticUniverseGateway(data_dir=mock_data_dir)
        universes = gateway.list_universes()

        assert "other_file" not in universes
        assert len(universes) == 2  # Only sp500 and nasdaq100

    def test_list_universes_handles_empty_directory(self, tmp_path):
        """Should return empty list if no CSV files exist."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        gateway = StaticUniverseGateway(data_dir=empty_dir)
        universes = gateway.list_universes()

        assert universes == []


class TestGetUniverse:
    """Test loading universe data."""

    def test_get_universe_loads_sp500_successfully(self, gateway):
        """Should load S&P 500 constituents from CSV."""
        stocks = gateway.get_universe("sp500")

        assert len(stocks) == 3
        assert all(isinstance(stock, StockInfo) for stock in stocks)

        # Check first stock
        assert stocks[0].ticker == "AAPL"
        assert stocks[0].name == "Apple Inc."
        assert stocks[0].sector == "Technology"
        assert stocks[0].industry == "Consumer Electronics"

    def test_get_universe_loads_nasdaq100_successfully(self, gateway):
        """Should load NASDAQ-100 constituents from CSV."""
        stocks = gateway.get_universe("nasdaq100")

        assert len(stocks) == 2
        assert stocks[0].ticker == "TSLA"
        assert stocks[1].ticker == "NVDA"

    def test_get_universe_is_case_insensitive(self, gateway):
        """Should handle case-insensitive universe names."""
        stocks_lower = gateway.get_universe("sp500")
        stocks_upper = gateway.get_universe("SP500")
        stocks_mixed = gateway.get_universe("Sp500")

        assert len(stocks_lower) == len(stocks_upper) == len(stocks_mixed) == 3

    def test_get_universe_strips_whitespace_from_name(self, gateway):
        """Should strip whitespace from universe name."""
        stocks = gateway.get_universe("  sp500  ")
        assert len(stocks) == 3

    def test_get_universe_raises_error_for_empty_name(self, gateway):
        """Should raise ValueError for empty universe name."""
        with pytest.raises(ValueError, match="Universe name cannot be empty"):
            gateway.get_universe("")

        with pytest.raises(ValueError, match="Universe name cannot be empty"):
            gateway.get_universe("   ")

    def test_get_universe_raises_error_for_unknown_universe(self, gateway):
        """Should raise FileNotFoundError for unknown universe."""
        with pytest.raises(FileNotFoundError, match="Universe 'unknown' not found"):
            gateway.get_universe("unknown")

    def test_get_universe_error_includes_available_universes(self, gateway):
        """Should include list of available universes in error message."""
        with pytest.raises(FileNotFoundError, match="Available universes: nasdaq100, sp500"):
            gateway.get_universe("missing")

    def test_get_universe_handles_missing_sector_gracefully(self, mock_data_dir):
        """Should default to 'Unknown' for missing sector/industry."""
        csv_file = mock_data_dir / "test_constituents.csv"
        csv_file.write_text(
            "ticker,company_name,sector,industry\n"
            "TEST,Test Corp,,\n"  # Empty sector and industry
        )

        gateway = StaticUniverseGateway(data_dir=mock_data_dir)
        stocks = gateway.get_universe("test")

        assert stocks[0].sector == "Unknown"
        assert stocks[0].industry == "Unknown"

    def test_get_universe_skips_rows_with_empty_ticker(self, mock_data_dir):
        """Should skip rows with empty ticker."""
        csv_file = mock_data_dir / "test_constituents.csv"
        csv_file.write_text(
            "ticker,company_name,sector,industry\n"
            ",Empty Ticker Corp,Tech,Software\n"
            "VALID,Valid Corp,Tech,Software\n"
        )

        gateway = StaticUniverseGateway(data_dir=mock_data_dir)
        stocks = gateway.get_universe("test")

        assert len(stocks) == 1
        assert stocks[0].ticker == "VALID"

    def test_get_universe_handles_malformed_rows_gracefully(self, mock_data_dir, capfd):
        """Should continue processing when encountering malformed rows."""
        csv_file = mock_data_dir / "test_constituents.csv"
        csv_file.write_text(
            "ticker,company_name,sector,industry\n"
            "GOOD1,Good Corp,Tech,Software\n"
            "BAD,Bad Corp\n"  # Missing columns
            "GOOD2,Another Good Corp,Finance,Banking\n"
        )

        gateway = StaticUniverseGateway(data_dir=mock_data_dir)
        stocks = gateway.get_universe("test")

        # Should get the two valid rows
        assert len(stocks) == 2
        assert stocks[0].ticker == "GOOD1"
        assert stocks[1].ticker == "GOOD2"

        # Should print warning about malformed row
        captured = capfd.readouterr()
        assert "Warning" in captured.out
        assert "row 3" in captured.out

    def test_get_universe_raises_error_for_missing_columns(self, mock_data_dir):
        """Should raise ValueError if CSV is missing required columns."""
        csv_file = mock_data_dir / "bad_constituents.csv"
        csv_file.write_text(
            "ticker,name\n"  # Missing company_name, sector, industry
            "AAPL,Apple\n"
        )

        gateway = StaticUniverseGateway(data_dir=mock_data_dir)

        with pytest.raises(ValueError, match="CSV file missing required columns"):
            gateway.get_universe("bad")

    def test_get_universe_raises_error_for_empty_csv(self, mock_data_dir):
        """Should raise ValueError if CSV contains no valid stocks."""
        csv_file = mock_data_dir / "empty_constituents.csv"
        csv_file.write_text(
            "ticker,company_name,sector,industry\n"
            # No data rows
        )

        gateway = StaticUniverseGateway(data_dir=mock_data_dir)

        with pytest.raises(ValueError, match="No valid stocks found"):
            gateway.get_universe("empty")

    def test_get_universe_handles_unicode_company_names(self, mock_data_dir):
        """Should correctly handle Unicode characters in company names."""
        csv_file = mock_data_dir / "international_constituents.csv"
        csv_file.write_text(
            "ticker,company_name,sector,industry\n"
            "ACME,ACME Société Européenne,Consumer Goods,Retail\n"
            "TECH,技術株式会社,Technology,Software\n",
            encoding="utf-8"
        )

        gateway = StaticUniverseGateway(data_dir=mock_data_dir)
        stocks = gateway.get_universe("international")

        assert len(stocks) == 2
        assert "Société" in stocks[0].name
        assert "技術" in stocks[1].name


class TestIntegrationWithRealData:
    """Integration tests with actual S&P 500 data."""

    def test_load_real_sp500_data_if_exists(self):
        """Should load real S&P 500 data from project if it exists."""
        try:
            gateway = StaticUniverseGateway()  # Uses default data dir
            stocks = gateway.get_universe("sp500")

            # Basic sanity checks
            assert len(stocks) > 0
            assert all(isinstance(stock, StockInfo) for stock in stocks)
            assert all(stock.ticker for stock in stocks)
            assert all(stock.name for stock in stocks)

        except FileNotFoundError:
            # Skip test if data doesn't exist yet
            pytest.skip("Real S&P 500 data not available")
