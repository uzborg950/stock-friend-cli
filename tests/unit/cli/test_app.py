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


class TestStrategyCommands:
    """Test cases for strategy subcommands."""

    @patch("stock_friend.cli.app.get_mock_strategies")
    def test_strategy_list_displays_all_strategies(
        self, mock_get_strategies: MagicMock
    ) -> None:
        """Test that strategy list command displays all strategies."""
        mock_get_strategies.return_value = [
            {
                "id": "1",
                "name": "Momentum Strategy",
                "description": "High momentum stocks",
                "universe": "SP500",
                "created_date": "2024-01-01",
                "conditions": ["MCDX > 0", "Volume > 1M"],
            },
            {
                "id": "2",
                "name": "Value Strategy",
                "description": "Undervalued stocks",
                "universe": "SP500",
                "created_date": "2024-01-02",
                "conditions": ["P/E < 15"],
            },
        ]

        result = runner.invoke(app, ["strategy", "list"])
        assert result.exit_code == 0
        assert "Momentum Strategy" in result.stdout
        assert "Value Strategy" in result.stdout

    @patch("stock_friend.cli.app.get_mock_strategies")
    def test_strategy_list_handles_empty_list(
        self, mock_get_strategies: MagicMock
    ) -> None:
        """Test that strategy list handles empty strategy list."""
        mock_get_strategies.return_value = []

        result = runner.invoke(app, ["strategy", "list"])
        assert result.exit_code == 0
        assert "No strategies found" in result.stdout

    @patch("stock_friend.cli.app._find_strategy_by_id_or_name")
    def test_strategy_view_with_valid_id_as_positional_arg(
        self, mock_find_strategy: MagicMock
    ) -> None:
        """Test strategy view command with valid ID as positional argument."""
        mock_find_strategy.return_value = {
            "id": "1",
            "name": "Momentum Strategy",
            "description": "High momentum stocks",
            "universe": "SP500",
            "created_date": "2024-01-01",
            "conditions": ["MCDX > 0", "Volume > 1M"],
        }

        result = runner.invoke(app, ["strategy", "view", "1"])
        assert result.exit_code == 0
        assert "Momentum Strategy" in result.stdout
        assert "MCDX > 0" in result.stdout
        mock_find_strategy.assert_called_once_with("1")

    @patch("stock_friend.cli.app._find_strategy_by_id_or_name")
    def test_strategy_view_with_valid_name_as_positional_arg(
        self, mock_find_strategy: MagicMock
    ) -> None:
        """Test strategy view command with valid name as positional argument."""
        mock_find_strategy.return_value = {
            "id": "1",
            "name": "Momentum Strategy",
            "description": "High momentum stocks",
            "universe": "SP500",
            "created_date": "2024-01-01",
            "conditions": ["MCDX > 0", "Volume > 1M"],
        }

        result = runner.invoke(app, ["strategy", "view", "momentum"])
        assert result.exit_code == 0
        assert "Momentum Strategy" in result.stdout
        mock_find_strategy.assert_called_once_with("momentum")

    @patch("stock_friend.cli.app._find_strategy_by_id_or_name")
    def test_strategy_view_with_quoted_name_as_positional_arg(
        self, mock_find_strategy: MagicMock
    ) -> None:
        """Test strategy view command with quoted name as positional argument."""
        mock_find_strategy.return_value = {
            "id": "1",
            "name": "Default Momentum Strategy",
            "description": "High momentum stocks",
            "universe": "SP500",
            "created_date": "2024-01-01",
            "conditions": ["MCDX > 0", "Volume > 1M"],
        }

        result = runner.invoke(app, ["strategy", "view", "Default Momentum Strategy"])
        assert result.exit_code == 0
        assert "Default Momentum Strategy" in result.stdout
        mock_find_strategy.assert_called_once_with("Default Momentum Strategy")

    @patch("stock_friend.cli.app._find_strategy_by_id_or_name")
    def test_strategy_view_with_invalid_identifier(
        self, mock_find_strategy: MagicMock
    ) -> None:
        """Test strategy view command with invalid identifier."""
        mock_find_strategy.return_value = None

        result = runner.invoke(app, ["strategy", "view", "999"])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()
        assert "strategy list" in result.stdout.lower()

    def test_strategy_view_requires_identifier_argument(self) -> None:
        """Test that strategy view command requires identifier argument."""
        result = runner.invoke(app, ["strategy", "view"])
        assert result.exit_code != 0
        # Typer shows errors in stderr, not stdout
        output = result.stdout + (result.stderr or "")
        assert "Missing argument" in output or "required" in output.lower()


class TestPortfolioCommands:
    """Test cases for portfolio subcommands."""

    @patch("stock_friend.cli.app.get_mock_portfolios")
    def test_portfolio_list_displays_all_portfolios(
        self, mock_get_portfolios: MagicMock
    ) -> None:
        """Test that portfolio list command displays all portfolios."""
        mock_get_portfolios.return_value = [
            {
                "id": "1",
                "name": "Growth Portfolio",
                "strategy_name": "Momentum Strategy",
                "description": "High growth stocks",
                "created_date": "2024-01-01",
                "holdings": [{"ticker": "AAPL"}],
                "total_value": 10000.0,
                "total_cost": 9000.0,
                "total_gain_loss": 1000.0,
                "total_gain_loss_pct": 11.11,
            },
            {
                "id": "2",
                "name": "Value Portfolio",
                "strategy_name": "Value Strategy",
                "description": "Undervalued stocks",
                "created_date": "2024-01-02",
                "holdings": [{"ticker": "MSFT"}],
                "total_value": 5000.0,
                "total_cost": 5500.0,
                "total_gain_loss": -500.0,
                "total_gain_loss_pct": -9.09,
            },
        ]

        result = runner.invoke(app, ["portfolio", "list"])
        assert result.exit_code == 0
        assert "Growth Portfolio" in result.stdout
        assert "Value Portfolio" in result.stdout

    @patch("stock_friend.cli.app.get_mock_portfolios")
    def test_portfolio_list_handles_empty_list(
        self, mock_get_portfolios: MagicMock
    ) -> None:
        """Test that portfolio list handles empty portfolio list."""
        mock_get_portfolios.return_value = []

        result = runner.invoke(app, ["portfolio", "list"])
        assert result.exit_code == 0
        assert "No portfolios found" in result.stdout

    @patch("stock_friend.cli.app._find_portfolio_by_id_or_name")
    def test_portfolio_view_with_valid_id_as_positional_arg(
        self, mock_find_portfolio: MagicMock
    ) -> None:
        """Test portfolio view command with valid ID as positional argument."""
        mock_find_portfolio.return_value = {
            "id": "1",
            "name": "Growth Portfolio",
            "strategy_name": "Momentum Strategy",
            "description": "High growth stocks",
            "created_date": "2024-01-01",
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
            ],
            "total_value": 10000.0,
            "total_cost": 9000.0,
            "total_gain_loss": 1000.0,
            "total_gain_loss_pct": 11.11,
        }

        result = runner.invoke(app, ["portfolio", "view", "1"])
        assert result.exit_code == 0
        assert "Growth Portfolio" in result.stdout
        # Rich may truncate ticker, so check for the full company name instead
        assert "Apple Inc." in result.stdout
        mock_find_portfolio.assert_called_once_with("1")

    @patch("stock_friend.cli.app._find_portfolio_by_id_or_name")
    def test_portfolio_view_with_valid_name_as_positional_arg(
        self, mock_find_portfolio: MagicMock
    ) -> None:
        """Test portfolio view command with valid name as positional argument."""
        mock_find_portfolio.return_value = {
            "id": "1",
            "name": "Growth Portfolio",
            "strategy_name": "Momentum Strategy",
            "description": "High growth stocks",
            "created_date": "2024-01-01",
            "holdings": [],
            "total_value": 10000.0,
            "total_cost": 9000.0,
            "total_gain_loss": 1000.0,
            "total_gain_loss_pct": 11.11,
        }

        result = runner.invoke(app, ["portfolio", "view", "growth"])
        assert result.exit_code == 0
        assert "Growth Portfolio" in result.stdout
        mock_find_portfolio.assert_called_once_with("growth")

    @patch("stock_friend.cli.app._find_portfolio_by_id_or_name")
    def test_portfolio_view_with_quoted_name_as_positional_arg(
        self, mock_find_portfolio: MagicMock
    ) -> None:
        """Test portfolio view command with quoted name as positional argument."""
        mock_find_portfolio.return_value = {
            "id": "1",
            "name": "Growth Portfolio",
            "strategy_name": "Momentum Strategy",
            "description": "High growth stocks",
            "created_date": "2024-01-01",
            "holdings": [],
            "total_value": 10000.0,
            "total_cost": 9000.0,
            "total_gain_loss": 1000.0,
            "total_gain_loss_pct": 11.11,
        }

        result = runner.invoke(app, ["portfolio", "view", "Growth Portfolio"])
        assert result.exit_code == 0
        assert "Growth Portfolio" in result.stdout
        mock_find_portfolio.assert_called_once_with("Growth Portfolio")

    @patch("stock_friend.cli.app._find_portfolio_by_id_or_name")
    def test_portfolio_view_with_invalid_identifier(
        self, mock_find_portfolio: MagicMock
    ) -> None:
        """Test portfolio view command with invalid identifier."""
        mock_find_portfolio.return_value = None

        result = runner.invoke(app, ["portfolio", "view", "999"])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()
        assert "portfolio list" in result.stdout.lower()

    def test_portfolio_view_requires_identifier_argument(self) -> None:
        """Test that portfolio view command requires identifier argument."""
        result = runner.invoke(app, ["portfolio", "view"])
        assert result.exit_code != 0
        # Typer shows errors in stderr, not stdout
        output = result.stdout + (result.stderr or "")
        assert "Missing argument" in output or "required" in output.lower()


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
