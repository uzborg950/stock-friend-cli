"""
Zoya API compliance gateway implementation.

Integrates with Zoya Finance GraphQL API for halal stock screening.
"""

import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
from typing import Dict, List, Optional

import requests

from stock_friend.gateways.compliance.base import (
    ComplianceException,
    IComplianceGateway,
)
from stock_friend.infrastructure.cache_manager import CacheManager
from stock_friend.infrastructure.rate_limiter import RateLimiter
from stock_friend.models.compliance import ComplianceStatus

logger = logging.getLogger(__name__)


def retry_on_failure(max_attempts: int = 3, backoff_factor: float = 2.0):
    """
    Decorator for retry logic with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Multiplier for backoff delay
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    attempt += 1
                    last_exception = e

                    if attempt < max_attempts:
                        delay = backoff_factor ** attempt
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")

            raise last_exception

        return wrapper

    return decorator


class ZoyaComplianceGateway(IComplianceGateway):
    """
    Zoya API compliance gateway using GraphQL.

    Integrates with Zoya Finance API for shariah-compliant stock screening.

    Features:
    - GraphQL API with sandbox and live environments
    - Rate limit: 10 requests per second (configurable)
    - Aggressive caching (30 days TTL - compliance rarely changes)
    - Batch operations using GraphQL queries
    - Automatic retries with exponential backoff
    - Data accuracy: Returns unknown status when data unavailable

    Authentication:
    - API key in Authorization header
    - Sandbox: Authorization: sandbox-YOUR_API_KEY
    - Live: Authorization: live-YOUR_API_KEY

    API Endpoints:
    - Sandbox: https://sandbox-api.zoya.finance/graphql (default)
    - Live: https://api.zoya.finance/graphql (default)
    - URLs can be overridden via api_url parameter

    Example:
        >>> gateway = ZoyaComplianceGateway(
        ...     api_key="sandbox-a566b7b5-f0ce-4428-b842-3e3a20a19249",
        ...     api_url="https://sandbox-api.zoya.finance/graphql"
        ... )
        >>> status = gateway.check_compliance("AAPL")
        >>> print(status.is_compliant)
        True
    """

    def __init__(
        self,
        api_key: str,
        api_url: str,
        cache_manager: Optional[CacheManager] = None,
        rate_limiter: Optional[RateLimiter] = None,
        cache_ttl_days: int = 30,
    ):
        """
        Initialize Zoya compliance gateway.

        Args:
            api_key: Zoya API key
            api_url: Zoya GraphQL API endpoint URL
            cache_manager: Optional cache manager (recommended)
            rate_limiter: Optional rate limiter (recommended)
            cache_ttl_days: Cache TTL in days (default: 30)

        Note:
            The environment (sandbox/live) is inferred from the API key prefix.
        """
        self.api_key = api_key
        self.api_url = api_url
        self.cache_manager = cache_manager
        self.rate_limiter = rate_limiter
        self.cache_ttl_days = cache_ttl_days

        # Infer environment from API key prefix
        if api_key.startswith("sandbox-"):
            self.environment = "sandbox"
        elif api_key.startswith("live-"):
            self.environment = "live"
        else:
            # Default to sandbox if prefix not recognized
            self.environment = "sandbox"
            logger.warning(
                f"Could not infer environment from API key prefix. Defaulting to 'sandbox'. "
                f"Expected key to start with 'sandbox-' or 'live-'"
            )

        # Configure rate limiter: 10 requests per second = 36000 requests per hour
        if self.rate_limiter:
            self.rate_limiter.configure("zoya", requests_per_hour=36000)

        logger.info(
            f"Initialized ZoyaComplianceGateway (environment={self.environment}, api_url={api_url})"
        )

    def check_compliance(self, ticker: str) -> ComplianceStatus:
        """
        Check compliance for single stock using Zoya API.

        Args:
            ticker: Stock ticker symbol

        Returns:
            ComplianceStatus object with Zoya data

        Note:
            Returns unknown status (is_compliant=None) if stock not found in Zoya.
        """
        ticker = ticker.upper().strip()

        if not ticker:
            raise ValueError("Ticker cannot be empty")

        # Wrap with retry logic and handle exhaustion
        try:
            return self._check_compliance_with_retry(ticker)
        except requests.exceptions.RequestException as e:
            # Retries exhausted - return unknown status
            logger.error(f"All retry attempts exhausted for {ticker}: {e}")
            return ComplianceStatus(
                ticker=ticker,
                is_compliant=None,
                reasons=[f"Network error after retries: {str(e)}"],
                source="zoya",
            )

    @retry_on_failure(max_attempts=3, backoff_factor=2.0)
    def _check_compliance_with_retry(self, ticker: str) -> ComplianceStatus:
        """Internal method with retry logic."""

        # Check cache first (30-day TTL)
        if self.cache_manager:
            cache_key = f"compliance:zoya:{self.environment}:{ticker}"
            cached_status = self.cache_manager.get(cache_key)

            if cached_status is not None:
                logger.debug(f"Cache hit for {ticker} compliance")
                return cached_status

        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire("zoya")

        try:
            logger.info(f"Checking compliance for {ticker} via Zoya API")

            # GraphQL query for basic compliance report
            query = """
            query BasicReport($symbol: String!) {
              basicCompliance {
                report(symbol: $symbol) {
                  symbol
                  name
                  exchange
                  status
                  reportDate
                  purificationRatio
                }
              }
            }
            """

            variables = {"symbol": ticker}

            # Execute GraphQL request
            response = self._execute_graphql(query, variables)

            # Parse response
            report = response.get("data", {}).get("basicCompliance", {}).get("report")

            if not report:
                # Stock not found in Zoya - return unknown status
                logger.warning(f"{ticker} not found in Zoya. Returning unknown status.")
                status = ComplianceStatus(
                    ticker=ticker,
                    is_compliant=None,  # Unknown
                    reasons=["Not found in Zoya database"],
                    source="zoya",
                )
            else:
                # Parse Zoya status (basicCompliance returns uppercase with underscore)
                zoya_status = report.get("status", "").replace("_", "-").lower()
                is_compliant = self._parse_zoya_status(zoya_status)

                # Build reasons list
                reasons = []
                if not is_compliant and is_compliant is not None:
                    reasons.append("Non-compliant per Zoya screening")

                # Parse purification ratio
                purification_ratio = report.get("purificationRatio")

                status = ComplianceStatus(
                    ticker=ticker,
                    is_compliant=is_compliant,
                    compliance_score=(100.0 - float(purification_ratio * 100)) if purification_ratio else None,
                    reasons=reasons,
                    source="zoya",
                    shariah_compliant=is_compliant,
                )

            # Cache the result (30-day TTL)
            if self.cache_manager:
                cache_key = f"compliance:zoya:{self.environment}:{ticker}"
                ttl = timedelta(days=self.cache_ttl_days)
                self.cache_manager.set(cache_key, status, ttl=ttl)

            logger.info(f"{ticker} compliance: {status.is_compliant}")
            return status

        except ComplianceException:
            # Re-raise compliance exceptions
            raise
        except requests.exceptions.RequestException:
            # Re-raise network exceptions so retry decorator can handle them
            raise
        except Exception as e:
            logger.error(f"Failed to check compliance for {ticker}: {e}")
            # Return unknown status on other errors
            return ComplianceStatus(
                ticker=ticker,
                is_compliant=None,
                reasons=[f"API error: {str(e)}"],
                source="zoya",
            )

    def check_batch(self, tickers: List[str]) -> Dict[str, ComplianceStatus]:
        """
        Check compliance for multiple stocks (batch operation).

        Uses individual stock lookups (no true batch API in basicCompliance).

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping tickers to ComplianceStatus objects

        Note:
            Tickers not found in Zoya return unknown status.
        """
        if not tickers:
            return {}

        tickers = [ticker.upper().strip() for ticker in tickers]
        results = {}

        logger.info(f"Checking compliance for {len(tickers)} tickers via Zoya API")

        # Check each ticker individually
        for ticker in tickers:
            try:
                status = self.check_compliance(ticker)
                results[ticker] = status
            except Exception as e:
                logger.error(f"Error checking {ticker}: {e}")
                # Return unknown status on error
                results[ticker] = ComplianceStatus(
                    ticker=ticker,
                    is_compliant=None,
                    reasons=[f"API error: {str(e)}"],
                    source="zoya",
                )

        logger.info(f"Batch compliance check completed: {len(results)}/{len(tickers)} successful")
        return results

    def filter_compliant(self, tickers: List[str]) -> List[str]:
        """
        Filter to only halal-compliant stocks.

        Args:
            tickers: List of ticker symbols to filter

        Returns:
            List of compliant ticker symbols only (excludes non-compliant and unknown)
        """
        statuses = self.check_batch(tickers)
        compliant_tickers = [
            ticker for ticker, status in statuses.items() if status.is_compliant is True
        ]

        # Count different statuses for logging
        non_compliant = sum(1 for s in statuses.values() if s.is_compliant is False)
        unknown = sum(1 for s in statuses.values() if s.is_compliant is None)

        logger.info(
            f"Filtered {len(tickers)} stocks → {len(compliant_tickers)} compliant, "
            f"{non_compliant} non-compliant, {unknown} unknown"
        )

        return compliant_tickers

    def get_all_reports(
        self,
        status_filter: Optional[str] = None,
        asset_type: str = "stock",
        max_items: Optional[int] = None,
    ) -> List[Dict]:
        """
        Fetch all compliance reports from Zoya API with pagination.

        This method handles pagination automatically using nextToken to retrieve
        all available reports. Useful for building complete compliance datasets.

        Args:
            status_filter: Optional status filter (e.g., "COMPLIANT", "NOT_COMPLIANT", "QUESTIONABLE")
            asset_type: Asset type to query - "stock" or "fund" (default: "stock")
            max_items: Optional limit on total items to fetch (None = fetch all)

        Returns:
            List of report dictionaries containing symbol, name, exchange, status, etc.

        Example:
            >>> gateway = ZoyaComplianceGateway(api_key="...", environment="sandbox")
            >>> compliant_stocks = gateway.get_all_reports(status_filter="COMPLIANT", asset_type="stock")
            >>> print(f"Found {len(compliant_stocks)} compliant stocks")

        Note:
            - Respects rate limits (10 requests/second configured in __init__)
            - Results are NOT cached due to large dataset size
            - Each page returns up to ~1000 items (Zoya's default)
            - For production use, consider saving results to file/database
        """
        if asset_type not in ("stock", "fund"):
            raise ValueError(f"Invalid asset_type: {asset_type}. Must be 'stock' or 'fund'")

        all_items = []
        next_token = None
        page_count = 0

        logger.info(
            f"Fetching all {asset_type} reports from Zoya "
            f"(status_filter={status_filter}, max_items={max_items})"
        )

        try:
            while True:
                page_count += 1

                # Fetch page
                page_data = self._fetch_reports_page(
                    asset_type=asset_type,
                    status_filter=status_filter,
                    next_token=next_token,
                )

                # Extract items
                items = page_data.get("items", [])
                all_items.extend(items)

                logger.info(
                    f"Fetched page {page_count}: {len(items)} items "
                    f"(total so far: {len(all_items)})"
                )

                # Check if we've reached max_items
                if max_items and len(all_items) >= max_items:
                    all_items = all_items[:max_items]
                    logger.info(f"Reached max_items limit ({max_items}). Stopping pagination.")
                    break

                # Check for next page
                next_token = page_data.get("nextToken")
                if not next_token:
                    logger.info("No more pages. Pagination complete.")
                    break

            logger.info(
                f"Completed fetching {asset_type} reports: "
                f"{len(all_items)} items across {page_count} pages"
            )

            return all_items

        except Exception as e:
            logger.error(f"Failed to fetch all reports: {e}")
            raise ComplianceException(f"Failed to fetch all reports: {e}")

    def _fetch_reports_page(
        self,
        asset_type: str,
        status_filter: Optional[str] = None,
        next_token: Optional[str] = None,
    ) -> Dict:
        """
        Fetch a single page of reports from Zoya API.

        Args:
            asset_type: "stock" or "fund"
            status_filter: Optional status filter
            next_token: Pagination token for next page

        Returns:
            Dictionary with "items" and "nextToken" keys

        Raises:
            ComplianceException: If request fails
        """
        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire("zoya")

        # Build GraphQL query based on asset type
        if asset_type == "stock":
            # For stocks, use reports field with input filters (inline)
            # Build the input object inline since ReportInput type doesn't exist as variable
            input_parts = []
            if status_filter:
                input_parts.append(f'filters: {{ status: {status_filter} }}')
            if next_token:
                input_parts.append(f'nextToken: "{next_token}"')

            input_str = ", ".join(input_parts) if input_parts else ""
            input_clause = f"(input: {{ {input_str} }})" if input_str else ""

            query = f"""
            query GetStockReports {{
              basicCompliance {{
                reports{input_clause} {{
                  nextToken
                  items {{
                    symbol
                    name
                    exchange
                    status
                    reportDate
                    purificationRatio
                  }}
                }}
              }}
            }}
            """

            variables = {}
            field_name = "reports"

        else:  # fund
            # For funds, use funds field directly (no pagination support in query args)
            query = """
            query GetFundReports {
              basicCompliance {
                funds {
                  nextToken
                  items {
                    symbol
                    name
                    exchange
                    status
                    reportDate
                    holdingsAsOfDate
                  }
                }
              }
            }
            """

            # Funds query doesn't accept nextToken as argument
            variables = {}
            field_name = "funds"

        # Execute GraphQL request
        response = self._execute_graphql(query, variables)

        # Extract data
        data = response.get("data", {}).get("basicCompliance", {}).get(field_name, {})

        if not data:
            logger.warning(f"No data returned for {asset_type} reports")
            return {"items": [], "nextToken": None}

        return data

    def _parse_zoya_status(self, status_str: str) -> Optional[bool]:
        """
        Parse Zoya status string to compliance boolean.

        Args:
            status_str: Zoya status string (e.g., "compliant", "not-compliant", "questionable")

        Returns:
            True if compliant, False if non-compliant, None if unknown/questionable
        """
        status_lower = status_str.lower()

        if status_lower in ("compliant", "pass", "halal"):
            return True
        elif status_lower in ("not-compliant", "non-compliant", "fail", "haram"):
            return False
        else:
            # "questionable" or unknown status
            return None

    def _execute_graphql(self, query: str, variables: dict) -> dict:
        """
        Execute GraphQL query against Zoya API.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Response dictionary

        Raises:
            ComplianceException: If request fails
        """
        headers = {
            "Authorization": self.api_key,  # Format: "sandbox-KEY" or "live-KEY"
            "Content-Type": "application/json",
        }

        payload = {
            "query": query,
            "variables": variables,
        }

        response = requests.post(
            self.api_url,
            json=payload,
            headers=headers,
            timeout=30,
        )

        if response.status_code != 200:
            raise ComplianceException(
                f"Zoya API request failed: {response.status_code} - {response.text}"
            )

        data = response.json()

        # Check for GraphQL errors
        if "errors" in data:
            errors = data["errors"]
            raise ComplianceException(f"GraphQL errors: {errors}")

        return data

    def get_name(self) -> str:
        """
        Return gateway identifier.

        Returns:
            Gateway name (e.g., "zoya_sandbox", "zoya_live")
        """
        return f"zoya_{self.environment}"
