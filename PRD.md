# Product Requirements Document: Stock Strategy CLI

**Version:** 1.1
**Last Updated:** 2025-11-10
**Product Name:** stock-strategy-cli (stock-friend-cli)
**Status:** Ready for Architecture Review
**Target Audience:** System Architect
**Review Focus:** Technical architecture, system design, API contracts, data flows

---

## 1. Executive Summary

### 1.1 Product Overview

Stock Strategy CLI is a Python-based command-line tool designed for European retail investors seeking halal-compliant, momentum-based investment opportunities. The tool automates stock discovery and technical analysis by screening entire exchanges, market sectors, or ETF holdings against user-defined investment strategies while enforcing strict ethical (halal) and regulatory (EU/UCITS) compliance. Users can scan thousands of stocks across major indices (S&P 500, NASDAQ, Russell 2000) without manual stock research.

### 1.2 Core Value Proposition

- **Autonomous Stock Discovery:** Automatically screens entire exchanges (S&P 500, NASDAQ, Russell 2000) eliminating the need for manual stock discovery or ETF selection
- **Universe-Based Screening:** Screen thousands of stocks across entire markets, sectors, or market cap ranges - not limited to ETF holdings
- **Automated Strategy Execution:** Eliminates manual screening of hundreds of stocks against complex technical indicators
- **Ethical Compliance First:** Automatically filters non-halal stocks before any analysis
- **Pluggable Strategy Architecture:** Supports multiple investment strategies that can be easily added, modified, or removed
- **EU Regulatory Compliance:** Ensures all recommendations are accessible to European retail investors
- **Long-term Momentum Focus:** Identifies high-conviction opportunities using dual-indicator confirmation system

### 1.3 Success Metrics

- Time to screen 100+ stocks: < 2 minutes
- False positive rate for halal compliance: 0%
- Strategy execution accuracy: 100% (all conditions correctly evaluated)
- User satisfaction with CLI experience: > 4.0/5.0
- Portfolio tracking accuracy: 100%

---

## 2. Architectural Overview (For System Architect)

### 2.1 Key Architectural Challenges

**1. Pluggable Strategy System**
- **Challenge:** Design a flexible architecture where investment strategies can be added, modified, or removed without changing core system logic
- **Requirements:** Strategy evaluation engine must be completely decoupled from specific indicator implementations
- **Success Criteria:** Adding a new indicator requires zero changes to the strategy engine

**2. Multi-Source Data Integration**
- **Challenge:** Integrate data from multiple external APIs with varying schemas, rate limits, and reliability
- **Requirements:** Abstraction layer for data sources with failover, caching, and rate limiting
- **Success Criteria:** Swapping data providers requires changes only to the data access layer

**3. Performance at Scale**
- **Challenge:** Screen 500+ stocks in reasonable time (<10 minutes) while respecting API rate limits
- **Requirements:** Async/parallel data fetching, intelligent caching, batch processing
- **Success Criteria:** 500 stocks screened in <600 seconds with <5% API errors

**4. Halal Compliance Enforcement**
- **Challenge:** Guarantee zero false negatives (never recommend non-compliant stocks)
- **Requirements:** Fail-safe filtering architecture with audit trails
- **Success Criteria:** 100% halal filtering accuracy, comprehensive logging of all exclusions

**5. Extensibility for Web Migration**
- **Challenge:** Design CLI tool with eventual web application migration in mind
- **Requirements:** Business logic separated from presentation layer
- **Success Criteria:** Core engine can be extracted as standalone library with no CLI dependencies

### 2.2 System Boundaries

**In Scope:**
- Stock screening and analysis engine
- Investment strategy management system
- Portfolio tracking and validation
- Halal compliance filtering
- Local data storage and caching
- CLI user interface

**Out of Scope (Initial Release):**
- Real-time streaming data
- Trade execution capabilities
- Multi-user/cloud synchronization
- Web/mobile interfaces
- Backtesting engine (Phase 2)
- Financial ratio screening (Phase 2)

### 2.3 Critical Non-Functional Requirements

| Requirement Category | Specification | Priority |
|---------------------|---------------|----------|
| **Response Time** | 95% of operations complete in <5 seconds | P0 |
| **Availability** | Graceful degradation when APIs unavailable | P0 |
| **Data Accuracy** | 100% halal compliance filtering accuracy | P0 |
| **Extensibility** | Add new indicator in <4 hours development time | P0 |
| **Maintainability** | >80% unit test coverage, clear separation of concerns | P0 |
| **Security** | API keys encrypted at rest, no credentials in logs | P1 |
| **Scalability** | Support 1000+ stocks in portfolio without performance degradation | P1 |
| **Portability** | Run on Windows, macOS, Linux without platform-specific code | P1 |

### 2.4 Key Integration Points

| Integration | Type | Purpose | Criticality |
|-------------|------|---------|-------------|
| Yahoo Finance API | External REST | Stock price data (OHLCV) | Critical |
| Halal Screening API (Zoya/Musaffa) | External REST | Shariah compliance verification | Critical |
| **Stock Universe Provider** | **External REST / Static Files** | **Exchange/index constituent lists (S&P 500, NASDAQ, Russell 2000)** | **Critical** |
| **Sector/Market Cap Provider** | **External REST** | **Stock lists by sector and market capitalization** | **High** |
| ETF Holdings Provider | Web scraping / REST | Fund holdings data | High |
| Fundamental Data API | External REST | Financial metrics (P/E, EPS, etc.) | Medium |
| Local SQLite DB | Internal | Portfolio, strategies, cache storage | Critical |
| File System (JSON/CSV) | Internal | Configuration, strategy definitions, and static universe data | High |

### 2.5 Data Flow Summary

```
User Input (CLI)
    ↓
Application Service Layer (Orchestration)
    ↓
Strategy Engine (Business Logic)
    ↓
Indicator Implementations (Calculations)
    ↓
Data Access Layer (API Abstraction)
    ↓
Cache Layer (Performance)
    ↓
External APIs / Local Storage
```

**Critical Path:** User requests screening → Service fetches stock universe (exchange/sector/ETF/custom) → Halal filter applied → Technical data fetched (parallelized) → Indicators calculated → Strategy evaluated → Results displayed

---

## 3. Product Vision & Goals

### 3.1 Vision Statement

To empower ethical investors with institutional-grade technical analysis tools accessible through an intuitive command-line interface, enabling disciplined, data-driven investment decisions that align with Islamic finance principles and European regulatory requirements.

### 3.2 Product Goals

**Primary Goals:**
1. Enable rapid screening of entire exchanges, sectors, or custom stock universes for halal-compliant investment opportunities
2. Eliminate manual stock discovery by providing automated screening across thousands of stocks
3. Provide flexible, user-configurable investment strategy execution
4. Maintain continuous portfolio monitoring with day-to-day strategy analysis
5. Ensure 100% compliance with halal screening criteria
6. Deliver professional-grade technical indicator implementation (MCDX, B-XTrender)

**Secondary Goals:**
1. Educate users on momentum investing principles through clear signal explanations
2. Build foundation for future web-based visualization platform
3. Create extensible architecture supporting future indicator additions
4. Provide historical performance context for strategy validation

---

## 4. Target Users

### 4.1 Primary Persona: The Ethical Momentum Investor

**Profile:**
- **Location:** European Union (primary focus on retail investors in Germany, France, Netherlands, UK post-Brexit considerations)
- **Investment Philosophy:** Long-term wealth building with momentum opportunism
- **Religious/Ethical Requirements:** Strict halal compliance
- **Technical Proficiency:** Comfortable with command-line tools, understands basic technical analysis
- **Investment Experience:** Intermediate to advanced (understands P/E ratios, moving averages, momentum concepts)
- **Time Constraints:** Limited time for manual screening; needs automation

**Pain Points:**
- Manual screening of 500+ S&P stocks is time-prohibitive
- Difficulty identifying "smart money" accumulation signals
- Lack of tools combining halal screening with technical analysis
- Uncertainty about EU accessibility of certain securities
- Challenge tracking multiple positions against evolving strategies

**User Stories:**
1. "As an investor, I want to screen all S&P 500 stocks for halal-compliant momentum opportunities so I can find new positions without manual analysis."
2. "As a Muslim investor, I need automatic exclusion of haram stocks so I never accidentally analyze prohibited companies."
3. "As a portfolio holder, I want daily strategy checks on my positions so I know when momentum shifts."
4. "As a strategy experimenter, I want to modify indicator thresholds so I can optimize for current market conditions."

### 4.2 Secondary Persona: The Strategy Developer

**Profile:**
- Advanced technical analyst
- Interested in backtesting custom indicator combinations
- May contribute new indicators or strategies to the tool

---

## 5. Detailed Feature Requirements

### 5.1 Feature 1: Stock Screening Engine

**Priority:** P0 (Must Have - MVP)

**Description:**
Automated screening of stocks from multiple sources (entire exchanges, sectors, market cap ranges, ETF holdings, or custom lists) through a two-stage filtering process: (1) halal compliance, (2) investment strategy criteria. This eliminates the need for users to manually discover stocks or know which ETF to screen.

**User Flow:**
```
1. User selects "Screen Stocks" from main menu
2. System prompts: "Select screening universe:"

   [1] Screen by Exchange/Index
       • S&P 500 (503 stocks)
       • NASDAQ 100 (100 stocks)
       • NASDAQ Composite (3000+ stocks)
       • Russell 2000 (2000 stocks)
       • Dow Jones Industrial (30 stocks)
       • All US Stocks (5000+ stocks)

   [2] Screen by Sector
       • Technology
       • Healthcare
       • Financial Services
       • Consumer Discretionary
       • Consumer Staples
       • Industrials
       • Energy
       • Real Estate
       • Utilities
       • Materials
       • Communication Services

   [3] Screen by Market Cap
       • Large Cap (>$10B)
       • Mid Cap ($2B-$10B)
       • Small Cap ($200M-$2B)
       • Micro Cap (<$200M)

   [4] Screen ETF Holdings
       • Enter ETF ticker (e.g., SPY, QQQ, VTI, IWDA.AS)

   [5] Custom Stock List
       • Upload CSV file with tickers
       • Manually enter comma-separated tickers

3. User selects option (e.g., "[1] S&P 500")
4. System prompts: "Select investment strategy:"
   - Default Strategy (MCDX + B-XTrender)
   - Custom Strategy 1
   - Custom Strategy 2
   - [Create New Strategy]
5. System displays progress:
   "Screening 503 stocks from S&P 500...
   ✓ Retrieved ticker universe
   ✓ Halal screening: 387 compliant stocks identified (116 excluded)
   ✓ Fetching technical data for 387 stocks...
   ✓ Applying strategy criteria...

   RESULTS: 12 BUY SIGNALS FOUND"
6. System displays results table (see 4.1.3)
7. User can export results, view details, or add to portfolio
```

**Acceptance Criteria:**

**AC1: Stock Universe Retrieval**
- GIVEN a screening universe selection (exchange/index, sector, market cap, ETF, or custom list)
- WHEN user initiates screening
- THEN system retrieves appropriate ticker list:
  - For exchanges/indices: Load pre-defined constituent lists (S&P 500, NASDAQ, etc.)
  - For sectors: Query market data provider for stocks in specified sector
  - For market cap: Query market data provider for stocks within cap range
  - For ETFs: Retrieve current holdings list with stock tickers and weights
  - For custom lists: Parse user-provided CSV or comma-separated tickers
- AND system validates all tickers are legitimate stock symbols
- AND system handles API errors gracefully with retry logic (3 attempts)
- AND system caches universe data appropriately:
  - Exchange/index constituents: 30 days (updated monthly)
  - Sector listings: 7 days (updated weekly)
  - ETF holdings: 30 days (updated monthly)
  - Market cap queries: 24 hours (updated daily)

**AC2: Halal Compliance Filtering (Stage 1)**
- GIVEN a list of stock tickers from the selected universe (exchange, sector, ETF, etc.)
- WHEN halal screening is applied
- THEN system excludes ALL stocks in prohibited sectors (see Section 5)
- AND system displays count: "X compliant / Y excluded / Z total"
- AND system logs excluded stocks with exclusion reason
- AND user can optionally view excluded stocks list

**AC3: Strategy Application (Stage 2)**
- GIVEN halal-compliant stocks from Stage 1
- WHEN selected investment strategy is applied
- THEN system fetches required technical indicator data for each stock
- AND system evaluates ALL strategy conditions for each stock
- AND system identifies stocks where ALL conditions are met
- AND system handles missing data (e.g., newly IPO'd stocks with insufficient history)

**AC4: Results Display**
- GIVEN screening results
- THEN system displays results in formatted table:
```
BUY SIGNALS FOUND (12 matches):

Ticker | Company Name           | Sector     | MCDX Signal | B-XTrender | Price  | Match %
-------|------------------------|------------|-------------|------------|--------|--------
MSFT   | Microsoft Corp         | Technology | Banker      | Green      | $425   | 100%
AAPL   | Apple Inc              | Technology | Banker      | Green      | $189   | 100%
NVDA   | NVIDIA Corporation     | Technology | Banker      | Green      | $502   | 100%
...

Press 'Enter' for details | 'E' to export | 'A' to add all to portfolio | 'Q' to quit
```

**AC5: Performance Requirements**
- Screening 500 stocks completes in < 120 seconds
- Progress indicator updates every 10 stocks processed
- API rate limits respected (queued requests if necessary)

**AC6: EU Accessibility Verification**
- For each BUY SIGNAL result, system verifies:
  - Stock has KID documentation OR
  - UCITS-compliant ETF alternative exists
- If not EU-accessible, result is flagged: "[Non-EU] *Alternative needed"

**AC7: Error Handling**
- Invalid ticker: "Error: [TICKER] not found. Please verify ticker symbol."
- API unavailable: "Error: Unable to reach data provider. Retrying... (X/3)"
- No matches found: "No stocks met strategy criteria. Consider adjusting thresholds."

---

### 5.2 Feature 2: Investment Strategy Management

**Priority:** P0 (Must Have - MVP)

**Description:**
User interface for viewing, creating, modifying, and deleting investment strategies composed of technical indicators and fundamental data thresholds.

**User Flow - View Strategies:**
```
1. User selects "Investment Strategies" from main menu
2. System displays:

INVESTMENT STRATEGIES
=====================

[1] Default Momentum Strategy ⭐ (active)
    Description: Dual-indicator confirmation for banker accumulation
    Indicators:
      • MCDX = "Banker" OR "Smart Money"
      • B-XTrender = Green
    Created: 2025-01-15 | Last Used: 2025-11-10

[2] Aggressive Growth Strategy
    Description: High-growth stocks with strong momentum
    Indicators:
      • MCDX = "Banker"
      • B-XTrender = Green
      • SMA(20) > SMA(50) [Golden Cross]
    Fundamentals:
      • EPS Growth > 20%
      • P/E Ratio < 30
    Created: 2025-10-03 | Last Used: 2025-11-08

[3] Value Momentum Hybrid
    [Details...]

Options: [V]iew Details | [C]reate New | [E]dit | [D]elete | [B]ack
```

**User Flow - Create New Strategy:**
```
1. User selects "Create New Strategy"
2. System prompts: "Strategy Name:"
   User: "AI Semiconductor Play"
3. System prompts: "Description (optional):"
   User: "Target AI chip makers with institutional accumulation"
4. System displays indicator selection:

SELECT INDICATORS (Press Space to select, Enter to confirm):
Technical Indicators:
[ ] Simple Moving Average (SMA)
[X] MCDX (Multi-Color Divergence Index)
[X] B-XTrender (Momentum Trend)
[ ] RSI (Relative Strength Index)
[ ] MACD (Moving Average Convergence Divergence)

Fundamental Filters:
[X] EPS (Earnings Per Share)
[X] P/E Ratio (Price to Earnings)
[ ] Revenue Growth
[ ] Debt-to-Equity Ratio

5. For each selected indicator, system prompts for thresholds:

MCDX Configuration:
  Signal Type:
    [X] Banker (institutional accumulation)
    [X] Smart Money
    [ ] Neutral
    [ ] Retail (ignore)

B-XTrender Configuration:
  Color Signal:
    [X] Green (bullish)
    [ ] Yellow (neutral)
    [ ] Red (bearish)

EPS Configuration:
  Condition: [Greater Than] [Equal To] [Less Than]
  Value: 2.50
  Unit: [Dollars] [Growth %]

6. System confirms:
"Strategy 'AI Semiconductor Play' created successfully.
 Set as default strategy? [Y/n]"
```

**Acceptance Criteria:**

**AC1: Strategy Listing**
- GIVEN user accesses Investment Strategy menu
- THEN system displays all saved strategies with metadata:
  - Strategy name
  - Description
  - Number of indicators/conditions
  - Creation date
  - Last used date
  - Active/default indicator

**AC2: Default Strategy**
- System includes pre-configured "Default Momentum Strategy"
- Default strategy cannot be deleted (only modified)
- Default strategy implements: MCDX = "Banker" AND B-XTrender = Green

**AC3: Strategy Creation - Indicator Selection**
- User can select multiple indicators from categorized list:
  - **Technical Indicators:** SMA, MCDX, B-XTrender, RSI, MACD
  - **Fundamental Filters:** EPS, P/E, Revenue Growth, Debt-to-Equity, Market Cap
- Each indicator is selectable via checkbox/toggle interface

**AC4: Strategy Creation - Threshold Configuration**
- For MCDX:
  - User selects signal types to match: [Banker, Smart Money, Neutral, Retail]
  - Multiple selections use OR logic (match any selected)
- For B-XTrender:
  - User selects color signals to match: [Green, Yellow, Red]
  - Multiple selections use OR logic
- For SMA:
  - User configures period (default: 20, 50, 200)
  - User sets conditions: Price > SMA(20), SMA(20) > SMA(50), etc.
- For Fundamental Data:
  - User sets comparison operator: [>, <, =, >=, <=]
  - User sets numeric threshold value

**AC5: Strategy Logic Combination**
- ALL selected indicators/conditions must be met (AND logic)
- Within multi-value indicators (e.g., MCDX signals), OR logic applies
- Example: (MCDX = Banker OR Smart Money) AND (B-XTrender = Green) AND (EPS > 2.0)

**AC6: Strategy Persistence**
- Strategies saved to local configuration file (JSON format)
- Strategies persist across CLI sessions
- Strategies portable (can be exported/imported)

**AC7: Strategy Validation**
- System prevents creation of empty strategies (minimum 1 indicator required)
- System validates numeric thresholds (no negative P/E, etc.)
- System warns if strategy is too restrictive (optional: run quick test on sample data)

**AC8: Strategy Modification**
- User can edit existing strategies (opens editor with current settings pre-filled)
- Modifications create new version (version history tracked)
- User can revert to previous version

**AC9: Strategy Deletion**
- User can delete custom strategies (with confirmation prompt)
- Default strategy cannot be deleted
- If active strategy is deleted, system reverts to default

---

### 5.3 Feature 3: Portfolio Management

**Priority:** P0 (Must Have - MVP)

**Description:**
Persistent portfolio tracking with fundamental data display and day-to-day strategy validation.

**User Flow - View Portfolio:**
```
1. User selects "Portfolio" from main menu
2. System displays:

MY PORTFOLIO (8 holdings)
Last Updated: 2025-11-10 10:23 EST
===========================================

Ticker | Company            | Shares | Avg Cost | Current | Gain/Loss | P/E  | EPS   | Sector
-------|-----------------------|--------|----------|---------|-----------|------|-------|----------
MSFT   | Microsoft Corp        | 50     | $380.00  | $425.00 | +$2,250   | 35.2 | $12.07| Tech
AAPL   | Apple Inc             | 100    | $175.00  | $189.00 | +$1,400   | 31.8 | $5.96 | Tech
NVDA   | NVIDIA Corp           | 25     | $450.00  | $502.00 | +$1,300   | 68.4 | $7.34 | Tech
GOOGL  | Alphabet Inc          | 40     | $138.00  | $142.00 | +$160     | 25.6 | $5.55 | Tech
...

Total Portfolio Value: $87,450
Total Gain/Loss: +$12,380 (+16.5%)

Options: [R]un Strategy Check | [A]dd Stock | [D]elete Stock | [E]xport | [B]ack
```

**User Flow - Run Strategy Check:**
```
1. User presses 'R' for "Run Strategy Check"
2. System prompts: "Select strategy to apply:"
   - Default Momentum Strategy
   - Custom Strategy 1
   - [All Strategies]
3. User selects "Default Momentum Strategy"
4. System displays:

STRATEGY CHECK: Default Momentum Strategy
==========================================

✅ MSFT - Microsoft Corp
   Status: BUY SIGNAL MAINTAINED
   • MCDX: Banker (strong accumulation)
   • B-XTrender: Green
   Recommendation: HOLD (conditions still met)

✅ AAPL - Apple Inc
   Status: BUY SIGNAL MAINTAINED
   • MCDX: Banker
   • B-XTrender: Green
   Recommendation: HOLD

⚠️  GOOGL - Alphabet Inc
   Status: SIGNAL WEAKENING
   • MCDX: Neutral (changed from Banker on 2025-11-08)
   • B-XTrender: Yellow (changed from Green on 2025-11-09)
   Recommendation: MONITOR (consider exit if deteriorates further)

❌ TSLA - Tesla Inc
   Status: BUY SIGNAL LOST
   • MCDX: Retail (distribution detected)
   • B-XTrender: Red (bearish since 2025-11-06)
   Recommendation: CONSIDER EXIT (no longer meets criteria)

Summary: 5 Strong | 2 Weakening | 1 Lost Signal

Press Enter to return to portfolio menu
```

**Acceptance Criteria:**

**AC1: Portfolio Persistence**
- Portfolio data stored locally in JSON format
- Portfolio persists across CLI sessions
- Support multiple portfolios (optional: "Portfolio 1", "Portfolio 2")

**AC2: Add Stock to Portfolio**
- User enters ticker symbol
- System validates stock exists and is halal-compliant
- User enters: number of shares, average purchase price
- System calculates current value and gain/loss
- System confirms addition and displays updated portfolio

**AC3: Remove Stock from Portfolio**
- User selects stock by number or ticker
- System prompts for confirmation: "Remove [TICKER] from portfolio? [Y/n]"
- System removes stock and displays updated portfolio

**AC4: Fundamental Data Display**
- For each portfolio stock, display:
  - **Real-time:** Current price, daily % change
  - **Fundamentals:** P/E ratio, EPS, Market Cap, Sector
  - **Performance:** Total gain/loss ($), Total gain/loss (%)
  - **Position:** Number of shares, average cost basis

**AC5: Strategy Validation on Portfolio**
- User can apply any saved strategy to portfolio holdings
- System fetches current indicator values for each stock
- System evaluates each stock against strategy conditions
- Results categorized:
  - ✅ **Strong:** All conditions met (HOLD recommended)
  - ⚠️ **Weakening:** Some conditions no longer met (MONITOR)
  - ❌ **Lost Signal:** Most/all conditions failed (CONSIDER EXIT)

**AC6: Change Detection**
- System compares current indicator values to previous check
- Highlights changes: "MCDX: Banker → Neutral (changed 2 days ago)"
- Alerts user to significant deteriorations

**AC7: Portfolio Summary Statistics**
- Total portfolio value (current market value)
- Total gain/loss ($ and %)
- Sector allocation breakdown
- Top performer / worst performer

**AC8: Export Portfolio**
- Export portfolio to CSV format
- Include all fundamental data and current positions
- Filename format: portfolio_YYYY-MM-DD.csv

**AC9: Batch Operations**
- User can run strategy check on all holdings at once
- System processes each holding and generates comprehensive report
- Processing time < 30 seconds for 20 holdings

---

### 5.4 Feature 4: Main Menu & Navigation

**Priority:** P0 (Must Have - MVP)

**User Flow:**
```
STOCK STRATEGY CLI
v1.0.0 | Halal Momentum Analysis Tool
==========================================

[1] Screen Stocks
    Scan ETF holdings for buy signals using investment strategies

[2] Investment Strategies
    View, create, or modify investment strategies

[3] Portfolio
    Manage your holdings and run strategy checks

[4] Settings
    Configure API keys, preferences, and data sources

[5] Help & Documentation

[Q] Quit

Select option [1-5, Q]:
```

**Acceptance Criteria:**

**AC1: Clear Menu Structure**
- Main menu displays on CLI launch
- Numbered options with clear descriptions
- Navigation via number keys or letter shortcuts

**AC2: Navigation Flow**
- User can return to main menu from any sub-menu via 'B' (Back) or 'Q' (Quit to Main Menu)
- Consistent navigation patterns across all features
- Breadcrumb display: "Main Menu > Investment Strategies > Create New"

**AC3: Help System**
- Context-sensitive help available via '?' key in any menu
- Help displays keyboard shortcuts and option explanations

**AC4: Settings Menu**
- Configure API keys (stored securely)
- Set default strategy
- Configure data refresh intervals
- Set display preferences (currency, date format)

---

## 6. Halal Screening Requirements

### 6.1 Prohibited Business Activities

The system MUST automatically exclude stocks whose primary business operations include:

#### 6.1.1 Strictly Prohibited Sectors

**Defense & Weapons Manufacturing:**
- Companies manufacturing weapons, military equipment, ammunition
- Defense contractors with >5% revenue from weapons systems
- Examples to exclude: Lockheed Martin (LMT), Raytheon (RTX), BAE Systems (BA.L), Northrop Grumman (NOC)

**Gambling & Gaming:**
- Casinos and casino operators
- Sports betting platforms
- Online gambling platforms
- Lottery operators
- Examples to exclude: MGM Resorts (MGM), Caesars Entertainment (CZR), DraftKings (DKNG), Flutter Entertainment (FLTR.L)

**Alcohol Production & Distribution:**
- Alcoholic beverage manufacturers
- Breweries and distilleries
- Alcohol-focused distributors (>5% revenue from alcohol)
- Examples to exclude: Anheuser-Busch InBev (BUD), Diageo (DEO), Constellation Brands (STZ), Pernod Ricard (RI.PA)

**Tobacco:**
- Tobacco product manufacturers
- Cigarette and cigar producers
- Vaping/e-cigarette companies
- Examples to exclude: Philip Morris (PM), Altria (MO), British American Tobacco (BTI)

**Pornography & Adult Entertainment:**
- Adult content producers and distributors
- Adult entertainment venues
- Any company with primary business in adult content

**Conventional Banking & Interest-Based Finance:**
- Traditional interest-based banks
- Subprime lending institutions
- Payday loan companies
- Examples to exclude: JPMorgan Chase (JPM), Bank of America (BAC), Wells Fargo (WFC), Citigroup (C), Goldman Sachs (GS)

**Pork Production:**
- Pork processing and production companies
- Companies with >5% revenue from pork products
- Example: Smithfield Foods (owned by WH Group, 0288.HK)

### 6.2 Financial Screening Criteria (Shariah Ratios)

In addition to business activity screening, the system should implement financial ratio thresholds based on AAOIFI (Accounting and Auditing Organization for Islamic Financial Institutions) standards:

**Debt Ratio:**
- Total debt / Market capitalization < 33%
- OR: Total debt / Total assets < 30%

**Cash & Interest-Bearing Securities:**
- (Cash + Interest-bearing securities) / Market capitalization < 33%

**Accounts Receivable:**
- Accounts receivable / Total assets < 50%

**Impure Income (Revenue Purification):**
- Income from non-compliant sources / Total revenue < 5%
- If 1-5% impure income: Stock is permissible but investor must donate equivalent percentage of dividends to charity

**Implementation Note:**
Phase 1 (MVP) focuses on business activity screening. Financial ratio screening can be implemented in Phase 2 as an optional enhanced filter.

### 6.3 Halal Screening Data Sources

**Primary Data Source:**
- **Zoya API** (zoya.finance) - Provides halal screening data
- **Musaffa API** (musaffa.com) - Alternative halal screening provider
- **Manual Classification Database:** Fallback CSV file mapping tickers to compliance status

**Screening Process:**
1. Query halal screening API with stock ticker
2. If API returns "Non-Compliant" → EXCLUDE from analysis
3. If API returns "Compliant" → Proceed to strategy evaluation
4. If API returns "Questionable" or "No Data" → Flag for manual review, optionally exclude by default

### 6.4 Halal Screening Acceptance Criteria

**AC1: Zero False Negatives**
- System MUST NEVER recommend a non-compliant stock
- When in doubt (missing data), system defaults to exclusion
- User can override only with explicit confirmation: "Force include [TICKER]? This stock has unverified compliance status. [Yes, I confirm / No]"

**AC2: Exclusion Transparency**
- System logs all exclusions with reason code:
  - "DEFENSE" - Defense/weapons sector
  - "GAMBLING" - Gaming/gambling sector
  - "ALCOHOL" - Alcohol production
  - "TOBACCO" - Tobacco products
  - "ADULT" - Adult entertainment
  - "BANKING" - Conventional banking
  - "PORK" - Pork production
  - "DEBT_RATIO" - Excessive debt (if financial screening enabled)
  - "IMPURE_INCOME" - Excessive non-compliant revenue

**AC3: User Visibility**
- User can view list of excluded stocks: "Show excluded stocks? [Y/n]"
- Excluded stocks displayed with reason: "JPM - Excluded: BANKING (Conventional bank)"

**AC4: Compliance Database Updates**
- System checks for halal screening data updates weekly
- User can manually trigger compliance database refresh
- System caches compliance status for 30 days

**AC5: Multi-Source Verification (Optional Enhancement)**
- Cross-reference multiple halal screening providers
- Flag discrepancies: "Warning: Zoya reports compliant, Musaffa reports questionable"

---

## 6A. Service Layer Architecture & API Contracts

### 6A.1 Core Services Overview

The system should be architected around distinct service layers that communicate through well-defined interfaces:

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI PRESENTATION LAYER                     │
│                  (Rich, Typer, Questionary)                   │
│                                                               │
│  • Input validation and sanitization                          │
│  • Output formatting and visualization                        │
│  • User interaction flows                                     │
│  • Progress indication                                        │
└────────────────────────┬──────────────────────────────────────┘
                         │
┌────────────────────────▼──────────────────────────────────────┐
│              APPLICATION ORCHESTRATION LAYER                   │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Screening   │  │  Strategy    │  │  Portfolio   │      │
│  │  Service     │  │  Service     │  │  Service     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                   STRATEGY EXECUTION ENGINE                   │
│                       (Business Logic Core)                   │
│                                                               │
│  • StrategyEvaluator: Evaluates strategies against data      │
│  • IndicatorRegistry: Manages available indicators           │
│  • ConditionEvaluator: Evaluates individual conditions       │
│  • ComplianceFilter: Enforces halal filtering rules          │
│                                                               │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                INDICATOR CALCULATION LAYER                    │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   MCDX   │  │ B-XTrender│  │   SMA    │  │  [New    │    │
│  │ Indicator│  │ Indicator │  │ Indicator│  │ Indicators]   │
│  └────┬─────┘  └────┬──────┘  └────┬─────┘  └────┬─────┘    │
│       │             │              │             │           │
│       └──────────All Implement IIndicator────────┘           │
│                                                               │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                    DATA ACCESS LAYER                          │
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ MarketDataGateway│  │ ComplianceGateway│                 │
│  └────────┬─────────┘  └────────┬─────────┘                 │
│           │                      │                           │
│  ┌────────▼─────────┐  ┌────────▼─────────┐                 │
│  │ StockUniverse    │  │ FundamentalData  │                 │
│  │ Gateway          │  │ Gateway          │                 │
│  └──────────────────┘  └──────────────────┘                 │
│                                                               │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                        │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ CacheManager │  │ RateLimiter  │  │ ErrorHandler │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Repository   │  │ ConfigManager│  │ Logger       │      │
│  │ (SQLite)     │  │ (JSON)       │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                    EXTERNAL SYSTEMS                           │
│                                                               │
│  • Yahoo Finance API                                         │
│  • Halal Screening APIs (Zoya, Musaffa)                     │
│  • Stock Universe Data Sources (S&P, NASDAQ, Russell lists) │
│  • ETF Holdings Data Sources                                 │
│  • Fundamental Data APIs                                     │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 6A.2 Service Interface Definitions

#### ScreeningService

**Purpose:** Orchestrates the stock screening workflow from universe selection to result delivery.

**Key Methods:**
```python
class ScreeningService:
    def screen_universe(
        self,
        universe_config: UniverseConfig,
        strategy_id: str,
        include_excluded: bool = False
    ) -> ScreeningResult:
        """
        Screen a stock universe against a strategy.

        Args:
            universe_config: Configuration specifying the stock universe
                           (exchange, sector, market cap, ETF, or custom list)
            strategy_id: ID of strategy to apply
            include_excluded: Whether to include halal-excluded stocks in results

        Returns:
            ScreeningResult containing matches, exclusions, and metadata

        Raises:
            UniverseNotFoundException: If universe cannot be retrieved
            StrategyNotFoundException: If strategy_id doesn't exist
            DataProviderException: If critical data sources unavailable
        """

    def screen_exchange(
        self,
        exchange: ExchangeType,
        strategy_id: str,
        include_excluded: bool = False
    ) -> ScreeningResult:
        """Convenience method for screening a specific exchange/index."""

    def screen_sector(
        self,
        sector: SectorType,
        strategy_id: str,
        include_excluded: bool = False
    ) -> ScreeningResult:
        """Convenience method for screening a specific sector."""

    def screen_etf(
        self,
        etf_ticker: str,
        strategy_id: str,
        include_excluded: bool = False
    ) -> ScreeningResult:
        """Convenience method for screening ETF holdings."""

    def screen_custom_list(
        self,
        tickers: List[str],
        strategy_id: str,
        include_excluded: bool = False
    ) -> ScreeningResult:
        """Convenience method for screening a custom ticker list."""

    def get_screening_progress(self, screening_id: str) -> ScreeningProgress:
        """Return progress information for long-running screening operation."""

    def export_results(
        self,
        screening_result: ScreeningResult,
        format: ExportFormat
    ) -> Path:
        """Export screening results to file (CSV, JSON, etc.)."""
```

**Data Models:**
```python
@dataclass
class UniverseConfig:
    """Configuration for specifying which stocks to screen."""
    universe_type: UniverseType  # Enum: EXCHANGE, SECTOR, MARKET_CAP, ETF, CUSTOM

    # Exchange/Index screening
    exchange: Optional[ExchangeType] = None

    # Sector screening
    sector: Optional[SectorType] = None

    # Market cap screening
    min_market_cap: Optional[Decimal] = None
    max_market_cap: Optional[Decimal] = None

    # ETF screening
    etf_ticker: Optional[str] = None

    # Custom list screening
    custom_tickers: Optional[List[str]] = None

class UniverseType(Enum):
    EXCHANGE = "exchange"
    SECTOR = "sector"
    MARKET_CAP = "market_cap"
    ETF = "etf"
    CUSTOM = "custom"

@dataclass
class ScreeningResult:
    universe_config: UniverseConfig
    universe_description: str  # Human-readable: "S&P 500", "Technology Sector", etc.
    strategy_id: str
    timestamp: datetime
    total_stocks: int
    compliant_stocks: int
    excluded_stocks: int
    matches: List[StockMatch]
    exclusions: List[StockExclusion]
    processing_time_seconds: float

@dataclass
class StockMatch:
    ticker: str
    company_name: str
    sector: str
    indicator_signals: Dict[str, Any]  # e.g., {"mcdx": "Banker", "xtrender": "Green"}
    match_confidence: float  # 0.0 to 1.0
    current_price: Decimal
    fundamental_data: Optional[FundamentalData]
    eu_accessible: bool

@dataclass
class StockExclusion:
    ticker: str
    company_name: str
    exclusion_reason: ExclusionReason  # Enum: DEFENSE, GAMBLING, ALCOHOL, etc.
    exclusion_details: str
```

#### StrategyService

**Purpose:** Manages investment strategy CRUD operations and evaluation logic.

**Key Methods:**
```python
class StrategyService:
    def create_strategy(self, strategy_config: StrategyConfig) -> Strategy:
        """Create and validate a new investment strategy."""

    def update_strategy(self, strategy_id: str, updates: StrategyConfig) -> Strategy:
        """Modify existing strategy (creates new version)."""

    def delete_strategy(self, strategy_id: str) -> bool:
        """Delete strategy (if not default and not in use)."""

    def get_strategy(self, strategy_id: str) -> Strategy:
        """Retrieve strategy by ID."""

    def list_strategies(self) -> List[StrategyMetadata]:
        """List all available strategies with metadata."""

    def evaluate_strategy(
        self,
        strategy: Strategy,
        stock_data: StockData
    ) -> StrategyEvaluationResult:
        """
        Evaluate a strategy against stock data.

        Returns:
            StrategyEvaluationResult with pass/fail and detailed condition results
        """
```

**Data Models:**
```python
@dataclass
class Strategy:
    id: str
    name: str
    description: str
    conditions: List[StrategyCondition]
    logic: LogicOperator  # Enum: AND, OR
    version: int
    created_at: datetime
    updated_at: datetime
    is_default: bool

@dataclass
class StrategyCondition:
    indicator_type: str  # "MCDX", "B-XTrender", "SMA", "EPS", etc.
    operator: ComparisonOperator  # Enum: EQUALS, IN, GT, LT, GTE, LTE
    values: List[Any]  # e.g., ["Banker", "Smart Money"] or [2.5]
    weight: float = 1.0  # For future weighted scoring

@dataclass
class StrategyEvaluationResult:
    strategy_id: str
    ticker: str
    passed: bool
    condition_results: List[ConditionResult]
    overall_confidence: float
    timestamp: datetime

@dataclass
class ConditionResult:
    condition: StrategyCondition
    passed: bool
    actual_value: Any
    expected_values: List[Any]
    message: str
```

#### PortfolioService

**Purpose:** Manages user portfolio holdings and strategy validation.

**Key Methods:**
```python
class PortfolioService:
    def add_holding(
        self,
        portfolio_id: str,
        ticker: str,
        shares: Decimal,
        avg_cost: Decimal
    ) -> Holding:
        """Add stock to portfolio with position details."""

    def remove_holding(self, portfolio_id: str, ticker: str) -> bool:
        """Remove stock from portfolio."""

    def get_portfolio(self, portfolio_id: str) -> Portfolio:
        """Retrieve complete portfolio with current valuations."""

    def validate_portfolio_against_strategy(
        self,
        portfolio_id: str,
        strategy_id: str
    ) -> PortfolioValidationResult:
        """
        Check all portfolio holdings against a strategy.

        Returns:
            Categorized results: Strong, Weakening, Lost Signal
        """

    def get_portfolio_summary(self, portfolio_id: str) -> PortfolioSummary:
        """Get aggregate statistics for portfolio."""
```

**Data Models:**
```python
@dataclass
class Portfolio:
    id: str
    name: str
    holdings: List[Holding]
    created_at: datetime
    updated_at: datetime

@dataclass
class Holding:
    ticker: str
    company_name: str
    shares: Decimal
    avg_cost_per_share: Decimal
    current_price: Decimal
    total_value: Decimal
    gain_loss_amount: Decimal
    gain_loss_percent: Decimal
    fundamental_data: FundamentalData
    last_updated: datetime

@dataclass
class PortfolioValidationResult:
    portfolio_id: str
    strategy_id: str
    timestamp: datetime
    strong_signals: List[HoldingValidation]  # All conditions met
    weakening_signals: List[HoldingValidation]  # Some conditions failed
    lost_signals: List[HoldingValidation]  # Most/all conditions failed

@dataclass
class HoldingValidation:
    holding: Holding
    evaluation_result: StrategyEvaluationResult
    status_change: Optional[StatusChange]  # If signals changed since last check
    recommendation: ActionRecommendation  # Enum: HOLD, MONITOR, CONSIDER_EXIT
```

### 6A.3 Data Gateway Abstractions

#### IMarketDataGateway Interface

**Purpose:** Abstract interface for stock price data providers.

```python
class IMarketDataGateway(ABC):
    @abstractmethod
    def get_historical_data(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        interval: DataInterval = DataInterval.DAILY
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data.

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """

    @abstractmethod
    def get_current_price(self, ticker: str) -> StockPrice:
        """Fetch current/latest price for a stock."""

    @abstractmethod
    def get_fundamental_data(self, ticker: str) -> FundamentalData:
        """Fetch fundamental metrics (EPS, P/E, etc.)."""

    @abstractmethod
    def batch_get_current_prices(self, tickers: List[str]) -> Dict[str, StockPrice]:
        """Optimized batch fetching of current prices."""
```

**Concrete Implementations:**
- `YahooFinanceGateway` (primary)
- `AlphaVantageGateway` (fallback)
- `MockMarketDataGateway` (testing)

#### IComplianceGateway Interface

**Purpose:** Abstract interface for halal screening providers.

```python
class IComplianceGateway(ABC):
    @abstractmethod
    def check_compliance(self, ticker: str) -> ComplianceStatus:
        """
        Check if stock is halal-compliant.

        Returns:
            ComplianceStatus with compliance result and reason codes
        """

    @abstractmethod
    def batch_check_compliance(
        self,
        tickers: List[str]
    ) -> Dict[str, ComplianceStatus]:
        """Batch compliance checking for multiple stocks."""

    @abstractmethod
    def get_compliance_details(self, ticker: str) -> ComplianceDetails:
        """Get detailed compliance breakdown (sector, debt ratios, etc.)."""
```

**Data Models:**
```python
@dataclass
class ComplianceStatus:
    ticker: str
    is_compliant: bool
    confidence: ConfidenceLevel  # Enum: HIGH, MEDIUM, LOW
    exclusion_reasons: List[ExclusionReason]
    last_updated: datetime
    data_source: str

@dataclass
class ComplianceDetails:
    ticker: str
    primary_business: str
    sector_breakdown: Dict[str, float]  # Sector -> % revenue
    debt_ratio: Optional[float]
    impure_income_ratio: Optional[float]
    compliance_status: ComplianceStatus
```

**Concrete Implementations:**
- `ZoyaComplianceGateway` (primary)
- `MusaffaComplianceGateway` (alternative)
- `LocalComplianceDatabase` (fallback, manual CSV)

#### IStockUniverseGateway Interface

**Purpose:** Abstract interface for retrieving stock universe lists (exchanges, sectors, market caps).

```python
class IStockUniverseGateway(ABC):
    @abstractmethod
    def get_exchange_constituents(self, exchange: ExchangeType) -> List[str]:
        """
        Get all tickers for a specific exchange/index.

        Args:
            exchange: Enum value (SP500, NASDAQ100, NASDAQ_COMPOSITE,
                     RUSSELL2000, DOW30, ALL_US)

        Returns:
            List of ticker symbols
        """

    @abstractmethod
    def get_stocks_by_sector(self, sector: SectorType) -> List[str]:
        """
        Get all stocks in a specific sector.

        Args:
            sector: Enum value (TECHNOLOGY, HEALTHCARE, FINANCIAL, etc.)

        Returns:
            List of ticker symbols in that sector
        """

    @abstractmethod
    def get_stocks_by_market_cap(
        self,
        min_cap: Optional[Decimal] = None,
        max_cap: Optional[Decimal] = None
    ) -> List[str]:
        """
        Get stocks within a market cap range.

        Args:
            min_cap: Minimum market cap in dollars (e.g., 10_000_000_000 for $10B)
            max_cap: Maximum market cap in dollars

        Returns:
            List of ticker symbols meeting criteria
        """

    @abstractmethod
    def get_etf_holdings(self, etf_ticker: str) -> List[ETFHolding]:
        """
        Get holdings of a specific ETF.

        Args:
            etf_ticker: ETF symbol (e.g., "SPY", "QQQ")

        Returns:
            List of holdings with ticker and weight information
        """

    @abstractmethod
    def validate_tickers(self, tickers: List[str]) -> Dict[str, bool]:
        """
        Validate that ticker symbols are legitimate.

        Args:
            tickers: List of ticker symbols to validate

        Returns:
            Dict mapping ticker -> is_valid (bool)
        """
```

**Data Models:**
```python
@dataclass
class ETFHolding:
    ticker: str
    company_name: str
    weight: Decimal  # Portfolio weight as percentage (e.g., 7.5 for 7.5%)
    shares: Optional[int]
    market_value: Optional[Decimal]

class ExchangeType(Enum):
    SP500 = "S&P 500"
    NASDAQ100 = "NASDAQ 100"
    NASDAQ_COMPOSITE = "NASDAQ Composite"
    RUSSELL2000 = "Russell 2000"
    DOW30 = "Dow Jones Industrial Average"
    ALL_US = "All US Stocks"

class SectorType(Enum):
    TECHNOLOGY = "Technology"
    HEALTHCARE = "Healthcare"
    FINANCIAL = "Financial Services"
    CONSUMER_DISCRETIONARY = "Consumer Discretionary"
    CONSUMER_STAPLES = "Consumer Staples"
    INDUSTRIALS = "Industrials"
    ENERGY = "Energy"
    REAL_ESTATE = "Real Estate"
    UTILITIES = "Utilities"
    MATERIALS = "Materials"
    COMMUNICATION = "Communication Services"
```

**Concrete Implementations:**
- `StaticUniverseGateway` (primary - uses local CSV/JSON files for exchange constituents)
- `YahooFinanceUniverseGateway` (fetches sector/market cap data from Yahoo Finance)
- `WikipediaUniverseGateway` (scrapes index constituents from Wikipedia tables)
- `ETFDatabaseGateway` (fetches ETF holdings from ETF Database Pro API)
- `MockUniverseGateway` (testing)

**Data Sources:**
- **Exchange/Index Constituents:** Static CSV files updated monthly
  - S&P 500: Wikipedia table scraping or manual updates
  - NASDAQ: NASDAQ official constituent list
  - Russell 2000: Russell indices constituent list
- **Sector Data:** Yahoo Finance screener or similar APIs
- **Market Cap Data:** Real-time queries to market data APIs
- **ETF Holdings:** ETF provider websites, ETF Database Pro API

### 6A.4 Strategy Engine Architecture

#### Core Components

**1. StrategyEvaluator**
```python
class StrategyEvaluator:
    """
    Evaluates strategies against stock data using registered indicators.
    """

    def __init__(
        self,
        indicator_registry: IndicatorRegistry,
        compliance_filter: ComplianceFilter
    ):
        self.indicator_registry = indicator_registry
        self.compliance_filter = compliance_filter

    def evaluate(
        self,
        strategy: Strategy,
        stock_data: StockData
    ) -> StrategyEvaluationResult:
        """
        Main evaluation method.

        Process:
        1. Check halal compliance (fail-fast if non-compliant)
        2. Calculate required indicators
        3. Evaluate each condition
        4. Apply logic (AND/OR) to combine results
        5. Return detailed evaluation result
        """
```

**2. IndicatorRegistry**
```python
class IndicatorRegistry:
    """
    Registry of available indicators with metadata.
    """

    def register_indicator(
        self,
        indicator_type: str,
        indicator_class: Type[IIndicator],
        metadata: IndicatorMetadata
    ) -> None:
        """Register a new indicator type."""

    def get_indicator(self, indicator_type: str) -> IIndicator:
        """Retrieve indicator instance by type."""

    def list_indicators(self) -> List[IndicatorMetadata]:
        """List all available indicators with metadata."""
```

**3. ComplianceFilter**
```python
class ComplianceFilter:
    """
    Enforces halal compliance filtering with audit trail.
    """

    def __init__(
        self,
        compliance_gateway: IComplianceGateway,
        exclusion_logger: ExclusionLogger
    ):
        self.compliance_gateway = compliance_gateway
        self.exclusion_logger = exclusion_logger

    def filter_stocks(
        self,
        tickers: List[str]
    ) -> FilterResult:
        """
        Filter stocks for compliance.

        Returns:
            FilterResult with compliant and excluded stocks, with reasons
        """
```

### 6A.5 Infrastructure Layer

#### CacheManager

**Purpose:** Manages data caching with TTL and invalidation logic.

```python
class CacheManager:
    """
    Multi-tier cache: Memory (LRU) -> SQLite -> API
    """

    def get(
        self,
        cache_type: CacheType,
        key: str
    ) -> Optional[CachedData]:
        """Retrieve from cache if not expired."""

    def set(
        self,
        cache_type: CacheType,
        key: str,
        value: Any,
        ttl_seconds: int
    ) -> None:
        """Store in cache with TTL."""

    def invalidate(
        self,
        cache_type: CacheType,
        key: Optional[str] = None
    ) -> None:
        """Invalidate cache entry or entire cache type."""
```

**Cache Types:**
- `STOCK_PRICE`: TTL 1 hour
- `FUNDAMENTAL_DATA`: TTL 24 hours
- `COMPLIANCE_STATUS`: TTL 30 days
- `EXCHANGE_CONSTITUENTS`: TTL 30 days (monthly updates)
- `SECTOR_STOCKS`: TTL 7 days (weekly updates)
- `MARKET_CAP_STOCKS`: TTL 24 hours (daily updates)
- `ETF_HOLDINGS`: TTL 30 days (monthly updates)
- `INDICATOR_CALCULATION`: TTL 1 hour

#### RateLimiter

**Purpose:** Enforce API rate limits to prevent throttling.

```python
class RateLimiter:
    """
    Token bucket algorithm for rate limiting.
    """

    def acquire(
        self,
        resource: str,
        tokens: int = 1
    ) -> bool:
        """
        Attempt to acquire tokens.

        Returns:
            True if acquired, False if rate limit would be exceeded
        """

    def wait_if_needed(
        self,
        resource: str,
        tokens: int = 1
    ) -> float:
        """Block until tokens available, return wait time."""
```

**Rate Limit Configurations:**
- `yahoo_finance`: 2000 requests/hour
- `zoya_api`: 1000 requests/day (configurable)
- `alpha_vantage`: 500 requests/day

### 6A.6 Data Flow Diagrams

#### Stock Screening Flow

```
User Initiates Screening
         ↓
CLI: Collect universe selection & strategy selection
     (Exchange/Index, Sector, Market Cap, ETF, or Custom List)
         ↓
ScreeningService.screen_universe(universe_config, strategy_id)
         ↓
1. StockUniverseGateway.get_tickers(universe_config)
   ├─→ For EXCHANGE: Load from static file/cache (S&P 500, NASDAQ, etc.)
   ├─→ For SECTOR: Query market data provider
   ├─→ For MARKET_CAP: Query market data provider
   ├─→ For ETF: Fetch holdings from ETF provider API
   ├─→ For CUSTOM: Parse user-provided ticker list
   ├─→ Check Cache (TTL varies by universe type)
   └─→ Return validated ticker list
         ↓
2. ComplianceFilter.filter_stocks(ticker_list)
   ├─→ Batch check compliance
   ├─→ ComplianceGateway.batch_check_compliance()
   ├─→ Separate compliant vs. excluded
   └─→ Log all exclusions with reasons
         ↓
3. MarketDataGateway.batch_get_historical_data(compliant_stocks)
   ├─→ Parallelize requests (asyncio)
   ├─→ Check Cache for each stock
   ├─→ Apply rate limiting
   └─→ Fetch missing data
         ↓
4. For each compliant stock:
   ├─→ IndicatorRegistry.get_indicator("MCDX").calculate(stock_data)
   ├─→ IndicatorRegistry.get_indicator("B-XTrender").calculate(stock_data)
   ├─→ [Additional indicators as per strategy]
   └─→ Cache indicator results
         ↓
5. StrategyEvaluator.evaluate(strategy, stock_with_indicators)
   ├─→ ConditionEvaluator.evaluate_condition() for each condition
   ├─→ Apply AND/OR logic
   └─→ Determine pass/fail
         ↓
6. Aggregate results
   ├─→ Collect all matches
   ├─→ Sort by match confidence / price / sector
   └─→ Format for display
         ↓
7. Return ScreeningResult to CLI
         ↓
CLI: Display results in formatted table
         ↓
User: Export / Add to portfolio / View details
```

#### Portfolio Strategy Validation Flow

```
User Requests Portfolio Validation
         ↓
CLI: Select portfolio & strategy
         ↓
PortfolioService.validate_portfolio_against_strategy(portfolio_id, strategy_id)
         ↓
1. PortfolioRepository.get_portfolio(portfolio_id)
   └─→ Fetch all holdings from SQLite
         ↓
2. For each holding:
   ├─→ MarketDataGateway.get_current_price(ticker)
   ├─→ MarketDataGateway.get_historical_data(ticker, last_50_days)
   └─→ MarketDataGateway.get_fundamental_data(ticker)
         ↓
3. For each holding:
   ├─→ Calculate indicators
   ├─→ StrategyEvaluator.evaluate(strategy, holding_data)
   └─→ Compare to previous evaluation (detect changes)
         ↓
4. Categorize holdings:
   ├─→ Strong: All conditions met
   ├─→ Weakening: Some conditions failed
   └─→ Lost: Most/all conditions failed
         ↓
5. Generate recommendations
   ├─→ Strong: HOLD
   ├─→ Weakening: MONITOR
   └─→ Lost: CONSIDER_EXIT
         ↓
6. Return PortfolioValidationResult
         ↓
CLI: Display categorized holdings with status changes
```

### 6A.7 Error Handling Strategy

**Error Categories:**

1. **User Input Errors** (4xx equivalent)
   - Invalid ticker symbol
   - Strategy not found
   - Invalid configuration
   - **Handling:** Clear error message, suggest corrections, no retry

2. **External Dependency Errors** (5xx equivalent)
   - API unavailable
   - Rate limit exceeded
   - Network timeout
   - **Handling:** Retry with exponential backoff, failover to backup provider, cache fallback

3. **Data Quality Errors**
   - Insufficient historical data
   - Missing fundamental metrics
   - **Handling:** Skip stock with warning, log issue, continue processing

4. **System Errors**
   - Database corruption
   - File system errors
   - **Handling:** Graceful degradation, preserve user data, clear error message

**Error Handling Pattern:**
```python
class ScreeningService:
    def screen_etf(self, etf_ticker: str, strategy_id: str) -> ScreeningResult:
        try:
            holdings = self._get_etf_holdings(etf_ticker)
        except ETFNotFoundException as e:
            raise UserInputError(f"ETF '{etf_ticker}' not found. Please verify ticker symbol.") from e
        except DataProviderException as e:
            # Try fallback provider
            try:
                holdings = self._get_etf_holdings_fallback(etf_ticker)
            except Exception as fallback_error:
                raise ServiceUnavailableError(
                    f"Unable to fetch ETF holdings. All data providers unavailable. "
                    f"Please try again later."
                ) from e

        # Continue with screening...
```

### 6A.8 Testing Strategy

**Test Pyramid:**

1. **Unit Tests (70% coverage target)**
   - Test individual components in isolation
   - Mock all external dependencies
   - Focus: Indicator calculations, strategy evaluation logic, condition evaluation

2. **Integration Tests (20% coverage target)**
   - Test service layer with real dependencies
   - Use test database, mock external APIs
   - Focus: Service orchestration, data flow, error handling

3. **End-to-End Tests (10% coverage target)**
   - Test complete user workflows
   - Use mock data providers (deterministic results)
   - Focus: Critical paths (screening, portfolio validation)

**Mock Strategies:**
- Mock external APIs with recorded responses (VCR.py)
- Use in-memory SQLite for database tests
- Provide mock implementations of gateways for testing

**Test Data:**
- Pre-defined stock datasets with known characteristics
- Compliant and non-compliant stocks
- Various indicator patterns (Banker, Neutral, Retail signals)

---

## 7. Investment Strategy Requirements

### 7.1 Core Investment Philosophy

**Strategy Evaluation Logic:**
- Strategies use **AND logic** between indicators (ALL conditions must be met)
- Within multi-value indicators, **OR logic** applies (e.g., MCDX = Banker OR Smart Money)
- A stock is a "BUY SIGNAL" only when 100% of strategy conditions are satisfied

**Example:**
```
Strategy: Default Momentum
  Condition 1: MCDX = "Banker" OR "Smart Money"
  Condition 2: B-XTrender = "Green"

Evaluation:
  Stock A: MCDX = "Banker", B-XTrender = "Green" → ✅ BUY SIGNAL (both met)
  Stock B: MCDX = "Banker", B-XTrender = "Yellow" → ❌ NO SIGNAL (Condition 2 failed)
  Stock C: MCDX = "Neutral", B-XTrender = "Green" → ❌ NO SIGNAL (Condition 1 failed)
```

### 7.2 Technical Indicator: MCDX (Multi-Color Divergence Index)

#### 7.2.1 Overview

MCDX is a proprietary volume-weighted indicator designed to identify institutional ("smart money") accumulation versus retail distribution. It analyzes price-volume relationships to detect divergences between price action and underlying buying/selling pressure.

#### 7.2.2 Interpretation

**Signal Types:**
- **"Banker" (Dark Green):** Strong institutional accumulation. Large players are aggressively buying.
- **"Smart Money" (Light Green):** Institutional interest with controlled accumulation.
- **"Neutral" (Yellow):** Balanced buying/selling, no clear directional bias.
- **"Retail" (Red):** Retail-driven price action, often distribution phase. Smart money exiting.

**Buy Signal Logic:**
- Recommend BUY when MCDX = "Banker" OR "Smart Money"
- Avoid when MCDX = "Neutral" or "Retail"

#### 6.2.3 Implementation Details

**Data Requirements:**
- Historical price data (Open, High, Low, Close) - minimum 30 days
- Historical volume data - minimum 30 days
- Tick-level data NOT required (daily OHLCV sufficient)

**TradingView Open-Source Implementation:**
- **Source:** TradingView Pine Script - MCDX indicator (search: "MCDX" or "Multi-Color Divergence")
- **License:** Verify open-source license permits commercial/redistribution use
- **Translation:** Pine Script logic must be translated to Python
- **Libraries:** Use `pandas`, `numpy` for calculations

**Calculation Pseudocode (High-Level):**
```python
# MCDX typically involves:
# 1. Calculate price momentum (rate of change)
# 2. Calculate volume momentum (volume relative to average)
# 3. Identify divergences between price and volume
# 4. Apply smoothing (moving averages)
# 5. Classify into signal categories based on thresholds

def calculate_mcdx(df):
    """
    df: DataFrame with columns ['date', 'open', 'high', 'low', 'close', 'volume']
    returns: DataFrame with additional column 'mcdx_signal' ['Banker', 'Smart Money', 'Neutral', 'Retail']
    """
    # Actual implementation requires full Pine Script translation
    # This is a simplified representation

    # Calculate volume-weighted price momentum
    df['price_roc'] = df['close'].pct_change(periods=14)
    df['volume_ratio'] = df['volume'] / df['volume'].rolling(window=20).mean()

    # Detect divergence
    df['divergence_score'] = (df['price_roc'] * df['volume_ratio']).rolling(window=5).mean()

    # Classify into signals based on thresholds
    df['mcdx_signal'] = pd.cut(
        df['divergence_score'],
        bins=[-np.inf, -0.05, 0.02, 0.10, np.inf],
        labels=['Retail', 'Neutral', 'Smart Money', 'Banker']
    )

    return df
```

**Output Format:**
- For each stock, return current MCDX signal: `{"ticker": "AAPL", "mcdx_signal": "Banker", "mcdx_score": 0.15}`

**Performance Requirements:**
- Calculate MCDX for 1 stock in < 0.5 seconds
- Batch calculation for 100 stocks in < 30 seconds

**Testing Requirements:**
- Validate against TradingView chart outputs for known stocks
- Document any deviations from original Pine Script implementation
- Unit tests for edge cases (low volume stocks, newly IPO'd stocks)

#### 6.2.4 User Configuration Options

**In Strategy Creation:**
- User selects which MCDX signals qualify as "buy":
  - [X] Banker (default: enabled)
  - [X] Smart Money (default: enabled)
  - [ ] Neutral (default: disabled)
  - [ ] Retail (default: disabled)

### 6.3 Technical Indicator: B-XTrender

#### 6.3.1 Overview

B-XTrender is a momentum-trend indicator that uses color coding to represent trend strength and direction. It combines moving averages and momentum oscillators to identify sustained directional moves.

#### 6.3.2 Interpretation

**Color Signals:**
- **Green:** Bullish momentum, uptrend confirmed. Buy/hold zone.
- **Yellow:** Neutral/transitional, momentum weakening or consolidating. Caution zone.
- **Red:** Bearish momentum, downtrend confirmed. Avoid/exit zone.

**Buy Signal Logic:**
- Recommend BUY only when B-XTrender = "Green"
- WAIT when B-XTrender = "Yellow"
- AVOID when B-XTrender = "Red"

#### 6.3.3 Implementation Details

**Data Requirements:**
- Historical price data (Close) - minimum 50 days
- Volume data (optional, depending on indicator variant)

**TradingView Open-Source Implementation:**
- **Source:** TradingView Pine Script - "B-XTrender" or "XTrender" indicator
- **License:** Verify open-source license
- **Translation:** Pine Script → Python

**Calculation Pseudocode (High-Level):**
```python
def calculate_b_xtrender(df):
    """
    df: DataFrame with columns ['date', 'close']
    returns: DataFrame with additional column 'xtrender_color' ['Green', 'Yellow', 'Red']
    """
    # Calculate fast and slow moving averages
    df['ema_fast'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=26, adjust=False).mean()

    # Calculate momentum (difference between EMAs)
    df['momentum'] = df['ema_fast'] - df['ema_slow']

    # Apply smoothing to momentum
    df['momentum_smooth'] = df['momentum'].ewm(span=9, adjust=False).mean()

    # Classify into color zones based on momentum strength
    def classify_color(momentum):
        if momentum > 0.02:  # Thresholds need calibration
            return 'Green'
        elif momentum < -0.02:
            return 'Red'
        else:
            return 'Yellow'

    df['xtrender_color'] = df['momentum_smooth'].apply(classify_color)

    return df
```

**Output Format:**
- For each stock, return current B-XTrender signal: `{"ticker": "AAPL", "xtrender_color": "Green", "momentum_score": 0.08}`

**Performance Requirements:**
- Calculate B-XTrender for 1 stock in < 0.3 seconds
- Batch calculation for 100 stocks in < 20 seconds

**Testing Requirements:**
- Validate against TradingView chart outputs
- Test sensitivity to different market conditions (trending vs. ranging)
- Unit tests for boundary conditions

#### 6.3.4 User Configuration Options

**In Strategy Creation:**
- User selects which B-XTrender colors qualify as "buy":
  - [X] Green (default: enabled)
  - [ ] Yellow (default: disabled)
  - [ ] Red (default: disabled)

### 6.4 Technical Indicator: Simple Moving Average (SMA)

#### 6.4.1 Overview

Standard moving average calculation, user-configurable for multiple time periods.

#### 6.4.2 Common Configurations

**Periods:**
- SMA(20): Short-term trend (1 month)
- SMA(50): Medium-term trend (2.5 months)
- SMA(200): Long-term trend (1 year)

**Typical Buy Conditions:**
- Price > SMA(20): Price above short-term support
- SMA(20) > SMA(50): "Golden Cross" (bullish crossover)
- Price > SMA(200): Price above long-term support

#### 6.4.3 Implementation

**Calculation:**
```python
def calculate_sma(df, period=20):
    """
    df: DataFrame with 'close' column
    period: lookback period for average
    returns: Series of SMA values
    """
    return df['close'].rolling(window=period).mean()
```

#### 6.4.4 User Configuration Options

**In Strategy Creation:**
- Select SMA periods: 10, 20, 50, 100, 200 (custom periods allowed)
- Set condition:
  - Price > SMA(X)
  - Price < SMA(X)
  - SMA(X) > SMA(Y) (crossover logic)
  - SMA(X) < SMA(Y)

### 6.5 Fundamental Data Filters

#### 6.5.1 Available Metrics

**Earnings & Profitability:**
- **EPS (Earnings Per Share):** Quarterly or TTM (trailing twelve months)
- **EPS Growth:** YoY percentage change
- **Profit Margin:** Net income / Revenue

**Valuation:**
- **P/E Ratio (Price-to-Earnings):** Current price / EPS
- **P/B Ratio (Price-to-Book):** Current price / Book value per share
- **PEG Ratio:** P/E / EPS growth rate

**Growth:**
- **Revenue Growth:** YoY percentage change
- **Earnings Growth:** YoY percentage change

**Financial Health:**
- **Debt-to-Equity Ratio:** Total debt / Total equity
- **Current Ratio:** Current assets / Current liabilities
- **Free Cash Flow:** Operating cash flow - Capital expenditures

**Market Data:**
- **Market Cap:** Current market capitalization
- **Daily Volume:** Average daily trading volume
- **52-Week High/Low:** Price range over past year

#### 6.5.2 User Configuration

**In Strategy Creation:**
- Select fundamental metric from dropdown
- Set comparison operator: >, <, =, >=, <=
- Set threshold value (numeric input)
- Example: "P/E Ratio < 30" AND "EPS Growth > 15%"

#### 6.5.3 Data Sources

- Primary: Yahoo Finance API, Alpha Vantage, Financial Modeling Prep
- Fallback: Scrape from public financial websites (with rate limiting)

### 6.6 Strategy Storage Format

**JSON Schema:**
```json
{
  "strategy_name": "Default Momentum Strategy",
  "description": "Dual-indicator confirmation for banker accumulation",
  "created_date": "2025-01-15",
  "last_modified": "2025-01-15",
  "version": 1,
  "is_default": true,
  "conditions": [
    {
      "indicator_type": "MCDX",
      "indicator_name": "Multi-Color Divergence Index",
      "operator": "IN",
      "values": ["Banker", "Smart Money"],
      "weight": 1.0
    },
    {
      "indicator_type": "B-XTrender",
      "indicator_name": "B-XTrender Momentum",
      "operator": "EQUALS",
      "values": ["Green"],
      "weight": 1.0
    }
  ],
  "logic": "AND"
}
```

---

## 7. Technical Requirements & Constraints

### 7.1 Technology Stack

**Programming Language:**
- Python 3.11+

**CLI Framework:**
- **Rich** (https://github.com/Textualize/rich): For beautiful terminal formatting, tables, progress bars
- **Typer** (https://typer.tiangolo.com/): For CLI command structure and argument parsing
- **Questionary** (https://github.com/tmbo/questionary): For interactive prompts and menus

**Data Processing:**
- **Pandas:** Data manipulation and analysis
- **NumPy:** Numerical calculations for indicators
- **TA-Lib** (optional): Technical analysis library (if MCDX/B-XTrender require complex TA functions)

**Data Visualization:**
- **Matplotlib / Plotext:** ASCII/terminal-based plotting for CLI charts
- **Plotly** (future): For web-based interactive charts

**API Clients:**
- **yfinance:** Yahoo Finance data retrieval
- **requests:** HTTP requests for APIs
- **aiohttp:** Async HTTP for parallel API calls (performance optimization)

**Data Storage:**
- **SQLite:** Local database for portfolio, strategies, cache
- **JSON:** Configuration files and strategy definitions

**Testing:**
- **pytest:** Unit and integration testing
- **pytest-mock:** Mocking external APIs
- **pytest-cov:** Code coverage reporting

**Dependency Management:**
- **Poetry** or **pip-tools:** Lock file for reproducible environments

### 7.2 Architecture Principles

**Pluggable Strategy Architecture:**

```
┌─────────────────────────────────────────┐
│         CLI Interface Layer             │
│   (Rich, Typer, Questionary)            │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│      Application Service Layer          │
│  • ScreeningService                     │
│  • StrategyService                      │
│  • PortfolioService                     │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│       Strategy Engine (Core)            │
│  • StrategyEvaluator                    │
│  • IndicatorRegistry                    │
│  • ConditionEvaluator                   │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│      Indicator Implementations          │
│  • MCDXIndicator (implements IIndicator)│
│  • BXTrenderIndicator                   │
│  • SMAIndicator                         │
│  • [Future indicators plug in here]     │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│         Data Access Layer               │
│  • StockDataProvider                    │
│  • HalalScreeningProvider               │
│  • FundHoldingsProvider                 │
│  • CacheManager                         │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│       External Data Sources             │
│  • Yahoo Finance API                    │
│  • Zoya/Musaffa Halal API               │
│  • ETF Holdings APIs                    │
└─────────────────────────────────────────┘
```

**Key Design Patterns:**

1. **Strategy Pattern:** Each indicator implements `IIndicator` interface
2. **Factory Pattern:** `IndicatorFactory` creates indicator instances based on configuration
3. **Repository Pattern:** Data access abstracted through repository interfaces
4. **Singleton Pattern:** `CacheManager` ensures single cache instance
5. **Observer Pattern (Future):** For real-time portfolio alerts

**Indicator Interface:**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd

class IIndicator(ABC):
    """Base interface for all technical indicators"""

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate indicator values

        Args:
            df: DataFrame with columns ['date', 'open', 'high', 'low', 'close', 'volume']

        Returns:
            DataFrame with additional indicator columns
        """
        pass

    @abstractmethod
    def get_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get current signal/status for most recent data point

        Returns:
            Dict with indicator-specific signal information
            Example: {"signal": "Banker", "score": 0.15, "timestamp": "2025-11-10"}
        """
        pass

    @abstractmethod
    def get_required_periods(self) -> int:
        """Return minimum number of data periods required for calculation"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return human-readable indicator name"""
        pass
```

**Adding New Indicators (Extensibility):**

To add a new indicator (e.g., RSI):
1. Create class `RSIIndicator(IIndicator)`
2. Implement required methods
3. Register in `IndicatorRegistry`
4. Update strategy creation UI to include RSI option
5. No changes to core engine required

### 7.3 Performance Requirements

**Response Times:**
- CLI startup: < 2 seconds
- Menu navigation: < 0.1 seconds
- Screen 100 stocks: < 120 seconds
- Screen 500 stocks: < 600 seconds (10 minutes)
- Portfolio strategy check (10 stocks): < 15 seconds
- Indicator calculation per stock: < 1 second

**Optimization Strategies:**
- **Parallel API Calls:** Use `asyncio` / `aiohttp` to fetch data for multiple stocks concurrently
- **Caching:** Cache stock data for 1 hour, fundamental data for 24 hours, halal compliance for 30 days
- **Batch Processing:** Process indicators in batches of 10 stocks
- **Progress Indicators:** Show real-time progress to maintain user engagement during long operations

**Rate Limiting:**
- Respect API rate limits (e.g., Yahoo Finance: 2000 requests/hour)
- Implement exponential backoff for failed requests
- Queue requests when approaching rate limits

### 7.4 Data Requirements

**Stock Price Data:**
- **Frequency:** Daily OHLCV (Open, High, Low, Close, Volume)
- **Historical Depth:** Minimum 200 days for long-term indicators
- **Real-time:** 15-minute delayed data acceptable for MVP
- **Source:** Yahoo Finance (primary), Alpha Vantage (backup)

**Fundamental Data:**
- **Frequency:** Quarterly earnings, annual financial statements
- **Metrics:** EPS, P/E, revenue, debt, cash flow (see Section 6.5.1)
- **Source:** Yahoo Finance, Financial Modeling Prep

**Halal Compliance Data:**
- **Source:** Zoya API, Musaffa API, manual database
- **Update Frequency:** Weekly automated updates
- **Coverage:** Minimum 5,000 stocks (all major US/EU exchanges)

**ETF Holdings Data:**
- **Source:** ETF provider websites (iShares, Vanguard scraping), ETF Database Pro API
- **Update Frequency:** Monthly (holdings change infrequently)
- **Coverage:** Major ETFs (SPY, QQQ, VTI, IWDA.AS, etc.)

### 7.5 Security & Privacy

**API Key Management:**
- Store API keys in `.env` file (gitignored)
- Encrypt API keys at rest using `cryptography` library
- Never log API keys

**Data Privacy:**
- All user data stored locally (no cloud sync in MVP)
- Portfolio data encrypted at rest
- No telemetry or usage tracking without explicit opt-in

**Dependency Security:**
- Use `pip-audit` to scan for vulnerable dependencies
- Pin dependency versions in `requirements.txt`
- Regular security updates

### 7.6 Error Handling

**Graceful Degradation:**
- If primary API fails, attempt backup API
- If all APIs fail, display cached data with timestamp warning
- If indicator cannot be calculated (insufficient data), skip stock with logged reason

**User-Friendly Error Messages:**
- Technical errors translated to plain language
- Actionable next steps provided
- Example: "Unable to fetch data for AAPL. Reason: API rate limit reached. Please try again in 15 minutes."

**Logging:**
- All errors logged to `logs/stock-cli.log`
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- User can enable verbose mode for troubleshooting

### 7.7 EU Regulatory Compliance

**KID (Key Information Document) Verification:**
- Check if stock has KID available for EU investors
- Data source: Manual database or EU regulatory databases
- Fallback: Flag stock as "EU accessibility unverified"

**UCITS Compliance:**
- For ETFs/funds, verify UCITS compliance
- Display UCITS status in screening results
- Warn user if recommended stock may not be accessible to EU retail investors

**PRIIPs Regulation:**
- Acknowledge that tool provides information, not investment advice
- Display disclaimer: "This tool provides technical analysis for informational purposes only. It is not investment advice. Consult a financial advisor before making investment decisions."

---

## 8. Data Requirements

### 8.1 Required APIs & Data Providers

**Priority 1 (MVP Critical):**

1. **Stock Price Data:**
   - **Provider:** Yahoo Finance (via `yfinance` library)
   - **Endpoint:** Historical OHLCV data
   - **Cost:** Free (rate-limited)
   - **Fallback:** Alpha Vantage API (free tier: 500 requests/day)

2. **Halal Screening:**
   - **Provider:** Zoya API (zoya.finance)
   - **Endpoint:** `/api/v1/stocks/{ticker}/compliance`
   - **Cost:** TBD (may require paid plan for API access)
   - **Fallback:** Musaffa API or manual CSV database

3. **ETF Holdings:**
   - **Provider:** Manual scraping from ETF provider websites (iShares, Vanguard)
   - **Endpoint:** Holdings CSV downloads
   - **Cost:** Free
   - **Fallback:** ETF Database Pro API (paid)

**Priority 2 (Enhanced Features):**

4. **Fundamental Data:**
   - **Provider:** Financial Modeling Prep API
   - **Endpoint:** `/api/v3/ratios/{ticker}`
   - **Cost:** Free tier available
   - **Fallback:** Yahoo Finance

5. **EU Accessibility Data:**
   - **Provider:** Manual database (initially curated)
   - **Future:** Integrate with EU regulatory databases

### 8.2 Data Caching Strategy

**Cache Durations:**
- Stock price data: 1 hour
- Fundamental data: 24 hours
- Halal compliance status: 30 days
- ETF holdings: 30 days
- Indicator calculations: 1 hour

**Cache Storage:**
- SQLite database: `cache.db`
- Tables: `price_cache`, `fundamental_cache`, `compliance_cache`, `holdings_cache`

**Cache Invalidation:**
- User can manually force refresh: "Update data" option in Settings
- Automatic refresh on cache expiration
- Cache purged weekly for stale entries

### 8.3 Data Quality & Validation

**Stock Data Validation:**
- Reject data with gaps > 5 consecutive days
- Flag stocks with suspiciously low volume (< 1000 shares/day)
- Validate price data: High >= Low, Close within [Low, High]

**Fundamental Data Validation:**
- Flag negative P/E ratios (indicate losses)
- Reject clearly erroneous values (e.g., P/E > 1000)

**Handling Missing Data:**
- If stock has < 50 days of data: Skip indicator calculation, log warning
- If specific fundamental metric unavailable: Skip that condition in strategy evaluation

---

## 9. User Experience Requirements

### 9.1 CLI Design Principles

**Clarity:**
- Clear, descriptive menu options
- No jargon without explanation
- Visual hierarchy using Rich formatting (bold, colors, panels)

**Efficiency:**
- Keyboard shortcuts for common actions
- Default options for quick execution
- Batch operations for bulk tasks

**Feedback:**
- Progress indicators for long-running operations
- Success/error confirmations with visual cues (✅ ❌ ⚠️)
- Estimated time remaining for lengthy processes

**Consistency:**
- Uniform navigation patterns (B = Back, Q = Quit, ? = Help)
- Consistent color scheme (Green = success, Red = error, Yellow = warning)
- Predictable menu structures

### 9.2 Visual Design (CLI Aesthetics)

**Color Scheme:**
- **Primary:** Cyan for headers and important information
- **Success:** Green for positive signals, confirmations
- **Warning:** Yellow for caution, neutral signals
- **Error:** Red for errors, bearish signals
- **Accent:** Magenta for highlights, emphasis

**Typography:**
- **Headers:** Bold, uppercase
- **Data Tables:** Monospaced alignment
- **Prompts:** Regular weight with colored prefix

**Layout:**
- Generous whitespace for readability
- Bordered panels for grouped information
- Aligned tables with column separators

**Example Visualization:**
```
╭─────────────────────────────────────────────────────────────╮
│                     SCREENING RESULTS                       │
│                  Default Momentum Strategy                  │
╰─────────────────────────────────────────────────────────────╯

📊 Screened 387 halal-compliant stocks from SPY
✅ Found 12 buy signals (3.1% hit rate)

┌────────┬──────────────────────┬─────────┬──────────┬──────────┐
│ Ticker │ Company              │ MCDX    │ XTrender │ Price    │
├────────┼──────────────────────┼─────────┼──────────┼──────────┤
│ MSFT   │ Microsoft Corp       │ 🟢 Banker│ 🟢 Green │ $425.00  │
│ AAPL   │ Apple Inc            │ 🟢 Banker│ 🟢 Green │ $189.50  │
│ NVDA   │ NVIDIA Corp          │ 🟢 Banker│ 🟢 Green │ $502.30  │
└────────┴──────────────────────┴─────────┴──────────┴──────────┘

[Enter] View Details  [E] Export  [A] Add All to Portfolio  [Q] Quit
```

### 9.3 Interactive Elements

**Menus:**
- Numbered options with letter shortcuts
- Multi-select checkboxes for batch operations
- Arrow key navigation (optional enhancement)

**Prompts:**
- Auto-complete for ticker symbol entry
- Input validation with immediate feedback
- Default values shown in [brackets]

**Progress Indicators:**
- Spinner for indeterminate tasks ("Fetching data...")
- Progress bar with percentage for batch operations ("Screening: [█████░░░░░] 50% (250/500)")
- Real-time status updates

### 9.4 Accessibility

**Screen Reader Compatibility:**
- ASCII-only mode for screen readers (disable emoji/box characters)
- Clear text descriptions of visual elements

**Keyboard-Only Navigation:**
- All features accessible without mouse
- Tab navigation between fields
- Enter/Space for selection

**Customization:**
- User can configure color scheme (Settings menu)
- Font size adjustable (terminal emulator dependent)

---

## 10. Future Considerations

### 10.1 Phase 2 Features (Post-MVP)

**Enhanced Indicators:**
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Volume-Weighted Average Price (VWAP)
- Custom indicator framework (user-defined Python scripts)

**Backtesting Engine:**
- Historical strategy performance simulation
- Risk-adjusted return metrics (Sharpe ratio, max drawdown)
- Compare multiple strategies side-by-side
- Optimize strategy parameters

**Financial Ratio Screening (Shariah Compliance):**
- Implement AAOIFI financial ratios (see Section 5.2)
- Automatic dividend purification calculator
- Generate purification reports for tax purposes

**Alerting System:**
- Email/SMS alerts when portfolio stocks lose buy signal
- Daily screening reports delivered automatically
- Price target alerts

**Multi-Portfolio Support:**
- Manage multiple portfolios (e.g., "Retirement", "Speculation")
- Portfolio comparison and rebalancing suggestions

### 10.2 Phase 3: Web Application

**Web UI Features:**
- Visual charting (interactive TradingView-style charts)
- Portfolio dashboard with real-time updates
- Drag-and-drop strategy builder
- Social features (share strategies, leaderboards)
- Mobile-responsive design

**Architecture:**
- Backend: FastAPI (Python) serving REST API
- Frontend: React or Vue.js
- Database: PostgreSQL (upgrade from SQLite)
- Deployment: Docker containers, cloud hosting (AWS/GCP)

**Migration Path:**
- CLI tool remains functional (for power users)
- Web app uses same core engine (shared Python library)
- User data syncs between CLI and web (optional cloud storage)

### 10.3 Advanced Analytics

**Machine Learning Enhancements:**
- Predict probability of strategy success
- Anomaly detection (identify unusual indicator patterns)
- Sentiment analysis integration (news, social media)

**Portfolio Optimization:**
- Modern Portfolio Theory (MPT) integration
- Efficient frontier visualization
- Risk-adjusted portfolio suggestions

**Market Regime Detection:**
- Automatically adjust strategies based on market conditions (bull/bear/sideways)
- Historical regime analysis

### 10.4 Community & Ecosystem

**Strategy Marketplace:**
- Users share custom strategies
- Community voting on best strategies
- Strategy performance leaderboards

**Open-Source Contributions:**
- Accept community-contributed indicators
- Plugin system for third-party extensions
- Comprehensive API documentation for developers

### 10.5 Compliance & Licensing

**Shariah Advisory Board:**
- Establish advisory board for ongoing compliance validation
- Annual compliance audits
- Transparent compliance methodology documentation

**Regulatory Considerations:**
- Ensure tool does not constitute regulated investment advice
- Terms of Service and disclaimers
- GDPR compliance for EU users (if cloud features added)

---

## 11. Acceptance Criteria Summary

### 11.1 MVP Must-Have Criteria

**Functional Requirements:**
- ✅ Screen stocks from at least 10 major ETFs (SPY, QQQ, IWDA, etc.)
- ✅ Halal screening excludes 100% of prohibited sectors
- ✅ Default Momentum Strategy (MCDX + B-XTrender) fully functional
- ✅ User can create minimum 1 custom strategy with 2+ indicators
- ✅ Portfolio supports minimum 20 holdings
- ✅ Strategy validation on portfolio completes in < 30 seconds for 10 stocks

**Technical Requirements:**
- ✅ CLI tool runs on Python 3.11+ without errors
- ✅ Installation via pip: `pip install stock-strategy-cli`
- ✅ All dependencies included in requirements.txt
- ✅ Unit test coverage > 80%
- ✅ Integration tests for core workflows

**User Experience:**
- ✅ Intuitive navigation (new users complete first screening in < 5 minutes)
- ✅ Clear error messages with actionable guidance
- ✅ Progress indicators for operations > 5 seconds
- ✅ Help documentation accessible via CLI and README

**Compliance:**
- ✅ Zero false negatives in halal screening (no prohibited stocks recommended)
- ✅ Disclaimer displayed on first launch (investment information, not advice)

### 11.2 Success Metrics (Post-Launch)

**Adoption Metrics:**
- 1,000 CLI downloads in first 3 months
- 50+ active weekly users

**Engagement Metrics:**
- Average 3+ screening operations per user per week
- 70%+ of users create custom strategies
- 60%+ of users maintain active portfolio

**Quality Metrics:**
- < 5% error rate in screening operations
- < 10 bug reports per month (after stabilization)
- > 4.0/5.0 user satisfaction (survey)

---

## 12. Open Questions & Decisions Needed

### 12.1 Technical Decisions

**Q1: TradingView Pine Script Translation**
- **Question:** Should we directly translate Pine Script, or re-implement MCDX/B-XTrender from first principles?
- **Options:**
  - A) Direct translation (faster, higher fidelity)
  - B) Re-implementation (may require reverse-engineering)
- **Recommendation:** Option A (direct translation) with validation against TradingView outputs

**Q2: Halal Screening API Selection**
- **Question:** Which halal screening provider should be primary?
- **Options:**
  - A) Zoya API (popular, may require paid plan)
  - B) Musaffa API (alternative)
  - C) Build manual database (most control, most maintenance)
- **Recommendation:** Option A (Zoya) with Option C (manual database) as fallback

**Q3: ETF Holdings Data Source**
- **Question:** How to reliably obtain ETF holdings?
- **Options:**
  - A) Web scraping (free, fragile)
  - B) Paid API (reliable, ongoing cost)
  - C) Manual CSV updates (labor-intensive)
- **Recommendation:** Option A (web scraping) for MVP, migrate to Option B for production

### 12.2 Product Decisions

**Q4: Freemium vs. Open-Source Model**
- **Question:** Should the CLI tool be fully open-source, or have premium features?
- **Options:**
  - A) Fully open-source (community-driven)
  - B) Freemium (basic free, advanced paid)
  - C) Open-core (core engine open, premium plugins paid)
- **Recommendation:** Option A for MVP, Option C for future sustainability

**Q5: Default Strategy Configuration**
- **Question:** Should default strategy be modifiable, or locked?
- **Recommendation:** Modifiable (user can adjust thresholds) but not deletable

**Q6: Portfolio Limit**
- **Question:** Should there be a limit on portfolio size?
- **Recommendation:** No hard limit for MVP, but warn if > 50 holdings (performance considerations)

### 12.3 Compliance Questions

**Q7: Investment Advice Disclaimer**
- **Question:** What disclaimers are legally required?
- **Action Required:** Consult legal advisor for EU/US investment advice regulations

**Q8: Shariah Compliance Certification**
- **Question:** Should we seek formal Shariah certification?
- **Recommendation:** Not required for MVP, but pursue for Phase 2 credibility

---

## 13. Appendix

### 13.1 Glossary

- **AAOIFI:** Accounting and Auditing Organization for Islamic Financial Institutions
- **B-XTrender:** Proprietary momentum indicator using color-coded signals
- **EPS:** Earnings Per Share
- **ETF:** Exchange-Traded Fund
- **Halal:** Permissible according to Islamic law
- **Haram:** Prohibited according to Islamic law
- **KID:** Key Information Document (EU regulatory requirement)
- **MCDX:** Multi-Color Divergence/Convergence Index (smart money indicator)
- **P/E Ratio:** Price-to-Earnings ratio
- **PRIIPs:** Packaged Retail and Insurance-based Investment Products (EU regulation)
- **Shariah:** Islamic law
- **SMA:** Simple Moving Average
- **UCITS:** Undertakings for Collective Investment in Transferable Securities (EU fund standard)

### 13.2 References

**Islamic Finance:**
- AAOIFI Shariah Standards: https://aaoifi.com/
- Shariah Stock Screening Methodologies: [Academic papers on Islamic finance screening]

**Technical Analysis:**
- TradingView Pine Script Documentation: https://www.tradingview.com/pine-script-docs/
- Technical Analysis Library (TA-Lib): https://ta-lib.org/

**APIs & Data Sources:**
- Yahoo Finance: https://finance.yahoo.com/
- Zoya (Halal Investing): https://www.zoya.finance/
- Alpha Vantage: https://www.alphavantage.co/

**CLI Development:**
- Rich (Python library): https://rich.readthedocs.io/
- Typer (CLI framework): https://typer.tiangolo.com/

### 13.3 Document History

| Version | Date       | Author | Changes                     |
|---------|------------|--------|-----------------------------|
| 1.0     | 2025-11-10 | AI     | Initial PRD creation        |

---

## Document Approval

**Prepared By:** The Halal Momentum Analyst (AI)
**Review Required By:** Strategy System Architect Agent
**Approval Required By:** Product Owner / Stakeholders

**Next Steps:**
1. **Strategy System Architect:** Review PRD and create detailed architecture design document
2. **Architect Deliverables Expected:**
   - Component diagram with dependencies
   - Database schema design (SQLite)
   - API gateway interface specifications
   - Service layer class diagrams
   - Deployment/packaging strategy
   - Technology stack validation/refinements
3. **Pragmatic Developer:** Implement architecture once approved
4. Begin Phase 1 (MVP) development sprint planning

---

## Architect's Implementation Checklist

### Critical Architectural Decisions Required

**1. Dependency Injection Framework**
- [ ] Evaluate options: `dependency-injector`, `injector`, or manual DI
- [ ] Recommendation: Design for testability with constructor injection

**2. Async vs. Sync Data Fetching**
- [ ] Decision: Use `asyncio` with `aiohttp` for parallel API calls?
- [ ] Alternative: Thread pools with `concurrent.futures`?
- [ ] Consideration: CLI simplicity vs. performance gains

**3. Database Schema Design**
- [ ] Tables needed:
  - `portfolios` (id, name, created_at, updated_at)
  - `holdings` (id, portfolio_id, ticker, shares, avg_cost, added_at)
  - `strategies` (id, name, description, conditions_json, created_at, version)
  - `cache_stock_prices` (ticker, date, open, high, low, close, volume, cached_at)
  - `cache_compliance` (ticker, is_compliant, reason, cached_at, expires_at)
  - `cache_fundamentals` (ticker, data_json, cached_at, expires_at)
- [ ] Design indexes for performance
- [ ] Migration strategy for schema changes

**4. Configuration Management**
- [ ] Config file location: `~/.stock-strategy-cli/config.json`
- [ ] Environment variables for sensitive data: API keys
- [ ] Strategy storage: SQLite or JSON files?
- [ ] Recommendation: JSON for strategies (portability), SQLite for data

**5. Error Handling Hierarchy**
```python
# Proposed exception hierarchy
class StockStrategyCLIException(Exception):
    """Base exception for all application errors"""

class UserInputError(StockStrategyCLIException):
    """Invalid user input (4xx equivalent)"""

class DataProviderException(StockStrategyCLIException):
    """External API/data provider issues (5xx equivalent)"""

class ConfigurationError(StockStrategyCLIException):
    """Invalid configuration or missing API keys"""

class DataQualityException(StockStrategyCLIException):
    """Data validation failures"""
```

**6. Logging Strategy**
- [ ] Log levels: DEBUG for development, INFO for production
- [ ] Log rotation: Daily rotation, keep 7 days
- [ ] Log format: Include timestamp, level, module, message
- [ ] Separate logs: `app.log` (general), `exclusions.log` (halal filtering audit)

**7. CLI Framework Selection**
- [ ] Validate: Typer + Rich + Questionary combination
- [ ] Alternative consideration: Click + Rich
- [ ] Decision rationale: Type hints, documentation generation, interactivity

**8. Performance Optimization Priorities**
- [ ] P0: Implement caching with proper TTLs
- [ ] P0: Parallelize API calls (asyncio or threads)
- [ ] P1: Batch API requests where possible
- [ ] P1: Lazy loading of indicator calculations
- [ ] P2: Result pagination for large screening outputs

### Architectural Patterns to Apply

**SOLID Principles Enforcement:**
1. **Single Responsibility:** Each service handles one domain concern
2. **Open/Closed:** Indicator registry allows extension without modification
3. **Liskov Substitution:** All IMarketDataGateway implementations are interchangeable
4. **Interface Segregation:** Narrow interfaces (IIndicator, IComplianceGateway)
5. **Dependency Inversion:** Services depend on abstractions, not concretions

**Design Patterns:**
1. **Strategy Pattern:** IIndicator interface for pluggable indicators
2. **Factory Pattern:** IndicatorRegistry creates indicator instances
3. **Repository Pattern:** Abstract data access (PortfolioRepository, StrategyRepository)
4. **Facade Pattern:** Service layer provides simple interface to complex subsystems
5. **Observer Pattern (Future):** For portfolio alerts and notifications

### Project Structure Recommendation

```
stock-strategy-cli/
├── pyproject.toml              # Poetry/pip-tools dependency management
├── README.md
├── .env.example                # Example environment variables
├── .gitignore
│
├── src/
│   └── stock_strategy_cli/
│       ├── __init__.py
│       ├── __main__.py         # CLI entry point
│       │
│       ├── cli/                # Presentation layer
│       │   ├── __init__.py
│       │   ├── main_menu.py
│       │   ├── screening_menu.py
│       │   ├── strategy_menu.py
│       │   ├── portfolio_menu.py
│       │   └── formatters.py   # Rich table formatters
│       │
│       ├── services/           # Application orchestration layer
│       │   ├── __init__.py
│       │   ├── screening_service.py
│       │   ├── strategy_service.py
│       │   └── portfolio_service.py
│       │
│       ├── strategy_engine/    # Business logic core
│       │   ├── __init__.py
│       │   ├── evaluator.py
│       │   ├── indicator_registry.py
│       │   ├── condition_evaluator.py
│       │   └── compliance_filter.py
│       │
│       ├── indicators/         # Indicator implementations
│       │   ├── __init__.py
│       │   ├── base.py         # IIndicator interface
│       │   ├── mcdx.py
│       │   ├── b_xtrender.py
│       │   ├── sma.py
│       │   └── fundamental.py
│       │
│       ├── gateways/           # Data access layer
│       │   ├── __init__.py
│       │   ├── market_data/
│       │   │   ├── base.py     # IMarketDataGateway
│       │   │   ├── yahoo_finance.py
│       │   │   └── alpha_vantage.py
│       │   ├── compliance/
│       │   │   ├── base.py     # IComplianceGateway
│       │   │   ├── zoya.py
│       │   │   ├── musaffa.py
│       │   │   └── local_db.py
│       │   └── fund_holdings/
│       │       ├── base.py
│       │       └── scraper.py
│       │
│       ├── infrastructure/     # Infrastructure layer
│       │   ├── __init__.py
│       │   ├── cache.py        # CacheManager
│       │   ├── rate_limiter.py
│       │   ├── repositories/
│       │   │   ├── portfolio_repo.py
│       │   │   └── strategy_repo.py
│       │   ├── config.py       # ConfigManager
│       │   └── logger.py
│       │
│       ├── models/             # Domain models & DTOs
│       │   ├── __init__.py
│       │   ├── screening.py    # ScreeningResult, StockMatch, etc.
│       │   ├── strategy.py     # Strategy, StrategyCondition
│       │   ├── portfolio.py    # Portfolio, Holding
│       │   ├── compliance.py   # ComplianceStatus, ExclusionReason
│       │   └── market_data.py  # StockPrice, FundamentalData
│       │
│       ├── exceptions.py       # Custom exception hierarchy
│       └── constants.py        # Enums, constants
│
├── tests/
│   ├── unit/
│   │   ├── test_indicators/
│   │   ├── test_strategy_engine/
│   │   └── test_services/
│   ├── integration/
│   │   ├── test_screening_workflow.py
│   │   └── test_portfolio_workflow.py
│   ├── fixtures/
│   │   ├── sample_stock_data.json
│   │   └── mock_api_responses/
│   └── conftest.py             # Pytest fixtures
│
├── docs/
│   ├── architecture.md         # To be created by architect
│   ├── api_contracts.md
│   └── development_guide.md
│
└── scripts/
    ├── setup_dev_env.sh
    └── run_tests.sh
```

### Key Architectural Principles for Implementation

**1. Separation of Concerns**
- CLI layer NEVER imports from `gateways` or `indicators` directly
- Services orchestrate but don't implement business logic
- Strategy engine is framework-agnostic (no CLI dependencies)

**2. Testability First**
- Every component has a corresponding interface/ABC
- Constructor injection for all dependencies
- No global state (Singleton pattern used sparingly)

**3. Performance Through Design**
- Async-first for I/O-bound operations (if using asyncio)
- Caching at gateway layer (transparent to services)
- Batch operations exposed at service layer

**4. Fail-Safe Compliance**
- Compliance check is FIRST operation, fail-fast if uncertain
- All exclusions logged with full audit trail
- No "soft" compliance checks (binary: compliant or excluded)

**5. Future-Proofing**
- Core engine can be extracted as standalone library
- Service layer provides REST-compatible interfaces (future API)
- Data models use dataclasses (easy serialization for future web app)

### Technology Stack Validation Checklist

**Required Libraries (verify compatibility):**
- [ ] Python 3.11+ (for modern type hints)
- [ ] `typer` >= 0.9.0 (CLI framework)
- [ ] `rich` >= 13.0.0 (terminal formatting)
- [ ] `questionary` >= 2.0.0 (interactive prompts)
- [ ] `pandas` >= 2.0.0 (data manipulation)
- [ ] `numpy` >= 1.24.0 (numerical calculations)
- [ ] `yfinance` >= 0.2.0 (Yahoo Finance API)
- [ ] `aiohttp` >= 3.9.0 (async HTTP client, if using async)
- [ ] `requests` >= 2.31.0 (sync HTTP client fallback)
- [ ] `SQLAlchemy` >= 2.0.0 (ORM for SQLite, optional)
- [ ] `pydantic` >= 2.0.0 (data validation, optional)
- [ ] `pytest` >= 7.4.0 (testing)
- [ ] `pytest-asyncio` (if using async)
- [ ] `pytest-mock` >= 3.12.0 (mocking)
- [ ] `pytest-cov` >= 4.1.0 (coverage)

**Optional/Alternative Libraries:**
- [ ] `TA-Lib` (technical analysis, requires C dependencies)
- [ ] `alpaca-trade-api` (alternative market data)
- [ ] `python-dotenv` (environment variable management)
- [ ] `click` (alternative to Typer)

### Open Questions for Architect to Resolve

1. **Async or Sync?**
   - Trade-off: Asyncio complexity vs. 2-3x performance gain
   - Recommendation: Start sync, refactor to async if performance issues

2. **Indicator Calculation Frequency**
   - Calculate on-demand or pre-calculate and cache?
   - Recommendation: On-demand with 1-hour cache TTL

3. **Multi-Portfolio Support Priority**
   - MVP: Single default portfolio or multiple portfolios?
   - Recommendation: Single portfolio for MVP, add multi-portfolio in Phase 2

4. **Strategy Versioning**
   - Track strategy modification history?
   - Recommendation: Yes, increment version number on modification, keep history

5. **Export Format Priority**
   - CSV only or also JSON/Excel?
   - Recommendation: CSV for MVP, JSON for machine readability

6. **CLI Installation Method**
   - PyPI package, standalone binary (PyInstaller), or source install?
   - Recommendation: PyPI package for MVP, consider binary for wider distribution

### Architect Deliverables Timeline

**Phase 1: Architecture Design (Week 1)**
- [ ] Review PRD and clarify ambiguities
- [ ] Create high-level architecture document
- [ ] Design database schema
- [ ] Define service interfaces
- [ ] Validate technology stack choices

**Phase 2: Detailed Design (Week 2)**
- [ ] Create sequence diagrams for critical workflows
- [ ] Design error handling and logging strategy
- [ ] Define data models and DTOs
- [ ] Specify testing strategy and mock approach
- [ ] Document deployment and packaging approach

**Phase 3: Handoff to Developer (Week 3)**
- [ ] Code architecture proof-of-concept (optional)
- [ ] Create scaffold project structure
- [ ] Document implementation patterns and conventions
- [ ] Define development milestones
- [ ] Review with pragmatic-developer agent

---

*This PRD is a living document and will be updated as requirements evolve based on architectural decisions and implementation feedback.*
