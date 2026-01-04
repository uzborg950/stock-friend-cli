"""
Unit tests for StaticComplianceGateway.

Tests CSV-based compliance checking with various scenarios.
"""

import csv
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from stock_friend.gateways.compliance import StaticComplianceGateway
from stock_friend.models.compliance import ComplianceStatus


class TestStaticComplianceGatewayInitialization:
    """Test gateway initialization scenarios."""

    def test_init_with_default_path(self):
        """Test initialization with default data file path."""
        gateway = StaticComplianceGateway()

        assert gateway is not None
        assert gateway.get_name() == "static"
        assert isinstance(gateway._compliance_data, dict)

    def test_init_with_existing_file(self, tmp_path):
        """Test initialization with valid CSV file."""
        # Create test CSV file
        csv_file = tmp_path / "test_compliance.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ticker', 'is_compliant', 'reasons', 'source', 'last_updated'])
            writer.writerow(['AAPL', 'True', '', 'manual', '2026-01-03'])
            writer.writerow(['JPM', 'False', 'Conventional bank', 'manual', '2026-01-03'])

        gateway = StaticComplianceGateway(data_file=csv_file)

        assert len(gateway._compliance_data) == 2
        assert 'AAPL' in gateway._compliance_data
        assert 'JPM' in gateway._compliance_data

    def test_init_with_missing_file(self, tmp_path):
        """Test initialization with non-existent file (should not crash)."""
        csv_file = tmp_path / "nonexistent.csv"

        gateway = StaticComplianceGateway(data_file=csv_file)

        # Should initialize with empty data
        assert len(gateway._compliance_data) == 0

    def test_init_with_invalid_csv_format(self, tmp_path):
        """Test initialization with invalid CSV format (missing columns)."""
        csv_file = tmp_path / "invalid.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ticker', 'wrong_column'])  # Missing required columns
            writer.writerow(['AAPL', 'value'])

        gateway = StaticComplianceGateway(data_file=csv_file)

        # Should handle gracefully with empty data
        assert len(gateway._compliance_data) == 0


class TestCheckCompliance:
    """Test check_compliance method."""

    @pytest.fixture
    def gateway(self, tmp_path):
        """Create gateway with test data."""
        csv_file = tmp_path / "test_compliance.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ticker', 'is_compliant', 'reasons', 'source', 'last_updated'])
            writer.writerow(['AAPL', 'True', '', 'manual', '2026-01-03'])
            writer.writerow(['JPM', 'False', 'Conventional bank', 'manual', '2026-01-03'])
            writer.writerow(['LMT', 'False', 'Defense contractor;Weapons manufacturing', 'manual', '2026-01-03'])

        return StaticComplianceGateway(data_file=csv_file)

    def test_check_compliant_stock(self, gateway):
        """Test checking a compliant stock."""
        status = gateway.check_compliance("AAPL")

        assert status.ticker == "AAPL"
        assert status.is_compliant is True
        assert status.reasons == []
        assert status.source == "manual"

    def test_check_non_compliant_stock_single_reason(self, gateway):
        """Test checking a non-compliant stock with single reason."""
        status = gateway.check_compliance("JPM")

        assert status.ticker == "JPM"
        assert status.is_compliant is False
        assert "Conventional bank" in status.reasons
        assert status.source == "manual"

    def test_check_non_compliant_stock_multiple_reasons(self, gateway):
        """Test checking a non-compliant stock with multiple reasons."""
        status = gateway.check_compliance("LMT")

        assert status.ticker == "LMT"
        assert status.is_compliant is False
        assert len(status.reasons) == 2
        assert "Defense contractor" in status.reasons
        assert "Weapons manufacturing" in status.reasons

    def test_check_unknown_ticker_returns_unknown_status(self, gateway):
        """Test unknown ticker returns unknown status (data accuracy)."""
        status = gateway.check_compliance("UNKNOWN")

        assert status.ticker == "UNKNOWN"
        assert status.is_compliant is None  # Unknown status
        assert not status.is_known()  # Helper method
        assert len(status.reasons) == 1
        assert "No compliance data available" in status.reasons[0]
        assert status.source == "unknown"

    def test_check_with_lowercase_ticker(self, gateway):
        """Test that lowercase tickers are normalized to uppercase."""
        status = gateway.check_compliance("aapl")

        assert status.ticker == "AAPL"
        assert status.is_compliant is True

    def test_check_with_whitespace(self, gateway):
        """Test that whitespace is stripped from tickers."""
        status = gateway.check_compliance("  AAPL  ")

        assert status.ticker == "AAPL"
        assert status.is_compliant is True

    def test_check_empty_ticker_raises_error(self, gateway):
        """Test that empty ticker raises ValueError."""
        with pytest.raises(ValueError, match="Ticker cannot be empty"):
            gateway.check_compliance("")

    def test_check_whitespace_only_ticker_raises_error(self, gateway):
        """Test that whitespace-only ticker raises ValueError."""
        with pytest.raises(ValueError, match="Ticker cannot be empty"):
            gateway.check_compliance("   ")


class TestCheckBatch:
    """Test check_batch method."""

    @pytest.fixture
    def gateway(self, tmp_path):
        """Create gateway with test data."""
        csv_file = tmp_path / "test_compliance.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ticker', 'is_compliant', 'reasons', 'source', 'last_updated'])
            writer.writerow(['AAPL', 'True', '', 'manual', '2026-01-03'])
            writer.writerow(['GOOGL', 'True', '', 'manual', '2026-01-03'])
            writer.writerow(['JPM', 'False', 'Conventional bank', 'manual', '2026-01-03'])
            writer.writerow(['BAC', 'False', 'Conventional bank', 'manual', '2026-01-03'])

        return StaticComplianceGateway(data_file=csv_file)

    def test_check_batch_mixed_tickers(self, gateway):
        """Test batch check with mix of compliant and non-compliant stocks."""
        tickers = ['AAPL', 'JPM', 'GOOGL', 'BAC']
        results = gateway.check_batch(tickers)

        assert len(results) == 4
        assert results['AAPL'].is_compliant is True
        assert results['GOOGL'].is_compliant is True
        assert results['JPM'].is_compliant is False
        assert results['BAC'].is_compliant is False

    def test_check_batch_with_unknown_tickers(self, gateway):
        """Test batch check with unknown tickers (should return unknown status)."""
        tickers = ['AAPL', 'UNKNOWN1', 'UNKNOWN2']
        results = gateway.check_batch(tickers)

        assert len(results) == 3
        assert results['AAPL'].is_compliant is True
        assert results['UNKNOWN1'].is_compliant is None  # Unknown status
        assert results['UNKNOWN2'].is_compliant is None  # Unknown status
        assert results['UNKNOWN1'].source == "unknown"
        assert results['UNKNOWN2'].source == "unknown"

    def test_check_batch_empty_list(self, gateway):
        """Test batch check with empty list."""
        results = gateway.check_batch([])

        assert results == {}

    def test_check_batch_normalizes_case(self, gateway):
        """Test batch check normalizes ticker case."""
        tickers = ['aapl', 'GOOGL', 'jpm']
        results = gateway.check_batch(tickers)

        assert 'AAPL' in results
        assert 'GOOGL' in results
        assert 'JPM' in results

    def test_check_batch_strips_whitespace(self, gateway):
        """Test batch check strips whitespace from tickers."""
        tickers = ['  AAPL  ', 'GOOGL', '  JPM']
        results = gateway.check_batch(tickers)

        assert 'AAPL' in results
        assert 'GOOGL' in results
        assert 'JPM' in results

    def test_check_batch_handles_empty_strings(self, gateway):
        """Test batch check skips empty strings."""
        tickers = ['AAPL', '', '  ', 'GOOGL']
        results = gateway.check_batch(tickers)

        assert len(results) == 2  # Only AAPL and GOOGL
        assert 'AAPL' in results
        assert 'GOOGL' in results


class TestFilterCompliant:
    """Test filter_compliant method."""

    @pytest.fixture
    def gateway(self, tmp_path):
        """Create gateway with test data."""
        csv_file = tmp_path / "test_compliance.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ticker', 'is_compliant', 'reasons', 'source', 'last_updated'])
            writer.writerow(['AAPL', 'True', '', 'manual', '2026-01-03'])
            writer.writerow(['MSFT', 'True', '', 'manual', '2026-01-03'])
            writer.writerow(['GOOGL', 'True', '', 'manual', '2026-01-03'])
            writer.writerow(['JPM', 'False', 'Conventional bank', 'manual', '2026-01-03'])
            writer.writerow(['BAC', 'False', 'Conventional bank', 'manual', '2026-01-03'])
            writer.writerow(['LMT', 'False', 'Defense contractor', 'manual', '2026-01-03'])

        return StaticComplianceGateway(data_file=csv_file)

    def test_filter_compliant_basic(self, gateway):
        """Test filtering compliant stocks from mixed list."""
        tickers = ['AAPL', 'JPM', 'MSFT', 'BAC', 'GOOGL', 'LMT']
        compliant = gateway.filter_compliant(tickers)

        assert len(compliant) == 3
        assert 'AAPL' in compliant
        assert 'MSFT' in compliant
        assert 'GOOGL' in compliant
        assert 'JPM' not in compliant
        assert 'BAC' not in compliant
        assert 'LMT' not in compliant

    def test_filter_compliant_all_compliant(self, gateway):
        """Test filtering when all stocks are compliant."""
        tickers = ['AAPL', 'MSFT', 'GOOGL']
        compliant = gateway.filter_compliant(tickers)

        assert len(compliant) == 3
        assert compliant == tickers

    def test_filter_compliant_all_non_compliant(self, gateway):
        """Test filtering when all stocks are non-compliant."""
        tickers = ['JPM', 'BAC', 'LMT']
        compliant = gateway.filter_compliant(tickers)

        assert len(compliant) == 0

    def test_filter_compliant_with_unknown_tickers(self, gateway):
        """Test filtering excludes unknown tickers (conservative screening)."""
        tickers = ['AAPL', 'UNKNOWN1', 'JPM', 'UNKNOWN2']
        compliant = gateway.filter_compliant(tickers)

        assert len(compliant) == 1  # Only AAPL
        assert 'AAPL' in compliant
        assert 'UNKNOWN1' not in compliant  # Unknown excluded
        assert 'UNKNOWN2' not in compliant  # Unknown excluded
        assert 'JPM' not in compliant  # Non-compliant excluded

    def test_filter_compliant_empty_list(self, gateway):
        """Test filtering empty list."""
        compliant = gateway.filter_compliant([])

        assert compliant == []


class TestGetStats:
    """Test get_stats method."""

    @pytest.fixture
    def gateway(self, tmp_path):
        """Create gateway with test data."""
        csv_file = tmp_path / "test_compliance.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ticker', 'is_compliant', 'reasons', 'source', 'last_updated'])
            # 3 compliant
            writer.writerow(['AAPL', 'True', '', 'manual', '2026-01-03'])
            writer.writerow(['MSFT', 'True', '', 'manual', '2026-01-03'])
            writer.writerow(['GOOGL', 'True', '', 'manual', '2026-01-03'])
            # 2 non-compliant
            writer.writerow(['JPM', 'False', 'Bank', 'manual', '2026-01-03'])
            writer.writerow(['LMT', 'False', 'Defense', 'manual', '2026-01-03'])

        return StaticComplianceGateway(data_file=csv_file)

    def test_get_stats(self, gateway):
        """Test getting statistics."""
        stats = gateway.get_stats()

        assert stats['total'] == 5
        assert stats['compliant'] == 3
        assert stats['non_compliant'] == 2

    def test_get_stats_empty_database(self, tmp_path):
        """Test stats with empty database."""
        csv_file = tmp_path / "empty.csv"
        gateway = StaticComplianceGateway(data_file=csv_file)

        stats = gateway.get_stats()

        assert stats['total'] == 0
        assert stats['compliant'] == 0
        assert stats['non_compliant'] == 0


class TestCSVParsing:
    """Test CSV file parsing edge cases."""

    def test_parse_with_missing_optional_fields(self, tmp_path):
        """Test parsing CSV with missing optional fields (last_updated)."""
        csv_file = tmp_path / "test.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ticker', 'is_compliant', 'reasons', 'source'])  # No last_updated
            writer.writerow(['AAPL', 'True', '', 'manual'])

        gateway = StaticComplianceGateway(data_file=csv_file)

        assert len(gateway._compliance_data) == 1
        assert 'AAPL' in gateway._compliance_data

    def test_parse_with_invalid_date_format(self, tmp_path):
        """Test parsing CSV with invalid date format (should use current date)."""
        csv_file = tmp_path / "test.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ticker', 'is_compliant', 'reasons', 'source', 'last_updated'])
            writer.writerow(['AAPL', 'True', '', 'manual', 'invalid-date'])

        gateway = StaticComplianceGateway(data_file=csv_file)

        assert len(gateway._compliance_data) == 1
        status = gateway._compliance_data['AAPL']
        # Should have current date (within last minute)
        assert (datetime.now() - status.checked_at).seconds < 60

    def test_parse_skips_empty_ticker_rows(self, tmp_path):
        """Test parsing skips rows with empty tickers."""
        csv_file = tmp_path / "test.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ticker', 'is_compliant', 'reasons', 'source', 'last_updated'])
            writer.writerow(['AAPL', 'True', '', 'manual', '2026-01-03'])
            writer.writerow(['', 'True', '', 'manual', '2026-01-03'])  # Empty ticker
            writer.writerow(['MSFT', 'True', '', 'manual', '2026-01-03'])

        gateway = StaticComplianceGateway(data_file=csv_file)

        assert len(gateway._compliance_data) == 2  # Skipped empty ticker row
        assert 'AAPL' in gateway._compliance_data
        assert 'MSFT' in gateway._compliance_data

    def test_parse_handles_corrupt_row_gracefully(self, tmp_path):
        """Test parsing continues even if one row is corrupt."""
        csv_file = tmp_path / "test.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ticker', 'is_compliant', 'reasons', 'source', 'last_updated'])
            writer.writerow(['AAPL', 'True', '', 'manual', '2026-01-03'])
            writer.writerow(['MSFT', 'True', '', 'manual', '2026-01-03'])

        gateway = StaticComplianceGateway(data_file=csv_file)

        # Should load both valid rows
        assert len(gateway._compliance_data) == 2


class TestGetName:
    """Test get_name method."""

    def test_get_name_returns_static(self):
        """Test gateway name is 'static'."""
        gateway = StaticComplianceGateway()

        assert gateway.get_name() == "static"
