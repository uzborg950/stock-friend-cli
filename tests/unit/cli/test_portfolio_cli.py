"""Unit tests for portfolio CLI module."""

from unittest.mock import MagicMock, patch

import pytest

from stock_friend.cli.portfolio_cli import (
    _add_holding_wizard,
    _check_strategy_compliance,
    _create_portfolio_wizard,
    _display_portfolio_holdings,
    _display_portfolio_summary,
    _export_portfolio_wizard,
    _list_portfolios,
    _remove_holding_wizard,
    _view_portfolio_details,
    run_portfolio_management,
)


class TestListPortfolios:
    """Test cases for listing portfolios."""

    @patch("stock_friend.cli.portfolio_cli.console.print")
    def test_list_portfolios_displays_portfolios(self, mock_print: MagicMock) -> None:
        """Test that _list_portfolios displays portfolio list."""
        _list_portfolios()
        assert mock_print.call_count > 0


class TestViewPortfolioDetails:
    """Test cases for viewing portfolio details."""

    @patch("stock_friend.cli.portfolio_cli._display_portfolio_holdings")
    @patch("stock_friend.cli.portfolio_cli._display_portfolio_summary")
    @patch("stock_friend.cli.portfolio_cli.select_from_list")
    def test_view_portfolio_details_displays_full_info(
        self,
        mock_select: MagicMock,
        mock_summary: MagicMock,
        mock_holdings: MagicMock,
    ) -> None:
        """Test that viewing details displays summary and holdings."""
        mock_select.return_value = "1: Growth Portfolio"
        _view_portfolio_details()

        mock_summary.assert_called_once()
        mock_holdings.assert_called_once()

    @patch("stock_friend.cli.portfolio_cli.select_from_list")
    def test_view_portfolio_details_handles_cancellation(self, mock_select: MagicMock) -> None:
        """Test that viewing details handles cancellation."""
        mock_select.return_value = None
        _view_portfolio_details()
        mock_select.assert_called_once()


class TestDisplayPortfolioSummary:
    """Test cases for displaying portfolio summary."""

    @patch("stock_friend.cli.portfolio_cli.console.print")
    def test_display_portfolio_summary_shows_info(self, mock_print: MagicMock) -> None:
        """Test that summary displays portfolio information."""
        mock_portfolio = {
            "id": "1",
            "name": "Test Portfolio",
            "description": "Test",
            "strategy_name": "Test Strategy",
            "created_date": "2024-01-01",
            "total_value": 10000.0,
            "total_cost": 9000.0,
            "total_gain_loss": 1000.0,
            "total_gain_loss_pct": 11.11,
        }

        _display_portfolio_summary(mock_portfolio)
        assert mock_print.call_count > 0


class TestDisplayPortfolioHoldings:
    """Test cases for displaying portfolio holdings."""

    @patch("stock_friend.cli.portfolio_cli.console.print")
    def test_display_portfolio_holdings_shows_table(self, mock_print: MagicMock) -> None:
        """Test that holdings are displayed in a table."""
        mock_portfolio = {
            "holdings": [
                {
                    "ticker": "AAPL",
                    "name": "Apple Inc.",
                    "shares": 10,
                    "cost_basis": 150.0,
                    "current_price": 175.0,
                    "current_value": 1750.0,
                    "gain_loss": 250.0,
                    "gain_loss_pct": 16.67,
                }
            ]
        }

        _display_portfolio_holdings(mock_portfolio)
        assert mock_print.call_count > 0


class TestCreatePortfolioWizard:
    """Test cases for portfolio creation wizard."""

    @patch("stock_friend.cli.portfolio_cli.confirm_action")
    @patch("stock_friend.cli.portfolio_cli.select_from_list")
    @patch("stock_friend.cli.portfolio_cli.get_text_input")
    @patch("stock_friend.cli.portfolio_cli.console.print")
    def test_create_portfolio_wizard_complete_flow(
        self,
        mock_print: MagicMock,
        mock_text_input: MagicMock,
        mock_select: MagicMock,
        mock_confirm: MagicMock,
    ) -> None:
        """Test complete portfolio creation flow."""
        mock_text_input.side_effect = ["Test Portfolio", "Test Description"]
        mock_select.return_value = "1: Default Momentum Strategy"
        mock_confirm.return_value = True

        _create_portfolio_wizard()

        assert mock_text_input.call_count == 2
        mock_select.assert_called_once()
        mock_confirm.assert_called_once()

    @patch("stock_friend.cli.portfolio_cli.get_text_input")
    @patch("stock_friend.cli.portfolio_cli.console.print")
    def test_create_portfolio_wizard_cancels_on_empty_name(
        self, mock_print: MagicMock, mock_text_input: MagicMock
    ) -> None:
        """Test wizard cancels when name is empty."""
        mock_text_input.return_value = None
        _create_portfolio_wizard()
        assert any("cancelled" in str(call).lower() for call in mock_print.call_args_list)


class TestAddHoldingWizard:
    """Test cases for adding holdings."""

    @patch("stock_friend.cli.portfolio_cli.confirm_action")
    @patch("stock_friend.cli.portfolio_cli.get_text_input")
    @patch("stock_friend.cli.portfolio_cli.select_from_list")
    @patch("stock_friend.cli.portfolio_cli.console.print")
    def test_add_holding_wizard_complete_flow(
        self,
        mock_print: MagicMock,
        mock_select: MagicMock,
        mock_text_input: MagicMock,
        mock_confirm: MagicMock,
    ) -> None:
        """Test complete add holding flow."""
        mock_select.return_value = "1: Growth Portfolio"
        mock_text_input.side_effect = ["AAPL", "10", "150.00"]
        mock_confirm.return_value = True

        _add_holding_wizard()

        mock_select.assert_called_once()
        assert mock_text_input.call_count == 3

    @patch("stock_friend.cli.portfolio_cli.get_text_input")
    @patch("stock_friend.cli.portfolio_cli.select_from_list")
    @patch("stock_friend.cli.portfolio_cli.console.print")
    def test_add_holding_wizard_handles_invalid_number(
        self, mock_print: MagicMock, mock_select: MagicMock, mock_text_input: MagicMock
    ) -> None:
        """Test wizard handles invalid number input."""
        mock_select.return_value = "1: Growth Portfolio"
        mock_text_input.side_effect = ["AAPL", "invalid", "150.00"]

        _add_holding_wizard()

        assert any("Invalid" in str(call) for call in mock_print.call_args_list)


class TestRemoveHoldingWizard:
    """Test cases for removing holdings."""

    @patch("stock_friend.cli.portfolio_cli.confirm_action")
    @patch("stock_friend.cli.portfolio_cli.select_from_list")
    @patch("stock_friend.cli.portfolio_cli.console.print")
    def test_remove_holding_wizard_requires_confirmation(
        self,
        mock_print: MagicMock,
        mock_select: MagicMock,
        mock_confirm: MagicMock,
    ) -> None:
        """Test that removal requires confirmation."""
        mock_select.side_effect = ["1: Growth Portfolio", "AAPL: 50 shares"]
        mock_confirm.return_value = True

        _remove_holding_wizard()

        assert mock_select.call_count == 2
        mock_confirm.assert_called_once()


class TestCheckStrategyCompliance:
    """Test cases for checking strategy compliance."""

    @patch("stock_friend.cli.portfolio_cli.select_from_list")
    @patch("stock_friend.cli.portfolio_cli.console.print")
    def test_check_strategy_compliance_shows_results(
        self, mock_print: MagicMock, mock_select: MagicMock
    ) -> None:
        """Test that compliance check displays results."""
        mock_select.return_value = "1: Growth Portfolio"
        _check_strategy_compliance()

        mock_select.assert_called_once()
        assert mock_print.call_count > 0


class TestExportPortfolioWizard:
    """Test cases for portfolio export."""

    @patch("stock_friend.cli.portfolio_cli.confirm_action")
    @patch("stock_friend.cli.portfolio_cli.select_from_list")
    @patch("stock_friend.cli.portfolio_cli.console.print")
    def test_export_portfolio_wizard_complete_flow(
        self,
        mock_print: MagicMock,
        mock_select: MagicMock,
        mock_confirm: MagicMock,
    ) -> None:
        """Test complete portfolio export flow."""
        mock_select.return_value = "1: Growth Portfolio"
        mock_confirm.return_value = True

        _export_portfolio_wizard()

        mock_select.assert_called_once()
        mock_confirm.assert_called_once()


class TestRunPortfolioManagement:
    """Test cases for portfolio management main loop."""

    @patch("stock_friend.cli.portfolio_cli._list_portfolios")
    @patch("stock_friend.cli.portfolio_cli.display_portfolio_menu")
    def test_run_portfolio_management_calls_list_portfolios(
        self, mock_menu: MagicMock, mock_list: MagicMock
    ) -> None:
        """Test that LIST_PORTFOLIOS option calls list function."""
        from stock_friend.cli.menu import PortfolioMenuOption

        mock_menu.side_effect = [
            PortfolioMenuOption.LIST_PORTFOLIOS,
            PortfolioMenuOption.BACK,
        ]
        run_portfolio_management()
        mock_list.assert_called_once()

    @patch("stock_friend.cli.portfolio_cli.display_portfolio_menu")
    def test_run_portfolio_management_exits_on_back(self, mock_menu: MagicMock) -> None:
        """Test that BACK option exits the loop."""
        from stock_friend.cli.menu import PortfolioMenuOption

        mock_menu.return_value = PortfolioMenuOption.BACK
        run_portfolio_management()
        mock_menu.assert_called_once()
