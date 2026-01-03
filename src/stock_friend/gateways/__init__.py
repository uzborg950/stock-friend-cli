"""
Data access gateways for external APIs.

This module contains gateway interfaces and implementations for accessing
external data sources (Alpha Vantage, compliance APIs, etc.).
"""

from stock_friend.gateways.base import IMarketDataGateway
from stock_friend.gateways.alpha_vantage_gateway import AlphaVantageGateway
from stock_friend.gateways.yfinance_gateway import YFinanceGateway
from stock_friend.gateways.universe_gateway import IUniverseGateway, StaticUniverseGateway

__all__ = [
    "IMarketDataGateway",
    "AlphaVantageGateway",
    "YFinanceGateway",
    "IUniverseGateway",
    "StaticUniverseGateway",
]
