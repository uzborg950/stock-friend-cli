"""
Mock API responses for testing.

Provides realistic mock data for Alpha Vantage API responses.
"""

from datetime import datetime

import pandas as pd


def get_mock_daily_adjusted_data(ticker: str = "AAPL") -> pd.DataFrame:
    """
    Get mock daily adjusted OHLCV data.

    Returns:
        DataFrame with 30 days of mock OHLCV data
    """
    dates = pd.date_range(end=datetime.now(), periods=30, freq="D")

    return pd.DataFrame(
        {
            "date": dates,
            "1. open": [150.0 + i for i in range(30)],
            "2. high": [152.0 + i for i in range(30)],
            "3. low": [149.0 + i for i in range(30)],
            "4. close": [151.0 + i for i in range(30)],
            "5. adjusted close": [151.0 + i for i in range(30)],
            "6. volume": [1000000 + i * 10000 for i in range(30)],
            "7. dividend amount": [0.0] * 30,
            "8. split coefficient": [1.0] * 30,
        }
    )


def get_mock_quote_data(ticker: str = "AAPL") -> pd.DataFrame:
    """
    Get mock quote (current price) data.

    Returns:
        DataFrame with current quote information
    """
    return pd.DataFrame(
        {
            "01. symbol": [ticker],
            "02. open": ["150.00"],
            "03. high": ["152.50"],
            "04. low": ["149.00"],
            "05. price": ["151.25"],
            "06. volume": ["1500000"],
            "07. latest trading day": ["2025-12-24"],
            "08. previous close": ["150.50"],
            "09. change": ["0.75"],
            "10. change percent": ["0.50%"],
        }
    )


def get_mock_company_overview(ticker: str = "AAPL") -> pd.DataFrame:
    """
    Get mock company overview (fundamental data).

    Returns:
        DataFrame with fundamental metrics
    """
    return pd.DataFrame(
        {
            "Symbol": [ticker],
            "Name": ["Apple Inc."],
            "Sector": ["Technology"],
            "Industry": ["Consumer Electronics"],
            "MarketCapitalization": ["3000000000000"],
            "PERatio": ["28.5"],
            "PriceToBookRatio": ["40.2"],
            "PriceToSalesRatioTTM": ["7.8"],
            "PEGRatio": ["2.1"],
            "EPS": ["6.15"],
            "QuarterlyEarningsGrowthYOY": ["0.112"],
            "BookValue": ["3.85"],
            "RevenueTTM": ["385000000000"],
            "QuarterlyRevenueGrowthYOY": ["0.089"],
            "ProfitMargin": ["0.266"],
            "ReturnOnEquityTTM": ["1.569"],
            "DebtToEquity": ["1.73"],
        }
    )


def get_empty_dataframe() -> pd.DataFrame:
    """
    Get empty DataFrame (for testing error cases).

    Returns:
        Empty DataFrame
    """
    return pd.DataFrame()
