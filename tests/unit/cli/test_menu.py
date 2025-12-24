"""Unit tests for menu module."""

from unittest.mock import MagicMock, patch

import pytest
import questionary

from stock_friend.cli.menu import (
    MenuOption,
    PortfolioMenuOption,
    StrategyMenuOption,
    confirm_action,
    display_main_menu,
    display_portfolio_menu,
    display_strategy_menu,
    display_welcome_banner,
    get_text_input,
    select_from_list,
    select_multiple,
)


class TestMenuOptions:
    """Test cases for menu option constants."""

    def test_menu_option_constants_exist(self) -> None:
        """Test that main menu option constants are defined."""
        assert hasattr(MenuOption, "SCREEN_STOCKS")
        assert hasattr(MenuOption, "MANAGE_STRATEGIES")
        assert hasattr(MenuOption, "MANAGE_PORTFOLIOS")
        assert hasattr(MenuOption, "EXIT")

    def test_strategy_menu_option_constants_exist(self) -> None:
        """Test that strategy menu option constants are defined."""
        assert hasattr(StrategyMenuOption, "LIST_STRATEGIES")
        assert hasattr(StrategyMenuOption, "CREATE_STRATEGY")
        assert hasattr(StrategyMenuOption, "EDIT_STRATEGY")
        assert hasattr(StrategyMenuOption, "DELETE_STRATEGY")
        assert hasattr(StrategyMenuOption, "BACK")

    def test_portfolio_menu_option_constants_exist(self) -> None:
        """Test that portfolio menu option constants are defined."""
        assert hasattr(PortfolioMenuOption, "LIST_PORTFOLIOS")
        assert hasattr(PortfolioMenuOption, "CREATE_PORTFOLIO")
        assert hasattr(PortfolioMenuOption, "VIEW_PORTFOLIO")
        assert hasattr(PortfolioMenuOption, "ADD_HOLDING")
        assert hasattr(PortfolioMenuOption, "REMOVE_HOLDING")
        assert hasattr(PortfolioMenuOption, "CHECK_STRATEGY")
        assert hasattr(PortfolioMenuOption, "EXPORT_PORTFOLIO")
        assert hasattr(PortfolioMenuOption, "BACK")


class TestDisplayWelcomeBanner:
    """Test cases for welcome banner display."""

    @patch("stock_friend.cli.menu.console.print")
    def test_display_welcome_banner_prints_output(self, mock_print: MagicMock) -> None:
        """Test that welcome banner prints output."""
        display_welcome_banner()
        assert mock_print.call_count >= 2  # At least banner and newlines


class TestDisplayMainMenu:
    """Test cases for main menu display."""

    @patch("questionary.select")
    def test_display_main_menu_calls_questionary_select(self, mock_select: MagicMock) -> None:
        """Test that main menu uses questionary.select."""
        mock_select.return_value.ask.return_value = MenuOption.EXIT
        result = display_main_menu()
        mock_select.assert_called_once()
        assert result == MenuOption.EXIT

    @patch("questionary.select")
    def test_display_main_menu_has_all_options(self, mock_select: MagicMock) -> None:
        """Test that main menu contains all expected options."""
        mock_select.return_value.ask.return_value = MenuOption.SCREEN_STOCKS
        display_main_menu()

        # Get the choices passed to questionary.select
        call_args = mock_select.call_args
        choices = call_args[1]["choices"]

        assert MenuOption.SCREEN_STOCKS in choices
        assert MenuOption.MANAGE_STRATEGIES in choices
        assert MenuOption.MANAGE_PORTFOLIOS in choices
        assert MenuOption.EXIT in choices


class TestDisplayStrategyMenu:
    """Test cases for strategy menu display."""

    @patch("questionary.select")
    def test_display_strategy_menu_calls_questionary_select(self, mock_select: MagicMock) -> None:
        """Test that strategy menu uses questionary.select."""
        mock_select.return_value.ask.return_value = StrategyMenuOption.BACK
        result = display_strategy_menu()
        mock_select.assert_called_once()
        assert result == StrategyMenuOption.BACK

    @patch("questionary.select")
    def test_display_strategy_menu_has_all_options(self, mock_select: MagicMock) -> None:
        """Test that strategy menu contains all expected options."""
        mock_select.return_value.ask.return_value = StrategyMenuOption.LIST_STRATEGIES
        display_strategy_menu()

        call_args = mock_select.call_args
        choices = call_args[1]["choices"]

        assert StrategyMenuOption.LIST_STRATEGIES in choices
        assert StrategyMenuOption.CREATE_STRATEGY in choices
        assert StrategyMenuOption.EDIT_STRATEGY in choices
        assert StrategyMenuOption.DELETE_STRATEGY in choices
        assert StrategyMenuOption.BACK in choices


class TestDisplayPortfolioMenu:
    """Test cases for portfolio menu display."""

    @patch("questionary.select")
    def test_display_portfolio_menu_calls_questionary_select(self, mock_select: MagicMock) -> None:
        """Test that portfolio menu uses questionary.select."""
        mock_select.return_value.ask.return_value = PortfolioMenuOption.BACK
        result = display_portfolio_menu()
        mock_select.assert_called_once()
        assert result == PortfolioMenuOption.BACK

    @patch("questionary.select")
    def test_display_portfolio_menu_has_all_options(self, mock_select: MagicMock) -> None:
        """Test that portfolio menu contains all expected options."""
        mock_select.return_value.ask.return_value = PortfolioMenuOption.LIST_PORTFOLIOS
        display_portfolio_menu()

        call_args = mock_select.call_args
        choices = call_args[1]["choices"]

        assert PortfolioMenuOption.LIST_PORTFOLIOS in choices
        assert PortfolioMenuOption.CREATE_PORTFOLIO in choices
        assert PortfolioMenuOption.VIEW_PORTFOLIO in choices
        assert PortfolioMenuOption.BACK in choices


class TestConfirmAction:
    """Test cases for confirmation prompt."""

    @patch("questionary.confirm")
    def test_confirm_action_returns_true_on_confirmation(self, mock_confirm: MagicMock) -> None:
        """Test that confirm_action returns True when user confirms."""
        mock_confirm.return_value.ask.return_value = True
        result = confirm_action("Are you sure?")
        assert result is True

    @patch("questionary.confirm")
    def test_confirm_action_returns_false_on_rejection(self, mock_confirm: MagicMock) -> None:
        """Test that confirm_action returns False when user rejects."""
        mock_confirm.return_value.ask.return_value = False
        result = confirm_action("Are you sure?")
        assert result is False

    @patch("questionary.confirm")
    def test_confirm_action_passes_message(self, mock_confirm: MagicMock) -> None:
        """Test that confirm_action passes message to questionary."""
        mock_confirm.return_value.ask.return_value = True
        confirm_action("Test message")
        call_args = mock_confirm.call_args
        assert call_args[0][0] == "Test message"


class TestGetTextInput:
    """Test cases for text input prompt."""

    @patch("questionary.text")
    def test_get_text_input_returns_user_input(self, mock_text: MagicMock) -> None:
        """Test that get_text_input returns user's input."""
        mock_text.return_value.ask.return_value = "test input"
        result = get_text_input("Enter text:")
        assert result == "test input"

    @patch("questionary.text")
    def test_get_text_input_uses_default_value(self, mock_text: MagicMock) -> None:
        """Test that get_text_input passes default value."""
        mock_text.return_value.ask.return_value = "default"
        get_text_input("Enter text:", default="default")
        call_args = mock_text.call_args
        assert call_args[1]["default"] == "default"


class TestSelectFromList:
    """Test cases for list selection prompt."""

    @patch("questionary.select")
    def test_select_from_list_returns_selected_option(self, mock_select: MagicMock) -> None:
        """Test that select_from_list returns selected option."""
        mock_select.return_value.ask.return_value = "Option 1"
        result = select_from_list("Choose:", ["Option 1", "Option 2"])
        assert result == "Option 1"

    @patch("questionary.select")
    def test_select_from_list_passes_choices(self, mock_select: MagicMock) -> None:
        """Test that select_from_list passes choices to questionary."""
        mock_select.return_value.ask.return_value = "Option 1"
        choices = ["Option 1", "Option 2", "Option 3"]
        select_from_list("Choose:", choices)
        call_args = mock_select.call_args
        assert call_args[1]["choices"] == choices


class TestSelectMultiple:
    """Test cases for multiple selection prompt."""

    @patch("questionary.checkbox")
    def test_select_multiple_returns_selected_options(self, mock_checkbox: MagicMock) -> None:
        """Test that select_multiple returns list of selected options."""
        mock_checkbox.return_value.ask.return_value = ["Option 1", "Option 3"]
        result = select_multiple("Choose multiple:", ["Option 1", "Option 2", "Option 3"])
        assert result == ["Option 1", "Option 3"]

    @patch("questionary.checkbox")
    def test_select_multiple_passes_choices(self, mock_checkbox: MagicMock) -> None:
        """Test that select_multiple passes choices to questionary."""
        mock_checkbox.return_value.ask.return_value = []
        choices = ["Option 1", "Option 2"]
        select_multiple("Choose:", choices)
        call_args = mock_checkbox.call_args
        assert call_args[1]["choices"] == choices
