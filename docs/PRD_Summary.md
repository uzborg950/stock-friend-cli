# Stock Strategy CLI - PRD Summary

## Executive Overview

**Product:** Stock Strategy CLI (stock-friend-cli)
**Target Users:** European retail investors seeking halal-compliant, momentum-based investments
**Core Value:** Automated stock discovery across entire exchanges/sectors with ethical compliance + technical analysis

## Key Features (MVP - P0)

1. **Stock Screening Engine**
   - Screen by: Exchange/Index (S&P 500, NASDAQ, Russell 2000), Sector, Market Cap, ETF Holdings, Custom Lists
   - Two-stage filtering: (1) Halal compliance → (2) Investment strategy criteria
   - Performance: Screen 500 stocks in <120 seconds

2. **Investment Strategy Management**
   - CRUD operations for user-defined strategies
   - Default strategy: MCDX = "Banker" AND B-XTrender = "Green"
   - Pluggable indicator system (MCDX, B-XTrender, SMA, fundamental filters)

3. **Portfolio Management**
   - Track holdings with real-time valuations
   - Daily strategy validation: Strong/Weakening/Lost signals
   - Position tracking with fundamental data display

4. **Main Menu & Navigation**
   - CLI interface with numbered options
   - Context-sensitive help system
   - Settings for API keys and preferences

## Critical Architecture Requirements

### Layered Architecture
```
CLI (Presentation) → Application Services → Strategy Engine →
Indicator Layer → Data Access (Gateways) → Infrastructure → External APIs
```

### Key Design Patterns
- **Strategy Pattern:** Pluggable indicators implementing IIndicator interface
- **Factory Pattern:** IndicatorRegistry for indicator instantiation
- **Repository Pattern:** Data persistence abstraction
- **Gateway Pattern:** External API abstraction (IMarketDataGateway, IComplianceGateway, IStockUniverseGateway)

### Non-Functional Requirements (P0)
- **Halal Compliance:** 100% accuracy, ZERO false negatives
- **Response Time:** 95% of operations <5 seconds
- **Extensibility:** Add new indicator in <4 hours
- **Test Coverage:** >80% unit test coverage
- **Portability:** Windows, macOS, Linux support

## Technical Indicators

### MCDX (Multi-Color Divergence Index)
- Detects institutional accumulation vs retail distribution
- Signals: "Banker" (strong buy), "Smart Money" (buy), "Neutral", "Retail" (avoid)
- Requires: 30+ days OHLCV data
- Performance: <0.5s per stock calculation

### B-XTrender
- Momentum-trend indicator with color coding
- Signals: Green (bullish), Yellow (neutral), Red (bearish)
- Requires: 50+ days close price data
- Performance: <0.3s per stock calculation

### Simple Moving Average (SMA)
- Standard MA with configurable periods (20, 50, 200)
- Conditions: Price > SMA(X), SMA(X) > SMA(Y) crossovers

## Halal Screening (ZERO FALSE NEGATIVES)

### Prohibited Sectors (Auto-Exclude)
- Defense/Weapons, Gambling, Alcohol, Tobacco, Pornography, Conventional Banking, Pork Production

### Financial Ratios (Phase 2)
- Debt/Market Cap <33%, Cash/Market Cap <33%, Accounts Receivable/Assets <50%, Impure Income <5%

### Data Sources
- Primary: Zoya API, Musaffa API
- Fallback: Local CSV database
- Cache: 30 days TTL

## Service Layer Architecture

### Core Services
1. **ScreeningService:** Orchestrates universe selection → compliance filtering → strategy application
2. **StrategyService:** CRUD for strategies + evaluation engine
3. **PortfolioService:** Holdings management + strategy validation

### Gateway Abstractions
- **IMarketDataGateway:** Yahoo Finance (primary), Alpha Vantage (fallback)
- **IComplianceGateway:** Zoya/Musaffa APIs + local database
- **IStockUniverseGateway:** Static files (exchanges), API queries (sectors/market cap), ETF providers

## Data Flow (Critical Path)

```
User Request → Universe Selection (Exchange/Sector/ETF/Custom) →
Halal Filter (Compliance Gateway) → Parallel Technical Data Fetch →
Indicator Calculation → Strategy Evaluation → Results Display
```

## Infrastructure Requirements

- **Caching:** L1 (memory LRU) + L2 (SQLite) with TTLs (1h-30d depending on data type)
- **Rate Limiting:** Token bucket algorithm per API provider
- **Database:** SQLite for portfolios, strategies, cache
- **Security:** API keys encrypted at rest, no credentials in logs

## Success Metrics
- Screen 100+ stocks in <2 minutes ✓
- Halal compliance false positive rate: 0% ✓
- Strategy execution accuracy: 100% ✓
- User satisfaction: >4.0/5.0

## Key Constraints
- EU/UCITS regulatory compliance required
- Long-term momentum focus (not day trading)
- CLI-first (web migration planned for Phase 2)
- Single-user local storage (no cloud sync in MVP)

---

**For detailed technical specifications, see:**
- `docs/TRD_Part1_Architecture.md` through `docs/TRD_Part5_Implementation_Testing.md`
- Complete API contracts in PRD Section 6A (PRD.md lines 776-1708)
- Full product requirements: `PRD.md`
