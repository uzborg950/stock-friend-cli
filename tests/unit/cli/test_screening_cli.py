"""Unit tests for screening CLI module."""

from unittest.mock import MagicMock, patch

import pytest

from stock_friend.cli.screening_cli import (
    _display_screening_results,
    _export_results_mock,
    _get_signal_color,
    _get_xtrender_color,
    _select_strategy,
    _select_universe,
    run_screening_workflow,
)


class TestSignalColorMapping:
    """Test cases for MCDX signal color mapping."""

    def test_get_signal_color_strong_buy(self) -> None:
        """Test color mapping for STRONG_BUY signal."""
        color = _get_signal_color("STRONG_BUY")
        assert color == "bright_green"

    def test_get_signal_color_buy(self) -> None:
        """Test color mapping for BUY signal."""
        color = _get_signal_color("BUY")
        assert color == "green"

    def test_get_signal_color_hold(self) -> None:
        """Test color mapping for HOLD signal."""
        color = _get_signal_color("HOLD")
        assert color == "yellow"

    def test_get_signal_color_sell(self) -> None:
        """Test color mapping for SELL signal."""
        color = _get_signal_color("SELL")
        assert color == "red"

    def test_get_signal_color_unknown(self) -> None:
        """Test color mapping for unknown signal."""
        color = _get_signal_color("UNKNOWN")
        assert color == "white"


class TestXTrenderColorMapping:
    """Test cases for B-XTrender color mapping."""

    def test_get_xtrender_color_green(self) -> None:
        """Test color mapping for GREEN trend."""
        color = _get_xtrender_color("GREEN")
        assert color == "green"

    def test_get_xtrender_color_yellow(self) -> None:
        """Test color mapping for YELLOW trend."""
        color = _get_xtrender_color("YELLOW")
        assert color == "yellow"

    def test_get_xtrender_color_red(self) -> None:
        """Test color mapping for RED trend."""
        color = _get_xtrender_color("RED")
        assert color == "red"

    def test_get_xtrender_color_unknown(self) -> None:
        """Test color mapping for unknown trend."""
        color = _get_xtrender_color("UNKNOWN")
        assert color == "white"


class TestSelectUniverse:
    """Test cases for universe selection."""

    @patch("stock_friend.cli.screening_cli.select_from_list")
    @patch("stock_friend.cli.screening_cli.console.print")
    def test_select_universe_returns_selected_value(
        self, mock_print: MagicMock, mock_select: MagicMock
    ) -> None:
        """Test that _select_universe returns the selected universe."""
        mock_select.return_value = "S&P 500"
        result = _select_universe()
        assert result == "S&P 500"

    @patch("stock_friend.cli.screening_cli.select_from_list")
    @patch("stock_friend.cli.screening_cli.console.print")
    def test_select_universe_returns_none_when_cancelled(
        self, mock_print: MagicMock, mock_select: MagicMock
    ) -> None:
        """Test that _select_universe returns None when cancelled."""
        mock_select.return_value = None
        result = _select_universe()
        assert result is None


class TestSelectStrategy:
    """Test cases for strategy selection."""

    @patch("stock_friend.cli.screening_cli._display_strategy_details")
    @patch("stock_friend.cli.screening_cli.select_from_list")
    @patch("stock_friend.cli.screening_cli.console.print")
    def test_select_strategy_returns_strategy_dict(
        self, mock_print: MagicMock, mock_select: MagicMock, mock_display: MagicMock
    ) -> None:
        """Test that _select_strategy returns a strategy dictionary."""
        mock_select.return_value = "Default Momentum Strategy - Test description"
        result = _select_strategy()
        assert result is not None
        assert isinstance(result, dict)
        assert result["name"] == "Default Momentum Strategy"

    @patch("stock_friend.cli.screening_cli.select_from_list")
    @patch("stock_friend.cli.screening_cli.console.print")
    def test_select_strategy_returns_none_when_cancelled(
        self, mock_print: MagicMock, mock_select: MagicMock
    ) -> None:
        """Test that _select_strategy returns None when cancelled."""
        mock_select.return_value = None
        result = _select_strategy()
        assert result is None


class TestDisplayScreeningResults:
    """Test cases for displaying screening results."""

    @patch("stock_friend.cli.screening_cli.console.print")
    def test_display_screening_results_prints_output(self, mock_print: MagicMock) -> None:
        """Test that _display_screening_results prints formatted output."""
        mock_results = [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "price": 175.50,
                "mcdx_signal": "STRONG_BUY",
                "b_xtrender": "GREEN",
                "halal_status": "COMPLIANT",
                "volume": "52.3M",
                "market_cap": "2.75T",
            }
        ]

        _display_screening_results(mock_results, "Test Strategy", "S&P 500")
        assert mock_print.call_count > 0

    @patch("stock_friend.cli.screening_cli.console.print")
    def test_display_screening_results_handles_empty_list(self, mock_print: MagicMock) -> None:
        """Test that _display_screening_results handles empty results."""
        _display_screening_results([], "Test Strategy", "S&P 500")
        assert mock_print.call_count > 0


class TestExportResultsMock:
    """Test cases for mock export functionality."""

    @patch("stock_friend.cli.screening_cli.console.print")
    @patch("stock_friend.cli.screening_cli.time.time")
    def test_export_results_mock_prints_confirmation(
        self, mock_time: MagicMock, mock_print: MagicMock
    ) -> None:
        """Test that _export_results_mock prints export confirmation."""
        mock_time.return_value = 1234567890
        mock_results = [{"ticker": "AAPL", "name": "Apple Inc.", "price": 175.50}]

        _export_results_mock(mock_results)
        assert mock_print.call_count > 0


class TestRunScreeningWorkflow:
    """Test cases for complete screening workflow."""

    @patch("stock_friend.cli.screening_cli.confirm_action")
    @patch("stock_friend.cli.screening_cli._export_results_mock")
    @patch("stock_friend.cli.screening_cli._display_screening_results")
    @patch("stock_friend.cli.screening_cli._display_screening_progress")
    @patch("stock_friend.cli.screening_cli._select_strategy")
    @patch("stock_friend.cli.screening_cli._select_universe")
    @patch("stock_friend.cli.screening_cli.console.print")
    def test_run_screening_workflow_complete_flow(
        self,
        mock_print: MagicMock,
        mock_select_universe: MagicMock,
        mock_select_strategy: MagicMock,
        mock_progress: MagicMock,
        mock_display_results: MagicMock,
        mock_export: MagicMock,
        mock_confirm: MagicMock,
    ) -> None:
        """Test complete screening workflow execution."""
        mock_select_universe.return_value = "S&P 500"
        mock_select_strategy.return_value = {
            "id": "1",
            "name": "Test Strategy",
            "description": "Test",
        }
        mock_confirm.return_value = True

        run_screening_workflow()

        mock_select_universe.assert_called_once()
        mock_select_strategy.assert_called_once()
        mock_progress.assert_called_once()
        mock_display_results.assert_called_once()
        mock_export.assert_called_once()

    @patch("stock_friend.cli.screening_cli._select_universe")
    @patch("stock_friend.cli.screening_cli.console.print")
    def test_run_screening_workflow_exits_when_universe_cancelled(
        self, mock_print: MagicMock, mock_select_universe: MagicMock
    ) -> None:
        """Test workflow exits when universe selection is cancelled."""
        mock_select_universe.return_value = None
        run_screening_workflow()
        mock_select_universe.assert_called_once()

    @patch("stock_friend.cli.screening_cli._select_strategy")
    @patch("stock_friend.cli.screening_cli._select_universe")
    @patch("stock_friend.cli.screening_cli.console.print")
    def test_run_screening_workflow_exits_when_strategy_cancelled(
        self,
        mock_print: MagicMock,
        mock_select_universe: MagicMock,
        mock_select_strategy: MagicMock,
    ) -> None:
        """Test workflow exits when strategy selection is cancelled."""
        mock_select_universe.return_value = "S&P 500"
        mock_select_strategy.return_value = None
        run_screening_workflow()
        mock_select_strategy.assert_called_once()

    @patch("stock_friend.cli.screening_cli.get_mock_screening_results")
    @patch("stock_friend.cli.screening_cli._display_screening_progress")
    @patch("stock_friend.cli.screening_cli._select_strategy")
    @patch("stock_friend.cli.screening_cli._select_universe")
    @patch("stock_friend.cli.screening_cli.console.print")
    def test_run_screening_workflow_handles_no_results(
        self,
        mock_print: MagicMock,
        mock_select_universe: MagicMock,
        mock_select_strategy: MagicMock,
        mock_progress: MagicMock,
        mock_get_results: MagicMock,
    ) -> None:
        """Test workflow handles case with no screening results."""
        mock_select_universe.return_value = "S&P 500"
        mock_select_strategy.return_value = {"id": "1", "name": "Test"}
        mock_get_results.return_value = []

        run_screening_workflow()

        # Should print message about no results
        assert any("No stocks" in str(call) for call in mock_print.call_args_list)
