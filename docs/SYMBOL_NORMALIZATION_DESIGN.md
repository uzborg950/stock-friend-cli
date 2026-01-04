# Symbol Normalization Architecture Design

## Problem Statement

Different data providers use different symbol formats for the same securities:
- **yfinance**: Ticker with market suffix (e.g., "BMW.DE", "AAPL")
- **Zoya Compliance**: Base ticker with Bloomberg exchange codes (e.g., "BMW", exchange="GR")
- **Alpha Vantage**: Different conventions

Without normalization, compliance data cannot reliably match market data, causing:
- False negatives (compliant stocks marked unknown)
- False positives (non-compliant stocks slip through)
- Audit trail issues
- Loss of professional credibility

## Solution: Symbol Normalization Service

### Design Principles

1. **Single Source of Truth**: StockData model contains both gateway-specific and normalized identifiers
2. **Explicit Exchange**: Always store which exchange the data represents
3. **Transparent to User**: User searches with familiar tickers (AAPL, BMW.DE)
4. **Gateway Abstraction**: Normalization happens in service layer, not gateways
5. **Audit Trail**: Log all symbol transformations for debugging
6. **Conservative Screening**: When uncertain, mark as unknown (maintain zero false positives)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Input: "BMW.DE"                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           UniverseGateway (yfinance)                        │
│  Returns: StockData(                                        │
│    ticker="BMW.DE",                                         │
│    exchange="FRA",                                          │
│    isin="DE0005190003"  # Future                            │
│  )                                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         SymbolNormalizationService                          │
│  1. Extract base symbol: "BMW.DE" → "BMW"                  │
│  2. Map exchange code: "FRA" → "GR" (Bloomberg)            │
│  3. Detect market type: EU stock vs US stock               │
│  4. Generate normalized symbol: "BMW"                       │
│  5. Log transformation for audit                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         ComplianceGateway (Zoya)                            │
│  Checks: "BMW" with context from normalization             │
│  Returns: ComplianceStatus                                  │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 3.5: Symbol Normalization Service (IMMEDIATE)

**Priority: CRITICAL - Blocks production use**

Create `src/stock_friend/services/symbol_normalization_service.py`:

```python
class SymbolNormalizationService:
    """
    Normalize stock symbols between different gateway formats.

    Responsibilities:
    - Remove market suffixes (.DE, .L, .F) from yfinance tickers
    - Map exchange codes between providers
    - Handle special cases (ADRs, preferred shares, dual listings)
    - Maintain audit trail of transformations
    """

    # Exchange suffix mappings (yfinance → description)
    EXCHANGE_SUFFIXES = {
        ".DE": "XETR",  # Deutsche Börse (Xetra)
        ".F": "XFRA",   # Frankfurt Stock Exchange
        ".L": "XLON",   # London Stock Exchange
        ".PA": "XPAR",  # Euronext Paris
        ".AS": "XAMS",  # Euronext Amsterdam
        ".MI": "XMIL",  # Borsa Italiana (Milan)
        # US markets have no suffix in yfinance
    }

    # Bloomberg exchange codes (for Zoya compatibility)
    BLOOMBERG_CODES = {
        "XNGS": "NASDAQ Global Select",
        "XNYS": "New York Stock Exchange",
        "XETR": "Deutsche Börse Xetra",
        "XLON": "London Stock Exchange",
        # ... more codes
    }

    def normalize_for_compliance(
        self,
        ticker: str,
        exchange: Optional[str] = None,
        source_gateway: str = "yfinance"
    ) -> NormalizedSymbol:
        """
        Normalize ticker for compliance gateway lookup.

        Args:
            ticker: Gateway-specific ticker (e.g., "BMW.DE", "AAPL")
            exchange: Exchange code from gateway (if available)
            source_gateway: Which gateway provided this symbol

        Returns:
            NormalizedSymbol with:
            - base_symbol: Clean ticker for compliance check ("BMW", "AAPL")
            - original_ticker: Original input for audit trail
            - exchange_code: Normalized exchange code
            - confidence: HIGH/MEDIUM/LOW (for unknown mappings)
            - notes: Explanation of transformation
        """

    def extract_base_symbol(self, ticker: str) -> str:
        """
        Remove exchange suffix from ticker.

        Examples:
            "BMW.DE" → "BMW"
            "AAPL" → "AAPL"
            "RDS.B" → "RDS.B" (class B shares, keep suffix)
        """

    def get_exchange_from_suffix(self, ticker: str) -> Optional[str]:
        """
        Extract exchange code from ticker suffix.

        Examples:
            "BMW.DE" → "XETR"
            "AAPL" → None (US market, no suffix)
        """
```

**Data Structure:**
```python
@dataclass
class NormalizedSymbol:
    """Normalized symbol with audit trail."""

    base_symbol: str  # Clean ticker for compliance check
    original_ticker: str  # Original input (audit trail)
    exchange_code: Optional[str]  # Bloomberg-style code
    market_region: str  # "US", "EU", "UK", etc.
    confidence: SymbolConfidence  # HIGH, MEDIUM, LOW
    transformation_notes: List[str]  # What was done
    timestamp: datetime  # When normalized
```

### Phase 4: ISIN Integration (STRATEGIC)

**Priority: HIGH - Production enhancement**

**Why ISIN?**
- **Universal Standard**: ISO 6166 international standard
- **Unique Identifier**: US0378331005 = Apple Inc, regardless of exchange
- **Both Gateways Support It**: yfinance can fetch ISIN, Zoya accepts it
- **Handles Multi-Listing**: Same ISIN for stock listed on multiple exchanges
- **Regulatory Compliant**: Used in official financial reporting

**Implementation:**

1. **Update StockData Model:**
```python
@dataclass
class StockData:
    ticker: str  # Gateway-specific (e.g., "BMW.DE")
    exchange: str  # Gateway-specific code
    isin: Optional[str] = None  # Universal identifier (NEW)
    sedol: Optional[str] = None  # UK identifier (Future)
    # ... existing fields
```

2. **Update Gateways to Fetch ISIN:**
```python
# In YFinanceGateway
def get_stock_data(self, ticker: str) -> StockData:
    info = yf.Ticker(ticker).info
    return StockData(
        ticker=ticker,
        isin=info.get("isin"),  # Fetch if available
        # ...
    )
```

3. **ISIN-Based Compliance Lookup:**
```python
# In ComplianceService
def check_compliance(self, stock: StockData) -> ComplianceStatus:
    # Priority 1: Use ISIN if available (most accurate)
    if stock.isin:
        return compliance_gateway.check_by_isin(stock.isin)

    # Priority 2: Use normalized symbol
    normalized = normalization_service.normalize_for_compliance(
        stock.ticker,
        stock.exchange
    )

    if normalized.confidence == SymbolConfidence.LOW:
        logger.warning(f"Low confidence mapping: {normalized.transformation_notes}")

    return compliance_gateway.check_compliance(normalized.base_symbol)
```

## Edge Cases & Special Handling

### 1. American Depositary Receipts (ADRs)
```
Example: "DTEGY" (Deutsche Telekom ADR)
- US-traded, but represents German company
- Different compliance profile than "DTE.DE"
- Solution: Keep separate, use ISIN to distinguish
```

### 2. Dual-Class Shares
```
Example: "BRK.A" vs "BRK.B" (Berkshire Hathaway)
- Different share classes, same compliance
- Solution: Preserve class suffix in base_symbol
```

### 3. Preferred Shares
```
Example: "BAC-PL" (Bank of America Preferred)
- Different instrument type
- Solution: Preserve preferred indicator
```

### 4. Unknown Exchanges
```
Example: New exchange not in mapping table
- Solution: Return LOW confidence, log for manual review
- Conservative: Mark as unknown rather than guess
```

## Integration with Existing Services

### ComplianceService Enhancement

```python
class ComplianceService:
    """
    Orchestrates compliance checking with symbol normalization.
    """

    def __init__(
        self,
        compliance_gateway: IComplianceGateway,
        normalization_service: SymbolNormalizationService,
    ):
        self.gateway = compliance_gateway
        self.normalizer = normalization_service

    def check_stock_compliance(self, stock: StockData) -> ComplianceStatus:
        """
        Check compliance with automatic symbol normalization.

        Handles:
        - Symbol format conversion
        - ISIN-based lookup (when available)
        - Audit trail logging
        - Error handling for unmappable symbols
        """

        # Try ISIN first (most accurate)
        if stock.isin:
            try:
                return self.gateway.check_by_isin(stock.isin)
            except NotImplementedError:
                pass  # Gateway doesn't support ISIN, fall back

        # Normalize symbol
        normalized = self.normalizer.normalize_for_compliance(
            stock.ticker,
            stock.exchange,
        )

        # Log transformation for audit
        logger.info(
            f"Symbol normalization: {stock.ticker} → {normalized.base_symbol} "
            f"(confidence: {normalized.confidence})"
        )

        # Check compliance with normalized symbol
        status = self.gateway.check_compliance(normalized.base_symbol)

        # Attach normalization metadata to status
        status.normalization_info = normalized

        return status
```

## Testing Strategy

### Unit Tests
- Test all exchange suffix removals
- Test edge cases (dual-class, ADRs, preferred)
- Test confidence scoring
- Test audit trail generation

### Integration Tests
- Test full flow: yfinance → normalization → Zoya
- Test with real European stocks (BMW.DE, DTE.DE)
- Test with US stocks (AAPL, MSFT)
- Test unknown exchanges (should return LOW confidence)

### Data Quality Tests
- Validate mapping tables completeness
- Test against known ISIN database
- Compare normalized results with manual verification

## Configuration

Add to `.env`:
```bash
# Symbol Normalization
SYMBOL_NORMALIZATION_ENABLED=true
SYMBOL_NORMALIZATION_LOG_LEVEL=INFO
SYMBOL_NORMALIZATION_CONFIDENCE_THRESHOLD=MEDIUM  # Reject LOW confidence
```

## Monitoring & Observability

### Metrics to Track
- Symbol normalization success rate
- Confidence level distribution (HIGH/MEDIUM/LOW)
- Unmappable symbols (requires manual review)
- ISIN lookup success rate
- Symbol transformation cache hit rate

### Logging
```python
logger.info(f"Symbol normalized: {original} → {normalized} [confidence: {conf}]")
logger.warning(f"Low confidence mapping: {ticker} - {notes}")
logger.error(f"Unmappable symbol: {ticker} - unknown exchange {exchange}")
```

## Rollout Plan

**Week 1: Symbol Normalization Service**
- Implement SymbolNormalizationService
- Add mapping tables for major exchanges
- Unit tests for all transformations

**Week 2: ComplianceService Integration**
- Update ComplianceService to use normalization
- Integration tests with real stocks
- Validate European stock handling

**Week 3: ISIN Support**
- Add ISIN to StockData model
- Update gateways to fetch ISIN
- Implement ISIN-based compliance lookup

**Week 4: Production Validation**
- Test with full S&P 500 + UCITS universe
- Manual spot-checks for accuracy
- Performance testing
- Documentation

## Success Criteria

- ✅ Zero false positives (non-compliant stocks marked compliant)
- ✅ <1% false negatives (compliant stocks marked unknown due to mapping issues)
- ✅ 95%+ HIGH confidence mappings for major markets (US, DE, UK, FR)
- ✅ Full audit trail for all symbol transformations
- ✅ <100ms normalization latency per symbol
- ✅ Support for S&P 500, NASDAQ-100, DAX-40, FTSE-100

## Analyst Perspective: Is This Worth It?

**YES - Critical for Production Use**

A professional financial analyst would say:

*"Symbol mapping is not a nice-to-have - it's the foundation of data integrity. Without it, I can't trust that the compliance data matches the stock I'm analyzing. Given that this tool targets European UCITS funds with German listings, symbol normalization is table stakes. Start with pragmatic normalization for major exchanges, then add ISIN support strategically. But don't go to production without this - it's the difference between a prototype and a professional tool."*

**Priority: CRITICAL - Must complete before Phase 3 is production-ready**
