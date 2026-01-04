"""
Configuration module for stock-friend-cli.

Provides convenient imports for all configuration classes.
Each provider has its own settings class for clean separation of concerns.

Usage:
    >>> from stock_friend.infrastructure.config import (
    ...     ComplianceSettings,
    ...     ZoyaComplianceSettings,
    ...     StaticComplianceSettings,
    ... )
    >>>
    >>> compliance = ComplianceSettings()
    >>> print(compliance.provider)
    'static'
"""

from .compliance_settings import ComplianceSettings
from .zoya_compliance_settings import ZoyaComplianceSettings
from .static_compliance_settings import StaticComplianceSettings

__all__ = [
    "ComplianceSettings",
    "ZoyaComplianceSettings",
    "StaticComplianceSettings",
]
