"""Zoya-specific compliance configuration."""

import logging
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class ZoyaComplianceSettings(BaseSettings):
    """
    Zoya API compliance configuration.

    Zoya provides a GraphQL API with sandbox and live environments.
    Rate limit: 10 requests per second.

    Environment Variables:
        COMPLIANCE_ZOYA_API_KEY: Zoya API key
        COMPLIANCE_ZOYA_ENVIRONMENT: 'sandbox' or 'live'
        COMPLIANCE_ZOYA_API_URL_SANDBOX: Sandbox API URL
        COMPLIANCE_ZOYA_API_URL_LIVE: Live API URL
        COMPLIANCE_ZOYA_REQUESTS_PER_SECOND: Rate limit
        COMPLIANCE_ZOYA_CACHE_TTL_DAYS: Cache TTL in days

    Example:
        >>> settings = ZoyaComplianceSettings()
        >>> print(settings.environment)
        'sandbox'
        >>> print(settings.get_api_url())
        'https://api.zoya.finance/graphql'
    """

    api_key: str = Field(
        default="sandbox-a566b7b5-f0ce-4428-b842-3e3a20a19249",
        description="Zoya API key (sandbox key provided for development)"
    )

    environment: str = Field(
        default="sandbox",
        description="Zoya environment: 'sandbox' or 'live'"
    )

    api_url_sandbox: str = Field(
        default="https://sandbox-api.zoya.finance/graphql",
        description="Zoya sandbox GraphQL endpoint"
    )

    api_url_live: str = Field(
        default="https://api.zoya.finance/graphql",
        description="Zoya live GraphQL endpoint"
    )

    requests_per_second: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Rate limit: requests per second (default: 10)"
    )

    cache_ttl_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Cache TTL for compliance checks in days (default: 30)"
    )

    model_config = SettingsConfigDict(
        env_prefix="COMPLIANCE_ZOYA_",
        case_sensitive=False,
        env_file=".env",
        extra="ignore",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """
        Validate environment.

        Args:
            v: Environment name

        Returns:
            Lowercase environment name

        Raises:
            ValueError: If environment is not 'sandbox' or 'live'
        """
        v_lower = v.lower()
        if v_lower not in {"sandbox", "live"}:
            raise ValueError(
                f"Invalid environment: {v}. Must be 'sandbox' or 'live'"
            )
        return v_lower

    def get_api_url(self) -> str:
        """
        Get API URL based on environment.

        Returns:
            API URL for current environment (sandbox or live)

        Example:
            >>> settings = ZoyaComplianceSettings(environment="sandbox")
            >>> settings.get_api_url()
            'https://api.zoya.finance/graphql'
        """
        return self.api_url_live if self.environment == "live" else self.api_url_sandbox

    def masked_api_key(self) -> str:
        """
        Return masked API key for logging.

        Returns:
            Masked API key (shows first 8 and last 4 characters)

        Example:
            >>> settings = ZoyaComplianceSettings()
            >>> settings.masked_api_key()
            'sandbox-...9249'
        """
        if not self.api_key or len(self.api_key) < 12:
            return "***"
        return f"{self.api_key[:8]}...{self.api_key[-4:]}"

    def get_requests_per_hour(self) -> int:
        """
        Convert requests per second to requests per hour for rate limiter.

        Returns:
            Requests per hour (requests_per_second * 3600)

        Example:
            >>> settings = ZoyaComplianceSettings(requests_per_second=10)
            >>> settings.get_requests_per_hour()
            36000
        """
        return self.requests_per_second * 3600
