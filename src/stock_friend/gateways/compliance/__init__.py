"""
Compliance gateway package for halal stock screening.

Provides abstract interface and implementations for checking stock compliance
with Islamic investment principles.

This package will contain:
- base.py: Abstract interface (IComplianceGateway) and exceptions
- zoya_gateway.py: Zoya API implementation (Phase 3)
- musaffa_gateway.py: Musaffa API implementation (future)
- static_gateway.py: CSV-based implementation (Phase 2)

Usage:
    >>> from stock_friend.gateways.compliance import IComplianceGateway, ComplianceException
    >>> from stock_friend.gateways.compliance import StaticComplianceGateway
    >>>
    >>> gateway = StaticComplianceGateway()
    >>> status = gateway.check_compliance("AAPL")
"""

from .base import (
    IComplianceGateway,
    ComplianceException,
    ComplianceDataNotFoundError,
)
from .static_gateway import StaticComplianceGateway
from .zoya_gateway import ZoyaComplianceGateway

__all__ = [
    "IComplianceGateway",
    "ComplianceException",
    "ComplianceDataNotFoundError",
    "StaticComplianceGateway",
    "ZoyaComplianceGateway",
]
