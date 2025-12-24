"""Stock screening CLI interface."""

import time
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from stock_friend.cli.menu import confirm_action, select_from_list
from stock_friend.cli.mock_data import (
    get_mock_screening_results,
    get_mock_strategies,
    get_mock_universes,
)

console = Console()


def run_screening_workflow() -> None:
    """Execute the complete stock screening workflow."""
    console.print("\n[bold cyan]Stock Screening Wizard[/bold cyan]\n")

    universe = _select_universe()
    if not universe:
        return

    strategy = _select_strategy()
    if not strategy:
        return

    _display_screening_progress()

    results = get_mock_screening_results(universe, strategy["id"])

    if not results:
        console.print("\n[yellow]No stocks matched the screening criteria.[/yellow]\n")
        return

    _display_screening_results(results, strategy["name"], universe)

    if confirm_action("Would you like to export these results to CSV?"):
        _export_results_mock(results)


def _select_universe() -> str | None:
    """
    Prompt user to select a screening universe.

    Returns:
        Selected universe name or None if cancelled.
    """
    universes = get_mock_universes()

    console.print("[cyan]Step 1:[/cyan] Select screening universe")
    selected = select_from_list("Choose a universe to screen:", universes)

    if not selected:
        return None

    console.print(f"[green]✓[/green] Selected universe: [bold]{selected}[/bold]\n")
    return selected


def _select_strategy() -> dict[str, Any] | None:
    """
    Prompt user to select an investment strategy.

    Returns:
        Selected strategy dictionary or None if cancelled.
    """
    strategies = get_mock_strategies()
    strategy_choices = [f"{s['name']} - {s['description']}" for s in strategies]

    console.print("[cyan]Step 2:[/cyan] Select investment strategy")
    selected = select_from_list("Choose a strategy:", strategy_choices)

    if not selected:
        return None

    # Extract strategy name from choice
    strategy_name = selected.split(" - ")[0]
    strategy = next((s for s in strategies if s["name"] == strategy_name), None)

    if strategy:
        console.print(f"[green]✓[/green] Selected strategy: [bold]{strategy['name']}[/bold]\n")
        _display_strategy_details(strategy)

    return strategy


def _display_strategy_details(strategy: dict[str, Any]) -> None:
    """
    Display detailed information about the selected strategy.

    Args:
        strategy: Strategy dictionary containing name, description, and conditions.
    """
    details_panel = Panel(
        f"[bold]{strategy['name']}[/bold]\n\n"
        f"[dim]Description:[/dim] {strategy['description']}\n\n"
        f"[dim]Conditions:[/dim]\n" + "\n".join(f"  • {cond}" for cond in strategy["conditions"]),
        title="Strategy Details",
        border_style="cyan",
    )
    console.print(details_panel)
    console.print()


def _display_screening_progress() -> None:
    """Display mock progress bar during screening operation."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Screening stocks...", total=None)
        time.sleep(1.5)  # Simulate processing time

        progress.update(task, description="[cyan]Applying halal filters...")
        time.sleep(0.8)

        progress.update(task, description="[cyan]Calculating indicators...")
        time.sleep(0.8)

        progress.update(task, description="[cyan]Ranking results...")
        time.sleep(0.5)

    console.print("[green]✓[/green] Screening complete!\n")


def _display_screening_results(
    results: list[dict[str, Any]], strategy_name: str, universe: str
) -> None:
    """
    Display screening results in a formatted Rich table.

    Args:
        results: List of stock result dictionaries.
        strategy_name: Name of the strategy used.
        universe: Name of the universe screened.
    """
    console.print(
        Panel(
            f"[bold]Strategy:[/bold] {strategy_name}\n"
            f"[bold]Universe:[/bold] {universe}\n"
            f"[bold]Results:[/bold] {len(results)} stocks",
            title="Screening Results",
            border_style="green",
        )
    )
    console.print()

    table = Table(show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("Ticker", style="bold yellow", width=8)
    table.add_column("Name", style="white", width=25)
    table.add_column("Price", justify="right", style="green", width=10)
    table.add_column("MCDX", justify="center", width=12)
    table.add_column("B-XTrender", justify="center", width=12)
    table.add_column("Halal", justify="center", width=10)
    table.add_column("Volume", justify="right", width=10)
    table.add_column("Market Cap", justify="right", width=12)

    for result in results:
        mcdx_color = _get_signal_color(result["mcdx_signal"])
        xtrender_color = _get_xtrender_color(result["b_xtrender"])
        halal_color = "green" if result["halal_status"] == "COMPLIANT" else "red"

        table.add_row(
            result["ticker"],
            result["name"],
            f"${result['price']:.2f}",
            f"[{mcdx_color}]{result['mcdx_signal']}[/{mcdx_color}]",
            f"[{xtrender_color}]{result['b_xtrender']}[/{xtrender_color}]",
            f"[{halal_color}]{result['halal_status']}[/{halal_color}]",
            result["volume"],
            result["market_cap"],
        )

    console.print(table)
    console.print()


def _get_signal_color(signal: str) -> str:
    """
    Get Rich color code for MCDX signal.

    Args:
        signal: MCDX signal value.

    Returns:
        Rich color string.
    """
    signal_colors = {
        "STRONG_BUY": "bright_green",
        "BUY": "green",
        "HOLD": "yellow",
        "SELL": "red",
        "STRONG_SELL": "bright_red",
    }
    return signal_colors.get(signal, "white")


def _get_xtrender_color(trend: str) -> str:
    """
    Get Rich color code for B-XTrender value.

    Args:
        trend: B-XTrender value.

    Returns:
        Rich color string.
    """
    trend_colors = {
        "GREEN": "green",
        "YELLOW": "yellow",
        "RED": "red",
    }
    return trend_colors.get(trend, "white")


def _export_results_mock(results: list[dict[str, Any]]) -> None:
    """
    Mock export of screening results to CSV.

    Args:
        results: List of stock result dictionaries.
    """
    filename = f"screening_results_{int(time.time())}.csv"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"[cyan]Exporting to {filename}...", total=None)
        time.sleep(1.0)  # Simulate export time

    console.print(f"[green]✓[/green] Results exported to: [bold]{filename}[/bold]\n")
    console.print(f"[dim]Note: In production, file will be saved to exports/ directory[/dim]\n")
