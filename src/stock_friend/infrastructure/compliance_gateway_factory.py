"""
Compliance gateway factory for creating compliance gateway instances.

Implements Factory Pattern for centralized compliance gateway instantiation with
proper dependency injection.
"""

import logging
from typing import Optional, TYPE_CHECKING

from stock_friend.gateways.compliance.base import IComplianceGateway
from stock_friend.infrastructure.cache_manager import CacheManager
from stock_friend.infrastructure.config import ApplicationConfig
from stock_friend.infrastructure.rate_limiter import RateLimiter

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from stock_friend.gateways.compliance import (
        StaticComplianceGateway,
        ZoyaComplianceGateway,
    )

logger = logging.getLogger(__name__)


class ComplianceGatewayFactory:
    """
    Factory for creating compliance gateway instances.

    Design Pattern: Factory Pattern
    Responsibility: Centralize compliance gateway instantiation with proper dependency injection

    Supported Gateways:
    - static: StaticComplianceGateway (CSV-based, no API key required, default)
    - zoya: ZoyaComplianceGateway (requires API key, sandbox or live)

    Usage:
        >>> config = ApplicationConfig()
        >>> cache = CacheManager()
        >>> rate_limiter = RateLimiter()
        >>> factory = ComplianceGatewayFactory(config, cache, rate_limiter)
        >>> gateway = factory.create_gateway()  # Uses config.compliance.provider
        >>> gateway = factory.create_gateway("zoya")  # Override provider
    """

    SUPPORTED_GATEWAYS = {"static", "zoya"}

    def __init__(
        self,
        config: ApplicationConfig,
        cache_manager: Optional[CacheManager] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        """
        Initialize compliance gateway factory.

        Args:
            config: Application configuration
            cache_manager: Optional cache manager for gateway caching
            rate_limiter: Optional rate limiter for API throttling
        """
        self.config = config
        self.cache_manager = cache_manager
        self.rate_limiter = rate_limiter

        logger.info(
            f"Initialized ComplianceGatewayFactory (default provider: {self.config.compliance.provider})"
        )

    def create_gateway(self, provider: Optional[str] = None) -> IComplianceGateway:
        """
        Create compliance gateway instance.

        Args:
            provider: Gateway provider ("static" or "zoya").
                     If None, uses config.compliance.provider.

        Returns:
            Configured IComplianceGateway instance

        Raises:
            ValueError: If provider is invalid or configuration is missing
        """
        # Use config provider if not explicitly specified
        if provider is None:
            provider = self.config.compliance.provider

        provider = provider.lower()

        # Validate provider
        if provider not in self.SUPPORTED_GATEWAYS:
            raise ValueError(
                f"Unsupported compliance provider: {provider}. "
                f"Must be one of: {', '.join(self.SUPPORTED_GATEWAYS)}"
            )

        logger.info(f"Creating compliance gateway: {provider}")

        # Create appropriate gateway
        if provider == "static":
            return self._create_static_gateway()
        elif provider == "zoya":
            return self._create_zoya_gateway()
        else:
            # Should never reach here due to validation above
            raise ValueError(f"Unsupported provider: {provider}")

    def _create_static_gateway(self) -> "StaticComplianceGateway":
        """
        Create static CSV-based compliance gateway.

        Returns:
            Configured StaticComplianceGateway instance

        Note:
            No API key required for static gateway. Uses CSV data file.
        """
        # Lazy import to avoid circular dependency
        from stock_friend.gateways.compliance import StaticComplianceGateway

        # Get data file path from config, if specified
        data_file = self.config.compliance_static.data_file or None

        gateway = StaticComplianceGateway(data_file=data_file)

        logger.info(
            f"Created StaticComplianceGateway (data file: {gateway.data_file.name})"
        )
        return gateway

    def _create_zoya_gateway(self) -> "ZoyaComplianceGateway":
        """
        Create Zoya compliance gateway with injected dependencies.

        Returns:
            Configured ZoyaComplianceGateway instance

        Raises:
            ValueError: If Zoya API key is not configured
        """
        # Lazy import to avoid circular dependency
        from stock_friend.gateways.compliance import ZoyaComplianceGateway

        # Validate API key is present
        if not self.config.compliance_zoya.api_key:
            raise ValueError(
                "Zoya API key is required when provider=zoya. "
                "Set COMPLIANCE_ZOYA_API_KEY environment variable. "
                "Get your API key from: https://developer.zoya.finance"
            )

        # Validate environment
        environment = self.config.compliance_zoya.environment.lower()
        if environment not in {"sandbox", "live"}:
            raise ValueError(
                f"Invalid Zoya environment: {self.config.compliance_zoya.environment}. "
                f"Must be 'sandbox' or 'live'"
            )

        # Get API URL based on environment (from .env or defaults)
        api_url = self.config.compliance_zoya.get_api_url()

        gateway = ZoyaComplianceGateway(
            api_key=self.config.compliance_zoya.api_key,
            api_url=api_url,
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter,
            cache_ttl_days=self.config.compliance_zoya.cache_ttl_days,
        )

        # Mask API key for logging
        masked_key = (
            f"{self.config.compliance_zoya.api_key[:10]}..."
            if len(self.config.compliance_zoya.api_key) > 10
            else "***"
        )

        logger.info(
            f"Created ZoyaComplianceGateway "
            f"(environment: {environment}, API URL: {api_url}, API key: {masked_key}, "
            f"cache TTL: {self.config.compliance_zoya.cache_ttl_days} days)"
        )
        return gateway
