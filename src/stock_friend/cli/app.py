"""Main Typer application for Stock Friend CLI."""

import sys
from typing import Annotated, Any

import typer
from rich.console import Console

from stock_friend.cli.menu import MenuOption, display_main_menu, display_welcome_banner
from stock_friend.cli.portfolio_cli import run_portfolio_management
from stock_friend.cli.screening_cli import run_screening_workflow
from stock_friend.cli.strategy_cli import run_strategy_management
from stock_friend.cli.mock_data import (
    get_mock_screening_results,
    get_mock_strategy_by_id,
    get_mock_strategies,
    get_mock_portfolios,
    get_mock_portfolio_by_id,
)
from difflib import get_close_matches
from stock_friend import __version__
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(
    name="stock-friend",
    help="Halal-compliant stock screening CLI tool",
    add_completion=False,
)

console = Console()

# Sub-applications for nested commands
strategy_app = typer.Typer(help="Manage investment strategies")
portfolio_app = typer.Typer(help="Manage investment portfolios")


def _find_strategy_by_id_or_name(identifier: str) -> dict[str, Any] | None:
    """
    Find strategy by ID or fuzzy match by name.

    Args:
        identifier: Strategy ID or name to search for.

    Returns:
        Strategy dictionary if found, None otherwise.
    """
    # Try exact ID match first
    strategy = get_mock_strategy_by_id(identifier)
    if strategy:
        return strategy

    # Try fuzzy match by name
    strategies = get_mock_strategies()
    if not strategies:
        return None

    strategy_names = [s["name"] for s in strategies]
    matches = get_close_matches(identifier, strategy_names, n=1, cutoff=0.6)

    if not matches:
        return None

    # Find strategy by matched name
    matched_name = matches[0]
    for strategy in strategies:
        if strategy["name"] == matched_name:
            return strategy

    return None


def _find_portfolio_by_id_or_name(identifier: str) -> dict[str, Any] | None:
    """
    Find portfolio by ID or fuzzy match by name.

    Args:
        identifier: Portfolio ID or name to search for.

    Returns:
        Portfolio dictionary if found, None otherwise.
    """
    # Try exact ID match first
    portfolio = get_mock_portfolio_by_id(identifier)
    if portfolio:
        return portfolio

    # Try fuzzy match by name
    portfolios = get_mock_portfolios()
    if not portfolios:
        return None

    portfolio_names = [p["name"] for p in portfolios]
    matches = get_close_matches(identifier, portfolio_names, n=1, cutoff=0.6)

    if not matches:
        return None

    # Find portfolio by matched name
    matched_name = matches[0]
    for portfolio in portfolios:
        if portfolio["name"] == matched_name:
            return portfolio

    return None


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


@strategy_app.command("list")
def strategy_list() -> None:
    """
    List all available investment strategies.

    Displays a formatted table showing strategy ID, name, description,
    and number of conditions for each strategy.
    """
    strategies = get_mock_strategies()

    if not strategies:
        console.print("\n[yellow]No strategies found.[/yellow]\n")
        return

    console.print("\n[bold cyan]Available Investment Strategies[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Name", style="bold yellow", width=30)
    table.add_column("Description", style="white", width=50)
    table.add_column("Conditions", justify="right", style="cyan", width=12)

    for strategy in strategies:
        table.add_row(
            strategy["id"],
            strategy["name"],
            strategy["description"],
            str(len(strategy["conditions"])),
        )

    console.print(table)
    console.print()


@strategy_app.command("view")
def strategy_view(
    identifier: Annotated[str, typer.Argument(help="Strategy ID or name to view")],
) -> None:
    """
    View detailed information about a specific strategy.

    Supports both exact ID match and fuzzy name matching.
    Displays strategy metadata (name, description, universe, created date)
    and all associated conditions with their indicator criteria.
    """
    strategy = _find_strategy_by_id_or_name(identifier)

    if not strategy:
        console.print(f"\n[red]Error:[/red] Strategy '{identifier}' not found.\n")
        console.print("[dim]Tip: Use 'strategy list' to see available strategies.[/dim]\n")
        sys.exit(1)

    conditions_text = "\n".join(f"  • {cond}" for cond in strategy["conditions"])

    details_panel = Panel(
        f"[bold cyan]Strategy Details[/bold cyan]\n\n"
        f"[bold]ID:[/bold] {strategy['id']}\n"
        f"[bold]Name:[/bold] {strategy['name']}\n"
        f"[bold]Description:[/bold] {strategy['description']}\n"
        f"[bold]Universe:[/bold] {strategy['universe']}\n"
        f"[bold]Created:[/bold] {strategy['created_date']}\n\n"
        f"[bold cyan]Conditions:[/bold cyan]\n"
        f"{conditions_text}",
        border_style="cyan",
        expand=False,
    )

    console.print("\n")
    console.print(details_panel)
    console.print("\n")


@portfolio_app.command("list")
def portfolio_list() -> None:
    """
    List all portfolios with summary information.

    Displays a formatted table showing portfolio ID, name, number of holdings,
    total value, and performance metrics (gain/loss and return percentage).
    """
    portfolios = get_mock_portfolios()

    if not portfolios:
        console.print("\n[yellow]No portfolios found.[/yellow]\n")
        return

    console.print("\n[bold cyan]Your Portfolios[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Name", style="bold yellow", width=25)
    table.add_column("Strategy", style="cyan", width=25)
    table.add_column("Holdings", justify="right", style="white", width=10)
    table.add_column("Value", justify="right", style="green", width=15)
    table.add_column("Gain/Loss", justify="right", style="white", width=15)
    table.add_column("Return %", justify="right", style="white", width=10)

    for portfolio in portfolios:
        gain_loss_color = "green" if portfolio["total_gain_loss"] >= 0 else "red"
        return_pct_color = "green" if portfolio["total_gain_loss_pct"] >= 0 else "red"

        table.add_row(
            portfolio["id"],
            portfolio["name"],
            portfolio["strategy_name"],
            str(len(portfolio["holdings"])),
            f"${portfolio['total_value']:,.2f}",
            f"[{gain_loss_color}]${portfolio['total_gain_loss']:,.2f}[/{gain_loss_color}]",
            f"[{return_pct_color}]{portfolio['total_gain_loss_pct']:+.2f}%[/{return_pct_color}]",
        )

    console.print(table)
    console.print()


@portfolio_app.command("view")
def portfolio_view(
    identifier: Annotated[str, typer.Argument(help="Portfolio ID or name to view")],
) -> None:
    """
    View detailed information about a specific portfolio.

    Supports both exact ID match and fuzzy name matching.
    Displays portfolio metadata, performance summary, and a detailed table
    of all holdings including ticker, shares, cost basis, current price,
    value, and gain/loss metrics.
    """
    portfolio = _find_portfolio_by_id_or_name(identifier)

    if not portfolio:
        console.print(f"\n[red]Error:[/red] Portfolio '{identifier}' not found.\n")
        console.print("[dim]Tip: Use 'portfolio list' to see available portfolios.[/dim]\n")
        sys.exit(1)

    _display_portfolio_summary_panel(portfolio)
    _display_holdings_table(portfolio)


def _display_portfolio_summary_panel(portfolio: dict[str, Any]) -> None:
    """
    Display portfolio summary panel with performance metrics.

    Args:
        portfolio: Portfolio dictionary with summary information.
    """
    gain_loss_color = "green" if portfolio["total_gain_loss"] >= 0 else "red"
    return_pct_color = "green" if portfolio["total_gain_loss_pct"] >= 0 else "red"

    summary_panel = Panel(
        f"[bold]{portfolio['name']}[/bold]\n\n"
        f"[dim]Description:[/dim] {portfolio['description']}\n"
        f"[dim]Strategy:[/dim] {portfolio['strategy_name']}\n"
        f"[dim]Created:[/dim] {portfolio['created_date']}\n\n"
        f"[bold cyan]Performance Summary[/bold cyan]\n"
        f"[bold]Total Value:[/bold] ${portfolio['total_value']:,.2f}\n"
        f"[bold]Total Cost:[/bold] ${portfolio['total_cost']:,.2f}\n"
        f"[bold]Gain/Loss:[/bold] [{gain_loss_color}]${portfolio['total_gain_loss']:,.2f}[/{gain_loss_color}]\n"
        f"[bold]Return:[/bold] [{return_pct_color}]{portfolio['total_gain_loss_pct']:+.2f}%[/{return_pct_color}]",
        title=f"Portfolio Details - {portfolio['id']}",
        border_style="cyan",
    )

    console.print("\n")
    console.print(summary_panel)
    console.print()


def _display_holdings_table(portfolio: dict[str, Any]) -> None:
    """
    Display portfolio holdings in a formatted table.

    Args:
        portfolio: Portfolio dictionary containing holdings.
    """
    console.print("[bold cyan]Holdings[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("Ticker", style="bold yellow", width=8)
    table.add_column("Name", style="white", width=25)
    table.add_column("Shares", justify="right", style="white", width=10)
    table.add_column("Cost Basis", justify="right", style="dim", width=12)
    table.add_column("Current Price", justify="right", style="cyan", width=14)
    table.add_column("Value", justify="right", style="green", width=12)
    table.add_column("Gain/Loss", justify="right", style="white", width=12)
    table.add_column("Return %", justify="right", style="white", width=10)

    for holding in portfolio["holdings"]:
        gain_loss_color = "green" if holding["gain_loss"] >= 0 else "red"
        return_pct_color = "green" if holding["gain_loss_pct"] >= 0 else "red"

        table.add_row(
            holding["ticker"],
            holding["name"],
            str(holding["shares"]),
            f"${holding['cost_basis']:.2f}",
            f"${holding['current_price']:.2f}",
            f"${holding['current_value']:,.2f}",
            f"[{gain_loss_color}]${holding['gain_loss']:,.2f}[/{gain_loss_color}]",
            f"[{return_pct_color}]{holding['gain_loss_pct']:+.2f}%[/{return_pct_color}]",
        )

    console.print(table)
    console.print()


# Register sub-applications with main app
app.add_typer(strategy_app, name="strategy")
app.add_typer(portfolio_app, name="portfolio")


if __name__ == "__main__":
    app()
