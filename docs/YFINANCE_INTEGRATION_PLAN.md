# YFinance Gateway Integration Plan

## 🎯 Current Progress

**Status**: Phase 1-3 Complete ✅ | Infrastructure Solid | Ready for Service Layer

| Phase | Status | Coverage | Tests | Duration |
|-------|--------|----------|-------|----------|
| **Phase 1: Configuration** | ✅ Complete | 99% | 21 tests | ~2h |
| **Phase 2: Dependencies** | ✅ Complete | N/A | N/A | ~0.5h |
| **Phase 3: YFinanceGateway** | ✅ Complete | 93% | 24 tests | ~4h |
| **Phase 5: Gateway Factory** | ✅ Complete | 97% | 20 tests | ~2h |
| Phase 4: Indicator Calculator | ⏭️ Deferred | - | - | - |
| Phase 6: Service Layer | 📋 Next | - | - | - |
| Phase 7: Bootstrap Module | 📋 Next | - | - | - |
| Phase 8: CLI Integration | 📋 Pending | - | - | - |
| Phase 9: Testing | 📋 Pending | - | - | - |
| Phase 10: Documentation | 📋 Pending | - | - | - |

**Total Tests Passing**: 65/65 ✅
**Average Coverage**: 93%+ on new components
**Time Invested**: ~8.5 hours
**Remaining Estimated**: 23-37.5 hours

---

## Overview
Integrate YFinance as the primary market data gateway with Alpha Vantage as fallback. Implement full service layer with dependency injection following TRD architecture.

**Estimated Effort**: 32-46 hours (~1 week)
**Risk**: Medium | **Complexity**: Medium-High

## Architecture

```
CLI Layer → Service Layer → IMarketDataGateway Interface
                              ├── YFinanceGateway (primary)
                              └── AlphaVantageGateway (fallback)
                                   ↓
                              Infrastructure (Cache, RateLimiter)
                              IndicatorCalculator (pandas-ta)
```

## Key Decisions

1. **YFinance Primary**: Superior batch performance, no API limits (25 req/day Alpha Vantage)
2. **Separate IndicatorCalculator**: Single Responsibility - gateways fetch, calculator computes
3. **Gateway Factory Pattern**: Centralized instantiation, clean DI
4. **Bootstrap Module**: Facade for complex dependency wiring
5. **Environment Variable Config**: `MARKET_DATA_PROVIDER=yfinance` (default) or `=alpha_vantage`
6. **Aggressive Caching**: 24h TTL for YFinance OHLCV (vs 1h for Alpha Vantage)

---

## Implementation Phases

### Phase 1: Configuration ✅ COMPLETE (2 hours) ⚙️
**Status**: ✅ Completed | **Coverage**: 99% | **Tests**: 21 passing

**File**: `src/stock_friend/infrastructure/config.py`

**Changes**:
- Replace `APISettings` with `GatewaySettings`
- Add `provider` field (default: "yfinance")
- Make `alpha_vantage_api_key` optional (only required if provider=alpha_vantage)
- Add `yfinance_rate_limit` field (default: 2000 req/hour)
- Add validators for provider and conditional API key

**Environment Variables**:
```bash
MARKET_DATA_PROVIDER=yfinance  # or alpha_vantage
MARKET_DATA_ALPHA_VANTAGE_API_KEY=key  # required only if provider=alpha_vantage
MARKET_DATA_YFINANCE_RATE_LIMIT=2000
```

**Tests**: ✅
- ✅ Invalid provider raises ValueError
- ✅ alpha_vantage requires API key
- ✅ yfinance works without API key
- ✅ Default provider is yfinance
- ✅ 21 total tests passing

**Test File**: `tests/unit/test_config.py`

---

### Phase 2: Dependencies ✅ COMPLETE (0.5 hours) 📦
**Status**: ✅ Completed

**File**: `pyproject.toml`

**Added**: ✅
```toml
yfinance = "^1.0"           # Latest stable (upgraded from ^0.2.50)
pandas-ta = "^0.4.71b0"     # Latest stable (upgraded from ^0.3.14b)
```

**Installed**: ✅
```bash
conda activate stock
poetry add yfinance pandas-ta  # Completed successfully
```

---

### Phase 3: YFinanceGateway ✅ COMPLETE (4 hours) 🔌
**Status**: ✅ Completed | **Coverage**: 93% | **Tests**: 24 passing

**File**: `src/stock_friend/gateways/yfinance_gateway.py` (527 lines)

**Key Features**:
- No API key required (constructor: `cache_manager`, `rate_limiter`, `requests_per_hour=2000`)
- Batch optimization: Use `yf.download(tickers, threads=True)` for parallel fetching
- Aggressive caching: 24h TTL for OHLCV, 15min for current prices
- Retry logic: Exponential backoff (2s, 4s, 8s) with 3 attempts
- Column standardization: Map yfinance columns to standard format
- Error handling: Empty DataFrames, network errors, missing columns

**Methods to Implement**:
```python
class YFinanceGateway(IMarketDataGateway):
    get_stock_data(ticker, start_date, end_date, period) -> StockData
    get_batch_stock_data(tickers, ...) -> Dict[str, StockData]  # Uses yf.download()
    get_current_price(ticker) -> Decimal
    get_batch_current_prices(tickers) -> Dict[str, Decimal]
    get_fundamental_data(ticker) -> Optional[FundamentalData]
    get_name() -> str  # Returns "yfinance"
```

**Tests**: ✅
- ✅ Mock `yf.Ticker` and `yf.download` with `@patch`
- ✅ Test successful retrieval, batch optimization, caching, rate limiting
- ✅ Test error handling (empty DataFrame, network errors)
- ✅ Test column standardization
- ✅ 24 total tests passing (all 6 methods + edge cases)

**Test File**: `tests/unit/test_yfinance_gateway.py` (425 lines)

**Real-World Testing**: ✅ Validated with live YFinance API
- Single stock data: ✅ AAPL (21 data points)
- Current prices: ✅ MSFT ($488.02)
- Batch operations: ✅ GOOGL, TSLA (parallel fetch)
- Fundamentals: ✅ Apple Inc. (market cap $4.06T)

---

### Phase 4: Indicator Calculator ⏭️ DEFERRED (3-4 hours) 📊
**Status**: ⏭️ Deferred (Algorithm-heavy, will implement after infrastructure)
**Risk**: Medium

**File**: `src/stock_friend/indicators/calculator.py`

**Design**: Separate service using pandas-ta library

**Indicators**:
- **MCDX**: `ta.macd(close, fast=12, slow=26, signal=9)`
- **SMA**: `ta.sma(close, length=50)`
- **B-XTrender**: `ta.bbands(close, length=20, std=2.0)`

**Implementation**:
```python
class IndicatorCalculator:
    @staticmethod
    def calculate_mcdx(df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame

    @staticmethod
    def calculate_sma(df: pd.DataFrame, period=50) -> pd.DataFrame

    @staticmethod
    def calculate_b_xtrender(df: pd.DataFrame, period=20, std_dev=2.0) -> pd.DataFrame

    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame, indicators: Dict) -> pd.DataFrame
```

**Tests**: ⏭️ Deferred
- Unit tests with small known DataFrames
- Test each indicator separately
- Test insufficient data handling
- Integration test with real gateway data

**Reason for Deferral**: Focus on solid infrastructure first. Indicators require algorithm validation and testing, which is more complex. Will implement after service layer is complete.

---

### Phase 5: Gateway Factory ✅ COMPLETE (2 hours) 🏭
**Status**: ✅ Completed | **Coverage**: 97% | **Tests**: 20 passing

**File**: `src/stock_friend/infrastructure/gateway_factory.py` (160 lines)

**Implementation**:
```python
class GatewayFactory:
    SUPPORTED_GATEWAYS = {"yfinance", "alpha_vantage"}

    def __init__(self, config, cache_manager, rate_limiter)

    def create_gateway(self, provider: Optional[str] = None) -> IMarketDataGateway:
        # Uses config.gateway.provider if provider is None
        # Returns YFinanceGateway or AlphaVantageGateway
        # Validates provider, raises ValueError if Alpha Vantage without API key

    def _create_yfinance_gateway() -> YFinanceGateway
    def _create_alpha_vantage_gateway() -> AlphaVantageGateway
```

**Implementation Notes**: ✅
- Used lazy imports (`TYPE_CHECKING`) to avoid circular dependencies
- Factory pattern with dependency injection
- Supports runtime provider switching
- Validates configuration before gateway creation

**Tests**: ✅
- ✅ Test each gateway type creation
- ✅ Test provider validation
- ✅ Test missing API key error for Alpha Vantage
- ✅ Test default provider from config
- ✅ Test explicit provider override
- ✅ 20 total tests passing (including edge cases)

**Test File**: `tests/unit/test_gateway_factory.py` (238 lines)

---

### Phase 6: Service Layer 📋 NEXT (6-8 hours) 🔧
**Status**: 📋 Next Phase | **Risk**: Medium-High

**Files**:
- `src/stock_friend/services/__init__.py`
- `src/stock_friend/services/screening_service.py`
- `src/stock_friend/services/portfolio_service.py`
- `src/stock_friend/services/strategy_service.py`

#### ScreeningService

**Responsibilities**: Fetch stock data, calculate indicators, apply strategy filters

```python
class ScreeningService:
    def __init__(self, market_data_gateway: IMarketDataGateway,
                 indicator_calculator: IndicatorCalculator)

    def screen_stocks(self, tickers: List[str], indicators: Dict,
                     period: str = "1y") -> Dict[str, StockData]:
        # 1. Fetch via gateway.get_batch_stock_data()
        # 2. Calculate indicators for each stock
        # 3. Return enriched StockData

    def get_stock_with_indicators(self, ticker: str, indicators: Dict,
                                  period: str = "1y") -> StockData
```

#### PortfolioService

**Responsibilities**: Update portfolio prices, calculate performance metrics

```python
class PortfolioService:
    def __init__(self, market_data_gateway: IMarketDataGateway)

    def update_portfolio_prices(self, portfolio: Portfolio) -> Portfolio:
        # Fetch current prices via gateway.get_batch_current_prices()
        # Update holdings

    def validate_holdings(self, tickers: List[str]) -> Dict[str, bool]
```

#### StrategyService

**Responsibilities**: Minimal (strategy logic in database/domain layer)

**Tests**:
- Mock gateway for deterministic tests
- Test service methods with edge cases
- Test error handling (gateway failures)

---

### Phase 7: Bootstrap Module 📋 PENDING (2-3 hours) 🚀
**Status**: 📋 Pending | **Risk**: Low

**File**: `src/stock_friend/infrastructure/bootstrap.py`

**Purpose**: Centralize dependency initialization (Facade pattern)

**Implementation**:
```python
@dataclass
class ApplicationContext:
    config: ApplicationConfig
    cache_manager: CacheManager
    rate_limiter: RateLimiter
    gateway: IMarketDataGateway
    indicator_calculator: IndicatorCalculator
    screening_service: ScreeningService
    portfolio_service: PortfolioService
    strategy_service: StrategyService

def initialize_app(env_file: Optional[str] = None,
                  gateway_override: Optional[str] = None) -> ApplicationContext:
    """
    Initialize application with all dependencies.

    Steps:
    1. Load config (ApplicationConfig)
    2. Configure logging
    3. Initialize infrastructure (cache, rate limiter)
    4. Create gateway via GatewayFactory
    5. Initialize indicator calculator
    6. Initialize services (inject dependencies)
    7. Return ApplicationContext
    """

def create_test_context(gateway_type="yfinance") -> ApplicationContext:
    """Create context for testing with in-memory cache."""
```

**Tests**:
- Test initialization succeeds with valid config
- Test initialization fails with invalid config
- Test gateway_override works
- Test create_test_context()

---

### Phase 8: CLI Integration 📋 PENDING (3-4 hours) 🖥️
**Status**: 📋 Pending | **Risk**: Medium

**File**: `src/stock_friend/cli/app.py`

**Changes**:
1. Remove all `mock_data` imports and references
2. Add `from stock_friend.infrastructure.bootstrap import initialize_app`
3. Global ApplicationContext with lazy initialization
4. Update all commands to use services from context
5. Error handling for initialization failures
6. Display active gateway in `version` command

**Implementation Pattern**:
```python
_app_context: ApplicationContext = None

def get_app_context() -> ApplicationContext:
    global _app_context
    if _app_context is None:
        try:
            console.print("[cyan]Initializing...[/cyan]")
            _app_context = initialize_app()
            console.print(f"[green]✓[/green] Using {_app_context.gateway.get_name()}\n")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}\n")
            sys.exit(1)
    return _app_context

def run_interactive_menu():
    app_context = get_app_context()
    run_screening_workflow(app_context.screening_service)
    run_portfolio_management(app_context.portfolio_service)
    run_strategy_management(app_context.strategy_service)
```

**Update CLI Modules**:
- `src/stock_friend/cli/screening_cli.py`: Accept `ScreeningService` parameter
- `src/stock_friend/cli/portfolio_cli.py`: Accept `PortfolioService` parameter
- `src/stock_friend/cli/strategy_cli.py`: Accept `StrategyService` parameter

**Tests**:
- Manual CLI testing
- Test initialization error handling
- Test gateway display

---

### Phase 9: Testing 📋 PENDING (Incremental + 5-7 hours) 🧪
**Status**: 📋 Incremental (Phase 1-5 complete) | **Risk**: Low

**Test Structure**:
```
tests/
├── unit/
│   ├── test_yfinance_gateway.py       # ✅ COMPLETE (24 tests, 93% coverage)
│   ├── test_config.py                 # ✅ COMPLETE (21 tests, 99% coverage)
│   ├── test_gateway_factory.py        # ✅ COMPLETE (20 tests, 97% coverage)
│   ├── test_indicator_calculator.py   # ⏭️ DEFERRED
│   ├── test_screening_service.py      # 📋 PENDING
│   ├── test_portfolio_service.py      # 📋 PENDING
│   ├── test_alpha_vantage_gateway.py  # EXISTING (keep passing)
│   └── cli/                           # 📋 PENDING (update to use services)
├── integration/
│   ├── test_yfinance_integration.py   # 📋 PENDING
│   └── test_alpha_vantage_integration.py  # EXISTING (keep)
└── fixtures/
    └── mock_responses.py              # 📋 PENDING (add YFinance mocks)
```

**Coverage Targets** (Updated):
- ✅ YFinanceGateway: 93% (Target: >90%) ✅ **EXCEEDED**
- ⏭️ IndicatorCalculator: Deferred (Target: >95%)
- 📋 Services: Pending (Target: >85%)
- ✅ GatewayFactory: 97% (Target: >90%) ✅ **EXCEEDED**
- 📋 Bootstrap: Pending (Target: >80%)
- **Current Overall: 35% → Target: >85%**

**Completed Tests**: 65/65 passing ✅

**Test Commands**:
```bash
# Unit tests only (fast)
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=src --cov-report=html --cov-report=term

# Integration tests (requires network)
pytest tests/integration/ -v

# All tests
pytest -v
```

---

### Phase 10: Documentation 📋 PENDING (2-3 hours) 📝
**Status**: 📋 Pending | **Risk**: Low

**Files to Create/Update**:

1. **`.env.example`**: Multi-gateway configuration template
2. **`docs/MIGRATION_GUIDE_YFINANCE.md`**: Step-by-step migration guide
3. **`CLAUDE.md`**: Add gateway configuration section
4. **`README.md`**: Update installation instructions

**`.env.example` Updates**:
```bash
# Gateway Configuration
MARKET_DATA_PROVIDER=yfinance  # or alpha_vantage
MARKET_DATA_ALPHA_VANTAGE_API_KEY=key  # required only if provider=alpha_vantage
MARKET_DATA_YFINANCE_RATE_LIMIT=2000  # optional, default: 2000 req/hour
```

**Migration Guide Contents**:
- Overview of changes
- Breaking changes (configuration)
- Step-by-step migration
- FAQ (API key, rate limits, gateway selection)
- Rollback plan
- Performance comparison table

---

## Success Criteria ✅

### Functionality
- ✅ YFinance gateway implements all 6 IMarketDataGateway methods ✅ **COMPLETE**
- ✅ Batch operations use `yf.download()` efficiently ✅ **COMPLETE**
- ⏭️ Indicator calculator produces correct MCDX, SMA, B-XTrender values (Deferred)
- 📋 Service layer orchestrates data fetching + indicator calculation (Next)
- 📋 CLI commands work with real data (no mock data) (Pending)

### Performance
- ✅ Single stock fetch: <2s (95th percentile) ✅ **VALIDATED** (AAPL: ~1s)
- ✅ 100 stock batch (YFinance): <60s ✅ **ACHIEVABLE** (parallel yf.download)
- ✅ 100 stock batch (Alpha Vantage): ~20min (rate limited) ✅ **KNOWN**
- ✅ Cache hit: <10ms ✅ **ACHIEVABLE** (DiskCache + memory)
- ⏭️ Indicator calculation: <0.5s per stock (Deferred)

### Quality
- 🔄 Overall test coverage: 35% → Target: >85% (In Progress)
- ✅ YFinanceGateway: 93% ✅ **EXCEEDED TARGET** (>90%)
- ✅ GatewayFactory: 97% ✅ **EXCEEDED TARGET** (>90%)
- ✅ Config: 99% ✅ **EXCEEDED TARGET** (>90%)
- ⏭️ IndicatorCalculator: Deferred (>95%)
- 📋 Services: Pending (>85%)
- ✅ All existing Alpha Vantage tests pass ✅ **CONFIRMED**

### Usability
- ✅ Default configuration works out-of-box (YFinance, no API key) ✅ **COMPLETE**
- ✅ Clear error messages for configuration issues ✅ **COMPLETE**
- 📋 Migration guide for existing users (Pending)
- ✅ Backward compatibility with Alpha Vantage ✅ **MAINTAINED**

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| YFinance instability (web scraping) | High | Comprehensive error handling, retry logic, fallback to Alpha Vantage |
| Configuration breaking changes | Medium | Clear migration guide, .env.example, backward compatibility |
| Service layer bugs | High | Extensive unit tests with mocked gateways, integration tests |
| Indicator accuracy | High | Unit tests with known values, pandas-ta is battle-tested |
| Performance regression | Medium | Performance benchmarks, cache optimization |

---

## Critical Files for Implementation

1. ✅ **`src/stock_friend/infrastructure/config.py`** - Multi-gateway configuration (COMPLETE)
2. ✅ **`src/stock_friend/gateways/yfinance_gateway.py`** - YFinance implementation (COMPLETE)
3. ⏭️ **`src/stock_friend/indicators/calculator.py`** - pandas-ta indicator calculator (DEFERRED)
4. ✅ **`src/stock_friend/infrastructure/gateway_factory.py`** - Gateway instantiation (COMPLETE)
5. 📋 **`src/stock_friend/infrastructure/bootstrap.py`** - Dependency wiring (NEXT)
6. 📋 **`src/stock_friend/services/screening_service.py`** - Screening orchestration (NEXT)
7. 📋 **`src/stock_friend/services/portfolio_service.py`** - Portfolio management (NEXT)
8. 📋 **`src/stock_friend/cli/app.py`** - CLI integration with ApplicationContext (PENDING)

### Test Files Created

9. ✅ **`tests/unit/test_config.py`** - Config tests (21 tests, 99% coverage) (COMPLETE)
10. ✅ **`tests/unit/test_yfinance_gateway.py`** - YFinance tests (24 tests, 93% coverage) (COMPLETE)
11. ✅ **`tests/unit/test_gateway_factory.py`** - Factory tests (20 tests, 97% coverage) (COMPLETE)
12. ✅ **`docs/YFINANCE_INTEGRATION_PLAN.md`** - This plan document (COMPLETE)

---

## Implementation Order (Critical Dependencies)

```
Phase 1 (Config) → Phase 2 (Dependencies) → Phase 3 (YFinanceGateway)
                                          ↓
                                    Phase 4 (IndicatorCalculator)
                                          ↓
                                    Phase 5 (GatewayFactory)
                                          ↓
                                    Phase 6 (Services)
                                          ↓
                                    Phase 7 (Bootstrap)
                                          ↓
                                    Phase 8 (CLI Integration)
                                          ↓
                               Phase 9 (Testing) → Phase 10 (Documentation)
```

**Note**: Phases 3 and 4 can be done in parallel. Phase 9 should be incremental (write tests as you implement each phase).
