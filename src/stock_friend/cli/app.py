"""Main Typer application for Stock Friend CLI."""

import sys
from typing import Annotated

import typer
from rich.console import Console

from stock_friend.cli.menu import MenuOption, display_main_menu, display_welcome_banner
from stock_friend.cli.portfolio_cli import run_portfolio_management
from stock_friend.cli.screening_cli import run_screening_workflow
from stock_friend.cli.strategy_cli import run_strategy_management
from stock_friend.cli.mock_data import get_mock_screening_results, get_mock_strategy_by_id
from stock_friend import __version__

app = typer.Typer(
    name="stock-friend",
    help="Halal-compliant stock screening CLI tool",
    add_completion=False,
)

console = Console()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """
    Stock Friend CLI - Interactive menu-driven application.

    Launch the application to access stock screening, strategy management,
    and portfolio management features.
    """
    if ctx.invoked_subcommand is not None:
        return

    run_interactive_menu()


def run_interactive_menu() -> None:
    """Execute the main interactive menu loop."""
    display_welcome_banner()

    while True:
        try:
            choice = display_main_menu()

            if not choice or choice == MenuOption.EXIT:
                _exit_application()
                break

            if choice == MenuOption.SCREEN_STOCKS:
                run_screening_workflow()
            elif choice == MenuOption.MANAGE_STRATEGIES:
                run_strategy_management()
            elif choice == MenuOption.MANAGE_PORTFOLIOS:
                run_portfolio_management()

        except KeyboardInterrupt:
            _handle_keyboard_interrupt()
            break
        except Exception as e:
            _handle_error(e)


def _exit_application() -> None:
    """Display exit message and terminate application."""
    console.print("\n[cyan]Thank you for using Stock Friend CLI![/cyan]")
    console.print("[dim]May your investments be halal and profitable.[/dim]\n")
    sys.exit(0)


def _handle_keyboard_interrupt() -> None:
    """Handle Ctrl+C gracefully."""
    console.print("\n\n[yellow]Application interrupted by user.[/yellow]\n")
    sys.exit(0)


def _handle_error(error: Exception) -> None:
    """
    Handle unexpected errors gracefully.

    Args:
        error: The exception that occurred.
    """
    console.print(f"\n[red]Error:[/red] {str(error)}\n")
    console.print("[dim]Please try again or report this issue if it persists.[/dim]\n")


@app.command()
def screen(
    universe: Annotated[str, typer.Option(help="Screening universe")] = "SP500",
    strategy: Annotated[str, typer.Option(help="Strategy ID")] = "1",
) -> None:
    """
    Run stock screening with specified parameters.

    This is a non-interactive command for quick screening operations.
    """

    console.print(f"\n[cyan]Running screening on {universe} with strategy {strategy}...[/cyan]\n")

    strategy_obj = get_mock_strategy_by_id(strategy)
    if not strategy_obj:
        console.print(f"[red]Error:[/red] Strategy {strategy} not found.\n")
        sys.exit(1)

    results = get_mock_screening_results(universe, strategy)

    if not results:
        console.print("[yellow]No stocks matched the screening criteria.[/yellow]\n")
        return

    console.print(f"[green]Found {len(results)} matching stocks:[/green]\n")
    for result in results:
        console.print(
            f"  • [bold]{result['ticker']}[/bold] - {result['name']} "
            f"(${result['price']:.2f}) - MCDX: {result['mcdx_signal']}"
        )
    console.print()


@app.command()
def version() -> None:
    """Display application version information."""

    console.print(f"\n[cyan]Stock Friend CLI[/cyan] version [bold]{__version__}[/bold]\n")


if __name__ == "__main__":
    app()
