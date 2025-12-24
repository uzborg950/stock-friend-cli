"""Interactive menu system for Stock Friend CLI."""

import questionary
from rich.console import Console
from rich.panel import Panel

console = Console()


class MenuOption:
    """Enum-like class for menu options to ensure type safety."""

    SCREEN_STOCKS = "Screen Stocks"
    MANAGE_STRATEGIES = "Manage Strategies"
    MANAGE_PORTFOLIOS = "Manage Portfolios"
    EXIT = "Exit"


class StrategyMenuOption:
    """Menu options for strategy management."""

    LIST_STRATEGIES = "List Strategies"
    CREATE_STRATEGY = "Create New Strategy"
    EDIT_STRATEGY = "Edit Strategy"
    DELETE_STRATEGY = "Delete Strategy"
    BACK = "Back to Main Menu"


class PortfolioMenuOption:
    """Menu options for portfolio management."""

    LIST_PORTFOLIOS = "List Portfolios"
    CREATE_PORTFOLIO = "Create New Portfolio"
    VIEW_PORTFOLIO = "View Portfolio Details"
    ADD_HOLDING = "Add Holding to Portfolio"
    REMOVE_HOLDING = "Remove Holding from Portfolio"
    CHECK_STRATEGY = "Check Strategy Compliance"
    EXPORT_PORTFOLIO = "Export Portfolio"
    BACK = "Back to Main Menu"


def display_welcome_banner() -> None:
    """Display welcome banner with application title."""
    banner = Panel(
        "[bold cyan]Stock Friend CLI[/bold cyan]\n"
        "[dim]Halal-Compliant Stock Screening Tool[/dim]\n"
        "[dim]Version 0.1.0[/dim]",
        border_style="cyan",
        expand=False,
    )
    console.print("\n")
    console.print(banner)
    console.print("\n")


def display_main_menu() -> str:
    """
    Display main menu and return user selection.

    Returns:
        Selected menu option as string.
    """
    choices = [
        MenuOption.SCREEN_STOCKS,
        MenuOption.MANAGE_STRATEGIES,
        MenuOption.MANAGE_PORTFOLIOS,
        MenuOption.EXIT,
    ]

    return questionary.select(
        "What would you like to do?",
        choices=choices,
        style=_get_questionary_style(),
    ).ask()


def display_strategy_menu() -> str:
    """
    Display strategy management menu.

    Returns:
        Selected menu option as string.
    """
    choices = [
        StrategyMenuOption.LIST_STRATEGIES,
        StrategyMenuOption.CREATE_STRATEGY,
        StrategyMenuOption.EDIT_STRATEGY,
        StrategyMenuOption.DELETE_STRATEGY,
        StrategyMenuOption.BACK,
    ]

    return questionary.select(
        "Strategy Management",
        choices=choices,
        style=_get_questionary_style(),
    ).ask()


def display_portfolio_menu() -> str:
    """
    Display portfolio management menu.

    Returns:
        Selected menu option as string.
    """
    choices = [
        PortfolioMenuOption.LIST_PORTFOLIOS,
        PortfolioMenuOption.CREATE_PORTFOLIO,
        PortfolioMenuOption.VIEW_PORTFOLIO,
        PortfolioMenuOption.ADD_HOLDING,
        PortfolioMenuOption.REMOVE_HOLDING,
        PortfolioMenuOption.CHECK_STRATEGY,
        PortfolioMenuOption.EXPORT_PORTFOLIO,
        PortfolioMenuOption.BACK,
    ]

    return questionary.select(
        "Portfolio Management",
        choices=choices,
        style=_get_questionary_style(),
    ).ask()


def confirm_action(message: str) -> bool:
    """
    Display confirmation prompt.

    Args:
        message: Confirmation message to display.

    Returns:
        True if user confirms, False otherwise.
    """
    return questionary.confirm(
        message,
        default=False,
        style=_get_questionary_style(),
    ).ask()


def get_text_input(message: str, default: str = "") -> str:
    """
    Get text input from user.

    Args:
        message: Prompt message.
        default: Default value.

    Returns:
        User input as string.
    """
    return questionary.text(
        message,
        default=default,
        style=_get_questionary_style(),
    ).ask()


def select_from_list(message: str, choices: list[str]) -> str:
    """
    Display selection menu from a list of choices.

    Args:
        message: Prompt message.
        choices: List of options to choose from.

    Returns:
        Selected option as string.
    """
    return questionary.select(
        message,
        choices=choices,
        style=_get_questionary_style(),
    ).ask()


def select_multiple(message: str, choices: list[str]) -> list[str]:
    """
    Display checkbox menu for multiple selections.

    Args:
        message: Prompt message.
        choices: List of options to choose from.

    Returns:
        List of selected options.
    """
    return questionary.checkbox(
        message,
        choices=choices,
        style=_get_questionary_style(),
    ).ask()


def _get_questionary_style() -> questionary.Style:
    """
    Get consistent questionary style for all prompts.

    Returns:
        Questionary Style object.
    """
    return questionary.Style(
        [
            ("qmark", "fg:#5f87af bold"),
            ("question", "bold"),
            ("answer", "fg:#00af87 bold"),
            ("pointer", "fg:#00af87 bold"),
            ("highlighted", "fg:#00af87 bold"),
            ("selected", "fg:#00af87"),
            ("separator", "fg:#6c6c6c"),
            ("instruction", "fg:#858585"),
            ("text", ""),
            ("disabled", "fg:#858585 italic"),
        ]
    )
