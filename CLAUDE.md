# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

**Environment Setup:**

### conda environment
The conda environment called "stock" should always be activated. Thus assume it is already activated. There is no need
to check if it is activated because the user should have done it. 

```bash
# Install dependencies
poetry install

# Run the application
python -m stock_friend

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/stock_friend --cov-report=html --cov-report=term-missing
```

**Key Documentation:**
- Technical Requirements: `docs/TRD_Part1_Architecture.md` through `docs/TRD_Part5_Implementation_Testing.md`
- Product Requirements: `PRD.md`
- README: `README.md`

## Project Overview

**stock-friend-cli** is a Python-based CLI tool for European retail investors seeking halal-compliant, momentum-based investment opportunities.

**Core Capabilities:**
- Stock screening across exchanges (S&P 500, NASDAQ, Russell 2000)
- Halal compliance filtering (zero false negatives guarantee)
- Pluggable investment strategy system with technical indicators
- Portfolio management with strategy validation
- Multi-source data integration (Yahoo Finance, Alpha Vantage)

**Current Implementation Status:**
- ✅ CLI presentation layer with Rich UI and interactive menus
- ✅ Stock search service with yfinance integration
- ✅ Market data gateways (yfinance, Alpha Vantage) with pluggable architecture
- ✅ Configuration management with Pydantic Settings
- ✅ Caching infrastructure
- ✅ Comprehensive unit tests (18 test files, >80% coverage)
- ❌ Strategy evaluation engine (planned)
- ❌ Technical indicators (MCDX, B-XTrender, SMA) (planned)
- ❌ Halal compliance API integration (planned)
- ❌ SQLite persistence layer (planned)

## Development Environment

### Python Environment (Required)

**Environment Name:** `stock`
**Python Version:** 3.12

**Critical:** Always activate the conda environment before development:
```bash
conda activate stock
```

Verify environment:
```bash
python --version  # Should show 3.12.x
conda info --envs | grep '*'  # Should show 'stock'
```

### Dependency Management

This project uses **Poetry** for dependency management:

```bash
# Install Poetry (if needed)
pip install poetry

# Install project dependencies
poetry install

# Add new dependency
poetry add <package-name>

# Add dev dependency
poetry add --group dev <package-name>

# Update dependencies
poetry update
```

**Note:** Docker support is planned but not yet implemented. Use conda for all development.

## Architecture

### Layered Architecture

The system follows **strict layer separation** with dependency inversion:

```
┌─────────────────────────────────────┐
│  Presentation Layer (CLI)           │  ← Typer, Rich, Questionary
│  src/stock_friend/cli/              │
├─────────────────────────────────────┤
│  Service Layer                      │  ← Business logic orchestration
│  src/stock_friend/services/         │
├─────────────────────────────────────┤
│  Domain Models                      │  ← Pydantic dataclasses
│  src/stock_friend/models/           │
├─────────────────────────────────────┤
│  Data Access Layer (Gateways)      │  ← Abstract interfaces
│  src/stock_friend/gateways/         │
├─────────────────────────────────────┤
│  Infrastructure                     │  ← Config, cache, factories
│  src/stock_friend/infrastructure/   │
├─────────────────────────────────────┤
│  Presenters                         │  ← Data formatting for display
│  src/stock_friend/presenters/       │
└─────────────────────────────────────┘
```

### Key Design Patterns

1. **Gateway Pattern**: Abstract interfaces for external data sources
   - `IMarketDataGateway` - Base interface for all market data providers
   - Implementations: `YFinanceGateway`, `AlphaVantageGateway`
   - Allows pluggable data sources without changing service layer

2. **Factory Pattern**: Dynamic gateway creation based on configuration
   - `GatewayFactory` - Creates appropriate gateway based on `.env` config
   - Handles dependency injection (cache manager)

3. **Service Layer Pattern**: Business logic orchestration
   - Services depend on gateway abstractions, not implementations
   - Example: `SearchService` works with any `IMarketDataGateway`

4. **Repository Pattern**: Planned for data persistence (not yet implemented)

5. **Strategy Pattern**: Planned for pluggable investment strategies (not yet implemented)

### Dependency Flow

**Critical Rule:** Dependencies flow DOWNWARD and INWARD only:
- CLI → Services → Gateways → Infrastructure
- Services depend on gateway **interfaces**, not implementations
- Infrastructure instantiates concrete implementations via Factory

**Example:**
```python
# CORRECT: Service depends on interface
class SearchService:
    def __init__(self, gateway: IMarketDataGateway):
        self.gateway = gateway

# Factory creates concrete implementation
factory = GatewayFactory()
gateway = factory.create_gateway()  # Returns YFinanceGateway or AlphaVantageGateway
service = SearchService(gateway)
```

## Common Development Commands

### Running the Application

```bash
# Interactive mode (menu-driven)
python -m stock_friend

# Direct stock search
python -m stock_friend search AAPL

# Quick screening (mock data)
python -m stock_friend screen --universe "S&P 500" --strategy 1

# Version info
python -m stock_friend version

# List strategies
python -m stock_friend strategy list

# List portfolios
python -m stock_friend portfolio list
```

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_search_service.py

# Run specific test function
pytest tests/unit/test_search_service.py::test_search_stock_basic

# Run with coverage (generates HTML report)
pytest --cov=src/stock_friend --cov-report=html --cov-report=term-missing

# Open coverage report
open htmlcov/index.html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run tests matching a pattern
pytest -k "search"
```

### Code Quality

```bash
# Run Ruff linter
poetry run ruff check src/ tests/

# Auto-fix linting issues
poetry run ruff check --fix src/ tests/

# Type checking with MyPy
poetry run mypy src/

# Run all quality checks
poetry run ruff check src/ tests/ && poetry run mypy src/
```

### Configuration

Configuration uses **Pydantic Settings** with `.env` file support:

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
# Set MARKET_DATA_PROVIDER to 'yfinance' (default, no API key) or 'alpha_vantage' (requires API key)
```

**Environment Variables:**
- `MARKET_DATA_PROVIDER`: `yfinance` (default) or `alpha_vantage`
- `MARKET_DATA_ALPHA_VANTAGE_API_KEY`: Alpha Vantage API key (required only if provider=alpha_vantage)
- `MARKET_DATA_YFINANCE_RATE_LIMIT`: YFinance rate limit (default: 2000 req/hour)
- `CACHE_DIR`: Cache directory (default: `data/cache`)
- `CACHE_SIZE_MB`: Cache size limit (default: 500)
- `DATABASE_PATH`: SQLite database path (default: `data/stock_cli.db`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `RATE_LIMIT_REQUESTS_PER_HOUR`: Alpha Vantage rate limit (default: 300)

**Configuration Access:**
```python
from stock_friend.infrastructure.config import config

provider = config.gateway.provider  # 'yfinance' or 'alpha_vantage'
cache_dir = config.cache.dir
log_level = config.logging.level
```

## Project Structure

```
stock-friend-cli/
├── src/stock_friend/
│   ├── cli/                    # Presentation layer
│   │   ├── app.py             # Main Typer application
│   │   ├── menu.py            # Interactive menu system
│   │   ├── search_cli.py      # Stock search commands
│   │   ├── screening_cli.py   # Stock screening interface
│   │   ├── strategy_cli.py    # Strategy management
│   │   ├── portfolio_cli.py   # Portfolio management
│   │   └── mock_data.py       # Mock data for demos
│   ├── services/              # Service layer
│   │   └── search_service.py  # Stock search orchestration
│   ├── models/                # Domain models (Pydantic)
│   │   ├── stock_data.py      # StockData, FundamentalData, etc.
│   │   └── search_models.py   # SearchResult, StockDetailedInfo, etc.
│   ├── gateways/              # Data access abstractions
│   │   ├── base.py            # IMarketDataGateway interface
│   │   ├── yfinance_gateway.py
│   │   └── alpha_vantage_gateway.py
│   ├── infrastructure/        # Cross-cutting concerns
│   │   ├── config.py          # Pydantic Settings configuration
│   │   ├── gateway_factory.py # Factory for gateway creation
│   │   └── cache_manager.py   # Caching infrastructure
│   └── presenters/            # Data formatting for display
│       └── stock_presenter.py
├── tests/
│   ├── unit/                  # Unit tests (isolated, fast)
│   │   ├── test_search_service.py
│   │   ├── test_yfinance_gateway.py
│   │   ├── test_alpha_vantage_gateway.py
│   │   ├── test_config.py
│   │   └── cli/               # CLI tests with mocks
│   ├── integration/           # Integration tests (real DB, mocked APIs)
│   │   └── test_search_integration.py
│   └── fixtures/              # Shared test data
├── docs/                      # Technical specifications
│   ├── TRD_Part1_Architecture.md
│   ├── TRD_Part2_DataModels_Services.md
│   ├── TRD_Part3_Indicators_DataAccess.md
│   ├── TRD_Part4_Integration_Security_Performance.md
│   └── TRD_Part5_Implementation_Testing.md
├── pyproject.toml             # Poetry dependencies & config
├── .env.example               # Environment variable template
└── README.md                  # User-facing documentation
```

## Testing Strategy

**Test Pyramid:**
- 70% Unit Tests: Fast, isolated, mocked dependencies
- 20% Integration Tests: Real database, mocked external APIs
- 10% E2E Tests: Complete workflows with deterministic mock data

**Coverage Requirements:**
- Minimum 80% overall coverage
- New features MUST include unit tests
- Service layer changes require integration tests

**Mocking Strategy:**
```python
# Mock external APIs in tests
from unittest.mock import Mock

def test_search_service():
    mock_gateway = Mock(spec=IMarketDataGateway)
    mock_gateway.search_stock.return_value = [SearchResult(...)]

    service = SearchService(gateway=mock_gateway)
    results = service.search("AAPL")

    assert len(results) > 0
    mock_gateway.search_stock.assert_called_once_with("AAPL")
```

## Clean Code Principles

### SOLID Principles

**Single Responsibility:**
- Each class has ONE reason to change
- Example: `SearchService` orchestrates search, `YFinanceGateway` fetches data, `CacheManager` handles caching

**Open/Closed:**
- Open for extension, closed for modification
- Example: New market data providers extend `IMarketDataGateway` without changing services

**Liskov Substitution:**
- Derived classes must be substitutable for their base classes
- Example: Any `IMarketDataGateway` implementation can replace another

**Interface Segregation:**
- Clients should not depend on interfaces they don't use
- Example: `IMarketDataGateway` has focused methods, not a bloated interface

**Dependency Inversion:**
- Depend on abstractions, not concretions
- Example: Services depend on `IMarketDataGateway` interface, not `YFinanceGateway` class

### Code Style

**Type Hints:**
```python
# REQUIRED: All function signatures must have type hints
def search_stock(query: str, limit: int = 10) -> List[SearchResult]:
    pass
```

**Naming Conventions:**
```python
# Use verbose, semantic names
def calculate_moving_average_for_stock(prices: List[Decimal]) -> Decimal:  # GOOD
    pass

def calc_ma(p: List[Decimal]) -> Decimal:  # BAD
    pass
```

**Guard Clauses:**
```python
# Prefer early returns over nested if/else
def process_stock(ticker: str) -> Optional[StockData]:
    if not ticker:
        return None
    if len(ticker) > 10:
        return None

    # Main logic here
    return fetch_stock_data(ticker)
```

**Self-Documenting Code:**
```python
# Code should explain WHAT, docstrings explain WHY
def calculate_rsi(prices: List[Decimal], period: int = 14) -> Decimal:
    """
    Calculate Relative Strength Index.

    Uses 14-period default as per Wilder's original formula.
    RSI > 70 indicates overbought, RSI < 30 indicates oversold.
    """
    # Implementation is self-explanatory due to clear variable names
    gains = [max(prices[i] - prices[i-1], 0) for i in range(1, len(prices))]
    losses = [max(prices[i-1] - prices[i], 0) for i in range(1, len(prices))]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return Decimal(str(rsi))
```

## Common Tasks

### Adding a New Market Data Provider

1. Create new gateway class implementing `IMarketDataGateway`:
```python
# src/stock_friend/gateways/my_provider_gateway.py
from stock_friend.gateways.base import IMarketDataGateway

class MyProviderGateway(IMarketDataGateway):
    def get_stock_data(self, ticker: str, ...) -> StockData:
        # Implementation
        pass

    def search_stock(self, query: str) -> List[SearchResult]:
        # Implementation
        pass
```

2. Update `GatewayFactory` to support new provider:
```python
# src/stock_friend/infrastructure/gateway_factory.py
if provider == "my_provider":
    return MyProviderGateway(...)
```

3. Add configuration in `config.py`:
```python
# Add to GatewaySettings
my_provider_api_key: Optional[str] = Field(...)
```

4. Add tests:
```python
# tests/unit/test_my_provider_gateway.py
def test_search_stock():
    gateway = MyProviderGateway(api_key="test")
    results = gateway.search_stock("AAPL")
    assert len(results) > 0
```

### Adding a New CLI Command

1. Add command to `app.py`:
```python
@app.command()
def my_command(
    param: Annotated[str, typer.Option(help="Parameter description")]
):
    """Command description."""
    # Implementation
    console.print("[green]Success![/green]")
```

2. Add tests:
```python
# tests/unit/cli/test_app.py
def test_my_command(runner):
    result = runner.invoke(app, ["my-command", "--param", "value"])
    assert result.exit_code == 0
```

### Adding a New Service

1. Create service class:
```python
# src/stock_friend/services/my_service.py
class MyService:
    def __init__(self, gateway: IMarketDataGateway):
        self.gateway = gateway

    def do_something(self, param: str) -> Result:
        # Business logic
        pass
```

2. Add unit tests with mocked gateway:
```python
# tests/unit/test_my_service.py
def test_do_something():
    mock_gateway = Mock(spec=IMarketDataGateway)
    service = MyService(gateway=mock_gateway)
    result = service.do_something("test")
    assert result is not None
```

## Implementation Notes

### Current vs. Planned Features

**Implemented:**
- CLI with interactive menus (Typer, Rich, Questionary)
- Stock search with yfinance integration
- Multi-provider architecture (yfinance, Alpha Vantage)
- Configuration management with Pydantic Settings
- Caching infrastructure
- Gateway pattern with factory

**Planned (See TRD docs):**
- Strategy evaluation engine
- Technical indicators (MCDX, B-XTrender, SMA)
- Halal compliance API integration (Zoya, Musaffa)
- SQLite persistence layer
- Portfolio performance tracking
- CSV export functionality

### Working with Mock Data

During development, the CLI uses mock data for demonstration:
- Mock strategies: Default Momentum, Conservative Growth, Aggressive Tech
- Mock stocks: AAPL, MSFT, GOOGL, NVDA, META, TSLA, AMD, ADBE, CRM, ORCL
- Mock portfolios: Growth Portfolio, Conservative Income

Mock data is in `src/stock_friend/cli/mock_data.py` and should be replaced with real service calls as features are implemented.

### Error Handling

```python
# Use custom exceptions for domain errors
from stock_friend.gateways.base import DataProviderException

try:
    data = gateway.get_stock_data(ticker)
except DataProviderException as e:
    logger.error(f"Failed to fetch data: {e}")
    console.print(f"[red]Error: {e}[/red]")
```

### Logging

```python
import logging
logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed information for debugging")
logger.info("General informational messages")
logger.warning("Warning messages for potential issues")
logger.error("Error messages for failures")
logger.critical("Critical issues requiring immediate attention")
```
### Clean Code Persona
Act as a Senior Clean Code Architect. Your goal is to write and refactor code that is production-ready, maintainable, and human-readable.

**Strictly adhere to the following directives:**

- **SOLID Principles**: Ensure classes/functions have a single responsibility and dependencies are abstracted.

- **DRY (Don't Repeat Yourself)**: Abstract repetitive logic into reusable utility functions or classes.

- **Readability First**: Use verbose, semantic variable names. Prefer Guard Clauses over nested if/else. Avoid magic numbers.

- **Self-Documenting**: The code structure should explain the what; comments should only explain the why. Resist writing line comments that can be easily understood by the code. Function level docstring should be minimal but effective without redundancy.

If you refactor existing code, briefly list the specific principles (e.g., 'Applied SRP', 'Removed Magic Numbers') used to improve it.

