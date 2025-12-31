"""
Gateway factory for creating market data gateway instances.

Implements Factory Pattern for centralized gateway instantiation with
proper dependency injection.
"""

import logging
from typing import Optional, TYPE_CHECKING

from stock_friend.gateways.base import IMarketDataGateway
from stock_friend.infrastructure.cache_manager import CacheManager
from stock_friend.infrastructure.config import ApplicationConfig
from stock_friend.infrastructure.rate_limiter import RateLimiter

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from stock_friend.gateways.alpha_vantage_gateway import AlphaVantageGateway
    from stock_friend.gateways.yfinance_gateway import YFinanceGateway

logger = logging.getLogger(__name__)


class GatewayFactory:
    """
    Factory for creating market data gateway instances.

    Design Pattern: Factory Pattern
    Responsibility: Centralize gateway instantiation with proper dependency injection

    Supported Gateways:
    - yfinance: YFinanceGateway (no API key required, default)
    - alpha_vantage: AlphaVantageGateway (requires API key)

    Usage:
        >>> config = ApplicationConfig()
        >>> cache = CacheManager()
        >>> rate_limiter = RateLimiter()
        >>> factory = GatewayFactory(config, cache, rate_limiter)
        >>> gateway = factory.create_gateway()  # Uses config.gateway.provider
        >>> gateway = factory.create_gateway("alpha_vantage")  # Override provider
    """

    SUPPORTED_GATEWAYS = {"yfinance", "alpha_vantage"}

    def __init__(
        self,
        config: ApplicationConfig,
        cache_manager: CacheManager,
        rate_limiter: RateLimiter,
    ):
        """
        Initialize gateway factory.

        Args:
            config: Application configuration
            cache_manager: Cache manager for gateway caching
            rate_limiter: Rate limiter for API throttling
        """
        self.config = config
        self.cache_manager = cache_manager
        self.rate_limiter = rate_limiter

        logger.info(
            f"Initialized GatewayFactory (default provider: {self.config.gateway.provider})"
        )

    def create_gateway(self, provider: Optional[str] = None) -> IMarketDataGateway:
        """
        Create market data gateway instance.

        Args:
            provider: Gateway provider ("yfinance" or "alpha_vantage").
                     If None, uses config.gateway.provider.

        Returns:
            Configured IMarketDataGateway instance

        Raises:
            ValueError: If provider is invalid or configuration is missing
        """
        # Use config provider if not explicitly specified
        if provider is None:
            provider = self.config.gateway.provider

        provider = provider.lower()

        # Validate provider
        if provider not in self.SUPPORTED_GATEWAYS:
            raise ValueError(
                f"Unsupported gateway provider: {provider}. "
                f"Must be one of: {', '.join(self.SUPPORTED_GATEWAYS)}"
            )

        logger.info(f"Creating gateway: {provider}")

        # Create appropriate gateway
        if provider == "yfinance":
            return self._create_yfinance_gateway()
        elif provider == "alpha_vantage":
            return self._create_alpha_vantage_gateway()
        else:
            # Should never reach here due to validation above
            raise ValueError(f"Unsupported provider: {provider}")

    def _create_yfinance_gateway(self) -> "YFinanceGateway":
        """
        Create YFinance gateway with injected dependencies.

        Returns:
            Configured YFinanceGateway instance

        Note:
            No API key required for YFinance
        """
        # Lazy import to avoid circular dependency
        from stock_friend.gateways.yfinance_gateway import YFinanceGateway

        gateway = YFinanceGateway(
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter,
            requests_per_hour=self.config.gateway.yfinance_rate_limit,
        )

        logger.info(
            f"Created YFinanceGateway (rate limit: {self.config.gateway.yfinance_rate_limit} req/hour)"
        )
        return gateway

    def _create_alpha_vantage_gateway(self) -> "AlphaVantageGateway":
        """
        Create Alpha Vantage gateway with injected dependencies.

        Returns:
            Configured AlphaVantageGateway instance

        Raises:
            ValueError: If Alpha Vantage API key is not configured
        """
        # Lazy import to avoid circular dependency
        from stock_friend.gateways.alpha_vantage_gateway import AlphaVantageGateway

        # Validate API key is present
        if not self.config.gateway.alpha_vantage_api_key:
            raise ValueError(
                "Alpha Vantage API key is required when provider=alpha_vantage. "
                "Set MARKET_DATA_ALPHA_VANTAGE_API_KEY environment variable. "
                "Get your free API key from: https://www.alphavantage.co/support/#api-key"
            )

        gateway = AlphaVantageGateway(
            api_key=self.config.gateway.alpha_vantage_api_key,
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter,
        )

        logger.info(
            f"Created AlphaVantageGateway (API key: {self.config.gateway.masked_alpha_vantage_key()})"
        )
        return gateway
