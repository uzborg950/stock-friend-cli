"""Investment strategy management CLI interface."""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from stock_friend.cli.menu import (
    StrategyMenuOption,
    confirm_action,
    display_strategy_menu,
    get_text_input,
    select_from_list,
    select_multiple,
)
from stock_friend.cli.mock_data import (
    get_mock_indicators,
    get_mock_strategies,
    get_mock_strategy_by_id,
    get_mock_universes,
)

console = Console()


def run_strategy_management() -> None:
    """Execute strategy management workflow."""
    while True:
        choice = display_strategy_menu()

        if not choice or choice == StrategyMenuOption.BACK:
            break

        if choice == StrategyMenuOption.LIST_STRATEGIES:
            _list_strategies()
        elif choice == StrategyMenuOption.CREATE_STRATEGY:
            _create_strategy_wizard()
        elif choice == StrategyMenuOption.EDIT_STRATEGY:
            _edit_strategy_wizard()
        elif choice == StrategyMenuOption.DELETE_STRATEGY:
            _delete_strategy_wizard()


def _list_strategies() -> None:
    """Display all available strategies in a formatted table."""
    strategies = get_mock_strategies()

    console.print("\n[bold cyan]Available Investment Strategies[/bold cyan]\n")

    if not strategies:
        console.print("[yellow]No strategies found.[/yellow]\n")
        return

    table = Table(show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Name", style="bold yellow", width=30)
    table.add_column("Description", style="white", width=50)
    table.add_column("Universe", style="cyan", width=15)
    table.add_column("Created", style="dim", width=12)

    for strategy in strategies:
        table.add_row(
            strategy["id"],
            strategy["name"],
            strategy["description"],
            strategy["universe"],
            strategy["created_date"],
        )

    console.print(table)
    console.print()

    # Allow viewing details of a specific strategy
    if confirm_action("Would you like to view details of a strategy?"):
        _view_strategy_details(strategies)


def _view_strategy_details(strategies: list[dict[str, Any]]) -> None:
    """
    Display detailed information about a selected strategy.

    Args:
        strategies: List of available strategies.
    """
    strategy_choices = [f"{s['id']}: {s['name']}" for s in strategies]
    selected = select_from_list("Select a strategy to view:", strategy_choices)

    if not selected:
        return

    strategy_id = selected.split(":")[0]
    strategy = get_mock_strategy_by_id(strategy_id)

    if not strategy:
        console.print("[red]Strategy not found.[/red]\n")
        return

    details_panel = Panel(
        f"[bold cyan]Strategy Details[/bold cyan]\n\n"
        f"[bold]ID:[/bold] {strategy['id']}\n"
        f"[bold]Name:[/bold] {strategy['name']}\n"
        f"[bold]Description:[/bold] {strategy['description']}\n"
        f"[bold]Universe:[/bold] {strategy['universe']}\n"
        f"[bold]Created:[/bold] {strategy['created_date']}\n\n"
        f"[bold cyan]Conditions:[/bold cyan]\n"
        + "\n".join(f"  • {cond}" for cond in strategy["conditions"]),
        border_style="cyan",
        expand=False,
    )
    console.print("\n")
    console.print(details_panel)
    console.print("\n")


def _create_strategy_wizard() -> None:
    """Interactive wizard for creating a new investment strategy."""
    console.print("\n[bold cyan]Create New Strategy[/bold cyan]\n")
    console.print("[dim]This wizard will guide you through creating a new strategy.[/dim]\n")

    # Step 1: Basic information
    name = get_text_input("Strategy name:")
    if not name:
        console.print("[yellow]Strategy creation cancelled.[/yellow]\n")
        return

    description = get_text_input("Strategy description:")
    if not description:
        console.print("[yellow]Strategy creation cancelled.[/yellow]\n")
        return

    # Step 2: Select universe
    universes = get_mock_universes()
    universe = select_from_list("Select screening universe:", universes)
    if not universe:
        console.print("[yellow]Strategy creation cancelled.[/yellow]\n")
        return

    # Step 3: Select indicators
    indicators = get_mock_indicators()
    indicator_choices = [f"{ind['name']} - {ind['description']}" for ind in indicators]
    selected_indicators = select_multiple(
        "Select indicators to use (space to select, enter to confirm):",
        indicator_choices,
    )

    if not selected_indicators:
        console.print("[yellow]Strategy creation cancelled.[/yellow]\n")
        return

    # Step 4: Define conditions
    console.print("\n[cyan]Define conditions for each selected indicator:[/cyan]\n")
    conditions = []
    for indicator in selected_indicators:
        indicator_name = indicator.split(" - ")[0]
        condition = get_text_input(f"Condition for {indicator_name}:")
        if condition:
            conditions.append(f"{indicator_name}: {condition}")

    # Step 5: Review and confirm
    _display_strategy_preview(name, description, universe, conditions)

    if confirm_action("Create this strategy?"):
        console.print("\n[green]✓[/green] Strategy created successfully!\n")
        console.print("[dim]Note: In production, strategy will be saved to database[/dim]\n")
    else:
        console.print("\n[yellow]Strategy creation cancelled.[/yellow]\n")


def _display_strategy_preview(
    name: str, description: str, universe: str, conditions: list[str]
) -> None:
    """
    Display preview of strategy before creation.

    Args:
        name: Strategy name.
        description: Strategy description.
        universe: Selected universe.
        conditions: List of indicator conditions.
    """
    preview_panel = Panel(
        f"[bold]{name}[/bold]\n\n"
        f"[dim]Description:[/dim] {description}\n"
        f"[dim]Universe:[/dim] {universe}\n\n"
        f"[dim]Conditions:[/dim]\n" + "\n".join(f"  • {cond}" for cond in conditions),
        title="Strategy Preview",
        border_style="cyan",
    )
    console.print("\n")
    console.print(preview_panel)
    console.print()


def _edit_strategy_wizard() -> None:
    """Interactive wizard for editing an existing strategy."""
    console.print("\n[bold cyan]Edit Strategy[/bold cyan]\n")

    strategies = get_mock_strategies()
    if not strategies:
        console.print("[yellow]No strategies available to edit.[/yellow]\n")
        return

    strategy_choices = [f"{s['id']}: {s['name']}" for s in strategies]
    selected = select_from_list("Select a strategy to edit:", strategy_choices)

    if not selected:
        return

    strategy_id = selected.split(":")[0]
    strategy = get_mock_strategy_by_id(strategy_id)

    if not strategy:
        console.print("[red]Strategy not found.[/red]\n")
        return

    console.print(f"\n[cyan]Editing:[/cyan] [bold]{strategy['name']}[/bold]\n")

    # Allow editing name
    new_name = get_text_input("New name (press enter to keep current):", strategy["name"])
    if not new_name:
        new_name = strategy["name"]

    # Allow editing description
    new_description = get_text_input(
        "New description (press enter to keep current):", strategy["description"]
    )
    if not new_description:
        new_description = strategy["description"]

    # Display preview
    console.print("\n[cyan]Updated Strategy:[/cyan]\n")
    console.print(f"[bold]Name:[/bold] {new_name}")
    console.print(f"[bold]Description:[/bold] {new_description}\n")

    if confirm_action("Save changes?"):
        console.print("\n[green]✓[/green] Strategy updated successfully!\n")
        console.print("[dim]Note: In production, changes will be saved to database[/dim]\n")
    else:
        console.print("\n[yellow]Edit cancelled.[/yellow]\n")


def _delete_strategy_wizard() -> None:
    """Interactive wizard for deleting a strategy."""
    console.print("\n[bold red]Delete Strategy[/bold red]\n")

    strategies = get_mock_strategies()
    if not strategies:
        console.print("[yellow]No strategies available to delete.[/yellow]\n")
        return

    strategy_choices = [f"{s['id']}: {s['name']}" for s in strategies]
    selected = select_from_list("Select a strategy to delete:", strategy_choices)

    if not selected:
        return

    strategy_id = selected.split(":")[0]
    strategy = get_mock_strategy_by_id(strategy_id)

    if not strategy:
        console.print("[red]Strategy not found.[/red]\n")
        return

    console.print(f"\n[red]Warning:[/red] You are about to delete strategy: [bold]{strategy['name']}[/bold]")
    console.print("[dim]This action cannot be undone.[/dim]\n")

    if confirm_action("Are you sure you want to delete this strategy?"):
        console.print("\n[green]✓[/green] Strategy deleted successfully!\n")
        console.print("[dim]Note: In production, strategy will be removed from database[/dim]\n")
    else:
        console.print("\n[yellow]Deletion cancelled.[/yellow]\n")
