"""Base compliance gateway configuration."""

import logging
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class ComplianceSettings(BaseSettings):
    """
    Generic compliance gateway configuration.

    Specifies which provider to use for halal compliance checking.
    Provider-specific settings are in separate files:
    - zoya_compliance_settings.py
    - static_compliance_settings.py

    Environment Variables:
        COMPLIANCE_PROVIDER: Provider name ('zoya' or 'static')

    Example:
        >>> settings = ComplianceSettings()
        >>> print(settings.provider)
        'static'
    """

    provider: str = Field(
        default="static",
        description="Compliance provider: 'zoya' or 'static'"
    )

    model_config = SettingsConfigDict(
        env_prefix="COMPLIANCE_",
        case_sensitive=False,
        env_file=".env",
        extra="ignore",
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """
        Validate provider is supported.

        Args:
            v: Provider name

        Returns:
            Lowercase provider name

        Raises:
            ValueError: If provider is not supported
        """
        v_lower = v.lower()
        valid_providers = {"zoya", "static"}

        if v_lower not in valid_providers:
            raise ValueError(
                f"Invalid provider: {v}. Must be one of: {', '.join(sorted(valid_providers))}"
            )

        return v_lower
