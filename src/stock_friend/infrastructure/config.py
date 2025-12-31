"""
Centralized configuration management using Pydantic Settings.

Handles environment variables, .env file loading, and configuration validation.
"""

import logging
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class GatewaySettings(BaseSettings):
    """Market data gateway configuration."""

    provider: str = Field(
        default="yfinance",
        description="Market data provider: 'yfinance' (default, no API key) or 'alpha_vantage' (requires API key)",
    )
    alpha_vantage_api_key: Optional[str] = Field(
        default=None,
        description="Alpha Vantage API key (required only if provider=alpha_vantage)",
    )
    yfinance_rate_limit: int = Field(
        default=2000,
        ge=1,
        description="YFinance rate limit (requests per hour, default: 2000)",
    )

    model_config = SettingsConfigDict(
        env_prefix="MARKET_DATA_",
        case_sensitive=False,
        env_file=".env",
        extra="ignore",
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider is supported."""
        v_lower = v.lower()
        if v_lower not in {"yfinance", "alpha_vantage"}:
            raise ValueError(
                f"Invalid provider: {v}. Must be 'yfinance' or 'alpha_vantage'"
            )
        return v_lower

    def validate_config(self) -> None:
        """
        Validate configuration consistency.

        Raises:
            ValueError: If alpha_vantage selected but API key missing
        """
        if self.provider == "alpha_vantage":
            if not self.alpha_vantage_api_key or self.alpha_vantage_api_key == "your_api_key_here":
                raise ValueError(
                    "MARKET_DATA_ALPHA_VANTAGE_API_KEY is required when provider=alpha_vantage. "
                    "Get your free API key from: https://www.alphavantage.co/support/#api-key"
                )

    def masked_alpha_vantage_key(self) -> str:
        """Return masked Alpha Vantage API key for logging."""
        if not self.alpha_vantage_api_key:
            return "N/A"
        if len(self.alpha_vantage_api_key) < 8:
            return "***"
        return f"{self.alpha_vantage_api_key[:4]}...{self.alpha_vantage_api_key[-4:]}"


class CacheSettings(BaseSettings):
    """Cache configuration."""

    dir: Path = Field(default=Path("data/cache"), description="Cache directory path")
    size_mb: int = Field(default=500, ge=10, description="Maximum cache size in MB")

    model_config = SettingsConfigDict(
        env_prefix="CACHE_", case_sensitive=False, env_file=".env", extra="ignore"
    )


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    path: Path = Field(
        default=Path("data/stock_cli.db"), description="SQLite database file path"
    )

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_", case_sensitive=False, env_file=".env", extra="ignore"
    )


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    model_config = SettingsConfigDict(
        env_prefix="LOG_", case_sensitive=False, env_file=".env", extra="ignore"
    )

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"Invalid logging level: {v}. Must be one of: {', '.join(valid_levels)}"
            )
        return v_upper


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration."""

    requests_per_hour: int = Field(
        default=300,
        ge=1,
        description="Maximum requests per hour for Alpha Vantage API",
    )

    model_config = SettingsConfigDict(
        env_prefix="RATE_LIMIT_", case_sensitive=False, env_file=".env", extra="ignore"
    )


class ApplicationConfig:
    """
    Facade for application configuration.

    Aggregates all configuration settings with automatic validation
    and .env file loading.

    Usage:
        >>> from stock_friend.infrastructure.config import config
        >>> provider = config.gateway.provider
        >>> cache_dir = config.cache.dir

    Environment Variables:
        MARKET_DATA_PROVIDER: Market data provider (default: yfinance)
        MARKET_DATA_ALPHA_VANTAGE_API_KEY: Alpha Vantage API key (required only if provider=alpha_vantage)
        MARKET_DATA_YFINANCE_RATE_LIMIT: YFinance rate limit (default: 2000 req/hour)
        CACHE_DIR: Cache directory path (default: data/cache)
        CACHE_SIZE_MB: Cache size limit in MB (default: 500, min: 10)
        DATABASE_PATH: SQLite database path (default: data/stock_cli.db)
        LOG_LEVEL: Logging level (default: INFO)
        RATE_LIMIT_REQUESTS_PER_HOUR: Rate limit (default: 300, min: 1)
    """

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            env_file: Optional path to .env file (default: searches for .env)

        Raises:
            ValueError: If configuration validation fails
        """
        # If env_file not specified, pydantic_settings will automatically
        # search for .env in current directory
        self.gateway = GatewaySettings()
        self.cache = CacheSettings()
        self.database = DatabaseSettings()
        self.logging = LoggingSettings()
        self.rate_limit = RateLimitSettings()

        # Validate gateway configuration consistency
        self.gateway.validate_config()

        logger.info("Configuration loaded successfully")
        logger.debug(f"Market Data Provider: {self.gateway.provider}")
        logger.debug(f"Alpha Vantage API Key: {self.gateway.masked_alpha_vantage_key()}")
        logger.debug(f"YFinance Rate Limit: {self.gateway.yfinance_rate_limit} req/hour")
        logger.debug(f"Cache Directory: {self.cache.dir}")
        logger.debug(f"Database Path: {self.database.path}")
        logger.debug(f"Log Level: {self.logging.level}")
        logger.debug(f"Rate Limit: {self.rate_limit.requests_per_hour} req/hour")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ApplicationConfig(\n"
            f"  gateway.provider={self.gateway.provider},\n"
            f"  gateway.alpha_vantage_api_key={self.gateway.masked_alpha_vantage_key()},\n"
            f"  gateway.yfinance_rate_limit={self.gateway.yfinance_rate_limit},\n"
            f"  cache.dir={self.cache.dir},\n"
            f"  cache.size_mb={self.cache.size_mb},\n"
            f"  database.path={self.database.path},\n"
            f"  logging.level={self.logging.level},\n"
            f"  rate_limit.requests_per_hour={self.rate_limit.requests_per_hour}\n"
            f")"
        )


# Singleton instance
config = ApplicationConfig()
