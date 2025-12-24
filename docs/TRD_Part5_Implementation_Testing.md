# Technical Requirements Document (TRD)
## stock-friend-cli: Halal-Compliant Stock Screening Tool

**Part 5: Implementation Strategy & Testing**

---

## Document Navigation

- **Part 1:** Architecture & Foundation
- **Part 2:** Data Models & Service Layer
- **Part 3:** Indicator Architecture & Data Access Layer
- **Part 4:** Integration, Security & Performance
- **Part 5:** Implementation Strategy & Testing (this document - FINAL)

---

## Phase 22: MVP Feature Breakdown

### 22.1 MVP Scope Definition

**MVP Goal:** Deliver a functional CLI tool that enables users to screen stocks from major exchanges using the default momentum strategy with halal compliance filtering.

**MVP Features (Must Have):**

1. ✅ Stock screening from S&P 500, NASDAQ, and custom lists
2. ✅ Halal compliance filtering (business activity only)
3. ✅ Default momentum strategy (MCDX + B-XTrender)
4. ✅ Strategy management (view, create, edit, delete)
5. ✅ Portfolio management (CRUD operations)
6. ✅ Strategy validation on portfolio holdings
7. ✅ Basic caching (1-hour TTL for OHLCV data)
8. ✅ CSV export for results
9. ✅ CLI interface with Rich formatting
10. ✅ SQLite persistence

**Out of Scope for MVP (Phase 2):**

- ❌ Financial ratio screening (debt ratios, impure income)
- ❌ Sector and market cap screening
- ❌ ETF holdings screening
- ❌ Real-time data streaming
- ❌ Backtesting engine
- ❌ Web interface
- ❌ Advanced indicators (RSI, MACD, Bollinger Bands)
- ❌ Multi-user support / cloud sync
- ❌ Excel export

---

### 22.2 Task Breakdown with Dependencies

```mermaid
graph TD
    A[Setup Project Structure] --> B[Implement Domain Models]
    A --> C[Setup Database Schema]

    B --> D[Implement Repository Layer]
    C --> D

    D --> E[Implement CacheManager]
    D --> F[Implement RateLimiter]

    E --> G[Implement MarketDataGateway]
    F --> G

    E --> H[Implement ComplianceGateway]
    F --> H

    E --> I[Implement UniverseGateway]

    B --> J[Implement IIndicator Interface]
    J --> K[Implement MCDXIndicator]
    J --> L[Implement BXTrenderIndicator]
    J --> M[Implement SMAIndicator]

    K --> N[Implement IndicatorRegistry]
    L --> N
    M --> N

    N --> O[Implement StrategyEvaluator]
    G --> O

    O --> P[Implement ScreeningService]
    H --> P
    I --> P

    D --> Q[Implement StrategyService]
    D --> R[Implement PortfolioService]

    O --> R
    G --> R

    P --> S[Implement CLI - Main Menu]
    Q --> S
    R --> S

    S --> T[Implement CLI - Screening]
    S --> U[Implement CLI - Strategies]
    S --> V[Implement CLI - Portfolio]

    T --> W[Integration Testing]
    U --> W
    V --> W

    W --> X[Performance Testing]
    X --> Y[MVP Complete]

    style A fill:#e1f5ff
    style Y fill:#90EE90
    style W fill:#FFE4B5
    style X fill:#FFE4B5
```

---

### 22.3 Detailed Task List with Estimates

#### Sprint 1: Foundation (Week 1)

**Task 1.1: Project Setup & Structure**
- **Difficulty:** 20
- **Estimate:** 4 hours
- **Dependencies:** None
- **Deliverables:**
  - Directory structure created
  - pyproject.toml with dependencies
  - Git repository initialized
  - .gitignore configured
  - README.md skeleton
- **Success Criteria:**
  - `poetry install` runs successfully
  - `python -m pytest` command works (even with 0 tests)

**Task 1.2: Domain Models Implementation**
- **Difficulty:** 35
- **Estimate:** 8 hours
- **Dependencies:** Task 1.1
- **Deliverables:**
  - Stock, Portfolio, Holding, Strategy models
  - ScreeningResult, StockMatch, StockExclusion models
  - ComplianceStatus, FundamentalData models
  - Unit tests for all models
- **Success Criteria:**
  - All models pass validation tests
  - 100% test coverage for domain models

**Task 1.3: Database Schema Implementation**
- **Difficulty:** 40
- **Estimate:** 8 hours
- **Dependencies:** Task 1.2
- **Deliverables:**
  - SQLite schema.sql file
  - DatabaseInitializer class
  - Migration support
  - Database initialization tests
- **Success Criteria:**
  - Database creates all tables successfully
  - Constraints and indexes work correctly
  - Default strategy inserted on init

---

#### Sprint 2: Infrastructure (Week 2)

**Task 2.1: Repository Layer**
- **Difficulty:** 45
- **Estimate:** 10 hours
- **Dependencies:** Task 1.3
- **Deliverables:**
  - IPortfolioRepository interface
  - SQLitePortfolioRepository implementation
  - IStrategyRepository interface
  - SQLiteStrategyRepository implementation
  - Unit tests with mocked database
- **Success Criteria:**
  - CRUD operations work for portfolios and strategies
  - Transactions rollback on errors

**Task 2.2: CacheManager Implementation**
- **Difficulty:** 50
- **Estimate:** 10 hours
- **Dependencies:** Task 1.3
- **Deliverables:**
  - Two-tier CacheManager (L1 memory + L2 SQLite)
  - TTL enforcement
  - LRU eviction for L1
  - Cache invalidation patterns
  - Unit tests
- **Success Criteria:**
  - Cache hit/miss rates measurable
  - Memory limit enforced
  - TTL expiration works correctly

**Task 2.3: RateLimiter Implementation**
- **Difficulty:** 42
- **Estimate:** 8 hours
- **Dependencies:** Task 1.1
- **Deliverables:**
  - Token bucket RateLimiter
  - Per-API configuration
  - Thread-safe implementation
  - Unit tests
- **Success Criteria:**
  - Rate limits enforced accurately
  - No race conditions in multi-threaded tests

---

#### Sprint 3: Data Access Layer (Week 3)

**Task 3.1: MarketDataGateway Implementation**
- **Difficulty:** 55
- **Estimate:** 12 hours
- **Dependencies:** Task 2.2, 2.3
- **Deliverables:**
  - YahooFinanceGateway class
  - OHLCV data retrieval
  - Current price fetching
  - Fundamental data fetching
  - Retry logic with exponential backoff
  - Integration tests with mocked API
- **Success Criteria:**
  - Successfully fetches data for 10 test tickers
  - Handles API failures gracefully
  - Cache integration works

**Task 3.2: ComplianceGateway Implementation**
- **Difficulty:** 52
- **Estimate:** 12 hours
- **Dependencies:** Task 2.2, 2.3
- **Deliverables:**
  - Multi-source ComplianceGateway
  - Zoya/Musaffa API integration
  - Local CSV database fallback
  - Zero false negatives enforcement
  - Integration tests with mocked APIs
- **Success Criteria:**
  - Correctly excludes all test non-compliant stocks
  - Fallback to local database works
  - Audit trail logs all exclusions

**Task 3.3: UniverseGateway Implementation**
- **Difficulty:** 48
- **Estimate:** 10 hours
- **Dependencies:** Task 2.2
- **Deliverables:**
  - StaticUniverseGateway for exchanges
  - S&P 500 constituent CSV file
  - NASDAQ constituent CSV file
  - Custom list validation
  - Unit tests
- **Success Criteria:**
  - Loads S&P 500 constituents (500+ stocks)
  - Validates ticker formats correctly

---

#### Sprint 4: Indicator System (Week 4)

**Task 4.1: IIndicator Interface & Registry**
- **Difficulty:** 38
- **Estimate:** 8 hours
- **Dependencies:** Task 1.2
- **Deliverables:**
  - IIndicator abstract base class
  - IndicatorMetadata class
  - IndicatorRegistry singleton
  - Factory pattern implementation
  - Unit tests
- **Success Criteria:**
  - Can register and retrieve indicators dynamically
  - Metadata schema validation works

**Task 4.2: MCDX Indicator Implementation**
- **Difficulty:** 70
- **Estimate:** 16 hours
- **Dependencies:** Task 4.1
- **Deliverables:**
  - MCDXIndicator class
  - Price momentum calculation
  - Volume ratio calculation
  - Divergence score calculation
  - Signal classification
  - Unit tests with known data
  - Performance benchmarks
- **Success Criteria:**
  - Calculates MCDX for 200 data points in <0.5s
  - Signals match manual calculations
  - Handles edge cases (low volume, insufficient data)

**Task 4.3: B-XTrender Indicator Implementation**
- **Difficulty:** 62
- **Estimate:** 12 hours
- **Dependencies:** Task 4.1
- **Deliverables:**
  - BXTrenderIndicator class
  - EMA calculations
  - Momentum smoothing
  - Color signal classification
  - Unit tests
  - Performance benchmarks
- **Success Criteria:**
  - Calculates B-XTrender for 200 data points in <0.3s
  - Signals are consistent with TradingView

**Task 4.4: SMA Indicator Implementation**
- **Difficulty:** 30
- **Estimate:** 6 hours
- **Dependencies:** Task 4.1
- **Deliverables:**
  - SMAIndicator class
  - Configurable periods
  - Unit tests
- **Success Criteria:**
  - SMA calculations match pandas rolling mean

---

#### Sprint 5: Business Logic (Week 5)

**Task 5.1: StrategyEvaluator Implementation**
- **Difficulty:** 65
- **Estimate:** 14 hours
- **Dependencies:** Task 4.2, 4.3, 4.4, Task 3.1
- **Deliverables:**
  - StrategyEvaluator class
  - Condition evaluation logic (AND/OR)
  - Multi-indicator coordination
  - Unit tests with mocked indicators
- **Success Criteria:**
  - Correctly evaluates all test strategies
  - Handles missing indicator data gracefully

**Task 5.2: ScreeningService Implementation**
- **Difficulty:** 60
- **Estimate:** 14 hours
- **Dependencies:** Task 5.1, Task 3.2, Task 3.3
- **Deliverables:**
  - ScreeningService class
  - Universe retrieval
  - Halal filtering stage
  - Strategy application stage
  - Result enrichment
  - Progress tracking
  - Unit and integration tests
- **Success Criteria:**
  - Successfully screens S&P 500 in <10 minutes
  - Correctly applies halal filter
  - Returns expected number of matches for test strategies

**Task 5.3: StrategyService Implementation**
- **Difficulty:** 45
- **Estimate:** 10 hours
- **Dependencies:** Task 2.1
- **Deliverables:**
  - StrategyService class
  - CRUD operations
  - Strategy validation
  - Default strategy enforcement
  - Unit tests
- **Success Criteria:**
  - Can create, read, update, delete strategies
  - Cannot delete default strategy
  - Validation catches invalid strategies

**Task 5.4: PortfolioService Implementation**
- **Difficulty:** 55
- **Estimate:** 12 hours
- **Dependencies:** Task 2.1, Task 5.1, Task 3.1
- **Deliverables:**
  - PortfolioService class
  - Holdings management
  - Strategy validation on portfolio
  - Change detection
  - Export to CSV
  - Unit tests
- **Success Criteria:**
  - Can manage portfolio holdings
  - Strategy checks work correctly
  - Detects signal changes

---

#### Sprint 6: CLI Layer (Week 6)

**Task 6.1: CLI Framework Setup**
- **Difficulty:** 35
- **Estimate:** 8 hours
- **Dependencies:** Task 1.1
- **Deliverables:**
  - Typer application structure
  - Rich console configuration
  - Questionary integration
  - Main menu skeleton
  - Unit tests for CLI utilities
- **Success Criteria:**
  - CLI launches and displays menu
  - Navigation works

**Task 6.2: Screening CLI Implementation**
- **Difficulty:** 50
- **Estimate:** 12 hours
- **Dependencies:** Task 6.1, Task 5.2
- **Deliverables:**
  - Universe selection prompts
  - Strategy selection prompts
  - Progress indicators
  - Result display with Rich tables
  - Export option
  - Integration tests
- **Success Criteria:**
  - User can complete screening workflow
  - Results displayed correctly

**Task 6.3: Strategy Management CLI**
- **Difficulty:** 45
- **Estimate:** 10 hours
- **Dependencies:** Task 6.1, Task 5.3
- **Deliverables:**
  - Strategy list display
  - Create strategy wizard
  - Edit strategy interface
  - Delete confirmation
  - Integration tests
- **Success Criteria:**
  - User can create custom strategies via CLI
  - Strategies persist across sessions

**Task 6.4: Portfolio Management CLI**
- **Difficulty:** 48
- **Estimate:** 10 hours
- **Dependencies:** Task 6.1, Task 5.4
- **Deliverables:**
  - Portfolio list display
  - Add/remove holdings
  - Strategy check display
  - Export portfolio
  - Integration tests
- **Success Criteria:**
  - User can manage portfolios via CLI
  - Strategy check results displayed clearly

---

#### Sprint 7: Testing & Polish (Week 7)

**Task 7.1: Integration Testing**
- **Difficulty:** 55
- **Estimate:** 12 hours
- **Dependencies:** All previous tasks
- **Deliverables:**
  - End-to-end test suite
  - Test scenarios for all major workflows
  - Mock data for external APIs
  - CI pipeline configuration
- **Success Criteria:**
  - All integration tests pass
  - >80% code coverage

**Task 7.2: Performance Testing**
- **Difficulty:** 45
- **Estimate:** 8 hours
- **Dependencies:** Task 7.1
- **Deliverables:**
  - Performance benchmarks
  - Load tests (100, 500 stocks)
  - Memory profiling
  - Optimization recommendations
- **Success Criteria:**
  - 500 stocks screened in <10 minutes
  - Memory usage <500MB for 500 stocks

**Task 7.3: Error Handling & Edge Cases**
- **Difficulty:** 40
- **Estimate:** 8 hours
- **Dependencies:** Task 7.1
- **Deliverables:**
  - Comprehensive error handling
  - User-friendly error messages
  - Edge case tests
  - Error recovery procedures
- **Success Criteria:**
  - No unhandled exceptions in test scenarios
  - Error messages are actionable

**Task 7.4: Documentation**
- **Difficulty:** 35
- **Estimate:** 8 hours
- **Dependencies:** All previous tasks
- **Deliverables:**
  - README.md with setup instructions
  - User guide for CLI
  - API documentation (Sphinx)
  - Contributing guidelines
  - Changelog
- **Success Criteria:**
  - New user can install and run tool following README
  - All public APIs documented

---

### 22.4 Critical Path & Time Estimates

**Critical Path:**
```
Project Setup (4h) →
Domain Models (8h) →
Database Schema (8h) →
Repository Layer (10h) →
CacheManager (10h) →
RateLimiter (8h) →
MarketDataGateway (12h) →
IIndicator Interface (8h) →
MCDX Indicator (16h) →
B-XTrender Indicator (12h) →
StrategyEvaluator (14h) →
ScreeningService (14h) →
CLI Framework (8h) →
Screening CLI (12h) →
Integration Testing (12h)
```

**Total Critical Path Time:** ~156 hours (≈4 weeks for 1 developer at 40 hours/week)

**Total Project Time (All Tasks):** ~280 hours (≈7 weeks for 1 developer)

**With Parallel Work (2 developers):** ~4 weeks

---

### 22.5 Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Pine Script → Python translation inaccuracy** | Medium | High | Validate against TradingView outputs; have test data |
| **Yahoo Finance API rate limiting** | High | Medium | Implement robust caching; respect rate limits |
| **Halal screening API unavailable** | Low | High | Implement local CSV fallback; cache for 30 days |
| **Performance targets not met** | Medium | Medium | Profile early; optimize hot paths; parallel processing |
| **Database schema changes needed** | Medium | Low | Implement migration system from start |
| **User experience issues in CLI** | Medium | Medium | Early user testing; iterate on feedback |

---

## Phase 23: Implementation Phases & Roadmap

### 23.1 Phase 1: MVP (7 weeks)

**Milestones:**

- **Week 1-2:** Foundation & Infrastructure
  - ✅ M1: Project structure and domain models complete
  - ✅ M2: Database and repository layer working

- **Week 3-4:** Data Access & Indicators
  - ✅ M3: All gateways implemented and tested
  - ✅ M4: MCDX and B-XTrender indicators working

- **Week 5:** Business Logic
  - ✅ M5: All services implemented
  - ✅ M6: Default strategy can screen S&P 500

- **Week 6:** CLI Implementation
  - ✅ M7: CLI functional for all major workflows

- **Week 7:** Testing & Documentation
  - ✅ M8: All tests passing, >80% coverage
  - ✅ M9: Documentation complete
  - ✅ **MVP RELEASE**

---

### 23.2 Phase 2: Enhanced Features (Future)

**Priority 1 (Next 4 weeks):**
- ETF holdings screening
- Sector and market cap screening
- Financial ratio screening (debt ratios, impure income)
- Additional indicators (RSI, MACD)
- Excel export

**Priority 2 (8-12 weeks out):**
- Backtesting engine
- Historical performance analysis
- Multiple portfolio support
- Enhanced visualizations (ASCII charts)

**Priority 3 (Future):**
- Web interface
- Real-time data streaming
- Cloud synchronization
- Mobile app

---

## Phase 24: Project Structure & Code Organization

### 24.1 Complete Directory Structure

```
stock-friend-cli/
├── src/
│   └── stock_friend/
│       ├── __init__.py
│       ├── __main__.py                 # Entry point: python -m stock_friend
│       │
│       ├── cli/                        # Presentation Layer
│       │   ├── __init__.py
│       │   ├── app.py                  # Main Typer application
│       │   ├── menu.py                 # Menu system
│       │   ├── screening_cli.py        # Screening commands
│       │   ├── strategy_cli.py         # Strategy commands
│       │   ├── portfolio_cli.py        # Portfolio commands
│       │   ├── settings_cli.py         # Settings commands
│       │   ├── display/                # Display utilities
│       │   │   ├── __init__.py
│       │   │   ├── tables.py           # Rich table formatters
│       │   │   ├── progress.py         # Progress bars
│       │   │   └── styles.py           # Color schemes
│       │   └── validators.py           # Input validators
│       │
│       ├── services/                   # Application Orchestration Layer
│       │   ├── __init__.py
│       │   ├── screening_service.py
│       │   ├── strategy_service.py
│       │   └── portfolio_service.py
│       │
│       ├── domain/                     # Business Logic Layer
│       │   ├── __init__.py
│       │   ├── models/                 # Domain models
│       │   │   ├── __init__.py
│       │   │   ├── stock.py
│       │   │   ├── portfolio.py
│       │   │   ├── strategy.py
│       │   │   ├── screening.py
│       │   │   ├── compliance.py
│       │   │   └── fundamental.py
│       │   │
│       │   ├── strategy_engine/        # Strategy execution
│       │   │   ├── __init__.py
│       │   │   ├── evaluator.py
│       │   │   ├── condition_evaluator.py
│       │   │   └── compliance_filter.py
│       │   │
│       │   └── validators.py           # Business validation logic
│       │
│       ├── indicators/                 # Indicator Calculation Layer
│       │   ├── __init__.py
│       │   ├── base.py                 # IIndicator interface
│       │   ├── registry.py             # IndicatorRegistry
│       │   ├── mcdx_indicator.py
│       │   ├── b_xtrender_indicator.py
│       │   ├── sma_indicator.py
│       │   └── metadata.py             # IndicatorMetadata
│       │
│       ├── data_access/                # Data Access Layer
│       │   ├── __init__.py
│       │   ├── gateways/               # External API gateways
│       │   │   ├── __init__.py
│       │   │   ├── market_data_gateway.py
│       │   │   ├── compliance_gateway.py
│       │   │   ├── universe_gateway.py
│       │   │   └── fundamental_gateway.py
│       │   │
│       │   └── repositories/           # Database repositories
│       │       ├── __init__.py
│       │       ├── base.py             # IRepository interfaces
│       │       ├── portfolio_repository.py
│       │       └── strategy_repository.py
│       │
│       ├── infrastructure/             # Infrastructure Layer
│       │   ├── __init__.py
│       │   ├── cache_manager.py
│       │   ├── rate_limiter.py
│       │   ├── config_manager.py
│       │   ├── security.py             # Encryption, API key management
│       │   ├── logger.py               # Logging configuration
│       │   ├── database.py             # Database initialization
│       │   └── container.py            # Dependency injection container
│       │
│       ├── utils/                      # Shared utilities
│       │   ├── __init__.py
│       │   ├── retry.py                # Retry decorators
│       │   ├── async_utils.py          # Async helpers
│       │   ├── circuit_breaker.py
│       │   └── sanitize.py             # Credential sanitization
│       │
│       └── exceptions.py               # Custom exceptions
│
├── data/                               # Data files
│   ├── universes/                      # Stock universe data
│   │   ├── sp500_constituents.csv
│   │   ├── nasdaq_constituents.csv
│   │   └── russell2000_constituents.csv
│   ├── compliance/                     # Compliance data
│   │   └── manual_classification.csv
│   └── stock-friend.db                 # SQLite database (created at runtime)
│
├── config/                             # Configuration files
│   ├── settings.json                   # Application settings
│   ├── logging.yaml                    # Logging configuration
│   └── *.key                           # Encrypted API keys (gitignored)
│
├── tests/                              # Test suite
│   ├── __init__.py
│   ├── conftest.py                     # Pytest fixtures
│   │
│   ├── unit/                           # Unit tests
│   │   ├── test_models/
│   │   ├── test_indicators/
│   │   ├── test_services/
│   │   ├── test_gateways/
│   │   └── test_repositories/
│   │
│   ├── integration/                    # Integration tests
│   │   ├── test_screening_workflow.py
│   │   ├── test_portfolio_workflow.py
│   │   └── test_strategy_workflow.py
│   │
│   ├── performance/                    # Performance tests
│   │   ├── test_indicator_performance.py
│   │   └── test_screening_performance.py
│   │
│   └── fixtures/                       # Test data
│       ├── sample_stock_data.csv
│       ├── mock_api_responses.json
│       └── test_strategies.json
│
├── logs/                               # Log files (created at runtime)
│   └── .gitkeep
│
├── exports/                            # Export directory (created at runtime)
│   └── .gitkeep
│
├── docs/                               # Documentation
│   ├── TRD_Part1_Architecture.md
│   ├── TRD_Part2_DataModels_Services.md
│   ├── TRD_Part3_Indicators_DataAccess.md
│   ├── TRD_Part4_Integration_Security_Performance.md
│   ├── TRD_Part5_Implementation_Testing.md
│   ├── user_guide.md
│   ├── api_reference.md
│   └── contributing.md
│
├── scripts/                            # Utility scripts
│   ├── setup_dev_env.py               # Development environment setup
│   ├── download_universe_data.py      # Download index constituents
│   └── migrate_database.py            # Database migrations
│
├── .github/                            # GitHub configuration
│   └── workflows/
│       ├── ci.yml                      # CI pipeline
│       └── release.yml                 # Release automation
│
├── pyproject.toml                      # Project configuration (Poetry)
├── poetry.lock                         # Dependency lock file
├── README.md                           # Project overview
├── CHANGELOG.md                        # Version history
├── LICENSE                             # MIT License
├── .gitignore                          # Git ignore rules
├── .env.example                        # Environment variables template
└── .python-version                     # Python version (3.11+)
```

---

### 24.2 Module Organization Guidelines

**Import Conventions:**

```python
# Standard library imports
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Third-party imports
import pandas as pd
import numpy as np
from rich.console import Console

# Local imports - absolute imports from package root
from stock_friend.domain.models.stock import Stock
from stock_friend.domain.models.strategy import Strategy
from stock_friend.services.screening_service import ScreeningService
from stock_friend.indicators.mcdx_indicator import MCDXIndicator
```

**Package Structure Rules:**

1. **Each layer is a package** with `__init__.py`
2. **Expose public API in `__init__.py`**
3. **Use absolute imports** (no relative imports like `from .. import`)
4. **One class per file** for major components
5. **Group related utilities** in single files

**Example `__init__.py`:**

```python
# src/stock_friend/indicators/__init__.py
"""
Indicator calculation layer.

This package provides technical indicators for stock analysis.
"""

from stock_friend.indicators.base import IIndicator, IndicatorMetadata
from stock_friend.indicators.registry import IndicatorRegistry, get_indicator_registry
from stock_friend.indicators.mcdx_indicator import MCDXIndicator
from stock_friend.indicators.b_xtrender_indicator import BXTrenderIndicator
from stock_friend.indicators.sma_indicator import SMAIndicator

__all__ = [
    "IIndicator",
    "IndicatorMetadata",
    "IndicatorRegistry",
    "get_indicator_registry",
    "MCDXIndicator",
    "BXTrenderIndicator",
    "SMAIndicator",
]
```

---

## Phase 25: Development Guidelines

### 25.1 Naming Conventions

**Classes:**
- PascalCase
- Noun or noun phrase
- Example: `ScreeningService`, `MCDXIndicator`, `CacheManager`

**Functions/Methods:**
- snake_case
- Verb or verb phrase
- Example: `get_stock_data()`, `calculate_momentum()`, `filter_halal_compliant()`

**Variables:**
- snake_case
- Descriptive, avoid abbreviations
- Example: `stock_data`, `compliance_status`, `screening_result`

**Constants:**
- UPPER_SNAKE_CASE
- Example: `MAX_CONCURRENT_REQUESTS`, `DEFAULT_TTL_HOURS`, `API_BASE_URL`

**Private Members:**
- Prefix with single underscore
- Example: `_cache`, `_validate_input()`, `_fetch_from_api()`

**Type Variables:**
- Single uppercase letter or PascalCase with "T" suffix
- Example: `T`, `KT`, `VT`, `ModelT`

---

### 25.2 Type Hints Standards

```python
from typing import List, Dict, Optional, Union, Any, Callable, TypeVar, Generic
from decimal import Decimal
from datetime import datetime, timedelta
import pandas as pd

# Always use type hints for function signatures
def get_stock_data(
    ticker: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> pd.DataFrame:
    """Type hints make code self-documenting."""
    pass

# Use Optional for nullable parameters
def find_stock(ticker: str) -> Optional[Stock]:
    """Returns Stock or None if not found."""
    pass

# Use Union for multiple possible types
def process_value(value: Union[int, float, Decimal]) -> Decimal:
    """Accepts int, float, or Decimal."""
    return Decimal(str(value))

# Use Callable for function parameters
def retry_on_failure(
    func: Callable[..., Any],
    max_attempts: int = 3
) -> Any:
    """Function that accepts any callable."""
    pass

# Use TypeVar for generic types
T = TypeVar('T')

def first_or_none(items: List[T]) -> Optional[T]:
    """Generic function works with any type."""
    return items[0] if items else None

# Class type hints
class CacheManager:
    """Cache manager with type-hinted attributes."""

    def __init__(self, max_size: int):
        self._cache: Dict[str, Any] = {}
        self._max_size: int = max_size
        self._hits: int = 0
        self._misses: int = 0

    def get(self, key: str) -> Optional[Any]:
        """Type-hinted method."""
        return self._cache.get(key)
```

---

### 25.3 Docstring Standards (Google Style)

```python
def screen_universe(
    self,
    universe_config: UniverseConfig,
    strategy_id: str,
    include_excluded: bool = False,
    progress_callback: Optional[Callable] = None
) -> ScreeningResult:
    """
    Screen a stock universe against a strategy.

    This method orchestrates the complete screening workflow:
    1. Retrieve stock universe
    2. Apply halal compliance filter
    3. Apply strategy conditions
    4. Enrich results with fundamental data

    Args:
        universe_config: Configuration specifying the stock universe
            (exchange, sector, market cap, ETF, or custom list)
        strategy_id: ID of strategy to apply
        include_excluded: Whether to include halal-excluded stocks in results.
            Defaults to False for safety.
        progress_callback: Optional callback for progress updates.
            Signature: callback(current: int, total: int, message: str)

    Returns:
        ScreeningResult containing matches, exclusions, and metadata

    Raises:
        UniverseNotFoundException: If universe cannot be retrieved
        StrategyNotFoundException: If strategy_id doesn't exist
        DataProviderException: If critical data sources unavailable

    Example:
        >>> config = UniverseConfig(
        ...     universe_type=UniverseType.EXCHANGE,
        ...     exchange=ExchangeType.SP500
        ... )
        >>> result = service.screen_universe(config, "default-strategy")
        >>> print(f"Found {result.matches_count} matches")
        Found 12 matches

    Note:
        This operation may take several minutes for large universes (500+ stocks).
        Progress callback is recommended for user feedback.
    """
    pass


class MCDXIndicator(IIndicator):
    """
    MCDX (Multi-Color Divergence Index) Indicator.

    Identifies institutional accumulation vs retail distribution through
    volume-weighted price momentum analysis.

    The MCDX indicator combines price momentum with volume analysis to
    detect divergences that signal "smart money" activity. Higher divergence
    scores indicate stronger institutional buying pressure.

    Attributes:
        momentum_period: Period for price momentum calculation (default: 14)
        volume_ma_period: Period for volume moving average (default: 20)
        smoothing_period: Period for smoothing divergence score (default: 5)
        threshold_banker: Threshold for "Banker" signal (default: 0.10)

    Example:
        >>> mcdx = MCDXIndicator()
        >>> df_with_mcdx = mcdx.calculate(stock_data)
        >>> signal = mcdx.get_signal(df_with_mcdx)
        >>> print(signal['signal'])
        'Banker'
    """

    def __init__(self, momentum_period: int = 14, ...):
        """
        Initialize MCDX indicator with configurable parameters.

        Args:
            momentum_period: Period for price momentum calculation (default: 14)
                Must be between 5 and 30.
            volume_ma_period: Period for volume moving average (default: 20)
                Must be between 10 and 50.
            smoothing_period: Period for smoothing divergence (default: 5)
                Must be between 3 and 10.
        """
        pass
```

---

### 25.4 Clean Code Standards (per CLAUDE.md)

#### Guard Clauses Over Nested If/Else

```python
# BAD: Nested conditionals reduce readability
def process_stock(ticker: str, strategy: Strategy) -> Optional[StockMatch]:
    if ticker:
        stock_data = get_stock_data(ticker)
        if stock_data is not None:
            if is_halal_compliant(ticker):
                signal = evaluate_strategy(stock_data, strategy)
                if signal.is_buy:
                    return create_match(ticker, signal)
    return None


# GOOD: Guard clauses with early returns
def process_stock(ticker: str, strategy: Strategy) -> Optional[StockMatch]:
    """Process a single stock against strategy."""

    # Guard: Validate ticker
    if not ticker:
        return None

    # Guard: Get stock data
    stock_data = get_stock_data(ticker)
    if stock_data is None:
        logger.warning(f"No data available for {ticker}")
        return None

    # Guard: Check halal compliance
    if not is_halal_compliant(ticker):
        logger.info(f"Excluded {ticker}: not halal compliant")
        return None

    # Guard: Evaluate strategy
    signal = evaluate_strategy(stock_data, strategy)
    if not signal.is_buy:
        return None

    # Happy path
    return create_match(ticker, signal)
```

#### DRY - Extract Common Logic

```python
# BAD: Repeated validation logic
def add_holding(self, ticker: str, shares: int):
    if not ticker or len(ticker) > 10:
        raise ValueError("Invalid ticker")
    if shares <= 0:
        raise ValueError("Shares must be positive")
    # ... add logic

def update_holding(self, ticker: str, shares: int):
    if not ticker or len(ticker) > 10:
        raise ValueError("Invalid ticker")
    if shares <= 0:
        raise ValueError("Shares must be positive")
    # ... update logic


# GOOD: Extract to utility functions
def validate_ticker(ticker: str) -> None:
    """Validate ticker format."""
    if not ticker or len(ticker) > 10:
        raise ValueError(f"Invalid ticker: {ticker}")

def validate_shares(shares: int) -> None:
    """Validate share count."""
    if shares <= 0:
        raise ValueError(f"Shares must be positive, got: {shares}")

def add_holding(self, ticker: str, shares: int):
    validate_ticker(ticker)
    validate_shares(shares)
    # ... add logic

def update_holding(self, ticker: str, shares: int):
    validate_ticker(ticker)
    validate_shares(shares)
    # ... update logic
```

#### Remove Magic Numbers

```python
# BAD: Magic numbers reduce readability
if score > 0.10:
    return "Banker"
elif score > 0.02:
    return "Smart Money"
elif score < -0.05:
    return "Retail"


# GOOD: Named constants
class MCDXThresholds:
    """MCDX signal classification thresholds."""
    BANKER = 0.10
    SMART_MONEY = 0.02
    RETAIL = -0.05

def classify_signal(score: float) -> str:
    """Classify MCDX divergence score into signal category."""
    if score >= MCDXThresholds.BANKER:
        return "Banker"
    elif score >= MCDXThresholds.SMART_MONEY:
        return "Smart Money"
    elif score <= MCDXThresholds.RETAIL:
        return "Retail"
    else:
        return "Neutral"
```

#### Semantic Variable Names

```python
# BAD: Cryptic abbreviations
def calc(df, p):
    r = df['c'].rolling(p).mean()
    return r


# GOOD: Self-documenting names
def calculate_simple_moving_average(
    data: pd.DataFrame,
    period: int
) -> pd.Series:
    """
    Calculate simple moving average of closing prices.

    Args:
        data: DataFrame containing 'close' column
        period: Lookback period for moving average

    Returns:
        Series of SMA values
    """
    closing_prices = data['close']
    moving_average = closing_prices.rolling(window=period).mean()
    return moving_average
```

---

### 25.5 Code Review Checklist

**Before Submitting PR:**

- [ ] All new code has type hints
- [ ] All public functions/classes have docstrings (Google style)
- [ ] No magic numbers (use named constants)
- [ ] Guard clauses used instead of nested if/else
- [ ] No repeated code (DRY principle applied)
- [ ] Variable names are semantic and descriptive
- [ ] Functions are small (<50 lines) and focused (SRP)
- [ ] No commented-out code
- [ ] All tests pass (`pytest`)
- [ ] Code coverage >80% (`pytest --cov`)
- [ ] No linting errors (`ruff check .`)
- [ ] Type checking passes (`mypy src/`)
- [ ] Secrets/API keys not committed
- [ ] Imports organized (stdlib, third-party, local)
- [ ] Error handling is comprehensive
- [ ] Logging added for important operations
- [ ] Performance considerations addressed

---

## Phase 26: Testing Strategy

### 26.1 Test Pyramid

```
                /\
               /  \
              /E2E \
             / 10%  \
            /________\
           /          \
          /Integration\
         /     20%     \
        /______________\
       /                \
      /    Unit Tests    \
     /        70%         \
    /____________________\
```

**Distribution:**
- **70% Unit Tests:** Fast, isolated, test individual components
- **20% Integration Tests:** Test component interactions
- **10% End-to-End Tests:** Test complete workflows

---

### 26.2 Unit Testing with Pytest

#### Test Structure

```python
# tests/unit/test_indicators/test_mcdx_indicator.py
"""
Unit tests for MCDX indicator.

Tests calculation logic, signal classification, and edge cases.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from stock_friend.indicators.mcdx_indicator import MCDXIndicator
from stock_friend.indicators.base import InsufficientDataError


class TestMCDXIndicator:
    """Test suite for MCDX indicator."""

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample stock data for testing."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 102,
            'low': np.random.randn(100).cumsum() + 98,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000000, 5000000, 100)
        })
        return df

    @pytest.fixture
    def mcdx_indicator(self) -> MCDXIndicator:
        """Create MCDX indicator instance."""
        return MCDXIndicator()

    def test_calculate_adds_required_columns(self, mcdx_indicator, sample_data):
        """Test that calculate() adds all expected columns."""
        result = mcdx_indicator.calculate(sample_data.copy())

        expected_columns = [
            'mcdx_price_momentum',
            'mcdx_volume_ratio',
            'mcdx_divergence',
            'mcdx_score',
            'mcdx_signal'
        ]

        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"

    def test_signal_categories_are_valid(self, mcdx_indicator, sample_data):
        """Test that all signals are valid categories."""
        result = mcdx_indicator.calculate(sample_data.copy())

        valid_signals = {"Banker", "Smart Money", "Neutral", "Retail"}
        unique_signals = set(result['mcdx_signal'].dropna().unique())

        assert unique_signals.issubset(valid_signals), \
            f"Invalid signals found: {unique_signals - valid_signals}"

    def test_insufficient_data_raises_error(self, mcdx_indicator):
        """Test that insufficient data raises InsufficientDataError."""
        short_df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10, freq='D'),
            'close': [100] * 10,
            'volume': [1000000] * 10
        })

        with pytest.raises(InsufficientDataError):
            mcdx_indicator.calculate(short_df)

    def test_get_signal_returns_expected_fields(self, mcdx_indicator, sample_data):
        """Test that get_signal() returns dictionary with expected fields."""
        result = mcdx_indicator.calculate(sample_data.copy())
        signal = mcdx_indicator.get_signal(result)

        assert isinstance(signal, dict)
        assert 'signal' in signal
        assert 'score' in signal
        assert 'volume_ratio' in signal
        assert 'momentum' in signal
        assert signal['signal'] in ["Banker", "Smart Money", "Neutral", "Retail"]

    def test_custom_thresholds(self):
        """Test indicator with custom thresholds."""
        mcdx = MCDXIndicator(
            threshold_banker=0.15,
            threshold_smart_money=0.05
        )

        assert mcdx.threshold_banker == 0.15
        assert mcdx.threshold_smart_money == 0.05

    @pytest.mark.parametrize("score,expected_signal", [
        (0.15, "Banker"),
        (0.05, "Smart Money"),
        (0.00, "Neutral"),
        (-0.10, "Retail"),
    ])
    def test_signal_classification(self, mcdx_indicator, score, expected_signal):
        """Test signal classification with known scores."""
        signal = mcdx_indicator._classify_signal(score)
        assert signal == expected_signal

    def test_performance_target(self, mcdx_indicator):
        """Test that calculation meets performance target (<0.5s for 200 points)."""
        import time

        large_df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=200, freq='D'),
            'open': np.random.randn(200).cumsum() + 100,
            'high': np.random.randn(200).cumsum() + 102,
            'low': np.random.randn(200).cumsum() + 98,
            'close': np.random.randn(200).cumsum() + 100,
            'volume': np.random.randint(1000000, 5000000, 200)
        })

        start = time.time()
        mcdx_indicator.calculate(large_df)
        elapsed = time.time() - start

        assert elapsed < 0.5, \
            f"Performance target not met: {elapsed:.3f}s (target: <0.5s)"
```

---

#### Mocking External APIs

```python
# tests/unit/test_gateways/test_market_data_gateway.py
"""
Unit tests for MarketDataGateway.

Uses mocks to test gateway logic without hitting real APIs.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime

from stock_friend.data_access.gateways.market_data_gateway import YahooFinanceGateway
from stock_friend.exceptions import DataProviderException


class TestYahooFinanceGateway:
    """Test suite for Yahoo Finance Gateway."""

    @pytest.fixture
    def cache_manager_mock(self):
        """Mock CacheManager."""
        mock = Mock()
        mock.get.return_value = None  # Cache miss by default
        return mock

    @pytest.fixture
    def rate_limiter_mock(self):
        """Mock RateLimiter."""
        mock = Mock()
        mock.acquire.return_value = None  # Allow all requests
        return mock

    @pytest.fixture
    def gateway(self, cache_manager_mock, rate_limiter_mock):
        """Create gateway instance with mocked dependencies."""
        return YahooFinanceGateway(cache_manager_mock, rate_limiter_mock)

    @patch('yfinance.Ticker')
    def test_get_stock_data_success(self, mock_ticker_class, gateway, cache_manager_mock):
        """Test successful stock data retrieval."""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker

        # Mock data
        mock_data = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=10, freq='D'),
            'Open': [100] * 10,
            'High': [105] * 10,
            'Low': [95] * 10,
            'Close': [102] * 10,
            'Volume': [1000000] * 10
        })
        mock_ticker.history.return_value = mock_data

        # Execute
        result = gateway.get_stock_data('AAPL')

        # Verify
        assert not result.empty
        assert 'date' in result.columns
        assert 'close' in result.columns
        mock_ticker.history.assert_called_once()
        cache_manager_mock.set.assert_called_once()

    @patch('yfinance.Ticker')
    def test_get_stock_data_api_failure(self, mock_ticker_class, gateway):
        """Test handling of API failure."""
        # Setup mock to raise exception
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker
        mock_ticker.history.side_effect = Exception("API Error")

        # Execute and verify exception
        with pytest.raises(DataProviderException) as exc_info:
            gateway.get_stock_data('AAPL')

        assert "API Error" in str(exc_info.value)

    def test_get_stock_data_cache_hit(self, gateway, cache_manager_mock):
        """Test that cached data is returned without API call."""
        # Setup cache to return data
        cached_data = pd.DataFrame({'close': [100, 101, 102]})
        cache_manager_mock.get.return_value = cached_data

        # Execute
        with patch('yfinance.Ticker') as mock_ticker:
            result = gateway.get_stock_data('AAPL')

            # Verify cache was used, API not called
            assert result.equals(cached_data)
            mock_ticker.assert_not_called()

    @patch('yfinance.Ticker')
    def test_retry_on_failure(self, mock_ticker_class, gateway):
        """Test that retry decorator retries failed calls."""
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker

        # First two calls fail, third succeeds
        mock_ticker.history.side_effect = [
            Exception("Failure 1"),
            Exception("Failure 2"),
            pd.DataFrame({
                'Date': pd.date_range('2024-01-01', periods=10, freq='D'),
                'Close': [100] * 10
            })
        ]

        # Execute - should succeed after retries
        result = gateway.get_stock_data('AAPL')

        # Verify retries occurred
        assert mock_ticker.history.call_count == 3
        assert not result.empty
```

---

### 26.3 Integration Testing

```python
# tests/integration/test_screening_workflow.py
"""
Integration tests for complete screening workflow.

Tests interaction between services, gateways, and database.
"""
import pytest
from decimal import Decimal

from stock_friend.services.screening_service import ScreeningService
from stock_friend.domain.models.strategy import UniverseConfig, UniverseType
from stock_friend.infrastructure.database import DatabaseInitializer


@pytest.mark.integration
class TestScreeningWorkflow:
    """Integration tests for screening workflow."""

    @pytest.fixture(scope="class")
    def test_database(self, tmp_path_factory):
        """Create temporary test database."""
        db_path = tmp_path_factory.mktemp("data") / "test.db"
        db_init = DatabaseInitializer(str(db_path))
        db_init.initialize()
        return str(db_path)

    @pytest.fixture
    def screening_service(self, test_database):
        """Create ScreeningService with real dependencies."""
        # Bootstrap real services (but with test data)
        from stock_friend.infrastructure.container import bootstrap_application

        container = bootstrap_application(
            config_path="tests/fixtures/test_config.json",
            db_path=test_database
        )

        return container.get(ScreeningService)

    def test_screen_custom_list_full_workflow(self, screening_service):
        """Test screening custom ticker list from start to finish."""
        # Prepare test data
        tickers = ["AAPL", "MSFT", "GOOGL"]  # Known good stocks

        config = UniverseConfig(
            universe_type=UniverseType.CUSTOM,
            custom_tickers=tickers
        )

        # Execute screening
        result = screening_service.screen_universe(
            config,
            strategy_id="default-momentum-strategy"
        )

        # Verify results
        assert result is not None
        assert result.total_stocks == len(tickers)
        assert result.compliant_stocks <= result.total_stocks
        assert result.matches_count >= 0
        assert len(result.matches) == result.matches_count

        # Verify all matches have required fields
        for match in result.matches:
            assert match.ticker
            assert match.current_price > Decimal("0")
            assert match.indicator_signals

    def test_screen_with_halal_exclusions(self, screening_service):
        """Test that halal filtering excludes non-compliant stocks."""
        # Include known non-compliant tickers
        tickers = ["JPM", "BAC", "MGM"]  # Banks and casino

        config = UniverseConfig(
            universe_type=UniverseType.CUSTOM,
            custom_tickers=tickers
        )

        # Execute screening
        result = screening_service.screen_universe(
            config,
            strategy_id="default-momentum-strategy",
            include_excluded=True
        )

        # Verify exclusions
        assert result.excluded_stocks > 0
        assert len(result.exclusions) == result.excluded_stocks

        # Verify exclusion reasons
        for exclusion in result.exclusions:
            assert exclusion.exclusion_reason in [
                "BANKING", "GAMBLING", "DEFENSE", "ALCOHOL",
                "TOBACCO", "ADULT", "PORK", "UNVERIFIED"
            ]

    def test_screen_with_progress_callback(self, screening_service):
        """Test that progress callback is called during screening."""
        progress_updates = []

        def progress_callback(current: int, total: int, message: str):
            progress_updates.append((current, total, message))

        config = UniverseConfig(
            universe_type=UniverseType.CUSTOM,
            custom_tickers=["AAPL", "MSFT"]
        )

        # Execute with callback
        screening_service.screen_universe(
            config,
            strategy_id="default-momentum-strategy",
            progress_callback=progress_callback
        )

        # Verify callbacks were made
        assert len(progress_updates) > 0
```

---

### 26.4 Performance Testing

```python
# tests/performance/test_screening_performance.py
"""
Performance tests for screening operations.

Uses pytest-benchmark for accurate measurements.
"""
import pytest
from pytest_benchmark.plugin import benchmark

from stock_friend.services.screening_service import ScreeningService


@pytest.mark.performance
class TestScreeningPerformance:
    """Performance benchmarks for screening operations."""

    @pytest.fixture
    def large_ticker_list(self):
        """Generate large list of tickers for performance testing."""
        # Use real S&P 500 tickers for realistic test
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"] * 20  # 100 tickers

    def test_screen_100_stocks_performance(self, screening_service, large_ticker_list, benchmark):
        """Benchmark screening 100 stocks."""

        config = UniverseConfig(
            universe_type=UniverseType.CUSTOM,
            custom_tickers=large_ticker_list
        )

        # Benchmark the operation
        result = benchmark(
            screening_service.screen_universe,
            config,
            "default-momentum-strategy"
        )

        # Verify performance target (<120 seconds for 100 stocks)
        assert benchmark.stats['mean'] < 120.0, \
            f"Performance target not met: {benchmark.stats['mean']:.2f}s (target: <120s)"

    def test_indicator_calculation_performance(self, mcdx_indicator, sample_large_data, benchmark):
        """Benchmark MCDX calculation performance."""

        # Benchmark calculation
        benchmark(mcdx_indicator.calculate, sample_large_data)

        # Verify target (<0.5s for 200 data points)
        assert benchmark.stats['mean'] < 0.5, \
            f"MCDX performance target not met: {benchmark.stats['mean']:.3f}s"
```

---

### 26.5 Test Fixtures Organization

```python
# tests/conftest.py
"""
Shared pytest fixtures for all tests.

Fixtures defined here are available to all test modules.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from stock_friend.infrastructure.database import DatabaseInitializer
from stock_friend.domain.models.strategy import Strategy, StrategyCondition


@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_stock_data():
    """Generate sample stock data for testing."""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    return pd.DataFrame({
        'date': dates,
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000000, 5000000, 100)
    })


@pytest.fixture
def test_database(tmp_path):
    """Create temporary test database."""
    db_path = tmp_path / "test.db"
    db_init = DatabaseInitializer(str(db_path))
    db_init.initialize()

    yield str(db_path)

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def default_strategy():
    """Create default momentum strategy for testing."""
    return Strategy(
        id="default-strategy",
        name="Default Momentum Strategy",
        description="MCDX + B-XTrender",
        conditions=[
            StrategyCondition(
                indicator_name="MCDX",
                field="signal",
                operator=ConditionOperator.IN,
                value=["Banker", "Smart Money"]
            ),
            StrategyCondition(
                indicator_name="B-XTrender",
                field="color",
                operator=ConditionOperator.EQUALS,
                value="Green"
            )
        ],
        is_default=True
    )


@pytest.fixture
def mock_yahoo_finance_response(test_data_dir):
    """Load mock Yahoo Finance API response."""
    import json
    response_file = test_data_dir / "mock_yahoo_response.json"
    with open(response_file) as f:
        return json.load(f)
```

---

## Phase 27: CLI Implementation

### 27.1 Main Application Structure

```python
# src/stock_friend/cli/app.py
"""
Main CLI application using Typer.

Entry point for the stock-friend-cli tool.
"""
import typer
from rich.console import Console
from rich.panel import Panel

from stock_friend.cli.screening_cli import screening_app
from stock_friend.cli.strategy_cli import strategy_app
from stock_friend.cli.portfolio_cli import portfolio_app
from stock_friend.cli.settings_cli import settings_app
from stock_friend.infrastructure.container import bootstrap_application
from stock_friend.infrastructure.logger import setup_logger

# Create main Typer app
app = typer.Typer(
    name="stock-friend",
    help="Halal-compliant stock screening CLI tool",
    add_completion=False
)

# Add sub-applications
app.add_typer(screening_app, name="screen", help="Screen stocks")
app.add_typer(strategy_app, name="strategy", help="Manage strategies")
app.add_typer(portfolio_app, name="portfolio", help="Manage portfolios")
app.add_typer(settings_app, name="settings", help="Configure settings")

# Rich console for output
console = Console()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    stock-friend-cli: Halal-compliant stock screening tool.

    Use --help to see available commands.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand - show main menu
        show_main_menu()


def show_main_menu():
    """Display interactive main menu."""
    from stock_friend.cli.menu import MainMenu

    console.print(Panel.fit(
        "[bold cyan]Stock Friend CLI[/bold cyan]\n"
        "[dim]Halal-compliant momentum stock screening[/dim]",
        border_style="cyan"
    ))

    menu = MainMenu()
    menu.run()


@app.command()
def version():
    """Show version information."""
    console.print("[bold]stock-friend-cli[/bold] version [cyan]1.0.0[/cyan]")


if __name__ == "__main__":
    # Setup logging
    setup_logger()

    # Bootstrap application
    container = bootstrap_application()

    # Run CLI
    app()
```

---

### 27.2 Interactive Menu with Questionary

```python
# src/stock_friend/cli/menu.py
"""
Interactive menu system using Questionary.
"""
import questionary
from rich.console import Console
from typing import Optional

console = Console()


class MainMenu:
    """Main menu for stock-friend-cli."""

    def __init__(self):
        self.running = True

    def run(self):
        """Run main menu loop."""
        while self.running:
            choice = self.show_menu()

            if choice == "Screen Stocks":
                self.screen_stocks_menu()
            elif choice == "Manage Strategies":
                self.strategies_menu()
            elif choice == "Manage Portfolio":
                self.portfolio_menu()
            elif choice == "Settings":
                self.settings_menu()
            elif choice == "Exit":
                self.running = False
                console.print("[yellow]Goodbye![/yellow]")

    def show_menu(self) -> str:
        """Display main menu and get user choice."""
        return questionary.select(
            "What would you like to do?",
            choices=[
                "Screen Stocks",
                "Manage Strategies",
                "Manage Portfolio",
                "Settings",
                questionary.Separator(),
                "Exit"
            ],
            style=questionary.Style([
                ('question', 'bold'),
                ('highlighted', 'cyan bold'),
            ])
        ).ask()

    def screen_stocks_menu(self):
        """Universe selection sub-menu."""
        universe_type = questionary.select(
            "Select universe to screen:",
            choices=[
                "S&P 500 (503 stocks)",
                "NASDAQ 100 (100 stocks)",
                "Custom Ticker List",
                questionary.Separator(),
                "Back"
            ]
        ).ask()

        if universe_type == "Back":
            return

        # Get strategy
        strategy = self.select_strategy()
        if not strategy:
            return

        # Execute screening
        from stock_friend.cli.screening_cli import run_screening
        run_screening(universe_type, strategy)
```

---

### 27.3 Rich Table Display

```python
# src/stock_friend/cli/display/tables.py
"""
Rich table formatters for CLI output.
"""
from rich.table import Table
from rich.console import Console
from typing import List

from stock_friend.domain.models.screening import StockMatch, ScreeningResult

console = Console()


def display_screening_results(result: ScreeningResult):
    """Display screening results in formatted table."""

    # Summary panel
    console.print(f"\n[bold]Screening Results:[/bold]")
    console.print(f"Universe: {result.universe_description}")
    console.print(f"Strategy: {result.strategy_name}")
    console.print(f"Total Stocks: {result.total_stocks}")
    console.print(f"Halal Compliant: [green]{result.compliant_stocks}[/green]")
    console.print(f"Excluded: [red]{result.excluded_stocks}[/red]")
    console.print(f"Matches: [bold cyan]{result.matches_count}[/bold cyan]")
    console.print(f"Processing Time: {result.processing_time_seconds:.2f}s\n")

    if result.matches_count == 0:
        console.print("[yellow]No matches found. Try adjusting strategy parameters.[/yellow]")
        return

    # Matches table
    table = Table(title="BUY SIGNALS FOUND", show_header=True, header_style="bold magenta")

    table.add_column("Ticker", style="cyan", width=8)
    table.add_column("Company", style="white", width=25)
    table.add_column("Sector", style="blue", width=15)
    table.add_column("Price", justify="right", style="green")
    table.add_column("MCDX", style="yellow")
    table.add_column("B-XTrender", style="magenta")
    table.add_column("P/E", justify="right")
    table.add_column("Match", justify="right", style="bold")

    for match in result.matches[:20]:  # Limit to 20 rows
        mcdx_signal = match.indicator_signals.get('MCDX', {}).get('signal', 'N/A')
        xtrender_color = match.indicator_signals.get('B-XTrender', {}).get('color', 'N/A')

        # Color code signals
        mcdx_display = f"[bold green]{mcdx_signal}[/bold green]" if mcdx_signal == "Banker" else mcdx_signal
        xtrender_display = f"[bold green]{xtrender_color}[/bold green]" if xtrender_color == "Green" else xtrender_color

        table.add_row(
            match.ticker,
            match.company_name[:24] if match.company_name else "N/A",
            match.sector[:14] if match.sector else "N/A",
            f"${match.current_price:.2f}" if match.current_price else "N/A",
            mcdx_display,
            xtrender_display,
            f"{match.pe_ratio:.1f}" if match.pe_ratio else "N/A",
            f"{match.match_confidence_pct}%"
        )

    console.print(table)

    if result.matches_count > 20:
        console.print(f"\n[dim]Showing 20 of {result.matches_count} matches. Export to CSV for full results.[/dim]")


def display_portfolio_summary(portfolio):
    """Display portfolio summary table."""
    table = Table(title=f"Portfolio: {portfolio.name}", show_header=True)

    table.add_column("Ticker", style="cyan")
    table.add_column("Shares", justify="right")
    table.add_column("Avg Cost", justify="right", style="yellow")
    table.add_column("Current", justify="right", style="green")
    table.add_column("Value", justify="right", style="green")
    table.add_column("Gain/Loss", justify="right")
    table.add_column("%", justify="right")

    for holding in portfolio.holdings:
        gain_loss_style = "green" if holding.gain_loss and holding.gain_loss > 0 else "red"
        gain_loss_symbol = "+" if holding.gain_loss and holding.gain_loss > 0 else ""

        table.add_row(
            holding.ticker,
            str(holding.shares),
            f"${holding.avg_cost:.2f}",
            f"${holding.current_price:.2f}" if holding.current_price else "N/A",
            f"${holding.current_value:.2f}" if holding.current_value else "N/A",
            f"[{gain_loss_style}]{gain_loss_symbol}${holding.gain_loss:.2f}[/{gain_loss_style}]" if holding.gain_loss else "N/A",
            f"[{gain_loss_style}]{gain_loss_symbol}{holding.gain_loss_pct:.1f}%[/{gain_loss_style}]" if holding.gain_loss_pct else "N/A"
        )

    console.print(table)

    # Summary row
    console.print(f"\n[bold]Total Value:[/bold] ${portfolio.total_value:.2f}")
    gain_loss_style = "green" if portfolio.total_gain_loss > 0 else "red"
    console.print(f"[bold]Total Gain/Loss:[/bold] [{gain_loss_style}]${portfolio.total_gain_loss:.2f} ({portfolio.total_gain_loss_pct:.1f}%)[/{gain_loss_style}]")
```

---

### 27.4 Progress Indicators

```python
# src/stock_friend/cli/display/progress.py
"""
Progress indicators for long-running operations.
"""
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console

console = Console()


def create_screening_progress() -> Progress:
    """Create progress bar for screening operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    )


# Usage in ScreeningService
def screen_with_progress(service, config, strategy_id):
    """Screen stocks with progress indication."""

    with create_screening_progress() as progress:
        # Track overall progress
        main_task = progress.add_task(
            "[cyan]Screening stocks...",
            total=100
        )

        def progress_callback(current, total, message):
            percentage = (current / total) * 100
            progress.update(main_task, completed=percentage, description=f"[cyan]{message}")

        result = service.screen_universe(
            config,
            strategy_id,
            progress_callback=progress_callback
        )

    return result
```

---

## Phase 28: Logging & Monitoring

### 28.1 Logging Configuration

```python
# src/stock_friend/infrastructure/logger.py
"""
Logging configuration for stock-friend-cli.
"""
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime


def setup_logger(
    log_level: str = "INFO",
    log_dir: str = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    Setup application-wide logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        max_bytes: Maximum size of each log file
        backup_count: Number of backup log files to keep
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger("stock_friend")
    logger.setLevel(getattr(logging, log_level.upper()))

    # File handler with rotation
    log_file = log_path / "stock-friend.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )

    # Console handler
    console_handler = logging.StreamHandler()

    # Formatter with structured format
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Logging initialized")

    return logger
```

---

## Phase 29: Deployment & Distribution

### 29.1 pyproject.toml (Poetry Configuration)

```toml
[tool.poetry]
name = "stock-friend-cli"
version = "1.0.0"
description = "Halal-compliant stock screening CLI tool with momentum analysis"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
license = "MIT"
homepage = "https://github.com/yourusername/stock-friend-cli"
repository = "https://github.com/yourusername/stock-friend-cli"
keywords = ["stock", "screening", "halal", "momentum", "investing", "cli"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Financial and Insurance Industry",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Office/Business :: Financial :: Investment",
]

[tool.poetry.dependencies]
python = "^3.11"
pandas = "^2.1.0"
numpy = "^1.24.0"
yfinance = "^0.2.30"
rich = "^13.5.0"
typer = {extras = ["all"], version = "^0.9.0"}
questionary = "^2.0.0"
pydantic = "^2.4.0"
cryptography = "^41.0.0"
keyring = "^24.2.0"
python-dotenv = "^1.0.0"
aiohttp = "^3.9.0"
requests = "^2.31.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
pytest-mock = "^3.11.1"
pytest-asyncio = "^0.21.1"
pytest-benchmark = "^4.0.0"
mypy = "^1.5.0"
ruff = "^0.1.0"
black = "^23.9.0"
ipython = "^8.15.0"

[tool.poetry.scripts]
stock-friend = "stock_friend.cli.app:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --cov=stock_friend --cov-report=html --cov-report=term-missing"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = "yfinance.*"
ignore_missing_imports = true
```

---

## Phase 30: Documentation Requirements

### 30.1 README.md Structure

```markdown
# stock-friend-cli

Halal-compliant stock screening CLI tool with momentum-based technical analysis.

## Features

- 🕌 **Halal Compliance Filtering** - Automatic exclusion of non-compliant stocks
- 📊 **Technical Analysis** - MCDX and B-XTrender momentum indicators
- 🔍 **Universe Screening** - Screen S&P 500, NASDAQ, or custom lists
- 📁 **Portfolio Management** - Track holdings and validate strategy compliance
- ⚙️ **Custom Strategies** - Create and manage investment strategies
- 💾 **Local-First** - All data stored locally, no cloud dependencies

## Installation

### Prerequisites

- Python 3.11 or higher
- pip or Poetry

### Install via pip

```bash
pip install stock-friend-cli
```

### Install via Poetry

```bash
git clone https://github.com/yourusername/stock-friend-cli.git
cd stock-friend-cli
poetry install
```

## Quick Start

```bash
# Launch interactive menu
stock-friend

# Screen S&P 500 with default strategy
stock-friend screen sp500 --strategy default

# List strategies
stock-friend strategy list

# Manage portfolio
stock-friend portfolio list
```

## Documentation

- [User Guide](docs/user_guide.md)
- [API Reference](docs/api_reference.md)
- [Contributing](docs/contributing.md)

## License

MIT License - see [LICENSE](LICENSE) for details
```

---

**End of Part 5: Implementation Strategy & Testing**

This completes the comprehensive Technical Requirements Document (TRD) for stock-friend-cli!

## TRD Summary

The complete Technical Requirements Document spans 5 parts:

✅ **Part 1:** Architecture & Foundation (7 Mermaid diagrams, system architecture, design patterns, SOLID principles)

✅ **Part 2:** Data Models & Service Layer (complete domain models, database schema with ER diagram, service interfaces)

✅ **Part 3:** Indicator Architecture & Data Access Layer (complete indicator implementations, gateway implementations)

✅ **Part 4:** Integration, Security & Performance (API integration, caching, rate limiting, security, error handling)

✅ **Part 5:** Implementation Strategy & Testing (MVP breakdown, testing strategy, CLI implementation, deployment)

**Total Pages:** ~150 pages of technical specifications
**Total Code Examples:** 100+ complete Python implementations
**Total Mermaid Diagrams:** 10+ architectural and workflow diagrams
**Total Test Examples:** 15+ complete test cases

The TRD is now **100% COMPLETE** and ready for implementation!