"""Portfolio management CLI interface."""

import time
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from stock_friend.cli.menu import (
    PortfolioMenuOption,
    confirm_action,
    display_portfolio_menu,
    get_text_input,
    select_from_list,
)
from stock_friend.cli.mock_data import (
    get_mock_portfolio_by_id,
    get_mock_portfolios,
    get_mock_strategies,
)

console = Console()


def run_portfolio_management() -> None:
    """Execute portfolio management workflow."""
    while True:
        choice = display_portfolio_menu()

        if not choice or choice == PortfolioMenuOption.BACK:
            break

        if choice == PortfolioMenuOption.LIST_PORTFOLIOS:
            _list_portfolios()
        elif choice == PortfolioMenuOption.CREATE_PORTFOLIO:
            _create_portfolio_wizard()
        elif choice == PortfolioMenuOption.VIEW_PORTFOLIO:
            _view_portfolio_details()
        elif choice == PortfolioMenuOption.ADD_HOLDING:
            _add_holding_wizard()
        elif choice == PortfolioMenuOption.REMOVE_HOLDING:
            _remove_holding_wizard()
        elif choice == PortfolioMenuOption.CHECK_STRATEGY:
            _check_strategy_compliance()
        elif choice == PortfolioMenuOption.EXPORT_PORTFOLIO:
            _export_portfolio_wizard()


def _list_portfolios() -> None:
    """Display all portfolios with summary information."""
    portfolios = get_mock_portfolios()

    console.print("\n[bold cyan]Your Portfolios[/bold cyan]\n")

    if not portfolios:
        console.print("[yellow]No portfolios found.[/yellow]\n")
        return

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


def _view_portfolio_details() -> None:
    """Display detailed information about a selected portfolio."""
    portfolios = get_mock_portfolios()

    if not portfolios:
        console.print("\n[yellow]No portfolios available.[/yellow]\n")
        return

    portfolio_choices = [f"{p['id']}: {p['name']}" for p in portfolios]
    selected = select_from_list("\nSelect a portfolio to view:", portfolio_choices)

    if not selected:
        return

    portfolio_id = selected.split(":")[0]
    portfolio = get_mock_portfolio_by_id(portfolio_id)

    if not portfolio:
        console.print("\n[red]Portfolio not found.[/red]\n")
        return

    _display_portfolio_summary(portfolio)
    _display_portfolio_holdings(portfolio)


def _display_portfolio_summary(portfolio: dict[str, Any]) -> None:
    """
    Display portfolio summary panel.

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


def _display_portfolio_holdings(portfolio: dict[str, Any]) -> None:
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


def _create_portfolio_wizard() -> None:
    """Interactive wizard for creating a new portfolio."""
    console.print("\n[bold cyan]Create New Portfolio[/bold cyan]\n")

    # Step 1: Basic information
    name = get_text_input("Portfolio name:")
    if not name:
        console.print("[yellow]Portfolio creation cancelled.[/yellow]\n")
        return

    description = get_text_input("Portfolio description:")
    if not description:
        console.print("[yellow]Portfolio creation cancelled.[/yellow]\n")
        return

    # Step 2: Select strategy
    strategies = get_mock_strategies()
    strategy_choices = [f"{s['id']}: {s['name']}" for s in strategies]
    selected_strategy = select_from_list("Select a strategy for this portfolio:", strategy_choices)

    if not selected_strategy:
        console.print("[yellow]Portfolio creation cancelled.[/yellow]\n")
        return

    strategy_name = selected_strategy.split(": ")[1]

    # Step 3: Review and confirm
    preview_panel = Panel(
        f"[bold]{name}[/bold]\n\n"
        f"[dim]Description:[/dim] {description}\n"
        f"[dim]Strategy:[/dim] {strategy_name}\n\n"
        f"[dim]Note: Add holdings after creation[/dim]",
        title="Portfolio Preview",
        border_style="cyan",
    )
    console.print("\n")
    console.print(preview_panel)
    console.print()

    if confirm_action("Create this portfolio?"):
        console.print("\n[green]✓[/green] Portfolio created successfully!\n")
        console.print("[dim]Note: In production, portfolio will be saved to database[/dim]\n")
    else:
        console.print("\n[yellow]Portfolio creation cancelled.[/yellow]\n")


def _add_holding_wizard() -> None:
    """Interactive wizard for adding a holding to a portfolio."""
    console.print("\n[bold cyan]Add Holding to Portfolio[/bold cyan]\n")

    portfolios = get_mock_portfolios()
    if not portfolios:
        console.print("[yellow]No portfolios available. Create a portfolio first.[/yellow]\n")
        return

    # Select portfolio
    portfolio_choices = [f"{p['id']}: {p['name']}" for p in portfolios]
    selected = select_from_list("Select portfolio:", portfolio_choices)

    if not selected:
        return

    portfolio_id = selected.split(":")[0]
    portfolio_name = selected.split(": ")[1]

    # Get holding details
    ticker = get_text_input("Stock ticker (e.g., AAPL):")
    if not ticker:
        console.print("[yellow]Operation cancelled.[/yellow]\n")
        return

    shares_str = get_text_input("Number of shares:")
    if not shares_str:
        console.print("[yellow]Operation cancelled.[/yellow]\n")
        return

    cost_basis_str = get_text_input("Cost basis per share:")
    if not cost_basis_str:
        console.print("[yellow]Operation cancelled.[/yellow]\n")
        return

    # Validate and display preview
    try:
        shares = int(shares_str)
        cost_basis = float(cost_basis_str)
    except ValueError:
        console.print("\n[red]Invalid number format.[/red]\n")
        return

    console.print(f"\n[cyan]Adding to portfolio:[/cyan] [bold]{portfolio_name}[/bold]")
    console.print(f"[bold]Ticker:[/bold] {ticker.upper()}")
    console.print(f"[bold]Shares:[/bold] {shares}")
    console.print(f"[bold]Cost Basis:[/bold] ${cost_basis:.2f}\n")

    if confirm_action("Add this holding?"):
        console.print("\n[green]✓[/green] Holding added successfully!\n")
        console.print("[dim]Note: In production, holding will be saved to database[/dim]\n")
    else:
        console.print("\n[yellow]Operation cancelled.[/yellow]\n")


def _remove_holding_wizard() -> None:
    """Interactive wizard for removing a holding from a portfolio."""
    console.print("\n[bold red]Remove Holding from Portfolio[/bold red]\n")

    portfolios = get_mock_portfolios()
    if not portfolios:
        console.print("[yellow]No portfolios available.[/yellow]\n")
        return

    # Select portfolio
    portfolio_choices = [f"{p['id']}: {p['name']}" for p in portfolios]
    selected = select_from_list("Select portfolio:", portfolio_choices)

    if not selected:
        return

    portfolio_id = selected.split(":")[0]
    portfolio = get_mock_portfolio_by_id(portfolio_id)

    if not portfolio or not portfolio["holdings"]:
        console.print("\n[yellow]No holdings in this portfolio.[/yellow]\n")
        return

    # Select holding to remove
    holding_choices = [f"{h['ticker']}: {h['shares']} shares" for h in portfolio["holdings"]]
    selected_holding = select_from_list("Select holding to remove:", holding_choices)

    if not selected_holding:
        return

    ticker = selected_holding.split(":")[0]

    console.print(f"\n[red]Warning:[/red] Remove {ticker} from [bold]{portfolio['name']}[/bold]?")
    console.print("[dim]This action cannot be undone.[/dim]\n")

    if confirm_action("Are you sure?"):
        console.print("\n[green]✓[/green] Holding removed successfully!\n")
        console.print("[dim]Note: In production, holding will be removed from database[/dim]\n")
    else:
        console.print("\n[yellow]Operation cancelled.[/yellow]\n")


def _check_strategy_compliance() -> None:
    """Check if portfolio holdings comply with assigned strategy."""
    console.print("\n[bold cyan]Check Strategy Compliance[/bold cyan]\n")

    portfolios = get_mock_portfolios()
    if not portfolios:
        console.print("[yellow]No portfolios available.[/yellow]\n")
        return

    # Select portfolio
    portfolio_choices = [f"{p['id']}: {p['name']}" for p in portfolios]
    selected = select_from_list("Select portfolio:", portfolio_choices)

    if not selected:
        return

    portfolio_id = selected.split(":")[0]
    portfolio = get_mock_portfolio_by_id(portfolio_id)

    if not portfolio:
        console.print("\n[red]Portfolio not found.[/red]\n")
        return

    # Simulate checking strategy compliance
    console.print(f"\n[cyan]Checking compliance for:[/cyan] [bold]{portfolio['name']}[/bold]")
    console.print(f"[cyan]Strategy:[/cyan] {portfolio['strategy_name']}\n")

    time.sleep(1.0)  # Simulate processing

    # Mock results - in production, this would evaluate actual strategy conditions
    compliant_holdings = ["AAPL", "MSFT"]
    non_compliant_holdings = ["NVDA"]

    if compliant_holdings:
        console.print("[green]✓ Compliant Holdings:[/green]")
        for ticker in compliant_holdings:
            console.print(f"  • {ticker}")
        console.print()

    if non_compliant_holdings:
        console.print("[yellow]⚠ Non-Compliant Holdings:[/yellow]")
        for ticker in non_compliant_holdings:
            console.print(f"  • {ticker} - Does not meet strategy conditions")
        console.print()

    console.print("[dim]Note: In production, this will evaluate real-time indicator data[/dim]\n")


def _export_portfolio_wizard() -> None:
    """Interactive wizard for exporting a portfolio to CSV."""
    console.print("\n[bold cyan]Export Portfolio[/bold cyan]\n")

    portfolios = get_mock_portfolios()
    if not portfolios:
        console.print("[yellow]No portfolios available.[/yellow]\n")
        return

    # Select portfolio
    portfolio_choices = [f"{p['id']}: {p['name']}" for p in portfolios]
    selected = select_from_list("Select portfolio to export:", portfolio_choices)

    if not selected:
        return

    portfolio_id = selected.split(":")[0]
    portfolio = get_mock_portfolio_by_id(portfolio_id)

    if not portfolio:
        console.print("\n[red]Portfolio not found.[/red]\n")
        return

    filename = f"portfolio_{portfolio['id']}_{int(time.time())}.csv"

    console.print(f"\n[cyan]Exporting:[/cyan] [bold]{portfolio['name']}[/bold]")
    console.print(f"[cyan]Filename:[/cyan] {filename}\n")

    if confirm_action("Export this portfolio?"):
        time.sleep(1.0)  # Simulate export
        console.print("\n[green]✓[/green] Portfolio exported successfully!\n")
        console.print(f"[dim]Note: In production, file will be saved to exports/ directory[/dim]\n")
    else:
        console.print("\n[yellow]Export cancelled.[/yellow]\n")
