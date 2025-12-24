"""Unit tests for mock data module."""

import pytest

from stock_friend.cli.mock_data import (
    get_mock_indicators,
    get_mock_portfolio_by_id,
    get_mock_portfolios,
    get_mock_screening_results,
    get_mock_strategies,
    get_mock_strategy_by_id,
    get_mock_universes,
)


class TestMockStrategies:
    """Test cases for mock strategy functions."""

    def test_get_mock_strategies_returns_list(self) -> None:
        """Test that get_mock_strategies returns a list."""
        strategies = get_mock_strategies()
        assert isinstance(strategies, list)
        assert len(strategies) > 0

    def test_mock_strategies_have_required_fields(self) -> None:
        """Test that each strategy has required fields."""
        strategies = get_mock_strategies()
        required_fields = ["id", "name", "description", "conditions", "universe", "created_date"]

        for strategy in strategies:
            for field in required_fields:
                assert field in strategy, f"Strategy missing field: {field}"

    def test_get_mock_strategy_by_id_returns_correct_strategy(self) -> None:
        """Test that get_mock_strategy_by_id returns the correct strategy."""
        strategy = get_mock_strategy_by_id("1")
        assert strategy is not None
        assert strategy["id"] == "1"
        assert strategy["name"] == "Default Momentum Strategy"

    def test_get_mock_strategy_by_id_returns_none_for_invalid_id(self) -> None:
        """Test that get_mock_strategy_by_id returns None for invalid ID."""
        strategy = get_mock_strategy_by_id("999")
        assert strategy is None


class TestMockPortfolios:
    """Test cases for mock portfolio functions."""

    def test_get_mock_portfolios_returns_list(self) -> None:
        """Test that get_mock_portfolios returns a list."""
        portfolios = get_mock_portfolios()
        assert isinstance(portfolios, list)
        assert len(portfolios) > 0

    def test_mock_portfolios_have_required_fields(self) -> None:
        """Test that each portfolio has required fields."""
        portfolios = get_mock_portfolios()
        required_fields = [
            "id",
            "name",
            "description",
            "strategy_id",
            "strategy_name",
            "holdings",
            "total_value",
            "total_cost",
            "total_gain_loss",
            "total_gain_loss_pct",
        ]

        for portfolio in portfolios:
            for field in required_fields:
                assert field in portfolio, f"Portfolio missing field: {field}"

    def test_portfolio_holdings_have_required_fields(self) -> None:
        """Test that portfolio holdings have required fields."""
        portfolios = get_mock_portfolios()
        required_fields = [
            "ticker",
            "name",
            "shares",
            "cost_basis",
            "current_price",
            "current_value",
            "gain_loss",
            "gain_loss_pct",
        ]

        for portfolio in portfolios:
            for holding in portfolio["holdings"]:
                for field in required_fields:
                    assert field in holding, f"Holding missing field: {field}"

    def test_get_mock_portfolio_by_id_returns_correct_portfolio(self) -> None:
        """Test that get_mock_portfolio_by_id returns the correct portfolio."""
        portfolio = get_mock_portfolio_by_id("1")
        assert portfolio is not None
        assert portfolio["id"] == "1"
        assert portfolio["name"] == "Growth Portfolio"

    def test_get_mock_portfolio_by_id_returns_none_for_invalid_id(self) -> None:
        """Test that get_mock_portfolio_by_id returns None for invalid ID."""
        portfolio = get_mock_portfolio_by_id("999")
        assert portfolio is None


class TestMockScreeningResults:
    """Test cases for mock screening results."""

    def test_get_mock_screening_results_returns_list(self) -> None:
        """Test that get_mock_screening_results returns a list."""
        results = get_mock_screening_results("SP500", "1")
        assert isinstance(results, list)

    def test_screening_results_have_required_fields(self) -> None:
        """Test that screening results have required fields."""
        results = get_mock_screening_results("SP500", "1")
        required_fields = [
            "ticker",
            "name",
            "price",
            "mcdx_signal",
            "b_xtrender",
            "halal_status",
            "volume",
            "market_cap",
        ]

        for result in results:
            for field in required_fields:
                assert field in result, f"Result missing field: {field}"

    def test_screening_results_filtered_by_strategy(self) -> None:
        """Test that screening results are filtered based on strategy."""
        # Strategy 1: BUY or STRONG_BUY
        results_1 = get_mock_screening_results("SP500", "1")
        for result in results_1:
            assert result["mcdx_signal"] in ["BUY", "STRONG_BUY"]

        # Strategy 2: STRONG_BUY only
        results_2 = get_mock_screening_results("SP500", "2")
        for result in results_2:
            assert result["mcdx_signal"] == "STRONG_BUY"

        # Strategy 3: STRONG_BUY + GREEN
        results_3 = get_mock_screening_results("SP500", "3")
        for result in results_3:
            assert result["mcdx_signal"] == "STRONG_BUY"
            assert result["b_xtrender"] == "GREEN"


class TestMockUniversesAndIndicators:
    """Test cases for mock universes and indicators."""

    def test_get_mock_universes_returns_list(self) -> None:
        """Test that get_mock_universes returns a list."""
        universes = get_mock_universes()
        assert isinstance(universes, list)
        assert len(universes) > 0

    def test_mock_universes_contain_expected_values(self) -> None:
        """Test that mock universes contain expected values."""
        universes = get_mock_universes()
        assert "S&P 500" in universes
        assert "NASDAQ 100" in universes
        assert "Custom List" in universes

    def test_get_mock_indicators_returns_list(self) -> None:
        """Test that get_mock_indicators returns a list."""
        indicators = get_mock_indicators()
        assert isinstance(indicators, list)
        assert len(indicators) > 0

    def test_mock_indicators_have_required_fields(self) -> None:
        """Test that mock indicators have required fields."""
        indicators = get_mock_indicators()
        required_fields = ["id", "name", "description"]

        for indicator in indicators:
            for field in required_fields:
                assert field in indicator, f"Indicator missing field: {field}"

    def test_mock_indicators_contain_expected_values(self) -> None:
        """Test that mock indicators contain expected indicator types."""
        indicators = get_mock_indicators()
        indicator_ids = [ind["id"] for ind in indicators]

        assert "mcdx" in indicator_ids
        assert "b_xtrender" in indicator_ids
        assert "sma_200" in indicator_ids
