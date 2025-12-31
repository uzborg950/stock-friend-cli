"""
Business services for stock-friend-cli.

This module contains the service layer that orchestrates business logic
by coordinating between gateways, repositories, and domain models.
"""

from stock_friend.services.search_service import SearchService

__all__ = ["SearchService"]
