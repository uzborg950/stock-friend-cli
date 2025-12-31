"""
Unit tests for GatewayFactory.

Tests the factory pattern implementation for creating market data gateways.
"""

import os
import pytest
from unittest.mock import patch, Mock

from stock_friend.gateways.base import IMarketDataGateway
from stock_friend.infrastructure.gateway_factory import GatewayFactory
from stock_friend.infrastructure.config import ApplicationConfig
from stock_friend.infrastructure.cache_manager import CacheManager
from stock_friend.infrastructure.rate_limiter import RateLimiter


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
def config_yfinance():
    """Create config with yfinance as provider."""
    with patch.dict(os.environ, {"MARKET_DATA_PROVIDER": "yfinance"}, clear=True):
        return ApplicationConfig()


@pytest.fixture
def config_alpha_vantage():
    """Create config with alpha_vantage as provider."""
    with patch.dict(
        os.environ,
        {
            "MARKET_DATA_PROVIDER": "alpha_vantage",
            "MARKET_DATA_ALPHA_VANTAGE_API_KEY": "test_key_123",
        },
        clear=True,
    ):
        return ApplicationConfig()


@pytest.fixture
def factory_yfinance(config_yfinance, mock_cache_manager, mock_rate_limiter):
    """Create GatewayFactory with yfinance config."""
    return GatewayFactory(config_yfinance, mock_cache_manager, mock_rate_limiter)


@pytest.fixture
def factory_alpha_vantage(config_alpha_vantage, mock_cache_manager, mock_rate_limiter):
    """Create GatewayFactory with alpha_vantage config."""
    return GatewayFactory(config_alpha_vantage, mock_cache_manager, mock_rate_limiter)


class TestGatewayFactoryInitialization:
    """Test GatewayFactory initialization."""

    def test_initialization_with_yfinance_config(self, factory_yfinance):
        """Test initialization with yfinance configuration."""
        assert factory_yfinance.config.gateway.provider == "yfinance"
        assert factory_yfinance.cache_manager is not None
        assert factory_yfinance.rate_limiter is not None

    def test_initialization_with_alpha_vantage_config(self, factory_alpha_vantage):
        """Test initialization with alpha_vantage configuration."""
        assert factory_alpha_vantage.config.gateway.provider == "alpha_vantage"
        assert factory_alpha_vantage.config.gateway.alpha_vantage_api_key == "test_key_123"


class TestCreateGateway:
    """Test create_gateway method."""

    def test_create_gateway_uses_config_provider_by_default(self, factory_yfinance):
        """Test that create_gateway uses config provider when not specified."""
        gateway = factory_yfinance.create_gateway()
        assert isinstance(gateway, IMarketDataGateway)
        assert gateway.get_name() == "yfinance"

    def test_create_gateway_explicit_yfinance(self, factory_yfinance):
        """Test explicit yfinance gateway creation."""
        gateway = factory_yfinance.create_gateway("yfinance")
        assert gateway.get_name() == "yfinance"

    def test_create_gateway_explicit_alpha_vantage(self, factory_alpha_vantage):
        """Test explicit alpha_vantage gateway creation."""
        gateway = factory_alpha_vantage.create_gateway("alpha_vantage")
        assert gateway.get_name() == "alpha_vantage"

    def test_create_gateway_case_insensitive(self, factory_yfinance):
        """Test that provider parameter is case-insensitive."""
        gateway1 = factory_yfinance.create_gateway("YFINANCE")
        gateway2 = factory_yfinance.create_gateway("yfinance")
        gateway3 = factory_yfinance.create_gateway("YFinance")

        assert gateway1.get_name() == "yfinance"
        assert gateway2.get_name() == "yfinance"
        assert gateway3.get_name() == "yfinance"

    def test_create_gateway_invalid_provider(self, factory_yfinance):
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported gateway provider"):
            factory_yfinance.create_gateway("invalid_provider")

    def test_create_gateway_override_config_provider(self, factory_yfinance):
        """Test overriding config provider with explicit parameter."""
        # Factory configured with yfinance, but override with alpha_vantage
        # This should fail because we don't have an API key
        with pytest.raises(ValueError, match="Alpha Vantage API key is required"):
            factory_yfinance.create_gateway("alpha_vantage")


class TestCreateYFinanceGateway:
    """Test YFinance gateway creation."""

    def test_create_yfinance_gateway_dependencies_injected(self, factory_yfinance):
        """Test that YFinance gateway receives injected dependencies."""
        gateway = factory_yfinance.create_gateway("yfinance")

        assert gateway.cache_manager is factory_yfinance.cache_manager
        assert gateway.rate_limiter is factory_yfinance.rate_limiter

    def test_create_yfinance_gateway_rate_limit_from_config(self, factory_yfinance):
        """Test that YFinance gateway uses rate limit from config."""
        gateway = factory_yfinance.create_gateway("yfinance")

        # Default rate limit should be 2000 from config
        assert gateway.requests_per_hour == 2000

    def test_create_yfinance_gateway_custom_rate_limit(
        self, mock_cache_manager, mock_rate_limiter
    ):
        """Test YFinance gateway with custom rate limit."""
        with patch.dict(
            os.environ, {"MARKET_DATA_YFINANCE_RATE_LIMIT": "5000"}, clear=True
        ):
            config = ApplicationConfig()
            factory = GatewayFactory(config, mock_cache_manager, mock_rate_limiter)
            gateway = factory.create_gateway("yfinance")

            assert gateway.requests_per_hour == 5000


class TestCreateAlphaVantageGateway:
    """Test Alpha Vantage gateway creation."""

    def test_create_alpha_vantage_gateway_with_api_key(self, factory_alpha_vantage):
        """Test Alpha Vantage gateway creation with API key."""
        gateway = factory_alpha_vantage.create_gateway("alpha_vantage")

        assert gateway.api_key == "test_key_123"
        assert gateway.cache_manager is factory_alpha_vantage.cache_manager
        assert gateway.rate_limiter is factory_alpha_vantage.rate_limiter

    def test_create_alpha_vantage_gateway_without_api_key(
        self, mock_cache_manager, mock_rate_limiter
    ):
        """Test Alpha Vantage gateway creation fails without API key."""
        with patch.dict(os.environ, {"MARKET_DATA_PROVIDER": "yfinance"}, clear=True):
            config = ApplicationConfig()
            factory = GatewayFactory(config, mock_cache_manager, mock_rate_limiter)

            with pytest.raises(ValueError, match="Alpha Vantage API key is required"):
                factory.create_gateway("alpha_vantage")

    def test_create_alpha_vantage_gateway_dependencies_injected(
        self, factory_alpha_vantage
    ):
        """Test that Alpha Vantage gateway receives injected dependencies."""
        gateway = factory_alpha_vantage.create_gateway("alpha_vantage")

        assert gateway.cache_manager is factory_alpha_vantage.cache_manager
        assert gateway.rate_limiter is factory_alpha_vantage.rate_limiter


class TestGatewaySwitching:
    """Test switching between different gateway providers."""

    def test_switch_from_yfinance_to_alpha_vantage(
        self, mock_cache_manager, mock_rate_limiter
    ):
        """Test switching from yfinance to alpha_vantage."""
        with patch.dict(
            os.environ,
            {
                "MARKET_DATA_PROVIDER": "yfinance",
                "MARKET_DATA_ALPHA_VANTAGE_API_KEY": "test_key_123",
            },
            clear=True,
        ):
            config = ApplicationConfig()
            factory = GatewayFactory(config, mock_cache_manager, mock_rate_limiter)

            # Default is yfinance
            gateway1 = factory.create_gateway()
            assert gateway1.get_name() == "yfinance"

            # Override to alpha_vantage
            gateway2 = factory.create_gateway("alpha_vantage")
            assert gateway2.get_name() == "alpha_vantage"

    def test_switch_from_alpha_vantage_to_yfinance(
        self, mock_cache_manager, mock_rate_limiter
    ):
        """Test switching from alpha_vantage to yfinance."""
        with patch.dict(
            os.environ,
            {
                "MARKET_DATA_PROVIDER": "alpha_vantage",
                "MARKET_DATA_ALPHA_VANTAGE_API_KEY": "test_key_123",
            },
            clear=True,
        ):
            config = ApplicationConfig()
            factory = GatewayFactory(config, mock_cache_manager, mock_rate_limiter)

            # Default is alpha_vantage
            gateway1 = factory.create_gateway()
            assert gateway1.get_name() == "alpha_vantage"

            # Override to yfinance
            gateway2 = factory.create_gateway("yfinance")
            assert gateway2.get_name() == "yfinance"


class TestGatewayFactoryEdgeCases:
    """Test edge cases and error conditions."""

    def test_supported_gateways_constant(self):
        """Test SUPPORTED_GATEWAYS constant is correct."""
        assert GatewayFactory.SUPPORTED_GATEWAYS == {"yfinance", "alpha_vantage"}

    def test_create_gateway_none_provider_uses_config(self, factory_yfinance):
        """Test that None provider uses config value."""
        gateway = factory_yfinance.create_gateway(None)
        assert gateway.get_name() == "yfinance"

    def test_multiple_gateway_instances_independent(self, factory_yfinance):
        """Test that multiple gateway instances are independent."""
        gateway1 = factory_yfinance.create_gateway("yfinance")
        gateway2 = factory_yfinance.create_gateway("yfinance")

        # Should be different instances
        assert gateway1 is not gateway2

    def test_factory_reusable_for_multiple_creations(self, factory_yfinance):
        """Test that factory can be reused for multiple gateway creations."""
        gateway1 = factory_yfinance.create_gateway()
        gateway2 = factory_yfinance.create_gateway()
        gateway3 = factory_yfinance.create_gateway()

        assert all(g.get_name() == "yfinance" for g in [gateway1, gateway2, gateway3])
