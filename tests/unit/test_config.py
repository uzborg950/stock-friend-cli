"""
Unit tests for configuration management.

Tests the GatewaySettings and ApplicationConfig classes with various
environment variable combinations.
"""

import os
import pytest
from unittest.mock import patch

from stock_friend.infrastructure.config import GatewaySettings, ApplicationConfig


class TestGatewaySettings:
    """Test GatewaySettings configuration class."""

    def test_default_provider_is_yfinance(self):
        """Test that default provider is yfinance."""
        with patch.dict(os.environ, {}, clear=True):
            settings = GatewaySettings()
            assert settings.provider == "yfinance"

    def test_default_yfinance_rate_limit(self):
        """Test that default yfinance rate limit is 2000."""
        with patch.dict(os.environ, {}, clear=True):
            settings = GatewaySettings()
            assert settings.yfinance_rate_limit == 2000

    def test_alpha_vantage_api_key_optional_by_default(self):
        """Test that alpha_vantage_api_key is optional (None by default)."""
        with patch.dict(os.environ, {}, clear=True):
            settings = GatewaySettings()
            assert settings.alpha_vantage_api_key is None

    def test_provider_from_env_variable(self):
        """Test loading provider from MARKET_DATA_PROVIDER env variable."""
        with patch.dict(os.environ, {"MARKET_DATA_PROVIDER": "alpha_vantage"}, clear=True):
            settings = GatewaySettings()
            assert settings.provider == "alpha_vantage"

    def test_provider_case_insensitive(self):
        """Test that provider is case-insensitive."""
        with patch.dict(os.environ, {"MARKET_DATA_PROVIDER": "YFINANCE"}, clear=True):
            settings = GatewaySettings()
            assert settings.provider == "yfinance"

    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises ValueError."""
        with patch.dict(os.environ, {"MARKET_DATA_PROVIDER": "invalid_provider"}, clear=True):
            with pytest.raises(ValueError, match="Invalid provider"):
                GatewaySettings()

    def test_alpha_vantage_api_key_from_env(self):
        """Test loading Alpha Vantage API key from env variable."""
        with patch.dict(
            os.environ,
            {"MARKET_DATA_ALPHA_VANTAGE_API_KEY": "test_key_12345"},
            clear=True,
        ):
            settings = GatewaySettings()
            assert settings.alpha_vantage_api_key == "test_key_12345"

    def test_yfinance_rate_limit_from_env(self):
        """Test loading YFinance rate limit from env variable."""
        with patch.dict(os.environ, {"MARKET_DATA_YFINANCE_RATE_LIMIT": "5000"}, clear=True):
            settings = GatewaySettings()
            assert settings.yfinance_rate_limit == 5000

    def test_yfinance_rate_limit_must_be_positive(self):
        """Test that yfinance_rate_limit must be >= 1."""
        with patch.dict(os.environ, {"MARKET_DATA_YFINANCE_RATE_LIMIT": "0"}, clear=True):
            with pytest.raises(ValueError):
                GatewaySettings()

    def test_validate_config_yfinance_no_api_key_required(self):
        """Test that yfinance provider doesn't require API key."""
        with patch.dict(os.environ, {"MARKET_DATA_PROVIDER": "yfinance"}, clear=True):
            settings = GatewaySettings()
            # Should not raise
            settings.validate_config()

    def test_validate_config_alpha_vantage_requires_api_key(self):
        """Test that alpha_vantage provider requires API key."""
        with patch.dict(os.environ, {"MARKET_DATA_PROVIDER": "alpha_vantage"}, clear=True):
            settings = GatewaySettings()
            with pytest.raises(ValueError, match="MARKET_DATA_ALPHA_VANTAGE_API_KEY is required"):
                settings.validate_config()

    def test_validate_config_alpha_vantage_with_api_key(self):
        """Test that alpha_vantage provider works with API key."""
        with patch.dict(
            os.environ,
            {
                "MARKET_DATA_PROVIDER": "alpha_vantage",
                "MARKET_DATA_ALPHA_VANTAGE_API_KEY": "valid_key_123",
            },
            clear=True,
        ):
            settings = GatewaySettings()
            # Should not raise
            settings.validate_config()

    def test_validate_config_alpha_vantage_placeholder_key_rejected(self):
        """Test that placeholder API key is rejected."""
        with patch.dict(
            os.environ,
            {
                "MARKET_DATA_PROVIDER": "alpha_vantage",
                "MARKET_DATA_ALPHA_VANTAGE_API_KEY": "your_api_key_here",
            },
            clear=True,
        ):
            settings = GatewaySettings()
            with pytest.raises(ValueError, match="MARKET_DATA_ALPHA_VANTAGE_API_KEY is required"):
                settings.validate_config()

    def test_masked_alpha_vantage_key_not_set(self):
        """Test masked key when no API key is set."""
        with patch.dict(os.environ, {}, clear=True):
            settings = GatewaySettings()
            assert settings.masked_alpha_vantage_key() == "N/A"

    def test_masked_alpha_vantage_key_short_key(self):
        """Test masked key with short API key."""
        with patch.dict(
            os.environ, {"MARKET_DATA_ALPHA_VANTAGE_API_KEY": "short"}, clear=True
        ):
            settings = GatewaySettings()
            assert settings.masked_alpha_vantage_key() == "***"

    def test_masked_alpha_vantage_key_normal_key(self):
        """Test masked key with normal length API key."""
        with patch.dict(
            os.environ,
            {"MARKET_DATA_ALPHA_VANTAGE_API_KEY": "abcdefgh12345678"},
            clear=True,
        ):
            settings = GatewaySettings()
            masked = settings.masked_alpha_vantage_key()
            assert masked.startswith("abcd")
            assert masked.endswith("5678")
            assert "..." in masked


class TestApplicationConfig:
    """Test ApplicationConfig facade class."""

    def test_initialization_with_yfinance_default(self):
        """Test initialization with yfinance as default provider."""
        with patch.dict(os.environ, {}, clear=True):
            config = ApplicationConfig()
            assert config.gateway.provider == "yfinance"
            assert config.gateway.alpha_vantage_api_key is None

    def test_initialization_with_alpha_vantage(self):
        """Test initialization with alpha_vantage provider."""
        with patch.dict(
            os.environ,
            {
                "MARKET_DATA_PROVIDER": "alpha_vantage",
                "MARKET_DATA_ALPHA_VANTAGE_API_KEY": "test_key_123",
            },
            clear=True,
        ):
            config = ApplicationConfig()
            assert config.gateway.provider == "alpha_vantage"
            assert config.gateway.alpha_vantage_api_key == "test_key_123"

    def test_initialization_validates_gateway_config(self):
        """Test that initialization validates gateway configuration."""
        with patch.dict(os.environ, {"MARKET_DATA_PROVIDER": "alpha_vantage"}, clear=True):
            with pytest.raises(ValueError, match="MARKET_DATA_ALPHA_VANTAGE_API_KEY is required"):
                ApplicationConfig()

    def test_repr_includes_gateway_info(self):
        """Test that __repr__ includes gateway information."""
        with patch.dict(os.environ, {}, clear=True):
            config = ApplicationConfig()
            repr_str = repr(config)
            assert "gateway.provider=yfinance" in repr_str
            assert "gateway.yfinance_rate_limit" in repr_str

    def test_all_settings_initialized(self):
        """Test that all settings groups are initialized."""
        with patch.dict(os.environ, {}, clear=True):
            config = ApplicationConfig()
            assert config.gateway is not None
            assert config.cache is not None
            assert config.database is not None
            assert config.logging is not None
            assert config.rate_limit is not None
