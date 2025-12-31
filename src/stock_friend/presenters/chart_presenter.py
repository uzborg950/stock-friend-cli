"""
Chart presenter for displaying stock price visualizations.

Uses plotext for terminal-based candlestick and line charts with Rich integration.
"""

import logging
from datetime import datetime
from typing import Literal, Optional

import plotext as plt
from rich.console import Console

from stock_friend.models.stock_data import StockData

logger = logging.getLogger(__name__)

ChartType = Literal["candlestick", "line", "both"]


class ChartPresenter:
    """
    Handles chart rendering for stock price data in the terminal.

    Design Principles:
    - Single Responsibility: Only concerned with chart visualization
    - Open/Closed: Easy to add new chart types without modification
    - Uses plotext for terminal rendering with dark theme matching Rich

    Examples:
        >>> presenter = ChartPresenter()
        >>> presenter.present_price_chart(stock_data, chart_type="candlestick")
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize chart presenter.

        Args:
            console: Rich console for terminal size detection (optional)
        """
        self.console = console or Console()

    def present_price_chart(
        self,
        stock_data: StockData,
        chart_type: ChartType = "candlestick",
        period: str = "3mo",
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        """
        Display stock price chart in terminal using plotext.

        Args:
            stock_data: StockData with OHLCV dataframe
            chart_type: Type of chart ("candlestick", "line", or "both")
            period: Time period label for title display
            width: Chart width in characters (auto-detect if None)
            height: Chart height in lines (auto-detect if None)

        Raises:
            ValueError: If stock_data is empty or missing required columns

        Example:
            >>> chart_presenter.present_price_chart(
            ...     stock_data=stock_data,
            ...     chart_type="candlestick",
            ...     period="3mo"
            ... )
        """
        df = stock_data.data

        # Validate data
        if df.empty:
            logger.warning(f"No data to plot for {stock_data.ticker}")
            self.console.print(
                f"[yellow]No historical data available for {stock_data.ticker}[/yellow]"
            )
            return

        required_cols = ["date", "open", "high", "low", "close", "volume"]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Configure plotext
        plt.clf()  # Clear previous plot
        plt.theme("dark")  # Match Rich dark theme

        # Auto-detect terminal size if not specified
        if width is None or height is None:
            term_width, term_height = self.console.size
            width = width or min(term_width - 4, 120)
            height = height or min(int(term_height * 0.4), 20)

        plt.plotsize(width, height)

        # Format dates for plotext
        dates = plt.datetimes_to_string(df["date"].tolist())

        # Render appropriate chart type
        if chart_type == "candlestick":
            self._plot_candlestick(df, dates, stock_data.ticker)
        elif chart_type == "line":
            self._plot_line(df, dates, stock_data.ticker)
        else:  # both
            self._plot_both(df, dates, stock_data.ticker)

        # Set title and labels
        plt.title(f"{stock_data.ticker} - {period} Price Chart")
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")

        # Display chart
        plt.show()

        logger.info(f"Displayed {chart_type} chart for {stock_data.ticker}")

    def _plot_candlestick(self, df, dates, ticker: str) -> None:
        """
        Plot candlestick chart using OHLC data.

        Args:
            df: DataFrame with OHLC columns
            dates: Formatted date strings
            ticker: Stock ticker for logging
        """
        # plotext candlestick expects capitalized column names
        ohlc_data = df[["open", "high", "low", "close"]].rename(
            columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
            }
        )
        plt.candlestick(dates, ohlc_data)
        logger.debug(f"Plotted candlestick chart for {ticker}")

    def _plot_line(self, df, dates, ticker: str) -> None:
        """
        Plot closing price as a smooth line chart.

        Args:
            df: DataFrame with price columns
            dates: Formatted date strings
            ticker: Stock ticker for logging
        """
        # Closing price line (braille for smooth curves)
        plt.plot(dates, df["close"].tolist(), label="Close", color="cyan", marker="braille")

        # plotext shows legends automatically when labels are provided
        logger.debug(f"Plotted line chart for {ticker}")

    def _plot_both(self, df, dates, ticker: str) -> None:
        """
        Plot candlestick with closing price line overlay.

        Combines candlestick bars with a cyan closing price line
        for detailed visualization.

        Args:
            df: DataFrame with OHLC columns
            dates: Formatted date strings
            ticker: Stock ticker for logging
        """
        # plotext candlestick expects capitalized column names
        ohlc_data = df[["open", "high", "low", "close"]].rename(
            columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
            }
        )

        # Candlestick base
        plt.candlestick(dates, ohlc_data)

        # Closing price overlay (braille for smooth line)
        plt.plot(dates, df["close"].tolist(), label="Close", color="cyan", marker="braille")

        # plotext shows legends automatically when labels are provided
        logger.debug(f"Plotted combined chart for {ticker}")

    def present_volume_chart(
        self,
        stock_data: StockData,
        period: str = "3mo",
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        """
        Display trading volume bar chart.

        Useful for analyzing volume patterns alongside price movements.

        Args:
            stock_data: StockData with volume column
            period: Time period label for title
            width: Chart width (auto-detect if None)
            height: Chart height (auto-detect if None)
        """
        df = stock_data.data

        if df.empty or "volume" not in df.columns:
            logger.warning(f"No volume data to plot for {stock_data.ticker}")
            return

        # Configure plotext
        plt.clf()
        plt.theme("dark")

        # Auto-detect size
        if width is None or height is None:
            term_width, term_height = self.console.size
            width = width or min(term_width - 4, 120)
            height = height or min(int(term_height * 0.25), 15)

        plt.plotsize(width, height)

        # Format dates
        dates = plt.datetimes_to_string(df["date"].tolist())

        # Plot volume bars
        plt.bar(dates, df["volume"].tolist(), color="green")

        plt.title(f"{stock_data.ticker} - {period} Trading Volume")
        plt.xlabel("Date")
        plt.ylabel("Volume")

        plt.show()

        logger.info(f"Displayed volume chart for {stock_data.ticker}")
