"""Static CSV-based compliance configuration."""

import logging
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class StaticComplianceSettings(BaseSettings):
    """
    Static CSV-based compliance configuration.

    Loads compliance data from local CSV file.
    Useful for testing, development, and offline scenarios.

    CSV Format:
        ticker,is_compliant,reasons,source
        AAPL,True,,manual
        JPM,False,Conventional bank,manual
        GOOGL,True,,manual

    Environment Variables:
        COMPLIANCE_STATIC_DATA_FILE: Path to CSV file

    Example:
        >>> settings = StaticComplianceSettings()
        >>> print(settings.data_file)
        PosixPath('data/compliance/halal_compliant_stocks.csv')
    """

    data_file: Path = Field(
        default=Path("data/compliance/halal_compliant_stocks.csv"),
        description="Path to compliance CSV file"
    )

    model_config = SettingsConfigDict(
        env_prefix="COMPLIANCE_STATIC_",
        case_sensitive=False,
        env_file=".env",
        extra="ignore",
    )
