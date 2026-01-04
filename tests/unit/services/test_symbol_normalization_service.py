"""
Unit tests for SymbolNormalizationService.

Tests symbol normalization between gateway formats with comprehensive
coverage of European markets, special cases, and edge cases.
"""

import pytest

from stock_friend.models.symbol import MarketRegion, SymbolConfidence
from stock_friend.services.symbol_normalization_service import (
    SymbolNormalizationService,
)


class TestSymbolNormalizationServiceInitialization:
    """Test service initialization."""

    def test_init_loads_exchange_mappings(self):
        """Test that service initializes with exchange mappings."""
        service = SymbolNormalizationService()

        assert service is not None
        assert len(service._suffix_map) > 0
        assert ".DE" in service._suffix_map
        assert ".L" in service._suffix_map
        assert ".PA" in service._suffix_map

    def test_supported_exchanges_returns_mappings(self):
        """Test getting list of supported exchanges."""
        service = SymbolNormalizationService()

        exchanges = service.get_supported_exchanges()

        assert len(exchanges) > 20  # Should have many major exchanges
        assert any(e.yfinance_suffix == ".DE" for e in exchanges)
        assert any(e.yfinance_suffix == ".L" for e in exchanges)


class TestEuropeanStockNormalization:
    """Test normalization of European stocks."""

    @pytest.fixture
    def service(self):
        """Create service for testing."""
        return SymbolNormalizationService()

    def test_german_stock_xetra(self, service):
        """Test German stock on Xetra (.DE)."""
        result = service.normalize_for_compliance("BMW.DE")

        assert result.base_symbol == "BMW"
        assert result.original_ticker == "BMW.DE"
        assert result.exchange_code == "XETR"
        assert result.market_region == MarketRegion.EU
        assert result.confidence == SymbolConfidence.HIGH
        assert any("Removed .DE" in note for note in result.transformation_notes)

    def test_german_stock_frankfurt(self, service):
        """Test German stock on Frankfurt (.F)."""
        result = service.normalize_for_compliance("SAP.F")

        assert result.base_symbol == "SAP"
        assert result.exchange_code == "XFRA"
        assert result.market_region == MarketRegion.EU
        assert result.confidence == SymbolConfidence.HIGH

    def test_uk_stock_london(self, service):
        """Test UK stock on London Stock Exchange (.L)."""
        result = service.normalize_for_compliance("HSBA.L")

        assert result.base_symbol == "HSBA"
        assert result.exchange_code == "XLON"
        assert result.market_region == MarketRegion.UK
        assert result.confidence == SymbolConfidence.HIGH

    def test_french_stock_euronext_paris(self, service):
        """Test French stock on Euronext Paris (.PA)."""
        result = service.normalize_for_compliance("MC.PA")

        assert result.base_symbol == "MC"
        assert result.exchange_code == "XPAR"
        assert result.market_region == MarketRegion.EU
        assert result.confidence == SymbolConfidence.HIGH

    def test_dutch_stock_euronext_amsterdam(self, service):
        """Test Dutch stock on Euronext Amsterdam (.AS)."""
        result = service.normalize_for_compliance("ASML.AS")

        assert result.base_symbol == "ASML"
        assert result.exchange_code == "XAMS"
        assert result.market_region == MarketRegion.EU

    def test_italian_stock_milan(self, service):
        """Test Italian stock on Borsa Italiana (.MI)."""
        result = service.normalize_for_compliance("ENI.MI")

        assert result.base_symbol == "ENI"
        assert result.exchange_code == "XMIL"
        assert result.market_region == MarketRegion.EU

    def test_swiss_stock(self, service):
        """Test Swiss stock (.SW)."""
        result = service.normalize_for_compliance("NESN.SW")

        assert result.base_symbol == "NESN"
        assert result.exchange_code == "XSWX"
        assert result.market_region == MarketRegion.EU

    def test_nordic_stock_stockholm(self, service):
        """Test Nordic stock on Stockholm exchange (.ST)."""
        result = service.normalize_for_compliance("VOLV-B.ST")

        assert result.base_symbol == "VOLV-B"
        assert result.exchange_code == "XSTO"
        assert result.market_region == MarketRegion.EU


class TestUSStockNormalization:
    """Test normalization of US stocks."""

    @pytest.fixture
    def service(self):
        """Create service for testing."""
        return SymbolNormalizationService()

    def test_us_stock_no_suffix(self, service):
        """Test US stock with no suffix (AAPL)."""
        result = service.normalize_for_compliance("AAPL")

        assert result.base_symbol == "AAPL"
        assert result.original_ticker == "AAPL"
        assert result.market_region == MarketRegion.US
        assert result.confidence == SymbolConfidence.HIGH
        assert any("US market" in note for note in result.transformation_notes)

    def test_us_stock_with_exchange_code(self, service):
        """Test US stock with explicit exchange code."""
        result = service.normalize_for_compliance("AAPL", exchange="NASDAQ")

        assert result.base_symbol == "AAPL"
        assert result.exchange_code == "XNGS"
        assert result.confidence == SymbolConfidence.HIGH


class TestSpecialCaseHandling:
    """Test handling of special cases."""

    @pytest.fixture
    def service(self):
        """Create service for testing."""
        return SymbolNormalizationService()

    def test_dual_class_shares_preserved(self, service):
        """Test that dual-class share suffixes are preserved."""
        result = service.normalize_for_compliance("BRK.A")

        assert result.base_symbol == "BRK.A"
        assert result.original_ticker == "BRK.A"
        assert result.confidence == SymbolConfidence.HIGH
        assert any("Preserved" in note for note in result.transformation_notes)

    def test_class_b_shares_preserved(self, service):
        """Test that class B shares are preserved."""
        result = service.normalize_for_compliance("GOOGL.A")

        # Note: This should be preserved since .A is a share class
        # However, if there's confusion with Austrian exchange (.A could also be Austria),
        # the service should prefer the special suffix interpretation
        assert result.base_symbol == "GOOGL.A"
        assert result.confidence == SymbolConfidence.HIGH

    def test_preferred_shares_preserved(self, service):
        """Test that preferred share suffixes are preserved."""
        result = service.normalize_for_compliance("BAC-PL")

        # The hyphen format for preferred should be preserved
        assert result.base_symbol == "BAC-PL"
        assert result.confidence == SymbolConfidence.HIGH

    def test_warrant_suffix_preserved(self, service):
        """Test that warrant suffixes are preserved."""
        result = service.normalize_for_compliance("SPCE.W")

        assert result.base_symbol == "SPCE.W"
        assert result.confidence == SymbolConfidence.HIGH

    def test_rights_suffix_preserved(self, service):
        """Test that rights suffixes are preserved."""
        result = service.normalize_for_compliance("XYZ.R")

        assert result.base_symbol == "XYZ.R"
        assert result.confidence == SymbolConfidence.HIGH


class TestExtractBaseSymbol:
    """Test extract_base_symbol helper method."""

    @pytest.fixture
    def service(self):
        """Create service for testing."""
        return SymbolNormalizationService()

    def test_extract_removes_german_suffix(self, service):
        """Test extracting base from German ticker."""
        assert service.extract_base_symbol("BMW.DE") == "BMW"
        assert service.extract_base_symbol("SAP.F") == "SAP"

    def test_extract_removes_uk_suffix(self, service):
        """Test extracting base from UK ticker."""
        assert service.extract_base_symbol("HSBA.L") == "HSBA"

    def test_extract_preserves_special_suffixes(self, service):
        """Test that special suffixes are preserved."""
        assert service.extract_base_symbol("BRK.A") == "BRK.A"
        assert service.extract_base_symbol("BRK.B") == "BRK.B"
        assert service.extract_base_symbol("BAC-A") == "BAC-A"

    def test_extract_us_stock_unchanged(self, service):
        """Test US stock without suffix stays the same."""
        assert service.extract_base_symbol("AAPL") == "AAPL"
        assert service.extract_base_symbol("MSFT") == "MSFT"

    def test_extract_handles_lowercase(self, service):
        """Test that lowercase input is normalized."""
        assert service.extract_base_symbol("bmw.de") == "BMW"
        assert service.extract_base_symbol("aapl") == "AAPL"

    def test_extract_handles_whitespace(self, service):
        """Test that whitespace is stripped."""
        assert service.extract_base_symbol("  BMW.DE  ") == "BMW"


class TestGetExchangeFromSuffix:
    """Test get_exchange_from_suffix helper method."""

    @pytest.fixture
    def service(self):
        """Create service for testing."""
        return SymbolNormalizationService()

    def test_get_exchange_german_xetra(self, service):
        """Test getting exchange code for German Xetra."""
        assert service.get_exchange_from_suffix("BMW.DE") == "XETR"

    def test_get_exchange_frankfurt(self, service):
        """Test getting exchange code for Frankfurt."""
        assert service.get_exchange_from_suffix("SAP.F") == "XFRA"

    def test_get_exchange_london(self, service):
        """Test getting exchange code for London."""
        assert service.get_exchange_from_suffix("HSBA.L") == "XLON"

    def test_get_exchange_no_suffix_returns_none(self, service):
        """Test that US stock with no suffix returns None."""
        assert service.get_exchange_from_suffix("AAPL") is None

    def test_get_exchange_case_insensitive(self, service):
        """Test that lookup is case-insensitive."""
        assert service.get_exchange_from_suffix("bmw.de") == "XETR"
        assert service.get_exchange_from_suffix("BMW.DE") == "XETR"


class TestGetMarketRegion:
    """Test get_market_region helper method."""

    @pytest.fixture
    def service(self):
        """Create service for testing."""
        return SymbolNormalizationService()

    def test_german_stock_is_eu(self, service):
        """Test German stock is classified as EU."""
        assert service.get_market_region("BMW.DE") == MarketRegion.EU

    def test_uk_stock_is_uk(self, service):
        """Test UK stock is classified as UK."""
        assert service.get_market_region("HSBA.L") == MarketRegion.UK

    def test_french_stock_is_eu(self, service):
        """Test French stock is classified as EU."""
        assert service.get_market_region("MC.PA") == MarketRegion.EU

    def test_us_stock_is_us(self, service):
        """Test US stock is classified as US."""
        assert service.get_market_region("AAPL") == MarketRegion.US

    def test_asian_stock_is_asia(self, service):
        """Test Asian stock is classified as ASIA."""
        assert service.get_market_region("2330.T") == MarketRegion.ASIA


class TestGetExchangeInfo:
    """Test get_exchange_info helper method."""

    @pytest.fixture
    def service(self):
        """Create service for testing."""
        return SymbolNormalizationService()

    def test_get_info_by_suffix(self, service):
        """Test getting exchange info by suffix."""
        info = service.get_exchange_info(".DE")

        assert info is not None
        assert info.yfinance_suffix == ".DE"
        assert info.bloomberg_code == "XETR"
        assert info.exchange_name == "Deutsche Börse Xetra"
        assert info.market_region == MarketRegion.EU
        assert info.country_code == "DE"

    def test_get_info_by_bloomberg_code(self, service):
        """Test getting exchange info by Bloomberg code."""
        info = service.get_exchange_info("XLON")

        assert info is not None
        assert info.yfinance_suffix == ".L"
        assert info.bloomberg_code == "XLON"
        assert info.market_region == MarketRegion.UK

    def test_get_info_unknown_returns_none(self, service):
        """Test that unknown code returns None."""
        assert service.get_exchange_info(".UNKNOWN") is None
        assert service.get_exchange_info("XUNKNOWN") is None


class TestNormalizationAuditTrail:
    """Test audit trail functionality."""

    @pytest.fixture
    def service(self):
        """Create service for testing."""
        return SymbolNormalizationService()

    def test_transformation_notes_recorded(self, service):
        """Test that transformation notes are recorded."""
        result = service.normalize_for_compliance("BMW.DE")

        assert len(result.transformation_notes) > 0
        assert any(".DE" in note for note in result.transformation_notes)

    def test_summary_method_works(self, service):
        """Test that summary method produces readable output."""
        result = service.normalize_for_compliance("BMW.DE")
        summary = result.summary()

        assert "BMW.DE" in summary
        assert "BMW" in summary
        assert "HIGH" in summary

    def test_str_representation(self, service):
        """Test string representation of normalized symbol."""
        result = service.normalize_for_compliance("BMW.DE")
        str_repr = str(result)

        assert "BMW.DE" in str_repr
        assert "BMW" in str_repr


class TestConfidenceScoring:
    """Test confidence scoring logic."""

    @pytest.fixture
    def service(self):
        """Create service for testing."""
        return SymbolNormalizationService()

    def test_known_exchange_is_high_confidence(self, service):
        """Test known exchanges get HIGH confidence."""
        result = service.normalize_for_compliance("BMW.DE")
        assert result.confidence == SymbolConfidence.HIGH
        assert result.is_high_confidence()

    def test_us_stock_is_high_confidence(self, service):
        """Test US stocks get HIGH confidence."""
        result = service.normalize_for_compliance("AAPL")
        assert result.confidence == SymbolConfidence.HIGH

    def test_unknown_exchange_code_is_medium_confidence(self, service):
        """Test unknown exchange code gets MEDIUM confidence."""
        result = service.normalize_for_compliance("XYZ", exchange="UNKNOWN_EXCHANGE")
        assert result.confidence == SymbolConfidence.MEDIUM
        assert not result.is_low_confidence()


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def service(self):
        """Create service for testing."""
        return SymbolNormalizationService()

    def test_empty_ticker_handled(self, service):
        """Test empty ticker string."""
        result = service.normalize_for_compliance("")
        assert result.base_symbol == ""

    def test_whitespace_ticker_handled(self, service):
        """Test whitespace-only ticker."""
        result = service.normalize_for_compliance("   ")
        assert result.base_symbol == ""

    def test_very_long_ticker(self, service):
        """Test very long ticker symbol."""
        long_ticker = "VERYLONGTICKERSYMBOL" * 10
        result = service.normalize_for_compliance(long_ticker)
        assert result.base_symbol == long_ticker.upper()

    def test_ticker_with_numbers(self, service):
        """Test ticker with numbers."""
        result = service.normalize_for_compliance("3M")
        assert result.base_symbol == "3M"

    def test_ticker_with_special_characters(self, service):
        """Test ticker with special characters."""
        result = service.normalize_for_compliance("BRK-A")
        # Hyphen should be preserved (preferred share format)
        assert "BRK" in result.base_symbol


class TestSourceGatewayTracking:
    """Test source gateway tracking."""

    @pytest.fixture
    def service(self):
        """Create service for testing."""
        return SymbolNormalizationService()

    def test_default_source_gateway(self, service):
        """Test default source gateway."""
        result = service.normalize_for_compliance("BMW.DE")
        assert result.source_gateway == "yfinance"

    def test_custom_source_gateway(self, service):
        """Test custom source gateway."""
        result = service.normalize_for_compliance("BMW.DE", source_gateway="alpha_vantage")
        assert result.source_gateway == "alpha_vantage"


class TestMultipleExchangeSameTicker:
    """Test handling of same company on multiple exchanges."""

    @pytest.fixture
    def service(self):
        """Create service for testing."""
        return SymbolNormalizationService()

    def test_bmw_different_german_exchanges(self, service):
        """Test BMW on different German exchanges normalizes to same base."""
        xetra = service.normalize_for_compliance("BMW.DE")  # Xetra
        frankfurt = service.normalize_for_compliance("BMW.F")  # Frankfurt

        # Both should normalize to same base symbol
        assert xetra.base_symbol == frankfurt.base_symbol == "BMW"

        # But different exchange codes
        assert xetra.exchange_code == "XETR"
        assert frankfurt.exchange_code == "XFRA"
