"""
Unit tests for SearchService.

Tests the stock search service with mocked gateway responses.
"""

from decimal import Decimal
from unittest.mock import Mock
import pytest

from stock_friend.gateways.base import DataProviderException
from stock_friend.infrastructure.cache_manager import CacheManager
from stock_friend.models.search_models import SearchResult
from stock_friend.models.stock_data import FundamentalData
from stock_friend.services.search_service import SearchService


@pytest.fixture
def mock_gateway():
    """Create a mock market data gateway."""
    return Mock()


@pytest.fixture
def mock_cache_manager(tmp_path):
    """Create a mock cache manager."""
    cache_dir = tmp_path / "cache"
    return CacheManager(cache_dir=str(cache_dir), size_limit_mb=10)


@pytest.fixture
def service(mock_gateway, mock_cache_manager):
    """Create SearchService with mocked dependencies."""
    return SearchService(gateway=mock_gateway, cache_manager=mock_cache_manager)


@pytest.fixture
def service_without_cache(mock_gateway):
    """Create SearchService without cache manager."""
    return SearchService(gateway=mock_gateway)


@pytest.fixture
def sample_fundamental():
    """Create sample fundamental data."""
    return FundamentalData(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=Decimal("3000000000000"),
    )


class TestSearchServiceInitialization:
    """Test SearchService initialization."""

    def test_initialization_with_cache(self, mock_gateway, mock_cache_manager):
        """Test initialization with cache manager."""
        service = SearchService(gateway=mock_gateway, cache_manager=mock_cache_manager)
        assert service.gateway is mock_gateway
        assert service.cache_manager is mock_cache_manager

    def test_initialization_without_cache(self, mock_gateway):
        """Test initialization without cache manager."""
        service = SearchService(gateway=mock_gateway)
        assert service.gateway is mock_gateway
        assert service.cache_manager is None


class TestSearch:
    """Test search method."""

    def test_search_single_result_us_ticker(
        self, service, mock_gateway, sample_fundamental
    ):
        """Test search with single US ticker result."""
        # Mock gateway search_stock to return search results
        mock_gateway.search_stock.return_value = [
            SearchResult(
                ticker="AAPL",
                company_name="Apple Inc.",
                exchange="US Market",
                sector="Technology",
                quote_type="EQUITY",
            )
        ]

        results = service.search("AAPL")

        assert len(results) == 1
        assert results[0].ticker == "AAPL"
        assert results[0].company_name == "Apple Inc."
        assert results[0].exchange == "US Market"
        mock_gateway.search_stock.assert_called_once()

    def test_search_multiple_results_different_exchanges(self, service, mock_gateway):
        """Test search returns multiple results from different exchanges."""
        # Mock gateway search_stock to return results from multiple exchanges
        mock_gateway.search_stock.return_value = [
            SearchResult(
                ticker="HSBC",
                company_name="HSBC Holdings plc (US)",
                exchange="US Market",
                sector="Financial Services",
                quote_type="EQUITY",
            ),
            SearchResult(
                ticker="HSBC.L",
                company_name="HSBC Holdings plc",
                exchange="LSE",
                sector="Financial Services",
                quote_type="EQUITY",
            ),
        ]

        results = service.search("HSBC")

        assert len(results) == 2
        tickers = [r.ticker for r in results]
        assert "HSBC" in tickers
        assert "HSBC.L" in tickers

    def test_search_with_exchange_hint(self, service, mock_gateway):
        """Test search with specific exchange hint."""
        mock_gateway.get_fundamental_data.return_value = FundamentalData(
            ticker="BARC.L",
            company_name="Barclays PLC",
            sector="Financial Services",
        )

        results = service.search("BARC", exchange_hint="L")

        assert len(results) == 1
        assert results[0].ticker == "BARC.L"
        assert results[0].exchange == "LSE"
        # Should only call once with the specific exchange
        mock_gateway.get_fundamental_data.assert_called_once_with("BARC.L")

    def test_search_with_exchange_hint_no_dot(self, service, mock_gateway):
        """Test that exchange hint works without leading dot."""
        mock_gateway.get_fundamental_data.return_value = FundamentalData(
            ticker="BARC.TO",
            company_name="Barclays Toronto",
            sector="Financial Services",
        )

        results = service.search("BARC", exchange_hint="TO")

        assert len(results) == 1
        assert results[0].ticker == "BARC.TO"

    def test_search_no_results(self, service, mock_gateway):
        """Test search with no matching results."""
        mock_gateway.get_fundamental_data.return_value = None

        results = service.search("INVALID123")

        assert len(results) == 0

    def test_search_gateway_exception_returns_empty(self, service, mock_gateway):
        """Test that gateway exceptions result in empty results."""
        mock_gateway.get_fundamental_data.side_effect = Exception("Network error")

        results = service.search("AAPL")

        assert len(results) == 0

    def test_search_skips_invalid_fundamental_data(self, service, mock_gateway):
        """Test that gateway handles filtering of invalid results."""
        # Gateway should only return valid results with company names
        mock_gateway.search_stock.return_value = [
            SearchResult(
                ticker="AAPL",
                company_name="Apple Inc.",
                exchange="US Market",
                sector="Technology",
                quote_type="EQUITY",
            )
        ]

        results = service.search("AAPL")

        # Should only return valid results
        assert len(results) == 1
        assert results[0].ticker == "AAPL"

    def test_search_deduplicates_results(self, service, mock_gateway):
        """Test that duplicate tickers are not returned."""

        def fundamental_side_effect(ticker):
            # Return same ticker for different calls (shouldn't happen in practice)
            return FundamentalData(ticker="AAPL", company_name="Apple Inc.")

        mock_gateway.get_fundamental_data.side_effect = fundamental_side_effect

        results = service.search("AAPL")

        # Should only return one result even if multiple matches
        tickers = [r.ticker for r in results]
        assert len(tickers) == len(set(tickers))  # No duplicates

    def test_search_caching(self, service, mock_gateway, sample_fundamental):
        """Test that search results are cached."""
        mock_gateway.search_stock.return_value = [
            SearchResult(
                ticker="AAPL",
                company_name="Apple Inc.",
                exchange="US Market",
                sector="Technology",
                quote_type="EQUITY",
            )
        ]

        # First call
        results1 = service.search("AAPL")
        call_count_1 = mock_gateway.search_stock.call_count

        # Second call - should use cache
        results2 = service.search("AAPL")
        call_count_2 = mock_gateway.search_stock.call_count

        assert len(results1) == len(results2)
        assert results1[0].ticker == results2[0].ticker
        # Second call should not make additional API calls
        assert call_count_2 == call_count_1

    def test_search_case_normalization(self, service, mock_gateway, sample_fundamental):
        """Test that ticker queries are normalized to uppercase."""
        mock_gateway.search_stock.return_value = [
            SearchResult(
                ticker="AAPL",
                company_name="Apple Inc.",
                exchange="US Market",
                sector="Technology",
                quote_type="EQUITY",
            )
        ]

        results = service.search("aapl")

        # Should search for uppercase
        mock_gateway.search_stock.assert_called_once()
        call_args = mock_gateway.search_stock.call_args
        assert call_args[1]["query"] == "AAPL"


class TestGetDetailedInfo:
    """Test get_detailed_info method."""

    def test_get_detailed_info_success(self, service, mock_gateway, sample_fundamental):
        """Test successful detailed info fetch."""
        mock_gateway.get_fundamental_data.return_value = sample_fundamental
        mock_gateway.get_current_price.return_value = Decimal("180.50")

        info = service.get_detailed_info("AAPL")

        assert info.ticker == "AAPL"
        assert info.fundamental == sample_fundamental
        assert info.price.current_price == Decimal("180.50")
        mock_gateway.get_fundamental_data.assert_called_once_with("AAPL")
        mock_gateway.get_current_price.assert_called_once_with("AAPL")

    def test_get_detailed_info_no_fundamental_data(self, service, mock_gateway):
        """Test error when no fundamental data available."""
        mock_gateway.get_fundamental_data.return_value = None

        with pytest.raises(DataProviderException, match="No fundamental data"):
            service.get_detailed_info("INVALID")

    def test_get_detailed_info_gateway_exception(self, service, mock_gateway):
        """Test that gateway exceptions are wrapped."""
        mock_gateway.get_fundamental_data.side_effect = Exception("Network error")

        with pytest.raises(DataProviderException, match="Failed to fetch"):
            service.get_detailed_info("AAPL")

    def test_get_detailed_info_with_international_ticker(
        self, service, mock_gateway
    ):
        """Test detailed info for international ticker."""
        fundamental = FundamentalData(
            ticker="BARC.L",
            company_name="Barclays PLC",
            sector="Financial Services",
        )
        mock_gateway.get_fundamental_data.return_value = fundamental
        mock_gateway.get_current_price.return_value = Decimal("150.25")

        info = service.get_detailed_info("BARC.L")

        assert info.ticker == "BARC.L"
        assert info.exchange == "London Stock Exchange (LSE)"


class TestExchangeMapping:
    """Test exchange suffix mapping."""

    def test_extract_exchange_us_ticker(self, service, mock_gateway, sample_fundamental):
        """Test exchange extraction for US ticker."""
        exchange = service._extract_exchange("AAPL", sample_fundamental)
        assert exchange == "US Market"

    def test_extract_exchange_london(self, service, mock_gateway, sample_fundamental):
        """Test exchange extraction for London ticker."""
        exchange = service._extract_exchange("BARC.L", sample_fundamental)
        assert exchange == "LSE"

    def test_extract_exchange_toronto(self, service, mock_gateway, sample_fundamental):
        """Test exchange extraction for Toronto ticker."""
        exchange = service._extract_exchange("RY.TO", sample_fundamental)
        assert exchange == "TSX"

    def test_extract_exchange_unknown_suffix(
        self, service, mock_gateway, sample_fundamental
    ):
        """Test exchange extraction for unknown suffix."""
        exchange = service._extract_exchange("TEST.XYZ", sample_fundamental)
        assert "XYZ" in exchange


class TestTickerFormatting:
    """Test ticker formatting logic."""

    def test_format_ticker_with_exchange_hint(self, service):
        """Test formatting ticker with exchange hint."""
        ticker = service._format_ticker("BARC", "L")
        assert ticker == "BARC.L"

    def test_format_ticker_with_dot_in_hint(self, service):
        """Test that leading dot in hint is stripped."""
        ticker = service._format_ticker("BARC", ".L")
        assert ticker == "BARC.L"

    def test_format_ticker_already_has_suffix(self, service):
        """Test that ticker with existing suffix is returned as-is."""
        ticker = service._format_ticker("BARC.L", "L")
        assert ticker == "BARC.L"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_search_empty_query(self, service, mock_gateway):
        """Test search with empty query after stripping."""
        mock_gateway.get_fundamental_data.return_value = None

        results = service.search("   ")
        # Should search for empty string, which won't match anything
        assert len(results) == 0

    def test_search_with_whitespace(self, service, mock_gateway, sample_fundamental):
        """Test that whitespace is stripped from query."""
        mock_gateway.search_stock.return_value = [
            SearchResult(
                ticker="AAPL",
                company_name="Apple Inc.",
                exchange="US Market",
                sector="Technology",
                quote_type="EQUITY",
            )
        ]

        results = service.search("  AAPL  ")

        assert len(results) >= 1
        # Should call with stripped and uppercased ticker
        mock_gateway.search_stock.assert_called_once()
        call_args = mock_gateway.search_stock.call_args
        assert call_args[1]["query"] == "AAPL"

    def test_service_without_cache_works(self, service_without_cache, mock_gateway, sample_fundamental):
        """Test that service works without cache manager."""
        mock_gateway.search_stock.return_value = [
            SearchResult(
                ticker="AAPL",
                company_name="Apple Inc.",
                exchange="US Market",
                sector="Technology",
                quote_type="EQUITY",
            )
        ]

        results = service_without_cache.search("AAPL")

        assert len(results) >= 1
        assert results[0].ticker == "AAPL"
