"""
Stock information presenter.

Handles display formatting for stock search results and detailed information
using the Rich library for beautiful terminal output.
"""

import textwrap
from typing import Any, List, Optional

from decimal import Decimal
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from stock_friend.models.search_models import SearchResult, StockDetailedInfo


class StockPresenter:
    """
    Handles display formatting for stock search results.

    Follows Single Responsibility Principle:
    - Only concerned with presentation logic
    - No business logic or data fetching
    - Uses Rich library for terminal formatting

    Design Pattern: Presenter Pattern (from MVP)
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize stock presenter.

        Args:
            console: Rich console for output (creates default if not provided)
        """
        self.console = console or Console()

    def present_search_results(
        self, results: List[SearchResult], query: str
    ) -> Optional[SearchResult]:
        """
        Display search results grouped by type and handle user selection.

        Groups results by quote_type (EQUITY, ETF, MUTUALFUND, etc.) for easier browsing.

        Args:
            results: List of search results
            query: Original search query (for display)

        Returns:
            Selected SearchResult or None if user quits
        """
        if len(results) == 0:
            return None

        if len(results) == 1:
            # Single result, return immediately
            self.console.print(
                f"\n[green]✓[/green] Found match for '{query}': "
                f"[cyan bold]{results[0].ticker}[/cyan bold]\n"
            )
            return results[0]

        # Multiple results, group by type and show selection table
        self.console.print(
            f"\n[yellow]Found {len(results)} matches for '{query}':[/yellow]\n"
        )

        # Group results by quote_type
        grouped = self._group_results_by_type(results)

        # Create table with type grouping
        table = Table(show_header=True, header_style="cyan bold", show_lines=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Type", style="magenta", width=12)
        table.add_column("Ticker", style="bold", width=12)
        table.add_column("Company", style="", width=30)
        table.add_column("Exchange", style="dim", width=18)

        idx = 1
        for quote_type, type_results in grouped.items():
            # Add section header (first row of each type shows the type)
            for i, result in enumerate(type_results):
                table.add_row(
                    str(idx),
                    quote_type if i == 0 else "",  # Only show type on first row
                    result.ticker,
                    self._truncate_text(result.company_name, 28),
                    self._truncate_text(result.exchange, 16),
                )
                idx += 1

        self.console.print(table)
        self.console.print()

        # Prompt for selection
        choices = [str(i) for i in range(1, len(results) + 1)] + ["q"]
        choice = Prompt.ask(
            "Select an option or [dim]'q'[/dim] to quit",
            choices=choices,
            default="q",
        )

        if choice == "q":
            return None

        return results[int(choice) - 1]

    def _group_results_by_type(
        self, results: List[SearchResult]
    ) -> dict[str, List[SearchResult]]:
        """
        Group search results by quote_type.

        Groups results into categories like EQUITY, ETF, MUTUALFUND for better UX.
        Results without quote_type are grouped under "OTHER".

        Args:
            results: List of SearchResult objects

        Returns:
            Dictionary mapping quote_type to list of results
        """
        from collections import OrderedDict

        grouped = OrderedDict()

        # Define preferred order for types
        type_order = ["EQUITY", "ETF", "MUTUALFUND", "INDEX", "CRYPTOCURRENCY", "OTHER"]

        # Initialize groups
        for t in type_order:
            grouped[t] = []

        # Group results
        for result in results:
            quote_type = result.quote_type or "OTHER"
            # Normalize type
            quote_type = quote_type.upper()

            if quote_type not in grouped:
                grouped[quote_type] = []

            grouped[quote_type].append(result)

        # Remove empty groups
        grouped = OrderedDict((k, v) for k, v in grouped.items() if v)

        return grouped

    def present_detailed_info(self, info: StockDetailedInfo) -> None:
        """
        Display comprehensive stock information.

        Presents data in sectioned panels:
        1. Stock Information (identity)
        2. Price & Trading (current price, ranges, volume)
        3. Fundamentals (valuation metrics)
        4. Halal Compliance (compliance status)
        5. About (company description)

        Args:
            info: StockDetailedInfo to display
        """
        self.console.print()

        # Section 1: Stock Information
        self._print_stock_information_section(info)
        self.console.print()

        # Section 2: Price & Trading
        self._print_price_section(info)
        self.console.print()

        # Section 3: Fundamentals
        self._print_fundamentals_section(info)
        self.console.print()

        # Section 4: Halal Compliance (if available)
        if info.compliance_status:
            self._print_compliance_section(info)
            self.console.print()

        # Section 5: Description (if available)
        if info.description:
            self._print_description_section(info)
            self.console.print()

    def present_no_results(self, query: str) -> None:
        """
        Display helpful error message when no results found.

        Args:
            query: Original search query
        """
        self.console.print(
            f"\n[red bold]❌ No results found for '{query}'[/red bold]\n"
        )

        suggestions = Panel(
            "[yellow]Suggestions:[/yellow]\n"
            "• Check if the ticker symbol is correct\n"
            "• Try searching by company name: [cyan]search \"Company Name\"[/cyan]\n"
            "• Include exchange suffix for international stocks:\n"
            "  - London: .L (e.g., BARC.L)\n"
            "  - Toronto: .TO (e.g., RY.TO)\n"
            "  - Australia: .AX (e.g., CBA.AX)\n\n"
            "[yellow]Examples:[/yellow]\n"
            "  search AAPL\n"
            '  search "Apple Inc"\n'
            "  search BARC --exchange L",
            title="Help",
            border_style="yellow",
        )
        self.console.print(suggestions)

    def _print_stock_information_section(self, info: StockDetailedInfo) -> None:
        """Print stock identity information."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan bold", width=20)
        table.add_column()

        table.add_row("Company", info.company_name)
        table.add_row("Ticker", info.ticker)
        table.add_row("Exchange", info.exchange)

        if info.fundamental.sector:
            table.add_row("Sector", info.fundamental.sector)

        if info.fundamental.industry:
            table.add_row("Industry", info.fundamental.industry)

        panel = Panel(
            table,
            title="[cyan bold]STOCK INFORMATION",
            border_style="cyan",
        )
        self.console.print(panel)

    def _print_price_section(self, info: StockDetailedInfo) -> None:
        """Print price and trading information."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan bold", width=20)
        table.add_column()

        # Current price with change
        price = info.price.current_price
        price_text = Text()
        price_text.append(f"${price:.2f}", style="bold")

        if info.price.price_change is not None:
            change = info.price.price_change
            change_pct = info.price.price_change_pct
            color = "green" if change > 0 else "red" if change < 0 else "white"
            price_text.append(
                f"  {change:+.2f} ({change_pct:+.2%})", style=f"{color} bold"
            )

        table.add_row("Current Price", price_text)

        # Previous close
        if info.price.previous_close:
            table.add_row("Previous Close", f"${info.price.previous_close:.2f}")

        # Day range
        if info.price.day_low and info.price.day_high:
            table.add_row(
                "Day Range",
                f"${info.price.day_low:.2f} - ${info.price.day_high:.2f}",
            )

        # 52-week range
        if info.price.fifty_two_week_low and info.price.fifty_two_week_high:
            table.add_row(
                "52-Week Range",
                f"${info.price.fifty_two_week_low:.2f} - ${info.price.fifty_two_week_high:.2f}",
            )

        # Volume
        if info.price.volume:
            table.add_row("Volume", f"{info.price.volume:,}")

        panel = Panel(
            table,
            title="[cyan bold]PRICE & TRADING",
            border_style="cyan",
        )
        self.console.print(panel)

    def _print_fundamentals_section(self, info: StockDetailedInfo) -> None:
        """Print fundamental metrics."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan bold", width=20)
        table.add_column()

        fund = info.fundamental

        # Market Cap
        if fund.market_cap:
            table.add_row("Market Cap", self._format_market_cap(fund.market_cap))

        # P/E Ratio
        if fund.pe_ratio:
            table.add_row("P/E Ratio", f"{fund.pe_ratio:.2f}")

        # P/B Ratio
        if fund.pb_ratio:
            table.add_row("P/B Ratio", f"{fund.pb_ratio:.2f}")

        # EPS
        if fund.eps:
            table.add_row("EPS (TTM)", f"${fund.eps:.2f}")

        # ROE
        if fund.roe:
            table.add_row("ROE", f"{fund.roe:.2%}")

        # Profit Margin
        if fund.profit_margin:
            table.add_row("Profit Margin", f"{fund.profit_margin:.2%}")

        # Debt to Equity
        if fund.debt_to_equity:
            table.add_row("Debt/Equity", f"{fund.debt_to_equity:.2f}")

        panel = Panel(
            table,
            title="[cyan bold]FUNDAMENTALS",
            border_style="cyan",
        )
        self.console.print(panel)

    def _print_compliance_section(self, info: StockDetailedInfo) -> None:
        """Print halal compliance status."""
        if not info.compliance_status:
            return

        compliance = info.compliance_status
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan bold", width=20)
        table.add_column()

        # Status with colored icon
        status_text = Text()
        if compliance.is_compliant is True:
            status_text.append("✓ Compliant", style="green bold")
            border_color = "green"
        elif compliance.is_compliant is False:
            status_text.append("✗ Non-Compliant", style="red bold")
            border_color = "red"
        else:
            status_text.append("❓ Unknown", style="yellow bold")
            border_color = "yellow"

        table.add_row("Status", status_text)

        # Source
        source_display = compliance.source.title() if compliance.source else "Unknown"
        if compliance.source == "zoya":
            source_display = "Zoya Finance"
        table.add_row("Source", source_display)

        # Compliance Score (if available)
        if compliance.compliance_score is not None:
            score_text = Text()
            score_text.append(f"{compliance.compliance_score:.1f}/100", style="bold")
            table.add_row("Compliance Score", score_text)

        # Purification Ratio (if available)
        if compliance.compliance_score is not None:
            # Calculate purification from compliance score (100 - score = purification)
            purification_pct = 100.0 - compliance.compliance_score
            if purification_pct > 0:
                table.add_row("Purification", f"{purification_pct:.1f}%")

        # Reasons (if non-compliant or unknown)
        if compliance.reasons:
            reasons_text = ", ".join(compliance.reasons)
            table.add_row("Notes", self._truncate_text(reasons_text, 50))

        # Report Date (if available)
        if compliance.checked_at:
            date_str = compliance.checked_at.strftime("%Y-%m-%d")
            table.add_row("Checked", date_str)

        panel = Panel(
            table,
            title="[cyan bold]HALAL COMPLIANCE",
            border_style=border_color,
        )
        self.console.print(panel)

    def _print_description_section(self, info: StockDetailedInfo) -> None:
        """Print company description."""
        if not info.description:
            return

        # Wrap text to 70 characters
        wrapped_desc = textwrap.fill(info.description, width=70)

        panel = Panel(
            wrapped_desc,
            title="[cyan bold]ABOUT",
            border_style="cyan",
        )
        self.console.print(panel)

    @staticmethod
    def _format_market_cap(value: Decimal) -> str:
        """
        Format large numbers with T/B/M suffix.

        Args:
            value: Market cap value

        Returns:
            Formatted string (e.g., "2.5T", "150.3B", "5.2M")
        """
        value_float = float(value)

        if value_float >= 1e12:
            return f"${value_float/1e12:.2f}T"
        elif value_float >= 1e9:
            return f"${value_float/1e9:.2f}B"
        elif value_float >= 1e6:
            return f"${value_float/1e6:.2f}M"
        else:
            return f"${value_float:,.0f}"

    @staticmethod
    def _truncate_text(text: str, max_length: int) -> str:
        """
        Truncate text with ellipsis if too long.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."
