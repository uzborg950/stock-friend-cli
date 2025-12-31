"""
Search command for stock-friend CLI.

Provides stock search functionality by ticker symbol or company name.
"""

import logging
import sys
from typing import Optional

import typer
from rich.console import Console

from stock_friend.gateways.base import DataProviderException
from stock_friend.infrastructure.cache_manager import CacheManager
from stock_friend.infrastructure.config import ApplicationConfig
from stock_friend.infrastructure.gateway_factory import GatewayFactory
from stock_friend.infrastructure.rate_limiter import RateLimiter
from stock_friend.presenters.stock_presenter import StockPresenter
from stock_friend.presenters.chart_presenter import ChartPresenter, ChartType
from stock_friend.services.search_service import SearchService

logger = logging.getLogger(__name__)
console = Console()

# Global context for lazy initialization
_search_service: Optional[SearchService] = None
_stock_presenter: Optional[StockPresenter] = None
_chart_presenter: Optional[ChartPresenter] = None


def _get_search_service() -> SearchService:
    """
    Get or create SearchService instance with lazy initialization.

    This function initializes the full dependency stack:
    - ApplicationConfig (from environment)
    - CacheManager and RateLimiter
    - GatewayFactory -> IMarketDataGateway
    - SearchService

    Returns:
        SearchService instance

    Raises:
        SystemExit: If initialization fails
    """
    global _search_service

    if _search_service is None:
        try:
            # Initialize config
            config = ApplicationConfig()

            # Initialize infrastructure
            cache_manager = CacheManager(
                cache_dir=str(config.cache.dir),
                size_limit_mb=config.cache.size_mb,
            )
            rate_limiter = RateLimiter()

            # Create gateway via factory
            factory = GatewayFactory(config, cache_manager, rate_limiter)
            gateway = factory.create_gateway()

            # Create service
            _search_service = SearchService(
                gateway=gateway,
                cache_manager=cache_manager,
            )

            logger.info(f"Initialized search service with {gateway.get_name()} gateway")

        except Exception as e:
            console.print(f"[red]Failed to initialize search service:[/red] {e}")
            logger.exception("Search service initialization failed")
            raise typer.Exit(code=1)

    return _search_service


def _get_stock_presenter() -> StockPresenter:
    """Get or create StockPresenter instance."""
    global _stock_presenter

    if _stock_presenter is None:
        _stock_presenter = StockPresenter(console=console)

    return _stock_presenter


def _get_chart_presenter() -> ChartPresenter:
    """Get or create ChartPresenter instance."""
    global _chart_presenter

    if _chart_presenter is None:
        _chart_presenter = ChartPresenter(console=console)

    return _chart_presenter


def search_stock(
    query: str,
    exchange: Optional[str] = None,
    show_chart: bool = False,
    chart_period: str = "3mo",
    chart_type: ChartType = "candlestick",
) -> None:
    """
    Search for stocks by ticker symbol with optional price chart.

    This is the main entry point for the search command.
    Orchestrates the search flow:
    1. Initialize service and presenter
    2. Perform search (with loading indicator)
    3. Handle multiple results (user selection)
    4. Fetch and display detailed information
    5. Optionally display historical price chart

    Args:
        query: Ticker symbol (e.g., "AAPL", "BARC")
        exchange: Optional exchange suffix (e.g., "L", "TO")
        show_chart: Display historical price chart after search
        chart_period: Time period for chart ("1mo", "3mo", "6mo", "1y", "5y")
        chart_type: Chart type ("candlestick", "line", or "both")

    Examples:
        >>> search_stock("AAPL")  # Search only
        >>> search_stock("AAPL", show_chart=True)  # Search with 3-month candlestick
        >>> search_stock("NVDA", show_chart=True, chart_period="1y", chart_type="line")
    """
    try:
        # Get services
        service = _get_search_service()
        presenter = _get_stock_presenter()

        # Perform search with loading indicator
        with console.status(f"[cyan]Searching for '{query}'...[/cyan]", spinner="dots"):
            results = service.search(query, exchange_hint=exchange)

        # Handle no results
        if not results:
            presenter.present_no_results(query)
            raise typer.Exit(code=1)

        # Show selection if multiple results
        selected = presenter.present_search_results(results, query)
        if not selected:
            console.print("[yellow]Search cancelled[/yellow]")
            raise typer.Exit(code=0)

        # Fetch and display detailed info
        with console.status(
            f"[cyan]Fetching details for {selected.ticker}...[/cyan]", spinner="dots"
        ):
            info = service.get_detailed_info(selected.ticker)

        presenter.present_detailed_info(info)

        # Display price chart if requested
        if show_chart:
            chart_presenter = _get_chart_presenter()
            console.print()  # Blank line before chart

            with console.status(
                f"[cyan]Loading {chart_period} chart for {selected.ticker}...[/cyan]",
                spinner="dots",
            ):
                price_history = service.get_price_history(
                    ticker=selected.ticker,
                    period=chart_period,
                )

            chart_presenter.present_price_chart(
                stock_data=price_history,
                chart_type=chart_type,
                period=chart_period,
            )

    except DataProviderException as e:
        console.print(f"[red]Error fetching data:[/red] {e}")
        logger.error(f"Data provider error: {e}")
        raise typer.Exit(code=1)

    except typer.Exit:
        # Re-raise typer.Exit to preserve exit codes
        raise

    except KeyboardInterrupt:
        console.print("\n[yellow]Search cancelled by user[/yellow]")
        raise typer.Exit(code=130)

    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        logger.exception("Search command failed")
        raise typer.Exit(code=1)
