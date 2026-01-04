"""
Unit tests for ComplianceGatewayFactory.

Tests factory creation of compliance gateways with proper dependency injection.
"""

from unittest.mock import Mock, patch

import pytest

from stock_friend.gateways.compliance import (
    StaticComplianceGateway,
    ZoyaComplianceGateway,
)
from stock_friend.infrastructure.cache_manager import CacheManager
from stock_friend.infrastructure.compliance_gateway_factory import (
    ComplianceGatewayFactory,
)
from stock_friend.infrastructure.config import ApplicationConfig
from stock_friend.infrastructure.rate_limiter import RateLimiter


class TestComplianceGatewayFactoryInitialization:
    """Test factory initialization."""

    def test_init_with_all_dependencies(self):
        """Test initialization with all dependencies."""
        config = ApplicationConfig()
        cache = Mock(spec=CacheManager)
        rate_limiter = Mock(spec=RateLimiter)

        factory = ComplianceGatewayFactory(
            config=config,
            cache_manager=cache,
            rate_limiter=rate_limiter,
        )

        assert factory.config is config
        assert factory.cache_manager is cache
        assert factory.rate_limiter is rate_limiter

    def test_init_with_optional_dependencies(self):
        """Test initialization with optional dependencies as None."""
        config = ApplicationConfig()

        factory = ComplianceGatewayFactory(config=config)

        assert factory.config is config
        assert factory.cache_manager is None
        assert factory.rate_limiter is None


class TestCreateStaticGateway:
    """Test static gateway creation."""

    def test_create_static_gateway_default_provider(self):
        """Test creating static gateway as default provider."""
        config = ApplicationConfig()
        # Ensure static is the default
        config.compliance.provider = "static"

        factory = ComplianceGatewayFactory(config=config)
        gateway = factory.create_gateway()

        assert isinstance(gateway, StaticComplianceGateway)
        assert gateway.get_name() == "static"

    def test_create_static_gateway_explicit_provider(self):
        """Test creating static gateway with explicit provider."""
        config = ApplicationConfig()
        factory = ComplianceGatewayFactory(config=config)

        gateway = factory.create_gateway(provider="static")

        assert isinstance(gateway, StaticComplianceGateway)

    def test_create_static_gateway_case_insensitive(self):
        """Test provider name is case-insensitive."""
        config = ApplicationConfig()
        factory = ComplianceGatewayFactory(config=config)

        gateway = factory.create_gateway(provider="STATIC")

        assert isinstance(gateway, StaticComplianceGateway)


class TestCreateZoyaGateway:
    """Test Zoya gateway creation."""

    def test_create_zoya_gateway_sandbox(self):
        """Test creating Zoya gateway in sandbox environment."""
        config = ApplicationConfig()
        config.compliance_zoya.api_key = "sandbox-test-key"
        config.compliance_zoya.environment = "sandbox"
        config.compliance_zoya.cache_ttl_days = 30

        cache = Mock(spec=CacheManager)
        rate_limiter = Mock(spec=RateLimiter)

        factory = ComplianceGatewayFactory(
            config=config,
            cache_manager=cache,
            rate_limiter=rate_limiter,
        )

        gateway = factory.create_gateway(provider="zoya")

        assert isinstance(gateway, ZoyaComplianceGateway)
        assert gateway.get_name() == "zoya_sandbox"
        assert gateway.api_key == "sandbox-test-key"
        assert gateway.environment == "sandbox"
        assert gateway.cache_manager is cache
        assert gateway.rate_limiter is rate_limiter
        assert gateway.cache_ttl_days == 30

    def test_create_zoya_gateway_live(self):
        """Test creating Zoya gateway in live environment."""
        config = ApplicationConfig()
        config.compliance_zoya.api_key = "live-test-key"
        config.compliance_zoya.environment = "live"

        factory = ComplianceGatewayFactory(config=config)
        gateway = factory.create_gateway(provider="zoya")

        assert isinstance(gateway, ZoyaComplianceGateway)
        assert gateway.get_name() == "zoya_live"
        assert gateway.environment == "live"

    def test_create_zoya_gateway_normalizes_environment_case(self):
        """Test that environment is normalized to lowercase."""
        config = ApplicationConfig()
        config.compliance_zoya.api_key = "test-key"
        config.compliance_zoya.environment = "SANDBOX"

        factory = ComplianceGatewayFactory(config=config)
        gateway = factory.create_gateway(provider="zoya")

        assert gateway.environment == "sandbox"

    def test_create_zoya_gateway_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        config = ApplicationConfig()
        config.compliance_zoya.api_key = ""  # Empty API key

        factory = ComplianceGatewayFactory(config=config)

        with pytest.raises(ValueError, match="Zoya API key is required"):
            factory.create_gateway(provider="zoya")

    def test_create_zoya_gateway_invalid_environment_raises_error(self):
        """Test that invalid environment raises ValueError."""
        config = ApplicationConfig()
        config.compliance_zoya.api_key = "test-key"
        config.compliance_zoya.environment = "invalid"

        factory = ComplianceGatewayFactory(config=config)

        with pytest.raises(ValueError, match="Invalid Zoya environment"):
            factory.create_gateway(provider="zoya")


class TestInvalidProvider:
    """Test invalid provider handling."""

    def test_create_gateway_invalid_provider_raises_error(self):
        """Test that invalid provider raises ValueError."""
        config = ApplicationConfig()
        factory = ComplianceGatewayFactory(config=config)

        with pytest.raises(ValueError, match="Unsupported compliance provider"):
            factory.create_gateway(provider="invalid_provider")

    def test_supported_gateways_constant(self):
        """Test that SUPPORTED_GATEWAYS constant is correctly defined."""
        assert ComplianceGatewayFactory.SUPPORTED_GATEWAYS == {"static", "zoya"}


class TestProviderOverride:
    """Test provider override functionality."""

    def test_create_gateway_uses_config_provider_by_default(self):
        """Test that create_gateway uses config provider when not specified."""
        config = ApplicationConfig()
        config.compliance.provider = "static"

        factory = ComplianceGatewayFactory(config=config)
        gateway = factory.create_gateway()  # No provider specified

        assert isinstance(gateway, StaticComplianceGateway)

    def test_create_gateway_overrides_config_provider(self):
        """Test that explicit provider overrides config provider."""
        config = ApplicationConfig()
        config.compliance.provider = "static"
        config.compliance_zoya.api_key = "test-key"
        config.compliance_zoya.environment = "sandbox"

        factory = ComplianceGatewayFactory(config=config)
        gateway = factory.create_gateway(provider="zoya")  # Override to zoya

        assert isinstance(gateway, ZoyaComplianceGateway)


class TestDependencyInjection:
    """Test dependency injection into gateways."""

    def test_static_gateway_no_dependencies_required(self):
        """Test that static gateway can be created without cache/rate limiter."""
        config = ApplicationConfig()
        factory = ComplianceGatewayFactory(config=config)

        gateway = factory.create_gateway(provider="static")

        # Should succeed without cache_manager or rate_limiter
        assert isinstance(gateway, StaticComplianceGateway)

    def test_zoya_gateway_receives_dependencies(self):
        """Test that Zoya gateway receives injected dependencies."""
        config = ApplicationConfig()
        config.compliance_zoya.api_key = "test-key"

        cache = Mock(spec=CacheManager)
        rate_limiter = Mock(spec=RateLimiter)

        factory = ComplianceGatewayFactory(
            config=config,
            cache_manager=cache,
            rate_limiter=rate_limiter,
        )

        gateway = factory.create_gateway(provider="zoya")

        assert gateway.cache_manager is cache
        assert gateway.rate_limiter is rate_limiter
        # Verify rate limiter was configured (called during __init__)
        rate_limiter.configure.assert_called_once()

    def test_zoya_gateway_without_dependencies_still_works(self):
        """Test that Zoya gateway can be created without cache/rate limiter."""
        config = ApplicationConfig()
        config.compliance_zoya.api_key = "test-key"

        factory = ComplianceGatewayFactory(config=config)
        gateway = factory.create_gateway(provider="zoya")

        assert gateway.cache_manager is None
        assert gateway.rate_limiter is None
