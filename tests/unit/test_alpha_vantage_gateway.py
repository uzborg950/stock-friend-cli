"""
Unit tests for AlphaVantageGateway.

Tests the Alpha Vantage gateway implementation with mocked API responses.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from stock_friend.gateways.alpha_vantage_gateway import AlphaVantageGateway
from stock_friend.gateways.base import DataProviderException
from stock_friend.infrastructure.cache_manager import CacheManager
from stock_friend.infrastructure.rate_limiter import RateLimiter
from tests.fixtures.mock_responses import (
    get_empty_dataframe,
    get_mock_company_overview,
    get_mock_daily_adjusted_data,
    get_mock_quote_data,
)


@pytest.fixture
def mock_cache_manager(tmp_path):
    """Create a CacheManager for testing."""
    cache_dir = tmp_path / "cache"
    return CacheManager(cache_dir=str(cache_dir), size_limit_mb=10)


@pytest.fixture
def mock_rate_limiter():
    """Create a RateLimiter for testing."""
    return RateLimiter()


@pytest.fixture
def gateway(mock_cache_manager, mock_rate_limiter):
    """Create AlphaVantageGateway for testing."""
    return AlphaVantageGateway(
        api_key="test_api_key",
        cache_manager=mock_cache_manager,
        rate_limiter=mock_rate_limiter,
    )


@pytest.fixture
def gateway_without_infra():
    """Create AlphaVantageGateway without cache/rate limiter."""
    return AlphaVantageGateway(api_key="test_api_key")


class TestAlphaVantageGatewayInitialization:
    """Test gateway initialization."""

    def test_initialization_with_api_key(self):
        """Test gateway initializes with valid API key."""
        gateway = AlphaVantageGateway(api_key="test_key")
        assert gateway.api_key == "test_key"
        assert gateway.get_name() == "alpha_vantage"

    def test_initialization_without_api_key(self):
        """Test gateway raises error without API key."""
        with pytest.raises(ValueError, match="API key is required"):
            AlphaVantageGateway(api_key="")

    def test_initialization_with_infrastructure(
        self, mock_cache_manager, mock_rate_limiter
    ):
        """Test gateway initializes with cache and rate limiter."""
        gateway = AlphaVantageGateway(
            api_key="test_key",
            cache_manager=mock_cache_manager,
            rate_limiter=mock_rate_limiter,
        )
        assert gateway.cache_manager is not None
        assert gateway.rate_limiter is not None


class TestGetStockData:
    """Test get_stock_data method."""

    @patch("alpha_vantage.timeseries.TimeSeries.get_daily_adjusted")
    def test_get_stock_data_success(self, mock_get_daily, gateway):
        """Test successful stock data retrieval."""
        # Setup mock response
        mock_df = get_mock_daily_adjusted_data("AAPL")
        mock_get_daily.return_value = (mock_df, {"Symbol": "AAPL"})

        # Call gateway
        result = gateway.get_stock_data("AAPL")

        # Assertions
        assert result.ticker == "AAPL"
        assert result.source == "ALPHA_VANTAGE"
        assert len(result.data) == 30
        assert "date" in result.data.columns
        assert "open" in result.data.columns
        assert "close" in result.data.columns
        assert "volume" in result.data.columns

        # Verify API was called
        mock_get_daily.assert_called_once()

    @patch("alpha_vantage.timeseries.TimeSeries.get_daily_adjusted")
    def test_get_stock_data_cached(self, mock_get_daily, gateway):
        """Test stock data retrieval uses cache."""
        # Setup mock response
        mock_df = get_mock_daily_adjusted_data("AAPL")
        mock_get_daily.return_value = (mock_df, {"Symbol": "AAPL"})

        # First call - should hit API
        result1 = gateway.get_stock_data("AAPL")
        assert mock_get_daily.call_count == 1

        # Second call - should use cache
        result2 = gateway.get_stock_data("AAPL")
        assert mock_get_daily.call_count == 1  # No additional API call

        # Results should match
        assert result1.ticker == result2.ticker
        assert len(result1.data) == len(result2.data)

    @patch("alpha_vantage.timeseries.TimeSeries.get_daily_adjusted")
    def test_get_stock_data_empty_response(self, mock_get_daily, gateway):
        """Test error handling when API returns empty data."""
        # Setup mock to return empty DataFrame
        mock_get_daily.return_value = (get_empty_dataframe(), {})

        # Should raise DataProviderException (wraps ValueError internally)
        with pytest.raises(DataProviderException, match="No data returned"):
            gateway.get_stock_data("INVALID")

    @patch("alpha_vantage.timeseries.TimeSeries.get_daily_adjusted")
    def test_get_stock_data_with_date_filter(self, mock_get_daily, gateway):
        """Test stock data retrieval with date filtering."""
        # Setup mock response
        mock_df = get_mock_daily_adjusted_data("AAPL")
        mock_get_daily.return_value = (mock_df, {"Symbol": "AAPL"})

        # Call with date range
        start_date = datetime.now() - timedelta(days=10)
        end_date = datetime.now() - timedelta(days=5)

        result = gateway.get_stock_data("AAPL", start_date=start_date, end_date=end_date)

        # Should filter data
        assert len(result.data) < 30  # Less than full dataset

    @patch("alpha_vantage.timeseries.TimeSeries.get_daily_adjusted")
    def test_get_stock_data_api_error(self, mock_get_daily, gateway):
        """Test error handling when API raises exception."""
        # Setup mock to raise exception
        mock_get_daily.side_effect = Exception("API Error")

        # Should raise DataProviderException
        with pytest.raises(DataProviderException, match="Alpha Vantage error"):
            gateway.get_stock_data("AAPL")


class TestGetCurrentPrice:
    """Test get_current_price method."""

    @patch("alpha_vantage.timeseries.TimeSeries.get_quote_endpoint")
    def test_get_current_price_success(self, mock_get_quote, gateway):
        """Test successful current price retrieval."""
        # Setup mock response
        mock_df = get_mock_quote_data("AAPL")
        mock_get_quote.return_value = (mock_df, {})

        # Call gateway
        result = gateway.get_current_price("AAPL")

        # Assertions
        assert isinstance(result, Decimal)
        assert result == Decimal("151.25")

        # Verify API was called
        mock_get_quote.assert_called_once()

    @patch("alpha_vantage.timeseries.TimeSeries.get_quote_endpoint")
    def test_get_current_price_cached(self, mock_get_quote, gateway):
        """Test current price uses cache."""
        # Setup mock response
        mock_df = get_mock_quote_data("AAPL")
        mock_get_quote.return_value = (mock_df, {})

        # First call
        result1 = gateway.get_current_price("AAPL")
        assert mock_get_quote.call_count == 1

        # Second call - should use cache
        result2 = gateway.get_current_price("AAPL")
        assert mock_get_quote.call_count == 1  # No additional call

        assert result1 == result2

    @patch("alpha_vantage.timeseries.TimeSeries.get_quote_endpoint")
    def test_get_current_price_empty_response(self, mock_get_quote, gateway):
        """Test error when quote returns empty data."""
        # Setup mock to return empty DataFrame
        mock_get_quote.return_value = (get_empty_dataframe(), {})

        # Should raise error
        with pytest.raises(DataProviderException, match="No quote data available"):
            gateway.get_current_price("INVALID")


class TestGetFundamentalData:
    """Test get_fundamental_data method."""

    @patch("alpha_vantage.fundamentaldata.FundamentalData.get_company_overview")
    def test_get_fundamental_data_success(self, mock_get_overview, gateway):
        """Test successful fundamental data retrieval."""
        # Setup mock response
        mock_df = get_mock_company_overview("AAPL")
        mock_get_overview.return_value = (mock_df, {})

        # Call gateway
        result = gateway.get_fundamental_data("AAPL")

        # Assertions
        assert result is not None
        assert result.ticker == "AAPL"
        assert result.company_name == "Apple Inc."
        assert result.sector == "Technology"
        assert result.market_cap == Decimal("3000000000000")
        assert result.pe_ratio == 28.5

        # Verify API was called
        mock_get_overview.assert_called_once()

    @patch("alpha_vantage.fundamentaldata.FundamentalData.get_company_overview")
    def test_get_fundamental_data_cached(self, mock_get_overview, gateway):
        """Test fundamental data uses cache."""
        # Setup mock response
        mock_df = get_mock_company_overview("AAPL")
        mock_get_overview.return_value = (mock_df, {})

        # First call
        result1 = gateway.get_fundamental_data("AAPL")
        assert mock_get_overview.call_count == 1

        # Second call - should use cache
        result2 = gateway.get_fundamental_data("AAPL")
        assert mock_get_overview.call_count == 1

        assert result1.ticker == result2.ticker

    @patch("alpha_vantage.fundamentaldata.FundamentalData.get_company_overview")
    def test_get_fundamental_data_empty_response(self, mock_get_overview, gateway):
        """Test fundamental data returns None for empty response."""
        # Setup mock to return empty DataFrame
        mock_get_overview.return_value = (get_empty_dataframe(), {})

        # Should return None (not raise exception)
        result = gateway.get_fundamental_data("INVALID")
        assert result is None

    @patch("alpha_vantage.fundamentaldata.FundamentalData.get_company_overview")
    def test_get_fundamental_data_api_error(self, mock_get_overview, gateway):
        """Test fundamental data returns None on API error."""
        # Setup mock to raise exception
        mock_get_overview.side_effect = Exception("API Error")

        # Should return None (not raise exception)
        result = gateway.get_fundamental_data("AAPL")
        assert result is None


class TestBatchOperations:
    """Test batch operations."""

    @patch("alpha_vantage.timeseries.TimeSeries.get_daily_adjusted")
    def test_get_batch_stock_data(self, mock_get_daily, gateway):
        """Test batch stock data retrieval."""
        # Setup mock to return different data for each ticker
        def mock_response(symbol, outputsize):
            return (get_mock_daily_adjusted_data(symbol), {"Symbol": symbol})

        mock_get_daily.side_effect = mock_response

        # Call gateway with multiple tickers
        tickers = ["AAPL", "MSFT", "GOOGL"]
        results = gateway.get_batch_stock_data(tickers)

        # Assertions
        assert len(results) == 3
        assert "AAPL" in results
        assert "MSFT" in results
        assert "GOOGL" in results

        # Verify API was called for each ticker
        assert mock_get_daily.call_count == 3

    @patch("alpha_vantage.timeseries.TimeSeries.get_quote_endpoint")
    def test_get_batch_current_prices(self, mock_get_quote, gateway):
        """Test batch current price retrieval."""
        # Setup mock
        mock_df = get_mock_quote_data("AAPL")
        mock_get_quote.return_value = (mock_df, {})

        # Call gateway with multiple tickers
        tickers = ["AAPL", "MSFT"]
        results = gateway.get_batch_current_prices(tickers)

        # Assertions
        assert len(results) == 2
        assert "AAPL" in results
        assert "MSFT" in results
        assert all(isinstance(price, Decimal) for price in results.values())


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiter_configured(self, mock_rate_limiter):
        """Test rate limiter is configured on initialization."""
        gateway = AlphaVantageGateway(
            api_key="test_key", rate_limiter=mock_rate_limiter
        )

        # Verify rate limiter has the alpha_vantage bucket
        assert "alpha_vantage" in mock_rate_limiter.buckets

    @patch("alpha_vantage.timeseries.TimeSeries.get_daily_adjusted")
    def test_rate_limiter_called(self, mock_get_daily, gateway):
        """Test rate limiter is invoked before API calls."""
        # Setup mock
        mock_df = get_mock_daily_adjusted_data("AAPL")
        mock_get_daily.return_value = (mock_df, {"Symbol": "AAPL"})

        # Call gateway
        gateway.get_stock_data("AAPL")

        # Rate limiter should have consumed a token
        available_tokens = gateway.rate_limiter.get_available_tokens("alpha_vantage")
        assert available_tokens < 300  # Should be less than initial capacity
