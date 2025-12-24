"""Mock data for CLI demonstration and testing."""

from typing import Any

# Mock screening results with realistic stock data
MOCK_SCREENING_RESULTS: list[dict[str, Any]] = [
    {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "price": 175.50,
        "mcdx_signal": "STRONG_BUY",
        "b_xtrender": "GREEN",
        "halal_status": "COMPLIANT",
        "volume": "52.3M",
        "market_cap": "2.75T",
    },
    {
        "ticker": "MSFT",
        "name": "Microsoft Corp",
        "price": 380.25,
        "mcdx_signal": "BUY",
        "b_xtrender": "GREEN",
        "halal_status": "COMPLIANT",
        "volume": "23.1M",
        "market_cap": "2.82T",
    },
    {
        "ticker": "GOOGL",
        "name": "Alphabet Inc.",
        "price": 142.30,
        "mcdx_signal": "BUY",
        "b_xtrender": "GREEN",
        "halal_status": "COMPLIANT",
        "volume": "28.7M",
        "market_cap": "1.78T",
    },
    {
        "ticker": "NVDA",
        "name": "NVIDIA Corp",
        "price": 495.80,
        "mcdx_signal": "STRONG_BUY",
        "b_xtrender": "GREEN",
        "halal_status": "COMPLIANT",
        "volume": "45.2M",
        "market_cap": "1.22T",
    },
    {
        "ticker": "META",
        "name": "Meta Platforms Inc",
        "price": 352.90,
        "mcdx_signal": "BUY",
        "b_xtrender": "GREEN",
        "halal_status": "COMPLIANT",
        "volume": "18.5M",
        "market_cap": "895B",
    },
    {
        "ticker": "TSLA",
        "name": "Tesla Inc",
        "price": 248.50,
        "mcdx_signal": "HOLD",
        "b_xtrender": "YELLOW",
        "halal_status": "COMPLIANT",
        "volume": "112.3M",
        "market_cap": "788B",
    },
    {
        "ticker": "AMD",
        "name": "Advanced Micro Devices",
        "price": 138.75,
        "mcdx_signal": "BUY",
        "b_xtrender": "GREEN",
        "halal_status": "COMPLIANT",
        "volume": "67.8M",
        "market_cap": "224B",
    },
    {
        "ticker": "ADBE",
        "name": "Adobe Inc",
        "price": 592.40,
        "mcdx_signal": "STRONG_BUY",
        "b_xtrender": "GREEN",
        "halal_status": "COMPLIANT",
        "volume": "2.1M",
        "market_cap": "267B",
    },
    {
        "ticker": "CRM",
        "name": "Salesforce Inc",
        "price": 264.15,
        "mcdx_signal": "BUY",
        "b_xtrender": "GREEN",
        "halal_status": "COMPLIANT",
        "volume": "5.8M",
        "market_cap": "258B",
    },
    {
        "ticker": "ORCL",
        "name": "Oracle Corp",
        "price": 118.90,
        "mcdx_signal": "HOLD",
        "b_xtrender": "GREEN",
        "halal_status": "COMPLIANT",
        "volume": "8.2M",
        "market_cap": "329B",
    },
]

# Mock investment strategies
MOCK_STRATEGIES: list[dict[str, Any]] = [
    {
        "id": "1",
        "name": "Default Momentum Strategy",
        "description": "MCDX banker accumulation + B-XTrender green confirmation",
        "conditions": [
            "MCDX Signal >= BUY",
            "B-XTrender = GREEN",
            "Halal Status = COMPLIANT",
        ],
        "universe": "S&P 500",
        "created_date": "2024-01-15",
    },
    {
        "id": "2",
        "name": "Conservative Growth",
        "description": "Strong MCDX signals with SMA confirmation for low-risk growth",
        "conditions": [
            "MCDX Signal = STRONG_BUY",
            "Price > SMA(200)",
            "Halal Status = COMPLIANT",
        ],
        "universe": "NASDAQ",
        "created_date": "2024-02-10",
    },
    {
        "id": "3",
        "name": "Aggressive Tech Play",
        "description": "High momentum tech stocks with strong indicators",
        "conditions": [
            "MCDX Signal = STRONG_BUY",
            "B-XTrender = GREEN",
            "Sector = Technology",
            "Volume > 10M",
            "Halal Status = COMPLIANT",
        ],
        "universe": "NASDAQ",
        "created_date": "2024-03-05",
    },
]

# Mock portfolios with holdings
MOCK_PORTFOLIOS: list[dict[str, Any]] = [
    {
        "id": "1",
        "name": "Growth Portfolio",
        "description": "Long-term growth focused on tech leaders",
        "strategy_id": "1",
        "strategy_name": "Default Momentum Strategy",
        "holdings": [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "shares": 50,
                "cost_basis": 150.00,
                "current_price": 175.50,
                "current_value": 8775.00,
                "gain_loss": 1275.00,
                "gain_loss_pct": 17.00,
            },
            {
                "ticker": "MSFT",
                "name": "Microsoft Corp",
                "shares": 30,
                "cost_basis": 350.00,
                "current_price": 380.25,
                "current_value": 11407.50,
                "gain_loss": 907.50,
                "gain_loss_pct": 8.64,
            },
            {
                "ticker": "NVDA",
                "name": "NVIDIA Corp",
                "shares": 20,
                "cost_basis": 420.00,
                "current_price": 495.80,
                "current_value": 9916.00,
                "gain_loss": 1516.00,
                "gain_loss_pct": 18.05,
            },
        ],
        "total_value": 30098.50,
        "total_cost": 26500.00,
        "total_gain_loss": 3598.50,
        "total_gain_loss_pct": 13.58,
        "created_date": "2024-01-20",
    },
    {
        "id": "2",
        "name": "Conservative Income",
        "description": "Stable companies with consistent performance",
        "strategy_id": "2",
        "strategy_name": "Conservative Growth",
        "holdings": [
            {
                "ticker": "GOOGL",
                "name": "Alphabet Inc.",
                "shares": 75,
                "cost_basis": 135.00,
                "current_price": 142.30,
                "current_value": 10672.50,
                "gain_loss": 547.50,
                "gain_loss_pct": 5.41,
            },
            {
                "ticker": "ADBE",
                "name": "Adobe Inc",
                "shares": 15,
                "cost_basis": 550.00,
                "current_price": 592.40,
                "current_value": 8886.00,
                "gain_loss": 636.00,
                "gain_loss_pct": 7.71,
            },
        ],
        "total_value": 19558.50,
        "total_cost": 18375.00,
        "total_gain_loss": 1183.50,
        "total_gain_loss_pct": 6.44,
        "created_date": "2024-02-15",
    },
]

# Mock universe options
MOCK_UNIVERSES: list[str] = [
    "S&P 500",
    "NASDAQ 100",
    "Russell 2000",
    "Dow Jones Industrial",
    "Custom List",
]

# Mock indicator types
MOCK_INDICATORS: list[dict[str, str]] = [
    {"id": "mcdx", "name": "MCDX (Banker Accumulation)", "description": "Detects institutional buying patterns"},
    {"id": "b_xtrender", "name": "B-XTrender", "description": "Trend strength and direction indicator"},
    {"id": "sma_200", "name": "SMA(200)", "description": "200-day simple moving average"},
    {"id": "sma_50", "name": "SMA(50)", "description": "50-day simple moving average"},
    {"id": "volume", "name": "Volume", "description": "Trading volume threshold"},
]


def get_mock_screening_results(universe: str, strategy_id: str) -> list[dict[str, Any]]:
    """
    Get mock screening results filtered by universe and strategy.

    In production, this would call the ScreeningService.
    For CLI demonstration, returns a subset of mock results.
    """
    # Filter based on strategy to simulate different results
    if strategy_id == "1":  # Default Momentum
        return [r for r in MOCK_SCREENING_RESULTS if r["mcdx_signal"] in ["BUY", "STRONG_BUY"]]
    elif strategy_id == "2":  # Conservative Growth
        return [r for r in MOCK_SCREENING_RESULTS if r["mcdx_signal"] == "STRONG_BUY"]
    elif strategy_id == "3":  # Aggressive Tech
        return [r for r in MOCK_SCREENING_RESULTS if r["mcdx_signal"] == "STRONG_BUY"
                and r["b_xtrender"] == "GREEN"]
    return MOCK_SCREENING_RESULTS


def get_mock_strategies() -> list[dict[str, Any]]:
    """Get all mock strategies."""
    return MOCK_STRATEGIES


def get_mock_strategy_by_id(strategy_id: str) -> dict[str, Any] | None:
    """Get a specific mock strategy by ID."""
    for strategy in MOCK_STRATEGIES:
        if strategy["id"] == strategy_id:
            return strategy
    return None


def get_mock_portfolios() -> list[dict[str, Any]]:
    """Get all mock portfolios."""
    return MOCK_PORTFOLIOS


def get_mock_portfolio_by_id(portfolio_id: str) -> dict[str, Any] | None:
    """Get a specific mock portfolio by ID."""
    for portfolio in MOCK_PORTFOLIOS:
        if portfolio["id"] == portfolio_id:
            return portfolio
    return None


def get_mock_universes() -> list[str]:
    """Get available universe options."""
    return MOCK_UNIVERSES


def get_mock_indicators() -> list[dict[str, str]]:
    """Get available technical indicators."""
    return MOCK_INDICATORS
