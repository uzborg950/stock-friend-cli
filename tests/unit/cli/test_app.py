"""Unit tests for main application module."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from stock_friend.cli.app import (
    _exit_application,
    _handle_error,
    _handle_keyboard_interrupt,
    app,
    run_interactive_menu,
)

runner = CliRunner()


class TestCliCommands:
    """Test cases for CLI commands."""

    @patch("stock_friend.cli.app.run_interactive_menu")
    def test_main_command_without_args_runs_interactive_menu(
        self, mock_interactive: MagicMock
    ) -> None:
        """Test that running app without arguments starts interactive menu."""
        result = runner.invoke(app, [])
        mock_interactive.assert_called_once()

    def test_version_command_displays_version(self) -> None:
        """Test that version command displays version information."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.stdout

    @patch("stock_friend.cli.app.get_mock_screening_results")
    @patch("stock_friend.cli.app.get_mock_strategy_by_id")
    def test_screen_command_with_valid_parameters(
        self, mock_get_strategy: MagicMock, mock_get_results: MagicMock
    ) -> None:
        """Test screen command with valid parameters."""
        mock_get_strategy.return_value = {"id": "1", "name": "Test Strategy"}
        mock_get_results.return_value = [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "price": 175.50,
                "mcdx_signal": "BUY",
            }
        ]

        result = runner.invoke(app, ["screen", "--universe", "SP500", "--strategy", "1"])
        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.stdout}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "AAPL" in result.stdout

    @patch("stock_friend.cli.app.get_mock_strategy_by_id")
    def test_screen_command_with_invalid_strategy(
        self, mock_get_strategy: MagicMock
    ) -> None:
        """Test screen command with invalid strategy ID."""
        mock_get_strategy.return_value = None

        result = runner.invoke(app, ["screen", "--universe", "SP500", "--strategy", "999"])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()


class TestInteractiveMenu:
    """Test cases for interactive menu."""

    @patch("stock_friend.cli.app._exit_application")
    @patch("stock_friend.cli.app.run_screening_workflow")
    @patch("stock_friend.cli.app.display_main_menu")
    @patch("stock_friend.cli.app.display_welcome_banner")
    def test_run_interactive_menu_calls_screening(
        self,
        mock_banner: MagicMock,
        mock_menu: MagicMock,
        mock_screening: MagicMock,
        mock_exit: MagicMock,
    ) -> None:
        """Test that selecting screen stocks calls screening workflow."""
        from stock_friend.cli.menu import MenuOption

        mock_menu.side_effect = [MenuOption.SCREEN_STOCKS, MenuOption.EXIT]

        run_interactive_menu()

        mock_banner.assert_called_once()
        mock_screening.assert_called_once()

    @patch("stock_friend.cli.app._exit_application")
    @patch("stock_friend.cli.app.run_strategy_management")
    @patch("stock_friend.cli.app.display_main_menu")
    @patch("stock_friend.cli.app.display_welcome_banner")
    def test_run_interactive_menu_calls_strategy_management(
        self,
        mock_banner: MagicMock,
        mock_menu: MagicMock,
        mock_strategy: MagicMock,
        mock_exit: MagicMock,
    ) -> None:
        """Test that selecting manage strategies calls strategy management."""
        from stock_friend.cli.menu import MenuOption

        mock_menu.side_effect = [MenuOption.MANAGE_STRATEGIES, MenuOption.EXIT]

        run_interactive_menu()

        mock_strategy.assert_called_once()

    @patch("stock_friend.cli.app._exit_application")
    @patch("stock_friend.cli.app.run_portfolio_management")
    @patch("stock_friend.cli.app.display_main_menu")
    @patch("stock_friend.cli.app.display_welcome_banner")
    def test_run_interactive_menu_calls_portfolio_management(
        self,
        mock_banner: MagicMock,
        mock_menu: MagicMock,
        mock_portfolio: MagicMock,
        mock_exit: MagicMock,
    ) -> None:
        """Test that selecting manage portfolios calls portfolio management."""
        from stock_friend.cli.menu import MenuOption

        mock_menu.side_effect = [MenuOption.MANAGE_PORTFOLIOS, MenuOption.EXIT]

        run_interactive_menu()

        mock_portfolio.assert_called_once()

    @patch("stock_friend.cli.app._exit_application")
    @patch("stock_friend.cli.app.display_main_menu")
    @patch("stock_friend.cli.app.display_welcome_banner")
    def test_run_interactive_menu_exits_on_exit_option(
        self,
        mock_banner: MagicMock,
        mock_menu: MagicMock,
        mock_exit: MagicMock,
    ) -> None:
        """Test that selecting exit calls exit function."""
        from stock_friend.cli.menu import MenuOption

        mock_menu.return_value = MenuOption.EXIT

        run_interactive_menu()

        mock_exit.assert_called_once()

    @patch("stock_friend.cli.app._handle_keyboard_interrupt")
    @patch("stock_friend.cli.app.display_main_menu")
    @patch("stock_friend.cli.app.display_welcome_banner")
    def test_run_interactive_menu_handles_keyboard_interrupt(
        self,
        mock_banner: MagicMock,
        mock_menu: MagicMock,
        mock_handler: MagicMock,
    ) -> None:
        """Test that keyboard interrupt is handled gracefully."""
        mock_menu.side_effect = KeyboardInterrupt()

        run_interactive_menu()

        mock_handler.assert_called_once()

    @patch("stock_friend.cli.app._exit_application")
    @patch("stock_friend.cli.app._handle_error")
    @patch("stock_friend.cli.app.display_main_menu")
    @patch("stock_friend.cli.app.display_welcome_banner")
    def test_run_interactive_menu_handles_exceptions(
        self,
        mock_banner: MagicMock,
        mock_menu: MagicMock,
        mock_handler: MagicMock,
        mock_exit: MagicMock,
    ) -> None:
        """Test that general exceptions are handled gracefully."""
        from stock_friend.cli.menu import MenuOption

        test_error = Exception("Test error")
        # First call raises exception, second call returns EXIT to break loop
        mock_menu.side_effect = [test_error, MenuOption.EXIT]

        run_interactive_menu()

        mock_handler.assert_called_once_with(test_error)


class TestErrorHandlers:
    """Test cases for error handling functions."""

    @patch("stock_friend.cli.app.console.print")
    @patch("stock_friend.cli.app.sys.exit")
    def test_exit_application_prints_goodbye_message(
        self, mock_exit: MagicMock, mock_print: MagicMock
    ) -> None:
        """Test that exit application prints goodbye message."""
        _exit_application()
        mock_print.assert_called()
        mock_exit.assert_called_once_with(0)

    @patch("stock_friend.cli.app.console.print")
    @patch("stock_friend.cli.app.sys.exit")
    def test_handle_keyboard_interrupt_prints_message(
        self, mock_exit: MagicMock, mock_print: MagicMock
    ) -> None:
        """Test that keyboard interrupt handler prints message."""
        _handle_keyboard_interrupt()
        mock_print.assert_called()
        mock_exit.assert_called_once_with(0)

    @patch("stock_friend.cli.app.console.print")
    def test_handle_error_prints_error_message(self, mock_print: MagicMock) -> None:
        """Test that error handler prints error message."""
        test_error = Exception("Test error message")
        _handle_error(test_error)
        assert mock_print.call_count >= 1
