"""
Unit tests for ChartPresenter.

Tests the chart presentation logic with mocked plotext calls.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from rich.console import Console

from stock_friend.models.stock_data import StockData
from stock_friend.presenters.chart_presenter import ChartPresenter


@pytest.fixture
def mock_console():
    """Create a mock console."""
    console = Mock(spec=Console)
    console.size = (120, 30)  # Terminal size (width, height)
    return console


@pytest.fixture
def chart_presenter(mock_console):
    """Create ChartPresenter with mocked console."""
    return ChartPresenter(console=mock_console)


@pytest.fixture
def sample_stock_data():
    """Create sample stock data for testing."""
    df = pd.DataFrame(
        {
            "date": pd.date_range(start="2024-11-01", periods=20, freq="D"),
            "open": [100.0 + i for i in range(20)],
            "high": [105.0 + i for i in range(20)],
            "low": [98.0 + i for i in range(20)],
            "close": [102.0 + i for i in range(20)],
            "volume": [1000000 + i * 10000 for i in range(20)],
        }
    )

    return StockData(
        ticker="AAPL",
        data=df,
        fetched_at=datetime.now(),
        source="YFINANCE",
    )


class TestChartPresenterInitialization:
    """Test ChartPresenter initialization."""

    def test_initialization_with_console(self, mock_console):
        """Test initialization with custom console."""
        presenter = ChartPresenter(console=mock_console)
        assert presenter.console is mock_console

    def test_initialization_without_console(self):
        """Test initialization creates default console."""
        presenter = ChartPresenter()
        assert presenter.console is not None
        assert isinstance(presenter.console, Console)


class TestPresentPriceChart:
    """Test present_price_chart method."""

    @patch("stock_friend.presenters.chart_presenter.plt")
    def test_present_candlestick_chart(self, mock_plt, chart_presenter, sample_stock_data):
        """Test candlestick chart display."""
        chart_presenter.present_price_chart(
            stock_data=sample_stock_data,
            chart_type="candlestick",
            period="1mo",
        )

        # Verify plotext methods were called
        mock_plt.clf.assert_called_once()
        mock_plt.theme.assert_called_once_with("dark")
        mock_plt.plotsize.assert_called_once()
        mock_plt.candlestick.assert_called_once()
        mock_plt.title.assert_called_once()
        mock_plt.xlabel.assert_called_once_with("Date")
        mock_plt.ylabel.assert_called_once_with("Price (USD)")
        mock_plt.show.assert_called_once()

    @patch("stock_friend.presenters.chart_presenter.plt")
    def test_present_line_chart(self, mock_plt, chart_presenter, sample_stock_data):
        """Test line chart display."""
        chart_presenter.present_price_chart(
            stock_data=sample_stock_data,
            chart_type="line",
            period="3mo",
        )

        # Verify plotext methods were called
        mock_plt.clf.assert_called_once()
        mock_plt.plot.assert_called_once()  # Only closing price line
        # plotext shows legends automatically, no explicit legend() call
        mock_plt.show.assert_called_once()

    @patch("stock_friend.presenters.chart_presenter.plt")
    def test_present_both_chart(self, mock_plt, chart_presenter, sample_stock_data):
        """Test combined candlestick and line chart."""
        chart_presenter.present_price_chart(
            stock_data=sample_stock_data,
            chart_type="both",
            period="1y",
        )

        # Verify both candlestick and line plot were called
        mock_plt.candlestick.assert_called_once()
        mock_plt.plot.assert_called_once()
        # plotext shows legends automatically, no explicit legend() call
        mock_plt.show.assert_called_once()

    def test_stockdata_validation_rejects_empty_data(self):
        """Test that StockData validation rejects empty DataFrame."""
        # StockData should raise ValueError for empty or invalid data
        with pytest.raises(ValueError, match="Missing required columns"):
            StockData(
                ticker="EMPTY",
                data=pd.DataFrame(),
                fetched_at=datetime.now(),
                source="YFINANCE",
            )

    def test_stockdata_validation_rejects_missing_columns(self):
        """Test that StockData validation rejects missing columns."""
        incomplete_df = pd.DataFrame(
            {
                "date": pd.date_range(start="2024-11-01", periods=5, freq="D"),
                "close": [100.0, 101.0, 102.0, 103.0, 104.0],
                # Missing: open, high, low, volume
            }
        )

        # StockData __post_init__ should reject invalid data
        with pytest.raises(ValueError, match="Missing required columns"):
            StockData(
                ticker="INCOMPLETE",
                data=incomplete_df,
                fetched_at=datetime.now(),
                source="YFINANCE",
            )

    @patch("stock_friend.presenters.chart_presenter.plt")
    def test_present_chart_custom_dimensions(
        self, mock_plt, chart_presenter, sample_stock_data
    ):
        """Test chart with custom width and height."""
        chart_presenter.present_price_chart(
            stock_data=sample_stock_data,
            chart_type="candlestick",
            width=100,
            height=25,
        )

        # Verify custom dimensions were used
        mock_plt.plotsize.assert_called_once_with(100, 25)


class TestPresentVolumeChart:
    """Test present_volume_chart method."""

    @patch("stock_friend.presenters.chart_presenter.plt")
    def test_present_volume_chart(self, mock_plt, chart_presenter, sample_stock_data):
        """Test volume bar chart display."""
        chart_presenter.present_volume_chart(
            stock_data=sample_stock_data,
            period="3mo",
        )

        # Verify plotext methods for bar chart
        mock_plt.clf.assert_called_once()
        mock_plt.theme.assert_called_once_with("dark")
        mock_plt.bar.assert_called_once()
        mock_plt.title.assert_called_once()
        mock_plt.xlabel.assert_called_once_with("Date")
        mock_plt.ylabel.assert_called_once_with("Volume")
        mock_plt.show.assert_called_once()

    def test_stockdata_validation_requires_volume(self):
        """Test that StockData validation requires volume column."""
        no_volume_df = pd.DataFrame(
            {
                "date": pd.date_range(start="2024-11-01", periods=5, freq="D"),
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [105.0, 106.0, 107.0, 108.0, 109.0],
                "low": [98.0, 99.0, 100.0, 101.0, 102.0],
                "close": [102.0, 103.0, 104.0, 105.0, 106.0],
                # Missing volume
            }
        )

        # StockData __post_init__ should reject data without volume
        with pytest.raises(ValueError, match="Missing required columns"):
            StockData(
                ticker="NOVOL",
                data=no_volume_df,
                fetched_at=datetime.now(),
                source="YFINANCE",
            )


class TestDateFormatting:
    """Test date formatting for plotext."""

    @patch("stock_friend.presenters.chart_presenter.plt")
    def test_date_formatting(self, mock_plt, chart_presenter, sample_stock_data):
        """Test that dates are properly formatted for plotext."""
        chart_presenter.present_price_chart(
            stock_data=sample_stock_data,
            chart_type="line",
        )

        # Verify datetimes_to_string was called
        mock_plt.datetimes_to_string.assert_called_once()


class TestChartTypes:
    """Test different chart type rendering."""

    @patch("stock_friend.presenters.chart_presenter.plt")
    def test_all_chart_types(self, mock_plt, chart_presenter, sample_stock_data):
        """Test all three chart types render without errors."""
        chart_types = ["candlestick", "line", "both"]

        for chart_type in chart_types:
            mock_plt.reset_mock()

            chart_presenter.present_price_chart(
                stock_data=sample_stock_data,
                chart_type=chart_type,
                period="1mo",
            )

            # All chart types should call show()
            mock_plt.show.assert_called_once()
            # All chart types should set title
            mock_plt.title.assert_called_once()
