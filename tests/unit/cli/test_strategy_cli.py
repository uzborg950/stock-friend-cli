"""Unit tests for strategy CLI module."""

from unittest.mock import MagicMock, patch

import pytest

from stock_friend.cli.strategy_cli import (
    _create_strategy_wizard,
    _delete_strategy_wizard,
    _edit_strategy_wizard,
    _list_strategies,
    run_strategy_management,
)


class TestListStrategies:
    """Test cases for listing strategies."""

    @patch("stock_friend.cli.strategy_cli.confirm_action")
    @patch("stock_friend.cli.strategy_cli.console.print")
    def test_list_strategies_displays_strategies(
        self, mock_print: MagicMock, mock_confirm: MagicMock
    ) -> None:
        """Test that _list_strategies displays strategy list."""
        mock_confirm.return_value = False
        _list_strategies()
        assert mock_print.call_count > 0

    @patch("stock_friend.cli.strategy_cli._view_strategy_details")
    @patch("stock_friend.cli.strategy_cli.confirm_action")
    @patch("stock_friend.cli.strategy_cli.console.print")
    def test_list_strategies_allows_viewing_details(
        self,
        mock_print: MagicMock,
        mock_confirm: MagicMock,
        mock_view_details: MagicMock,
    ) -> None:
        """Test that user can view strategy details from list."""
        mock_confirm.return_value = True
        _list_strategies()
        mock_view_details.assert_called_once()


class TestCreateStrategyWizard:
    """Test cases for strategy creation wizard."""

    @patch("stock_friend.cli.strategy_cli.confirm_action")
    @patch("stock_friend.cli.strategy_cli.select_multiple")
    @patch("stock_friend.cli.strategy_cli.select_from_list")
    @patch("stock_friend.cli.strategy_cli.get_text_input")
    @patch("stock_friend.cli.strategy_cli.console.print")
    def test_create_strategy_wizard_complete_flow(
        self,
        mock_print: MagicMock,
        mock_text_input: MagicMock,
        mock_select: MagicMock,
        mock_select_multiple: MagicMock,
        mock_confirm: MagicMock,
    ) -> None:
        """Test complete strategy creation flow."""
        mock_text_input.side_effect = ["Test Strategy", "Test Description", "Condition 1"]
        mock_select.return_value = "S&P 500"
        mock_select_multiple.return_value = ["MCDX - Test"]
        mock_confirm.return_value = True

        _create_strategy_wizard()

        assert mock_text_input.call_count >= 2
        mock_select.assert_called_once()
        mock_select_multiple.assert_called_once()

    @patch("stock_friend.cli.strategy_cli.get_text_input")
    @patch("stock_friend.cli.strategy_cli.console.print")
    def test_create_strategy_wizard_cancels_on_empty_name(
        self, mock_print: MagicMock, mock_text_input: MagicMock
    ) -> None:
        """Test wizard cancels when name is empty."""
        mock_text_input.return_value = None
        _create_strategy_wizard()
        assert any("cancelled" in str(call).lower() for call in mock_print.call_args_list)


class TestEditStrategyWizard:
    """Test cases for strategy editing wizard."""

    @patch("stock_friend.cli.strategy_cli.confirm_action")
    @patch("stock_friend.cli.strategy_cli.get_text_input")
    @patch("stock_friend.cli.strategy_cli.select_from_list")
    @patch("stock_friend.cli.strategy_cli.console.print")
    def test_edit_strategy_wizard_complete_flow(
        self,
        mock_print: MagicMock,
        mock_select: MagicMock,
        mock_text_input: MagicMock,
        mock_confirm: MagicMock,
    ) -> None:
        """Test complete strategy editing flow."""
        mock_select.return_value = "1: Default Momentum Strategy"
        mock_text_input.side_effect = ["New Name", "New Description"]
        mock_confirm.return_value = True

        _edit_strategy_wizard()

        mock_select.assert_called_once()
        assert mock_text_input.call_count == 2
        mock_confirm.assert_called_once()

    @patch("stock_friend.cli.strategy_cli.select_from_list")
    @patch("stock_friend.cli.strategy_cli.console.print")
    def test_edit_strategy_wizard_handles_cancellation(
        self, mock_print: MagicMock, mock_select: MagicMock
    ) -> None:
        """Test wizard handles cancellation."""
        mock_select.return_value = None
        _edit_strategy_wizard()
        mock_select.assert_called_once()


class TestDeleteStrategyWizard:
    """Test cases for strategy deletion wizard."""

    @patch("stock_friend.cli.strategy_cli.confirm_action")
    @patch("stock_friend.cli.strategy_cli.select_from_list")
    @patch("stock_friend.cli.strategy_cli.console.print")
    def test_delete_strategy_wizard_requires_confirmation(
        self,
        mock_print: MagicMock,
        mock_select: MagicMock,
        mock_confirm: MagicMock,
    ) -> None:
        """Test that deletion requires user confirmation."""
        mock_select.return_value = "1: Default Momentum Strategy"
        mock_confirm.return_value = True

        _delete_strategy_wizard()

        mock_confirm.assert_called_once()

    @patch("stock_friend.cli.strategy_cli.confirm_action")
    @patch("stock_friend.cli.strategy_cli.select_from_list")
    @patch("stock_friend.cli.strategy_cli.console.print")
    def test_delete_strategy_wizard_cancels_on_rejection(
        self,
        mock_print: MagicMock,
        mock_select: MagicMock,
        mock_confirm: MagicMock,
    ) -> None:
        """Test that deletion is cancelled when user rejects."""
        mock_select.return_value = "1: Default Momentum Strategy"
        mock_confirm.return_value = False

        _delete_strategy_wizard()

        assert any("cancelled" in str(call).lower() for call in mock_print.call_args_list)


class TestRunStrategyManagement:
    """Test cases for strategy management main loop."""

    @patch("stock_friend.cli.strategy_cli._list_strategies")
    @patch("stock_friend.cli.strategy_cli.display_strategy_menu")
    def test_run_strategy_management_calls_list_strategies(
        self, mock_menu: MagicMock, mock_list: MagicMock
    ) -> None:
        """Test that LIST_STRATEGIES option calls list function."""
        from stock_friend.cli.menu import StrategyMenuOption

        mock_menu.side_effect = [StrategyMenuOption.LIST_STRATEGIES, StrategyMenuOption.BACK]
        run_strategy_management()
        mock_list.assert_called_once()

    @patch("stock_friend.cli.strategy_cli.display_strategy_menu")
    def test_run_strategy_management_exits_on_back(self, mock_menu: MagicMock) -> None:
        """Test that BACK option exits the loop."""
        from stock_friend.cli.menu import StrategyMenuOption

        mock_menu.return_value = StrategyMenuOption.BACK
        run_strategy_management()
        mock_menu.assert_called_once()
