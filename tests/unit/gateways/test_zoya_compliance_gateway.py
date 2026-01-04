"""
Unit tests for ZoyaComplianceGateway.

Tests GraphQL API integration with mocked responses.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
import requests

from stock_friend.gateways.compliance import (
    ComplianceException,
    ZoyaComplianceGateway,
)
from stock_friend.infrastructure.cache_manager import CacheManager
from stock_friend.infrastructure.rate_limiter import RateLimiter
from stock_friend.models.compliance import ComplianceStatus


class TestZoyaComplianceGatewayInitialization:
    """Test gateway initialization scenarios."""

    def test_init_with_sandbox_environment(self):
        """Test initialization with sandbox environment."""
        gateway = ZoyaComplianceGateway(
            api_key="sandbox-test-key",
            environment="sandbox",
        )

        assert gateway.api_key == "sandbox-test-key"
        assert gateway.environment == "sandbox"
        assert gateway.api_url == gateway.SANDBOX_URL
        assert gateway.cache_ttl_days == 30
        assert gateway.get_name() == "zoya_sandbox"

    def test_init_with_live_environment(self):
        """Test initialization with live environment."""
        gateway = ZoyaComplianceGateway(
            api_key="live-test-key",
            environment="live",
        )

        assert gateway.api_key == "live-test-key"
        assert gateway.environment == "live"
        assert gateway.api_url == gateway.LIVE_URL
        assert gateway.get_name() == "zoya_live"

    def test_init_with_invalid_environment_raises_error(self):
        """Test initialization with invalid environment raises ValueError."""
        with pytest.raises(ValueError, match="Invalid environment"):
            ZoyaComplianceGateway(
                api_key="test-key",
                environment="invalid",
            )

    def test_init_normalizes_environment_case(self):
        """Test that environment is normalized to lowercase."""
        gateway = ZoyaComplianceGateway(
            api_key="test-key",
            environment="SANDBOX",
        )

        assert gateway.environment == "sandbox"

    def test_init_with_cache_manager(self):
        """Test initialization with cache manager."""
        mock_cache = Mock(spec=CacheManager)
        gateway = ZoyaComplianceGateway(
            api_key="test-key",
            cache_manager=mock_cache,
        )

        assert gateway.cache_manager is mock_cache

    def test_init_with_rate_limiter(self):
        """Test initialization with rate limiter."""
        mock_rate_limiter = Mock(spec=RateLimiter)
        gateway = ZoyaComplianceGateway(
            api_key="test-key",
            rate_limiter=mock_rate_limiter,
        )

        assert gateway.rate_limiter is mock_rate_limiter
        # Should configure rate limiter: 10 req/sec = 36000 req/hour
        mock_rate_limiter.configure.assert_called_once_with("zoya", requests_per_hour=36000)

    def test_init_with_custom_cache_ttl(self):
        """Test initialization with custom cache TTL."""
        gateway = ZoyaComplianceGateway(
            api_key="test-key",
            cache_ttl_days=60,
        )

        assert gateway.cache_ttl_days == 60


class TestCheckCompliance:
    """Test check_compliance method."""

    @pytest.fixture
    def gateway(self):
        """Create gateway for testing."""
        return ZoyaComplianceGateway(api_key="sandbox-test-key")

    def test_check_compliant_stock(self, gateway):
        """Test checking a compliant stock."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "report": {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "exchange": "NASDAQ",
                        "status": "compliant",
                        "reportDate": "2026-01-01",
                        "businessScreen": "pass",
                        "financialScreen": "pass",
                        "purificationRatio": 0.01,
                        "nonCompliantRevenue": 0.005,
                        "questionableRevenue": 0.005,
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            status = gateway.check_compliance("AAPL")

            assert status.ticker == "AAPL"
            assert status.is_compliant is True
            assert status.shariah_compliant is True
            assert status.source == "zoya"
            assert status.compliance_score == pytest.approx(99.0)
            assert status.reasons == []

    def test_check_non_compliant_stock(self, gateway):
        """Test checking a non-compliant stock."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "report": {
                        "symbol": "JPM",
                        "name": "JPMorgan Chase",
                        "exchange": "NYSE",
                        "status": "not-compliant",
                        "reportDate": "2026-01-01",
                        "businessScreen": "fail",
                        "financialScreen": "pass",
                        "purificationRatio": 0.0,
                        "nonCompliantRevenue": 0.8,
                        "questionableRevenue": 0.0,
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            status = gateway.check_compliance("JPM")

            assert status.ticker == "JPM"
            assert status.is_compliant is False
            assert status.source == "zoya"
            assert "Non-compliant per Zoya screening" in status.reasons

    def test_check_stock_with_financial_screen_failure(self, gateway):
        """Test checking stock that fails financial screening."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "report": {
                        "symbol": "XYZ",
                        "name": "Test Company",
                        "status": "not-compliant",
                        "businessScreen": "pass",
                        "financialScreen": "fail",
                        "purificationRatio": 0.4,
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            status = gateway.check_compliance("XYZ")

            assert status.is_compliant is False
            assert "Non-compliant per Zoya screening" in status.reasons

    def test_check_questionable_stock_returns_unknown(self, gateway):
        """Test questionable status returns unknown (None)."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "report": {
                        "symbol": "TEST",
                        "name": "Test Inc",
                        "status": "questionable",
                        "businessScreen": "pass",
                        "financialScreen": "pass",
                        "purificationRatio": 0.05,
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            status = gateway.check_compliance("TEST")

            assert status.ticker == "TEST"
            assert status.is_compliant is None  # Questionable = unknown
            assert status.source == "zoya"

    def test_check_stock_not_found_returns_unknown(self, gateway):
        """Test stock not found in Zoya returns unknown status."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "report": None  # Stock not found
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            status = gateway.check_compliance("NOTFOUND")

            assert status.ticker == "NOTFOUND"
            assert status.is_compliant is None  # Unknown
            assert "Not found in Zoya database" in status.reasons
            assert status.source == "zoya"

    def test_check_with_lowercase_ticker(self, gateway):
        """Test that lowercase tickers are normalized to uppercase."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "report": {
                        "symbol": "AAPL",
                        "status": "compliant",
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            status = gateway.check_compliance("aapl")

            assert status.ticker == "AAPL"

    def test_check_with_whitespace(self, gateway):
        """Test that whitespace is stripped from tickers."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "report": {
                        "symbol": "AAPL",
                        "status": "compliant",
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            status = gateway.check_compliance("  AAPL  ")

            assert status.ticker == "AAPL"

    def test_check_empty_ticker_raises_error(self, gateway):
        """Test that empty ticker raises ValueError."""
        with pytest.raises(ValueError, match="Ticker cannot be empty"):
            gateway.check_compliance("")

    def test_check_with_cache_hit(self, gateway):
        """Test that cached results are returned without API call."""
        mock_cache = Mock(spec=CacheManager)
        cached_status = ComplianceStatus(
            ticker="AAPL",
            is_compliant=True,
            source="zoya",
        )
        mock_cache.get.return_value = cached_status

        gateway_with_cache = ZoyaComplianceGateway(
            api_key="test-key",
            cache_manager=mock_cache,
        )

        with patch("requests.post") as mock_post:
            status = gateway_with_cache.check_compliance("AAPL")

            assert status is cached_status
            mock_post.assert_not_called()  # No API call
            mock_cache.get.assert_called_once_with("compliance:zoya:sandbox:AAPL")

    def test_check_caches_result(self, gateway):
        """Test that results are cached after API call."""
        mock_cache = Mock(spec=CacheManager)
        mock_cache.get.return_value = None  # Cache miss

        gateway_with_cache = ZoyaComplianceGateway(
            api_key="test-key",
            cache_manager=mock_cache,
            cache_ttl_days=30,
        )

        mock_response = {
            "data": {
                "basicCompliance": {
                    "report": {
                        "symbol": "AAPL",
                        "status": "compliant",
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            status = gateway_with_cache.check_compliance("AAPL")

            # Should cache the result
            assert mock_cache.set.call_count == 1
            call_args = mock_cache.set.call_args
            assert call_args[0][0] == "compliance:zoya:sandbox:AAPL"  # Cache key
            assert call_args[0][1].ticker == "AAPL"  # Cached status
            assert call_args[1]["ttl"] == timedelta(days=30)  # TTL

    def test_check_applies_rate_limiting(self, gateway):
        """Test that rate limiting is applied before API call."""
        mock_rate_limiter = Mock(spec=RateLimiter)
        gateway_with_limiter = ZoyaComplianceGateway(
            api_key="test-key",
            rate_limiter=mock_rate_limiter,
        )

        mock_response = {
            "data": {
                "basicCompliance": {
                    "report": {
                        "symbol": "AAPL",
                        "status": "compliant",
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            gateway_with_limiter.check_compliance("AAPL")

            mock_rate_limiter.acquire.assert_called_once_with("zoya")

    def test_check_api_error_returns_unknown_status(self, gateway):
        """Test that API errors return unknown status after retries."""
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Network error")

            with patch("time.sleep"):  # Mock sleep to speed up test
                status = gateway.check_compliance("AAPL")

            assert status.ticker == "AAPL"
            assert status.is_compliant is None  # Unknown due to error
            assert "Network error after retries" in status.reasons[0]
            assert status.source == "zoya"
            assert mock_post.call_count == 3  # Should have retried

    def test_check_graphql_error_raises_exception(self, gateway):
        """Test that GraphQL errors raise ComplianceException."""
        mock_response = {
            "errors": [
                {
                    "message": "Invalid API key",
                    "extensions": {"code": "UNAUTHENTICATED"},
                }
            ]
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            with pytest.raises(ComplianceException, match="GraphQL errors"):
                gateway.check_compliance("AAPL")


class TestCheckBatch:
    """Test check_batch method."""

    @pytest.fixture
    def gateway(self):
        """Create gateway for testing."""
        return ZoyaComplianceGateway(api_key="sandbox-test-key")

    def test_check_batch_mixed_tickers(self, gateway):
        """Test batch check with mix of compliant and non-compliant stocks."""
        # check_batch calls check_compliance for each ticker individually
        responses = [
            {
                "data": {
                    "basicCompliance": {
                        "report": {"symbol": "AAPL", "status": "compliant", "purificationRatio": 0.01}
                    }
                }
            },
            {
                "data": {
                    "basicCompliance": {
                        "report": {"symbol": "JPM", "status": "not-compliant", "purificationRatio": 0.0}
                    }
                }
            },
            {
                "data": {
                    "basicCompliance": {
                        "report": {"symbol": "GOOGL", "status": "compliant", "purificationRatio": 0.02}
                    }
                }
            },
        ]

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.side_effect = responses

            tickers = ["AAPL", "JPM", "GOOGL"]
            results = gateway.check_batch(tickers)

            assert len(results) == 3
            assert results["AAPL"].is_compliant is True
            assert results["JPM"].is_compliant is False
            assert results["GOOGL"].is_compliant is True

    def test_check_batch_with_unknown_tickers(self, gateway):
        """Test batch check with tickers not found in Zoya."""
        # check_batch calls check_compliance for each ticker individually
        responses = [
            {
                "data": {
                    "basicCompliance": {
                        "report": {"symbol": "AAPL", "status": "compliant", "purificationRatio": 0.01}
                    }
                }
            },
            {
                "data": {
                    "basicCompliance": {
                        "report": None  # Not found
                    }
                }
            },
            {
                "data": {
                    "basicCompliance": {
                        "report": None  # Not found
                    }
                }
            },
        ]

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.side_effect = responses

            tickers = ["AAPL", "NOTFOUND1", "NOTFOUND2"]
            results = gateway.check_batch(tickers)

            assert len(results) == 3
            assert results["AAPL"].is_compliant is True
            assert results["NOTFOUND1"].is_compliant is None  # Unknown
            assert results["NOTFOUND2"].is_compliant is None  # Unknown
            assert "Not found in Zoya database" in results["NOTFOUND1"].reasons[0]

    def test_check_batch_empty_list(self, gateway):
        """Test batch check with empty list."""
        results = gateway.check_batch([])

        assert results == {}

    def test_check_batch_normalizes_case(self, gateway):
        """Test batch check normalizes ticker case."""
        # check_batch calls check_compliance for each ticker individually
        responses = [
            {
                "data": {
                    "basicCompliance": {
                        "report": {"symbol": "AAPL", "status": "compliant", "purificationRatio": 0.01}
                    }
                }
            },
            {
                "data": {
                    "basicCompliance": {
                        "report": {"symbol": "GOOGL", "status": "compliant", "purificationRatio": 0.02}
                    }
                }
            },
        ]

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.side_effect = responses

            tickers = ["aapl", "GOOGL"]
            results = gateway.check_batch(tickers)

            assert "AAPL" in results
            assert "GOOGL" in results

    def test_check_batch_uses_cache(self, gateway):
        """Test batch check uses cache for already-cached tickers."""
        mock_cache = Mock(spec=CacheManager)

        # AAPL is in cache
        cached_status = ComplianceStatus(ticker="AAPL", is_compliant=True, source="zoya")
        mock_cache.get.side_effect = lambda key: (
            cached_status if "AAPL" in key else None
        )

        gateway_with_cache = ZoyaComplianceGateway(
            api_key="test-key",
            cache_manager=mock_cache,
        )

        # Only GOOGL will make an API call (AAPL is cached)
        mock_response = {
            "data": {
                "basicCompliance": {
                    "report": {"symbol": "GOOGL", "status": "compliant", "purificationRatio": 0.02}
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            tickers = ["AAPL", "GOOGL"]
            results = gateway_with_cache.check_batch(tickers)

            assert len(results) == 2
            assert results["AAPL"] is cached_status  # From cache
            assert results["GOOGL"].ticker == "GOOGL"  # From API

            # API should only be called once for GOOGL (AAPL was cached)
            assert mock_post.call_count == 1

    def test_check_batch_api_error_returns_unknown_for_all(self, gateway):
        """Test batch check returns unknown for all tickers on API error."""
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Network error")

            tickers = ["AAPL", "GOOGL", "MSFT"]
            results = gateway.check_batch(tickers)

            assert len(results) == 3
            assert all(status.is_compliant is None for status in results.values())
            assert all("Network error after retries" in status.reasons[0] for status in results.values())


class TestFilterCompliant:
    """Test filter_compliant method."""

    @pytest.fixture
    def gateway(self):
        """Create gateway for testing."""
        return ZoyaComplianceGateway(api_key="sandbox-test-key")

    def test_filter_compliant_basic(self, gateway):
        """Test filtering compliant stocks from mixed list."""
        # filter_compliant calls check_batch which calls check_compliance for each ticker
        responses = [
            {
                "data": {
                    "basicCompliance": {
                        "report": {"symbol": "AAPL", "status": "compliant", "purificationRatio": 0.01}
                    }
                }
            },
            {
                "data": {
                    "basicCompliance": {
                        "report": {"symbol": "JPM", "status": "not-compliant", "purificationRatio": 0.0}
                    }
                }
            },
            {
                "data": {
                    "basicCompliance": {
                        "report": {"symbol": "GOOGL", "status": "compliant", "purificationRatio": 0.02}
                    }
                }
            },
        ]

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.side_effect = responses

            tickers = ["AAPL", "JPM", "GOOGL"]
            compliant = gateway.filter_compliant(tickers)

            assert len(compliant) == 2
            assert "AAPL" in compliant
            assert "GOOGL" in compliant
            assert "JPM" not in compliant

    def test_filter_compliant_excludes_unknown(self, gateway):
        """Test filtering excludes unknown tickers (conservative screening)."""
        # filter_compliant calls check_batch which calls check_compliance for each ticker
        responses = [
            {
                "data": {
                    "basicCompliance": {
                        "report": {"symbol": "AAPL", "status": "compliant", "purificationRatio": 0.01}
                    }
                }
            },
            {
                "data": {
                    "basicCompliance": {
                        "report": None  # Not found
                    }
                }
            },
            {
                "data": {
                    "basicCompliance": {
                        "report": None  # Not found
                    }
                }
            },
        ]

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.side_effect = responses

            tickers = ["AAPL", "NOTFOUND", "JPM"]
            compliant = gateway.filter_compliant(tickers)

            assert len(compliant) == 1
            assert "AAPL" in compliant
            assert "NOTFOUND" not in compliant  # Unknown excluded

    def test_filter_compliant_empty_list(self, gateway):
        """Test filtering empty list."""
        compliant = gateway.filter_compliant([])

        assert compliant == []


class TestParseZoyaStatus:
    """Test _parse_zoya_status method."""

    @pytest.fixture
    def gateway(self):
        """Create gateway for testing."""
        return ZoyaComplianceGateway(api_key="sandbox-test-key")

    def test_parse_compliant_status(self, gateway):
        """Test parsing compliant status strings."""
        assert gateway._parse_zoya_status("compliant") is True
        assert gateway._parse_zoya_status("COMPLIANT") is True
        assert gateway._parse_zoya_status("pass") is True
        assert gateway._parse_zoya_status("halal") is True

    def test_parse_non_compliant_status(self, gateway):
        """Test parsing non-compliant status strings."""
        assert gateway._parse_zoya_status("not-compliant") is False
        assert gateway._parse_zoya_status("non-compliant") is False
        assert gateway._parse_zoya_status("fail") is False
        assert gateway._parse_zoya_status("haram") is False

    def test_parse_questionable_status(self, gateway):
        """Test parsing questionable/unknown status strings."""
        assert gateway._parse_zoya_status("questionable") is None
        assert gateway._parse_zoya_status("unknown") is None
        assert gateway._parse_zoya_status("pending") is None


class TestExecuteGraphQL:
    """Test _execute_graphql method."""

    @pytest.fixture
    def gateway(self):
        """Create gateway for testing."""
        return ZoyaComplianceGateway(api_key="sandbox-test-key")

    def test_execute_graphql_success(self, gateway):
        """Test successful GraphQL execution."""
        mock_response_data = {
            "data": {"report": {"symbol": "AAPL", "status": "compliant"}}
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response_data

            query = "query Test { report { symbol } }"
            variables = {"input": {"symbol": "AAPL"}}

            result = gateway._execute_graphql(query, variables)

            assert result == mock_response_data
            # Verify request details
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["json"]["query"] == query
            assert call_kwargs["json"]["variables"] == variables
            assert call_kwargs["headers"]["Authorization"] == "sandbox-test-key"
            assert call_kwargs["headers"]["Content-Type"] == "application/json"
            assert call_kwargs["timeout"] == 30

    def test_execute_graphql_http_error(self, gateway):
        """Test GraphQL execution with HTTP error."""
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 401
            mock_post.return_value.text = "Unauthorized"

            query = "query Test { report { symbol } }"
            variables = {}

            with pytest.raises(ComplianceException, match="Zoya API request failed: 401"):
                gateway._execute_graphql(query, variables)

    def test_execute_graphql_with_graphql_errors(self, gateway):
        """Test GraphQL execution with GraphQL errors in response."""
        mock_response_data = {
            "errors": [
                {"message": "Invalid symbol", "extensions": {"code": "BAD_USER_INPUT"}}
            ]
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response_data

            query = "query Test { report { symbol } }"
            variables = {}

            with pytest.raises(ComplianceException, match="GraphQL errors"):
                gateway._execute_graphql(query, variables)


class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    @pytest.fixture
    def gateway(self):
        """Create gateway for testing."""
        return ZoyaComplianceGateway(api_key="sandbox-test-key")

    def test_retry_on_network_error(self, gateway):
        """Test retry logic on network errors."""
        # First 2 attempts fail, 3rd succeeds
        mock_response = {
            "data": {
                "basicCompliance": {
                    "report": {"symbol": "AAPL", "status": "compliant"}
                }
            }
        }

        call_count = 0

        def mock_post_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise requests.exceptions.ConnectionError("Network error")
            else:
                response = Mock()
                response.status_code = 200
                response.json.return_value = mock_response
                return response

        with patch("requests.post", side_effect=mock_post_side_effect):
            with patch("time.sleep"):  # Mock sleep to speed up test
                status = gateway.check_compliance("AAPL")

            assert status.ticker == "AAPL"
            assert status.is_compliant is True
            assert call_count == 3  # Retried 2 times, succeeded on 3rd

    def test_retry_exhaustion_returns_unknown(self, gateway):
        """Test that exhausted retries return unknown status."""
        call_count = 0

        def mock_post_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise requests.exceptions.ConnectionError("Network error")

        with patch("requests.post", side_effect=mock_post_side_effect):
            with patch("time.sleep"):  # Mock sleep to speed up test
                status = gateway.check_compliance("AAPL")

            assert status.is_compliant is None  # Unknown due to failure
            assert "Network error after retries" in status.reasons[0]
            assert call_count == 3  # Max retries


class TestGetName:
    """Test get_name method."""

    def test_get_name_sandbox(self):
        """Test gateway name for sandbox environment."""
        gateway = ZoyaComplianceGateway(api_key="test-key", environment="sandbox")
        assert gateway.get_name() == "zoya_sandbox"

    def test_get_name_live(self):
        """Test gateway name for live environment."""
        gateway = ZoyaComplianceGateway(api_key="test-key", environment="live")
        assert gateway.get_name() == "zoya_live"


class TestGetAllReports:
    """Test get_all_reports method."""

    @pytest.fixture
    def gateway(self):
        """Create gateway for testing."""
        return ZoyaComplianceGateway(api_key="sandbox-test-key")

    def test_get_all_reports_single_page(self, gateway):
        """Test fetching all reports with single page of results."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "reports": {
                        "items": [
                            {
                                "symbol": "AAPL",
                                "name": "Apple Inc.",
                                "exchange": "NASDAQ",
                                "status": "COMPLIANT",
                                "reportDate": "2026-01-01",
                                "purificationRatio": 0.01,
                            },
                            {
                                "symbol": "MSFT",
                                "name": "Microsoft Corporation",
                                "exchange": "NASDAQ",
                                "status": "COMPLIANT",
                                "reportDate": "2026-01-01",
                                "purificationRatio": 0.02,
                            },
                        ],
                        "nextToken": None,  # No more pages
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            results = gateway.get_all_reports(asset_type="stock")

            assert len(results) == 2
            assert results[0]["symbol"] == "AAPL"
            assert results[1]["symbol"] == "MSFT"
            assert mock_post.call_count == 1  # Single page

    def test_get_all_reports_multiple_pages(self, gateway):
        """Test fetching all reports with pagination."""
        # First page
        mock_response_page1 = {
            "data": {
                "basicCompliance": {
                    "reports": {
                        "items": [
                            {"symbol": "AAPL", "name": "Apple", "status": "COMPLIANT"},
                            {"symbol": "MSFT", "name": "Microsoft", "status": "COMPLIANT"},
                        ],
                        "nextToken": "page2_token",
                    }
                }
            }
        }

        # Second page
        mock_response_page2 = {
            "data": {
                "basicCompliance": {
                    "reports": {
                        "items": [
                            {"symbol": "GOOGL", "name": "Alphabet", "status": "COMPLIANT"},
                        ],
                        "nextToken": None,  # Last page
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.side_effect = [mock_response_page1, mock_response_page2]

            results = gateway.get_all_reports(asset_type="stock")

            assert len(results) == 3
            assert results[0]["symbol"] == "AAPL"
            assert results[1]["symbol"] == "MSFT"
            assert results[2]["symbol"] == "GOOGL"
            assert mock_post.call_count == 2  # Two pages

    def test_get_all_reports_with_status_filter(self, gateway):
        """Test fetching reports with status filter."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "reports": {
                        "items": [
                            {"symbol": "AAPL", "status": "COMPLIANT"},
                            {"symbol": "MSFT", "status": "COMPLIANT"},
                        ],
                        "nextToken": None,
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            results = gateway.get_all_reports(
                asset_type="stock",
                status_filter="COMPLIANT",
            )

            assert len(results) == 2
            # Verify status filter was passed inline in GraphQL query
            call_args = mock_post.call_args[1]["json"]
            query = call_args["query"]
            assert "filters: { status: COMPLIANT }" in query

    def test_get_all_reports_with_max_items_limit(self, gateway):
        """Test fetching reports with max_items limit."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "reports": {
                        "items": [
                            {"symbol": "AAPL", "status": "COMPLIANT"},
                            {"symbol": "MSFT", "status": "COMPLIANT"},
                            {"symbol": "GOOGL", "status": "COMPLIANT"},
                        ],
                        "nextToken": "more_pages_available",
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            results = gateway.get_all_reports(asset_type="stock", max_items=2)

            assert len(results) == 2  # Limited to max_items
            assert results[0]["symbol"] == "AAPL"
            assert results[1]["symbol"] == "MSFT"
            assert mock_post.call_count == 1  # Stopped after first page

    def test_get_all_reports_funds(self, gateway):
        """Test fetching fund reports."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "funds": {
                        "items": [
                            {"symbol": "UMMA", "name": "Wahed ETF", "status": "COMPLIANT"},
                            {"symbol": "HLAL", "name": "Wahed FTSE", "status": "COMPLIANT"},
                        ],
                        "nextToken": None,
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            results = gateway.get_all_reports(asset_type="fund")

            assert len(results) == 2
            assert results[0]["symbol"] == "UMMA"
            assert results[1]["symbol"] == "HLAL"

    def test_get_all_reports_invalid_asset_type(self, gateway):
        """Test that invalid asset_type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid asset_type"):
            gateway.get_all_reports(asset_type="invalid")

    def test_get_all_reports_empty_results(self, gateway):
        """Test fetching reports with no results."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "reports": {
                        "items": [],
                        "nextToken": None,
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            results = gateway.get_all_reports(asset_type="stock")

            assert len(results) == 0
            assert mock_post.call_count == 1

    def test_get_all_reports_applies_rate_limiting(self, gateway):
        """Test that rate limiting is applied during pagination."""
        mock_rate_limiter = Mock(spec=RateLimiter)
        gateway_with_limiter = ZoyaComplianceGateway(
            api_key="test-key",
            rate_limiter=mock_rate_limiter,
        )

        # Two pages of results
        mock_response_page1 = {
            "data": {
                "basicCompliance": {
                    "reports": {
                        "items": [{"symbol": "AAPL", "status": "COMPLIANT"}],
                        "nextToken": "page2",
                    }
                }
            }
        }

        mock_response_page2 = {
            "data": {
                "basicCompliance": {
                    "reports": {
                        "items": [{"symbol": "MSFT", "status": "COMPLIANT"}],
                        "nextToken": None,
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.side_effect = [mock_response_page1, mock_response_page2]

            results = gateway_with_limiter.get_all_reports(asset_type="stock")

            assert len(results) == 2
            assert mock_rate_limiter.acquire.call_count == 2  # Once per page

    def test_get_all_reports_api_error_raises_exception(self, gateway):
        """Test that API errors raise ComplianceException."""
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Network error")

            with pytest.raises(ComplianceException, match="Failed to fetch all reports"):
                gateway.get_all_reports(asset_type="stock")


class TestFetchReportsPage:
    """Test _fetch_reports_page method."""

    @pytest.fixture
    def gateway(self):
        """Create gateway for testing."""
        return ZoyaComplianceGateway(api_key="sandbox-test-key")

    def test_fetch_reports_page_stocks(self, gateway):
        """Test fetching a page of stock reports."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "reports": {
                        "items": [
                            {"symbol": "AAPL", "status": "COMPLIANT"},
                            {"symbol": "MSFT", "status": "COMPLIANT"},
                        ],
                        "nextToken": "next_page_token",
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            result = gateway._fetch_reports_page(asset_type="stock")

            assert len(result["items"]) == 2
            assert result["nextToken"] == "next_page_token"
            assert result["items"][0]["symbol"] == "AAPL"

    def test_fetch_reports_page_funds(self, gateway):
        """Test fetching a page of fund reports."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "funds": {
                        "items": [{"symbol": "UMMA", "status": "COMPLIANT"}],
                        "nextToken": None,
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            result = gateway._fetch_reports_page(asset_type="fund")

            assert len(result["items"]) == 1
            assert result["items"][0]["symbol"] == "UMMA"
            assert result["nextToken"] is None

    def test_fetch_reports_page_with_status_filter(self, gateway):
        """Test fetching page with status filter."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "reports": {
                        "items": [{"symbol": "AAPL", "status": "COMPLIANT"}],
                        "nextToken": None,
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            result = gateway._fetch_reports_page(
                asset_type="stock",
                status_filter="COMPLIANT",
            )

            assert len(result["items"]) == 1
            # Verify status filter was passed inline in GraphQL query
            call_args = mock_post.call_args[1]["json"]
            query = call_args["query"]
            assert "filters: { status: COMPLIANT }" in query

    def test_fetch_reports_page_with_next_token(self, gateway):
        """Test fetching page with pagination token."""
        mock_response = {
            "data": {
                "basicCompliance": {
                    "reports": {
                        "items": [{"symbol": "GOOGL", "status": "COMPLIANT"}],
                        "nextToken": None,
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            result = gateway._fetch_reports_page(
                asset_type="stock",
                next_token="pagination_token",
            )

            assert len(result["items"]) == 1
            # Verify nextToken was passed inline in GraphQL query
            call_args = mock_post.call_args[1]["json"]
            query = call_args["query"]
            assert 'nextToken: "pagination_token"' in query

    def test_fetch_reports_page_no_data_returns_empty(self, gateway):
        """Test fetching page with no data returns empty result."""
        mock_response = {"data": {"basicCompliance": {}}}

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            result = gateway._fetch_reports_page(asset_type="stock")

            assert result["items"] == []
            assert result["nextToken"] is None

    def test_fetch_reports_page_applies_rate_limiting(self, gateway):
        """Test that rate limiting is applied before fetching page."""
        mock_rate_limiter = Mock(spec=RateLimiter)
        gateway_with_limiter = ZoyaComplianceGateway(
            api_key="test-key",
            rate_limiter=mock_rate_limiter,
        )

        mock_response = {
            "data": {
                "basicCompliance": {
                    "reports": {
                        "items": [],
                        "nextToken": None,
                    }
                }
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            gateway_with_limiter._fetch_reports_page(asset_type="stock")

            mock_rate_limiter.acquire.assert_called_once_with("zoya")
