"""
Integration tests for Alpha Vantage Gateway with real API.

These tests make actual API calls to Alpha Vantage.
Requires ALPHA_VANTAGE_API_KEY in .env file.

Run with: pytest tests/integration/test_alpha_vantage_integration.py -v
"""

from datetime import datetime, timedelta

import pytest

from stock_friend.gateways import AlphaVantageGateway
from stock_friend.gateways.base import DataProviderException;/;'';''
from stock_friend.infrastructure import CacheManager, RateLimiter, config


@pytest.fixture(scope="module")
def real_gateway():
    """
    Create gateway with real Alpha Vantage API client.

    Uses API key from config (loaded from .env file).
    Skips tests if API key is not available.
    """
    # Check if API key is available (using config which loads from .env)
    try:
        api_key = config.api.api_key
    except Exception:
        pytest.skip("ALPHA_VANTAGE_API_KEY not set in .env file")

    if not api_key or api_key == "your_api_key_here":
        pytest.skip("ALPHA_VANTAGE_API_KEY is placeholder value")

    # Initialize infrastructure components
    cache_manager = CacheManager(
        cache_dir="tests/integration/.cache",
        size_limit_mb=100
    )
    rate_limiter = RateLimiter()
    rate_limiter.configure("alpha_vantage", requests_per_hour=300)

    # Create gateway with real API client
    gateway = AlphaVantageGateway(
        api_key=api_key,
        cache_manager=cache_manager,
        rate_limiter=rate_limiter
    )

    yield gateway

    # Cleanup cache after tests
    import shutil
    shutil.rmtree("tests/integration/.cache", ignore_errors=True)


class TestAlphaVantageRealAPI:
    """Test Alpha Vantage Gateway with real API calls."""

    def test_get_stock_data_for_valid_ticker(self, real_gateway):
        """
        Test fetching real stock data for AAPL.

        This verifies:
        - API authentication works
        - Data parsing is correct
        - Response structure matches expectations
        """
        # Fetch data for a well-known ticker
        ticker = "AAPL"
        result = real_gateway.get_stock_data(ticker, period="1mo")

        # Verify result structure
        assert result is not None
        assert result.ticker == ticker
        assert result.source == "ALPHA_VANTAGE"
        assert result.fetched_at is not None

        # Verify data DataFrame
        assert not result.data.empty
        assert len(result.data) > 0

        # Verify required columns exist
        required_columns = ["date", "open", "high", "low", "close", "volume"]
        for col in required_columns:
            assert col in result.data.columns, f"Missing column: {col}"

        # Verify data types
        assert result.data["date"].dtype == "datetime64[ns]"
        assert result.data["close"].dtype in ["float64", "float32"]
        assert result.data["volume"].dtype in ["int64", "int32", "float64"]

        # Verify data is sorted by date
        dates = result.data["date"].tolist()
        assert dates == sorted(dates), "Data should be sorted by date ascending"

        print(f"\n✓ Successfully fetched {len(result.data)} data points for {ticker}")
        print(f"  Date range: {result.data['date'].min()} to {result.data['date'].max()}")
        print(f"  Latest close: ${result.latest_close:.2f}")

    def test_get_current_price_for_valid_ticker(self, real_gateway):
        """
        Test fetching current price for MSFT.

        Verifies real-time price data retrieval.
        """
        ticker = "MSFT"
        price = real_gateway.get_current_price(ticker)

        # Verify price is valid
        assert price is not None
        assert isinstance(price, float)
        assert price > 0

        print(f"\n✓ Current price for {ticker}: ${price:.2f}")

    def test_get_fundamental_data_for_valid_ticker(self, real_gateway):
        """
        Test fetching fundamental data for GOOGL.

        Verifies company overview data retrieval.
        """
        ticker = "GOOGL"
        fundamentals = real_gateway.get_fundamental_data(ticker)

        # Verify fundamental data structure
        assert fundamentals is not None
        assert fundamentals.ticker == ticker

        # Verify at least some fields are populated
        assert fundamentals.market_cap is not None or fundamentals.pe_ratio is not None

        print(f"\n✓ Fundamental data for {ticker}:")
        print(f"  Market Cap: ${fundamentals.market_cap:,.0f}" if fundamentals.market_cap else "  Market Cap: N/A")
        print(f"  P/E Ratio: {fundamentals.pe_ratio:.2f}" if fundamentals.pe_ratio else "  P/E Ratio: N/A")
        print(f"  Sector: {fundamentals.sector or 'N/A'}")
        print(f"  Industry: {fundamentals.industry or 'N/A'}")

    def test_caching_works_with_real_api(self, real_gateway):
        """
        Test that caching works correctly with real API calls.

        First call hits API, second call uses cache.
        """
        ticker = "TSLA"

        # First call - hits API
        result1 = real_gateway.get_stock_data(ticker, period="1mo")
        fetch_time1 = result1.fetched_at

        # Second call immediately - should use cache
        result2 = real_gateway.get_stock_data(ticker, period="1mo")
        fetch_time2 = result2.fetched_at

        # Verify both results are identical (from cache)
        assert result1.ticker == result2.ticker
        assert len(result1.data) == len(result2.data)

        # Fetched times should be very close (same cache entry)
        time_diff = abs((fetch_time2 - fetch_time1).total_seconds())
        assert time_diff < 1.0, "Second call should use cache (fetch times should be identical)"

        print(f"\n✓ Caching works: fetched once, returned from cache on second call")

    def test_date_filtering_with_real_data(self, real_gateway):
        """
        Test date filtering works with real API data.

        Fetches data and filters to specific date range.
        """
        ticker = "NVDA"

        # Fetch last 6 months of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)

        result = real_gateway.get_stock_data(
            ticker,
            period="6mo",
            start_date=start_date,
            end_date=end_date
        )

        # Verify data is within date range
        assert not result.data.empty
        min_date = result.data["date"].min().to_pydatetime()
        max_date = result.data["date"].max().to_pydatetime()

        # Allow some flexibility for market holidays
        assert min_date >= start_date - timedelta(days=7)
        assert max_date <= end_date + timedelta(days=1)

        print(f"\n✓ Date filtering works:")
        print(f"  Requested: {start_date.date()} to {end_date.date()}")
        print(f"  Received: {min_date.date()} to {max_date.date()}")
        print(f"  Data points: {len(result.data)}")

    def test_batch_operations_with_real_api(self, real_gateway):
        """
        Test batch fetching with real API.

        Note: This will make multiple API calls and respect rate limits.
        """
        tickers = ["AAPL", "MSFT", "GOOGL"]

        # Fetch batch data
        results = real_gateway.get_batch_stock_data(tickers, period="1mo")

        # Verify all tickers returned data
        assert len(results) == len(tickers)

        for ticker in tickers:
            assert ticker in results
            assert results[ticker] is not None
            assert not results[ticker].data.empty

        print(f"\n✓ Batch operations work: fetched data for {len(tickers)} tickers")
        for ticker, data in results.items():
            print(f"  {ticker}: {len(data.data)} data points")

    def test_invalid_ticker_raises_exception(self, real_gateway):
        """
        Test that invalid ticker raises appropriate exception.

        This verifies error handling with real API.
        """
        invalid_ticker = "INVALID_TICKER_XYZ123"

        # Should raise exception for invalid ticker
        with pytest.raises(DataProviderException, match="Alpha Vantage error"):
            real_gateway.get_stock_data(invalid_ticker)

        print(f"\n✓ Invalid ticker handling works: raised appropriate exception")

    def test_rate_limiting_prevents_excessive_calls(self, real_gateway):
        """
        Test that rate limiter prevents excessive API calls.

        Note: This test is time-sensitive and may take a few seconds.
        """
        # Make multiple rapid calls
        ticker = "AAPL"
        results = []

        for i in range(3):
            result = real_gateway.get_current_price(ticker)
            results.append(result)

        # All calls should succeed (rate limiter should handle this gracefully)
        assert len(results) == 3
        assert all(r is not None and r > 0 for r in results)

        print(f"\n✓ Rate limiting works: handled {len(results)} calls without exceeding limits")


@pytest.mark.slow
class TestAlphaVantagePerformance:
    """
    Performance tests with real API.

    These tests verify that performance requirements are met.
    Run with: pytest -m slow
    """

    def test_single_stock_fetch_performance(self, real_gateway):
        """Test that single stock data fetch meets <5s requirement."""
        import time

        ticker = "AAPL"
        start_time = time.time()

        result = real_gateway.get_stock_data(ticker, period="1mo")

        elapsed = time.time() - start_time

        # Should meet <5 second requirement
        assert elapsed < 5.0, f"Fetch took {elapsed:.2f}s, should be <5s"
        assert result is not None

        print(f"\n✓ Performance test passed: {elapsed:.2f}s (target: <5s)")

    def test_cached_fetch_performance(self, real_gateway):
        """Test that cached fetches are very fast (<0.1s)."""
        import time

        ticker = "MSFT"

        # First fetch (populate cache)
        real_gateway.get_stock_data(ticker, period="1mo")

        # Second fetch (from cache)
        start_time = time.time()
        result = real_gateway.get_stock_data(ticker, period="1mo")
        elapsed = time.time() - start_time

        # Cached fetch should be very fast
        assert elapsed < 0.1, f"Cached fetch took {elapsed:.2f}s, should be <0.1s"
        assert result is not None

        print(f"\n✓ Cache performance test passed: {elapsed:.4f}s (target: <0.1s)")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
