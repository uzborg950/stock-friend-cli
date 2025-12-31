"""
Example script demonstrating how to use the AlphaVantageGateway.

This script shows:
1. How to initialize the gateway with caching and rate limiting
2. How to fetch stock data (OHLCV)
3. How to get current prices
4. How to retrieve fundamental data
5. How to perform batch operations

Requirements:
- Set ALPHA_VANTAGE_API_KEY environment variable
- Or pass API key directly (not recommended for production)
"""

import os
from datetime import datetime, timedelta

from stock_friend.gateways.alpha_vantage_gateway import AlphaVantageGateway
from stock_friend.infrastructure.cache_manager import CacheManager
from stock_friend.infrastructure.rate_limiter import RateLimiter


def main():
    """Run the example."""
    # Get API key from environment variable
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

    if not api_key:
        print("Error: ALPHA_VANTAGE_API_KEY environment variable not set")
        print("Get your free API key from: https://www.alphavantage.co/support/#api-key")
        return

    # Initialize infrastructure components
    print("Initializing cache manager and rate limiter...")
    cache_manager = CacheManager(cache_dir="data/cache", size_limit_mb=100)
    rate_limiter = RateLimiter()

    # Initialize gateway
    print("Initializing Alpha Vantage gateway...")
    gateway = AlphaVantageGateway(
        api_key=api_key, cache_manager=cache_manager, rate_limiter=rate_limiter
    )

    # Example 1: Get stock data (OHLCV)
    print("\n" + "=" * 60)
    print("Example 1: Fetching OHLCV data for AAPL")
    print("=" * 60)

    stock_data = gateway.get_stock_data("AAPL", period="1y")

    print(f"Ticker: {stock_data.ticker}")
    print(f"Source: {stock_data.source}")
    print(f"Data points: {stock_data.period_count}")
    print(f"Date range: {stock_data.date_range[0]} to {stock_data.date_range[1]}")
    print(f"Latest close: ${stock_data.latest_close}")
    print("\nFirst 5 rows:")
    print(stock_data.data.head())

    # Example 2: Get current price
    print("\n" + "=" * 60)
    print("Example 2: Getting current price for MSFT")
    print("=" * 60)

    current_price = gateway.get_current_price("MSFT")
    print(f"Current price: ${current_price}")

    # Example 3: Get fundamental data
    print("\n" + "=" * 60)
    print("Example 3: Fetching fundamental data for GOOGL")
    print("=" * 60)

    fundamental = gateway.get_fundamental_data("GOOGL")

    if fundamental:
        print(f"Company: {fundamental.company_name}")
        print(f"Sector: {fundamental.sector}")
        print(f"Industry: {fundamental.industry}")
        print(f"Market Cap: ${fundamental.market_cap:,.0f}" if fundamental.market_cap else "N/A")
        print(f"P/E Ratio: {fundamental.pe_ratio}" if fundamental.pe_ratio else "N/A")
        print(f"EPS: ${fundamental.eps}" if fundamental.eps else "N/A")
        print(f"Profit Margin: {fundamental.profit_margin*100:.2f}%" if fundamental.profit_margin else "N/A")
    else:
        print("Fundamental data not available")

    # Example 4: Batch operations
    print("\n" + "=" * 60)
    print("Example 4: Batch fetching current prices")
    print("=" * 60)

    tickers = ["AAPL", "MSFT", "GOOGL"]
    print(f"Fetching prices for: {', '.join(tickers)}")

    prices = gateway.get_batch_current_prices(tickers)

    print("\nResults:")
    for ticker, price in prices.items():
        print(f"  {ticker}: ${price}")

    # Example 5: Using date filters
    print("\n" + "=" * 60)
    print("Example 5: Fetching data with date filtering")
    print("=" * 60)

    start_date = datetime.now() - timedelta(days=90)
    end_date = datetime.now() - timedelta(days=30)

    stock_data_filtered = gateway.get_stock_data(
        "TSLA", start_date=start_date, end_date=end_date
    )

    print(f"Ticker: {stock_data_filtered.ticker}")
    print(f"Filtered data points: {stock_data_filtered.period_count}")
    print(f"Date range: {stock_data_filtered.date_range[0]} to {stock_data_filtered.date_range[1]}")

    # Show cache stats
    print("\n" + "=" * 60)
    print("Cache Statistics")
    print("=" * 60)

    stats = cache_manager.get_stats()
    print(f"Entries: {stats['entries']}")
    print(f"Size: {stats['size_mb']} MB")
    print(f"Cache directory: {stats['cache_dir']}")

    # Cleanup
    print("\nClosing cache...")
    cache_manager.close()
    print("Done!")


if __name__ == "__main__":
    main()
