"""
Unit tests for YFinanceGateway.

Tests the YFinance gateway implementation with mocked yfinance library responses.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
import pytest

from stock_friend.gateways.yfinance_gateway import YFinanceGateway
from stock_friend.gateways.base import DataProviderException, InsufficientDataError
from stock_friend.infrastructure.cache_manager import CacheManager
from stock_friend.infrastructure.rate_limiter import RateLimiter
from stock_friend.models.stock_data import StockData


@pytest.fixture
def mock_cache_manager(tmp_path):
    """Create a mock cache manager for testing."""
    cache_dir = tmp_path / "cache"
    return CacheManager(cache_dir=str(cache_dir), size_limit_mb=10)


@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter for testing."""
    return RateLimiter()


@pytest.fixture
def gateway(mock_cache_manager, mock_rate_limiter):
    """Create YFinanceGateway for testing."""
    return YFinanceGateway(
        cache_manager=mock_cache_manager,
        rate_limiter=mock_rate_limiter,
        requests_per_hour=2000,
    )


@pytest.fixture
def gateway_without_infra():
    """Create YFinanceGateway without cache/rate limiter."""
    return YFinanceGateway()


@pytest.fixture
def sample_ohlcv_df():
    """Create sample OHLCV DataFrame."""
    dates = pd.date_range(start="2025-01-01", periods=5, freq="D")
    df = pd.DataFrame(
        {
            "Date": dates,
            "Open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "High": [105.0, 106.0, 107.0, 108.0, 109.0],
            "Low": [95.0, 96.0, 97.0, 98.0, 99.0],
            "Close": [102.0, 103.0, 104.0, 105.0, 106.0],
            "Volume": [1000000, 1100000, 1200000, 1300000, 1400000],
        }
    )
    return df


class TestYFinanceGatewayInitialization:
    """Test YFinanceGateway initialization."""

    def test_initialization_with_all_params(self, mock_cache_manager, mock_rate_limiter):
        """Test initialization with all parameters."""
        gateway = YFinanceGateway(
            cache_manager=mock_cache_manager,
            rate_limiter=mock_rate_limiter,
            requests_per_hour=5000,
        )
        assert gateway.cache_manager is mock_cache_manager
        assert gateway.rate_limiter is mock_rate_limiter
        assert gateway.requests_per_hour == 5000

    def test_initialization_without_params(self):
        """Test initialization without optional parameters."""
        gateway = YFinanceGateway()
        assert gateway.cache_manager is None
        assert gateway.rate_limiter is None
        assert gateway.requests_per_hour == 2000

    def test_get_name_returns_yfinance(self, gateway):
        """Test that get_name returns 'yfinance'."""
        assert gateway.get_name() == "yfinance"


class TestGetStockData:
    """Test get_stock_data method."""

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_stock_data_success(self, mock_ticker_class, gateway, sample_ohlcv_df):
        """Test successful stock data retrieval."""
        # Mock yfinance Ticker
        mock_ticker = Mock()
        mock_ticker.history.return_value = sample_ohlcv_df
        mock_ticker_class.return_value = mock_ticker

        result = gateway.get_stock_data("AAPL", period="1mo")

        assert isinstance(result, StockData)
        assert result.ticker == "AAPL"
        assert result.source == "YFINANCE"
        assert len(result.data) == 5
        assert "date" in result.data.columns
        assert "open" in result.data.columns

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_stock_data_empty_dataframe(self, mock_ticker_class, gateway):
        """Test handling of empty DataFrame."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker

        with pytest.raises(InsufficientDataError, match="No data returned"):
            gateway.get_stock_data("INVALID", period="1mo")

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_stock_data_with_dates(self, mock_ticker_class, gateway, sample_ohlcv_df):
        """Test stock data retrieval with start and end dates."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = sample_ohlcv_df
        mock_ticker_class.return_value = mock_ticker

        start = datetime(2025, 1, 1)
        end = datetime(2025, 1, 5)
        result = gateway.get_stock_data("AAPL", start_date=start, end_date=end)

        assert isinstance(result, StockData)
        mock_ticker.history.assert_called_once_with(start=start, end=end)

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_stock_data_caching(self, mock_ticker_class, gateway, sample_ohlcv_df):
        """Test that stock data is cached."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = sample_ohlcv_df
        mock_ticker_class.return_value = mock_ticker

        # First call - should hit API
        result1 = gateway.get_stock_data("AAPL", period="1mo")
        assert mock_ticker.history.call_count == 1

        # Second call - should hit cache
        result2 = gateway.get_stock_data("AAPL", period="1mo")
        assert mock_ticker.history.call_count == 1  # No additional API call
        assert result1.ticker == result2.ticker

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_stock_data_ticker_normalization(self, mock_ticker_class, gateway, sample_ohlcv_df):
        """Test that ticker is normalized to uppercase."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = sample_ohlcv_df
        mock_ticker_class.return_value = mock_ticker

        result = gateway.get_stock_data("aapl", period="1mo")
        assert result.ticker == "AAPL"

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_stock_data_error_handling(self, mock_ticker_class, gateway):
        """Test error handling when API fails."""
        mock_ticker = Mock()
        mock_ticker.history.side_effect = Exception("Network error")
        mock_ticker_class.return_value = mock_ticker

        with pytest.raises(DataProviderException, match="YFinance error"):
            gateway.get_stock_data("AAPL", period="1mo")


class TestGetBatchStockData:
    """Test get_batch_stock_data method."""

    @patch("stock_friend.gateways.yfinance_gateway.yf.download")
    def test_get_batch_stock_data_single_ticker(self, mock_download, gateway, sample_ohlcv_df):
        """Test batch retrieval with single ticker."""
        mock_download.return_value = sample_ohlcv_df

        result = gateway.get_batch_stock_data(["AAPL"], period="1mo")

        assert len(result) == 1
        assert "AAPL" in result
        assert isinstance(result["AAPL"], StockData)

    @patch("stock_friend.gateways.yfinance_gateway.yf.download")
    def test_get_batch_stock_data_multiple_tickers(self, mock_download, gateway):
        """Test batch retrieval with multiple tickers."""
        # Create mock multi-ticker DataFrame
        dates = pd.date_range(start="2025-01-01", periods=3, freq="D")
        aapl_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": [100, 101, 102],
                "High": [105, 106, 107],
                "Low": [95, 96, 97],
                "Close": [102, 103, 104],
                "Volume": [1000000, 1100000, 1200000],
            }
        )
        msft_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": [200, 201, 202],
                "High": [205, 206, 207],
                "Low": [195, 196, 197],
                "Close": [202, 203, 204],
                "Volume": [2000000, 2100000, 2200000],
            }
        )

        # Mock multi-ticker DataFrame (grouped by ticker)
        multi_df = pd.concat({"AAPL": aapl_data, "MSFT": msft_data}, axis=1)
        mock_download.return_value = multi_df

        result = gateway.get_batch_stock_data(["AAPL", "MSFT"], period="1mo")

        assert len(result) == 2
        assert "AAPL" in result
        assert "MSFT" in result

    @patch("stock_friend.gateways.yfinance_gateway.yf.download")
    def test_get_batch_stock_data_empty_list(self, mock_download, gateway):
        """Test batch retrieval with empty ticker list."""
        result = gateway.get_batch_stock_data([], period="1mo")
        assert result == {}
        mock_download.assert_not_called()

    @patch("stock_friend.gateways.yfinance_gateway.yf.download")
    def test_get_batch_stock_data_partial_failure(self, mock_download, gateway):
        """Test batch retrieval with some tickers failing."""
        # Mock download that returns empty DataFrame for one ticker
        dates = pd.date_range(start="2025-01-01", periods=3, freq="D")
        aapl_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": [100, 101, 102],
                "High": [105, 106, 107],
                "Low": [95, 96, 97],
                "Close": [102, 103, 104],
                "Volume": [1000000, 1100000, 1200000],
            }
        )
        invalid_data = pd.DataFrame()  # Empty for invalid ticker

        multi_df = pd.concat({"AAPL": aapl_data, "INVALID": invalid_data}, axis=1)
        mock_download.return_value = multi_df

        result = gateway.get_batch_stock_data(["AAPL", "INVALID"], period="1mo")

        # Should return successful ticker only
        assert "AAPL" in result
        assert "INVALID" not in result or result.get("INVALID") is None


class TestGetCurrentPrice:
    """Test get_current_price method."""

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_current_price_success(self, mock_ticker_class, gateway):
        """Test successful current price retrieval."""
        mock_ticker = Mock()
        mock_ticker.info = {"currentPrice": 150.50}
        mock_ticker_class.return_value = mock_ticker

        price = gateway.get_current_price("AAPL")

        assert isinstance(price, Decimal)
        assert price == Decimal("150.50")

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_current_price_fallback_to_regular_market_price(
        self, mock_ticker_class, gateway
    ):
        """Test fallback to regularMarketPrice field."""
        mock_ticker = Mock()
        mock_ticker.info = {"regularMarketPrice": 151.75}
        mock_ticker_class.return_value = mock_ticker

        price = gateway.get_current_price("AAPL")
        assert price == Decimal("151.75")

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_current_price_fallback_to_previous_close(self, mock_ticker_class, gateway):
        """Test fallback to previousClose field."""
        mock_ticker = Mock()
        mock_ticker.info = {"previousClose": 149.25}
        mock_ticker_class.return_value = mock_ticker

        price = gateway.get_current_price("AAPL")
        assert price == Decimal("149.25")

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_current_price_no_data(self, mock_ticker_class, gateway):
        """Test error when no price data available."""
        mock_ticker = Mock()
        mock_ticker.info = {}
        mock_ticker_class.return_value = mock_ticker

        with pytest.raises(DataProviderException, match="No price data available"):
            gateway.get_current_price("INVALID")

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_current_price_caching(self, mock_ticker_class, gateway):
        """Test that current price is cached."""
        mock_ticker = Mock()
        mock_ticker.info = {"currentPrice": 150.50}
        mock_ticker_class.return_value = mock_ticker

        # First call
        price1 = gateway.get_current_price("AAPL")

        # Second call - should hit cache
        price2 = gateway.get_current_price("AAPL")

        assert price1 == price2
        # Ticker should only be created once
        assert mock_ticker_class.call_count == 1


class TestGetBatchCurrentPrices:
    """Test get_batch_current_prices method."""

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_batch_current_prices_success(self, mock_ticker_class, gateway):
        """Test batch current price retrieval."""
        # Mock different prices for different tickers
        def ticker_side_effect(symbol):
            mock_ticker = Mock()
            if symbol == "AAPL":
                mock_ticker.info = {"currentPrice": 150.50}
            elif symbol == "MSFT":
                mock_ticker.info = {"currentPrice": 250.75}
            return mock_ticker

        mock_ticker_class.side_effect = ticker_side_effect

        prices = gateway.get_batch_current_prices(["AAPL", "MSFT"])

        assert len(prices) == 2
        assert prices["AAPL"] == Decimal("150.50")
        assert prices["MSFT"] == Decimal("250.75")

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_batch_current_prices_partial_failure(self, mock_ticker_class, gateway):
        """Test batch price retrieval with some failures."""

        def ticker_side_effect(symbol):
            mock_ticker = Mock()
            if symbol == "AAPL":
                mock_ticker.info = {"currentPrice": 150.50}
            else:
                mock_ticker.info = {}  # No price data
            return mock_ticker

        mock_ticker_class.side_effect = ticker_side_effect

        prices = gateway.get_batch_current_prices(["AAPL", "INVALID"])

        # Should only return successful ticker
        assert len(prices) == 1
        assert "AAPL" in prices


class TestGetFundamentalData:
    """Test get_fundamental_data method."""

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_fundamental_data_success(self, mock_ticker_class, gateway):
        """Test successful fundamental data retrieval."""
        mock_ticker = Mock()
        mock_ticker.info = {
            "longName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "marketCap": 3000000000000,
            "trailingPE": 30.5,
            "priceToBook": 40.2,
            "trailingEps": 6.11,
        }
        mock_ticker_class.return_value = mock_ticker

        fundamental = gateway.get_fundamental_data("AAPL")

        assert fundamental is not None
        assert fundamental.ticker == "AAPL"
        assert fundamental.company_name == "Apple Inc."
        assert fundamental.sector == "Technology"
        assert fundamental.market_cap == Decimal("3000000000000")

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_fundamental_data_empty_info(self, mock_ticker_class, gateway):
        """Test fundamental data with empty info."""
        mock_ticker = Mock()
        mock_ticker.info = {}
        mock_ticker_class.return_value = mock_ticker

        fundamental = gateway.get_fundamental_data("INVALID")
        assert fundamental is None

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_fundamental_data_exception(self, mock_ticker_class, gateway):
        """Test that exceptions return None instead of raising."""
        mock_ticker = Mock()
        mock_ticker.info = Mock(side_effect=Exception("API error"))
        mock_ticker_class.return_value = mock_ticker

        # Should return None instead of raising
        fundamental = gateway.get_fundamental_data("AAPL")
        assert fundamental is None

    @patch("stock_friend.gateways.yfinance_gateway.yf.Ticker")
    def test_get_fundamental_data_caching(self, mock_ticker_class, gateway):
        """Test that fundamental data is cached."""
        mock_ticker = Mock()
        mock_ticker.info = {
            "longName": "Apple Inc.",
            "sector": "Technology",
        }
        mock_ticker_class.return_value = mock_ticker

        # First call
        fund1 = gateway.get_fundamental_data("AAPL")

        # Second call - should hit cache
        fund2 = gateway.get_fundamental_data("AAPL")

        assert fund1.company_name == fund2.company_name
        # Ticker should only be created once
        assert mock_ticker_class.call_count == 1
