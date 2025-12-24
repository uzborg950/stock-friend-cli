# Technical Requirements Document (TRD)
## stock-friend-cli: Halal-Compliant Stock Screening Tool

**Part 3: Indicator Architecture & Data Access Layer**

---

## Document Navigation

- **Part 1:** Architecture & Foundation
- **Part 2:** Data Models & Service Layer
- **Part 3:** Indicator Architecture & Data Access Layer (this document)
- **Part 4:** Integration, Security & Performance
- **Part 5:** Implementation & Testing Strategy

---

## Phase 8: IIndicator Interface & Registry

### 8.1 Complete IIndicator Abstract Base Class

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np

@dataclass
class IndicatorMetadata:
    """
    Metadata describing an indicator's characteristics.

    Used by UI to display indicator information and configuration options.
    """
    name: str
    display_name: str
    description: str
    category: str  # "momentum", "trend", "volatility", "volume", "fundamental"
    required_periods: int
    output_fields: List[str]  # Fields in signal dict (e.g., ["signal", "score"])
    configuration_schema: Dict[str, Any]  # JSON schema for user config
    author: str = "system"
    version: str = "1.0"

    def __str__(self) -> str:
        return f"{self.display_name} ({self.name})"


class IIndicator(ABC):
    """
    Abstract base class for all technical indicators.

    Design Principles:
    - Strategy Pattern: Each indicator is interchangeable
    - Open/Closed: Adding indicators doesn't modify strategy engine
    - Single Responsibility: Each indicator calculates one metric
    - Dependency Inversion: Strategy engine depends on this interface, not concrete implementations

    Implementation Guidelines:
    - Keep calculate() pure (no side effects)
    - Handle edge cases gracefully (insufficient data, NaN values)
    - Use vectorized pandas/numpy operations for performance
    - Document calculation methodology in docstrings
    - Provide sensible defaults for configuration parameters
    """

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate indicator values and add columns to DataFrame.

        This is the core calculation method. It must be pure and idempotent.

        Args:
            df: DataFrame with OHLCV data
                Required columns: ['date', 'open', 'high', 'low', 'close', 'volume']
                Index: DatetimeIndex or integer index
                Sorted: By date ascending (oldest first)

        Returns:
            Original DataFrame with added indicator columns
            New columns should follow naming convention: {indicator_name}_{field}
            Example: 'mcdx_signal', 'mcdx_score', 'xtrender_color'

        Raises:
            InsufficientDataError: If df has fewer rows than get_required_periods()
            ValueError: If required columns missing

        Performance:
            Target: <1 second for 200 data points
            Use vectorized operations, avoid Python loops

        Example:
            Input:  df with ['date', 'close', 'volume']
            Output: df with ['date', 'close', 'volume', 'mcdx_signal', 'mcdx_score']
        """
        pass

    @abstractmethod
    def get_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract current signal/status from most recent data point.

        This method interprets the calculated indicator values and returns
        a standardized signal dictionary.

        Args:
            df: DataFrame with indicator already calculated (via calculate())

        Returns:
            Dictionary with indicator-specific signal information
            Must include at least:
                - Primary signal field (e.g., "signal": "Banker")
                - Timestamp (e.g., "timestamp": "2025-11-10T10:23:00Z")
            Optional fields:
                - Numeric scores, confidence levels, additional context

        Example MCDX:
            {
                "signal": "Banker",
                "score": 0.15,
                "timestamp": "2025-11-10T10:23:00Z",
                "volume_ratio": 1.8
            }

        Example B-XTrender:
            {
                "color": "Green",
                "momentum": 0.08,
                "timestamp": "2025-11-10T10:23:00Z",
                "trend_strength": "strong"
            }
        """
        pass

    @abstractmethod
    def get_required_periods(self) -> int:
        """
        Return minimum number of data periods required for calculation.

        This determines how much historical data must be fetched.

        Returns:
            Integer number of periods (e.g., days for daily data)

        Example:
            MCDX requires 30 days: return 30
            SMA(200) requires 200 days: return 200
            B-XTrender requires 50 days: return 50

        Note:
            Add buffer for warmup periods if needed.
            Example: If you need 20-period MA, request 25 to handle NaN at start.
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Return unique indicator identifier.

        Returns:
            Unique string identifier (lowercase, alphanumeric + underscore)
            Used as key in indicator registry

        Example:
            "mcdx", "b_xtrender", "sma", "rsi"

        Note:
            Must be unique across all indicators
            Used in strategy configuration and database keys
        """
        pass

    @abstractmethod
    def get_metadata(self) -> IndicatorMetadata:
        """
        Return indicator metadata for UI and configuration.

        Returns:
            IndicatorMetadata object with full indicator description

        Example:
            IndicatorMetadata(
                name="mcdx",
                display_name="MCDX",
                description="Multi-Color Divergence Index for institutional accumulation",
                category="volume",
                required_periods=30,
                output_fields=["signal", "score"],
                configuration_schema={...}
            )
        """
        pass

    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate input DataFrame meets requirements.

        Override this method to add custom validation logic.

        Args:
            df: DataFrame to validate

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails with descriptive message
        """
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']

        for col in required_columns:
            if col not in df.columns:
                raise ValueError(
                    f"Missing required column: {col}. "
                    f"Available: {list(df.columns)}"
                )

        if len(df) < self.get_required_periods():
            raise InsufficientDataError(
                f"{self.get_name()} requires {self.get_required_periods()} periods, "
                f"but only {len(df)} provided"
            )

        # Check for excessive NaN values
        nan_pct = df[['open', 'high', 'low', 'close', 'volume']].isna().mean().mean()
        if nan_pct > 0.1:  # More than 10% NaN
            raise ValueError(f"Excessive missing data: {nan_pct:.1%} NaN values")

        return True

    def handle_insufficient_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle case where insufficient data is available.

        Override to provide custom handling (e.g., partial calculation).

        Args:
            df: DataFrame with insufficient data

        Returns:
            DataFrame with NaN values in indicator columns

        Default behavior: Add indicator columns filled with NaN
        """
        indicator_name = self.get_name()
        metadata = self.get_metadata()

        for field in metadata.output_fields:
            df[f"{indicator_name}_{field}"] = np.nan

        return df


class InsufficientDataError(Exception):
    """Raised when insufficient data periods are available for indicator calculation."""
    pass
```

---

### 8.2 IndicatorRegistry Implementation

```python
from typing import Type, Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class IndicatorRegistry:
    """
    Singleton registry for managing indicator instances.

    Responsibilities:
    - Register indicator classes
    - Instantiate indicators with configuration
    - List available indicators
    - Provide indicator metadata

    Design Pattern: Singleton + Factory
    """

    _instance: Optional['IndicatorRegistry'] = None
    _indicators: Dict[str, Type[IIndicator]] = {}
    _metadata_cache: Dict[str, IndicatorMetadata] = {}

    def __new__(cls) -> 'IndicatorRegistry':
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._indicators = {}
            cls._instance._metadata_cache = {}
        return cls._instance

    def register(self, indicator_class: Type[IIndicator], override: bool = False):
        """
        Register an indicator class.

        Args:
            indicator_class: Class implementing IIndicator
            override: Allow overriding existing registration

        Raises:
            ValueError: If indicator name already registered and override=False
            TypeError: If class doesn't implement IIndicator

        Example:
            registry = IndicatorRegistry()
            registry.register(MCDXIndicator)
            registry.register(BXTrenderIndicator)
        """
        if not issubclass(indicator_class, IIndicator):
            raise TypeError(
                f"{indicator_class.__name__} must implement IIndicator interface"
            )

        # Instantiate to get name (use default config)
        try:
            temp_instance = indicator_class()
            indicator_name = temp_instance.get_name()
        except Exception as e:
            raise ValueError(
                f"Failed to instantiate {indicator_class.__name__}: {e}"
            )

        if indicator_name in self._indicators and not override:
            raise ValueError(
                f"Indicator '{indicator_name}' already registered. "
                f"Use override=True to replace."
            )

        self._indicators[indicator_name] = indicator_class

        # Cache metadata
        self._metadata_cache[indicator_name] = temp_instance.get_metadata()

        logger.info(
            f"Registered indicator: {indicator_name} "
            f"({indicator_class.__name__})"
        )

    def get_indicator(self,
                     name: str,
                     config: Optional[Dict[str, Any]] = None) -> IIndicator:
        """
        Instantiate an indicator by name with optional configuration.

        Args:
            name: Indicator name (from get_name())
            config: Optional configuration dict matching indicator's schema

        Returns:
            Configured indicator instance

        Raises:
            KeyError: If indicator not registered
            ValueError: If configuration invalid

        Example:
            # With default configuration
            mcdx = registry.get_indicator("mcdx")

            # With custom configuration
            mcdx = registry.get_indicator("mcdx", {
                "volume_period": 25,
                "threshold_banker": 0.12
            })

            # SMA with period
            sma = registry.get_indicator("sma", {"period": 50})
        """
        if name not in self._indicators:
            available = ", ".join(self._indicators.keys())
            raise KeyError(
                f"Indicator '{name}' not registered. "
                f"Available indicators: {available}"
            )

        indicator_class = self._indicators[name]

        try:
            if config:
                instance = indicator_class(**config)
            else:
                instance = indicator_class()

            return instance

        except TypeError as e:
            raise ValueError(
                f"Invalid configuration for {name}: {e}. "
                f"Check indicator's configuration schema."
            )

    def list_indicators(self) -> List[str]:
        """
        List all registered indicator names.

        Returns:
            List of indicator names (sorted alphabetically)

        Example:
            >>> registry.list_indicators()
            ['b_xtrender', 'mcdx', 'rsi', 'sma']
        """
        return sorted(self._indicators.keys())

    def get_metadata(self, name: str) -> IndicatorMetadata:
        """
        Get metadata for an indicator.

        Args:
            name: Indicator name

        Returns:
            IndicatorMetadata object

        Raises:
            KeyError: If indicator not registered

        Example:
            metadata = registry.get_metadata("mcdx")
            print(f"{metadata.display_name}: {metadata.description}")
            print(f"Requires {metadata.required_periods} periods")
        """
        if name not in self._metadata_cache:
            raise KeyError(f"Indicator '{name}' not registered")

        return self._metadata_cache[name]

    def list_by_category(self, category: str) -> List[str]:
        """
        List indicators by category.

        Args:
            category: Category name ("momentum", "trend", "volume", etc.)

        Returns:
            List of indicator names in category

        Example:
            volume_indicators = registry.list_by_category("volume")
            # ['mcdx', 'obv', 'volume_profile']
        """
        return [
            name for name, metadata in self._metadata_cache.items()
            if metadata.category == category
        ]

    def unregister(self, name: str) -> bool:
        """
        Remove an indicator from registry.

        Args:
            name: Indicator name to remove

        Returns:
            True if removed, False if not found

        Note:
            Use with caution. Unregistering indicators may break existing strategies.
        """
        if name in self._indicators:
            del self._indicators[name]
            del self._metadata_cache[name]
            logger.info(f"Unregistered indicator: {name}")
            return True
        return False

    def clear(self):
        """
        Clear all registered indicators.

        Warning: This removes all indicators including built-ins.
                 Use only for testing or reinitialization.
        """
        self._indicators.clear()
        self._metadata_cache.clear()
        logger.warning("Cleared all registered indicators")


# Global registry instance
_global_registry = IndicatorRegistry()


def get_indicator_registry() -> IndicatorRegistry:
    """
    Get global indicator registry instance.

    Returns:
        Singleton IndicatorRegistry

    Example:
        from indicators import get_indicator_registry

        registry = get_indicator_registry()
        mcdx = registry.get_indicator("mcdx")
    """
    return _global_registry
```

---

### 8.3 Bootstrap and Auto-Registration

```python
def bootstrap_indicators():
    """
    Register all built-in indicators on module import.

    This function is called automatically when the indicators module is imported.
    It registers all standard indicators with the global registry.
    """
    registry = get_indicator_registry()

    # Register built-in indicators
    from .mcdx_indicator import MCDXIndicator
    from .b_xtrender_indicator import BXTrenderIndicator
    from .sma_indicator import SMAIndicator

    registry.register(MCDXIndicator)
    registry.register(BXTrenderIndicator)
    registry.register(SMAIndicator)

    logger.info(
        f"Bootstrapped indicators: {', '.join(registry.list_indicators())}"
    )


# Auto-register on module import
bootstrap_indicators()
```

---

### 8.4 Extensibility Example: Adding Custom Indicator

```python
"""
Example: Adding a custom RSI indicator

Demonstrates the extensibility of the indicator system.
"""

from indicators.base import IIndicator, IndicatorMetadata
from indicators import get_indicator_registry
import pandas as pd
import numpy as np
from typing import Dict, Any


class RSIIndicator(IIndicator):
    """
    Relative Strength Index (RSI) - Momentum oscillator.

    RSI measures the magnitude of recent price changes to evaluate
    overbought or oversold conditions.

    Calculation:
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss over period
    """

    def __init__(self,
                 period: int = 14,
                 overbought: float = 70,
                 oversold: float = 30):
        """
        Initialize RSI indicator.

        Args:
            period: Lookback period for RSI calculation
            overbought: Threshold for overbought condition (default: 70)
            oversold: Threshold for oversold condition (default: 30)
        """
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI values."""

        self.validate_data(df)

        # Calculate price changes
        delta = df['close'].diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gain and loss (exponential moving average)
        avg_gain = gain.ewm(span=self.period, adjust=False).mean()
        avg_loss = loss.ewm(span=self.period, adjust=False).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Add RSI column
        df['rsi_value'] = rsi

        # Classify signal
        df['rsi_signal'] = df['rsi_value'].apply(self._classify_signal)

        return df

    def _classify_signal(self, rsi_value: float) -> str:
        """Classify RSI value into signal category."""
        if pd.isna(rsi_value):
            return "unknown"
        elif rsi_value >= self.overbought:
            return "overbought"
        elif rsi_value <= self.oversold:
            return "oversold"
        else:
            return "neutral"

    def get_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get current RSI signal."""

        if 'rsi_value' not in df.columns:
            df = self.calculate(df)

        latest = df.iloc[-1]

        return {
            "value": float(latest['rsi_value']),
            "signal": latest['rsi_signal'],
            "timestamp": latest['date'].isoformat() if 'date' in df.columns else None,
            "overbought_threshold": self.overbought,
            "oversold_threshold": self.oversold
        }

    def get_required_periods(self) -> int:
        """RSI requires period + 1 for initial diff()."""
        return self.period + 1

    def get_name(self) -> str:
        return "rsi"

    def get_metadata(self) -> IndicatorMetadata:
        return IndicatorMetadata(
            name="rsi",
            display_name="RSI (Relative Strength Index)",
            description="Momentum oscillator measuring overbought/oversold conditions",
            category="momentum",
            required_periods=self.period + 1,
            output_fields=["value", "signal"],
            configuration_schema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "integer",
                        "minimum": 5,
                        "maximum": 50,
                        "default": 14,
                        "description": "Lookback period for RSI calculation"
                    },
                    "overbought": {
                        "type": "number",
                        "minimum": 50,
                        "maximum": 90,
                        "default": 70,
                        "description": "Overbought threshold"
                    },
                    "oversold": {
                        "type": "number",
                        "minimum": 10,
                        "maximum": 50,
                        "default": 30,
                        "description": "Oversold threshold"
                    }
                }
            },
            author="custom",
            version="1.0"
        )


# Register the custom indicator
registry = get_indicator_registry()
registry.register(RSIIndicator)

# Now RSI can be used in strategies!
# No changes needed to StrategyEvaluator or any other core component.
```

---

## Phase 9: MCDX Indicator Specification

### 9.1 Technical Overview

**MCDX (Multi-Color Divergence Index)** is a proprietary volume-weighted indicator designed to identify institutional ("smart money") accumulation versus retail distribution. It analyzes price-volume relationships to detect divergences between price action and underlying buying/selling pressure.

**Core Concept:**
- **Banker Accumulation:** High volume with strong price momentum (institutions buying)
- **Smart Money:** Moderate volume with positive momentum (informed accumulation)
- **Neutral:** Balanced buying/selling
- **Retail Distribution:** High volume with weak/negative price momentum (retail selling)

**Data Source:** TradingView Pine Script (open-source implementation to be translated to Python)

---

### 9.2 Calculation Algorithm

#### Step 1: Calculate Price Momentum (Rate of Change)

```python
def calculate_price_momentum(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate price rate of change (momentum).

    Args:
        df: DataFrame with 'close' column
        period: Lookback period for momentum calculation

    Returns:
        Series of price momentum values

    Formula:
        momentum = (close_today - close_N_periods_ago) / close_N_periods_ago
    """
    close = df['close']
    momentum = close.pct_change(periods=period)
    return momentum
```

#### Step 2: Calculate Volume Ratio (Volume Strength)

```python
def calculate_volume_ratio(df: pd.DataFrame, ma_period: int = 20) -> pd.Series:
    """
    Calculate volume ratio relative to moving average.

    Args:
        df: DataFrame with 'volume' column
        ma_period: Period for volume moving average

    Returns:
        Series of volume ratios

    Formula:
        volume_ratio = current_volume / MA(volume, ma_period)

    Interpretation:
        > 1.5: High volume (institutional activity likely)
        1.0-1.5: Above average volume
        0.5-1.0: Below average volume
        < 0.5: Very low volume
    """
    volume = df['volume']
    volume_ma = volume.rolling(window=ma_period).mean()
    volume_ratio = volume / volume_ma
    return volume_ratio
```

#### Step 3: Calculate Divergence Score

```python
def calculate_divergence_score(price_momentum: pd.Series,
                               volume_ratio: pd.Series,
                               smoothing_period: int = 5) -> pd.Series:
    """
    Calculate divergence score from price momentum and volume ratio.

    Args:
        price_momentum: Price rate of change
        volume_ratio: Volume relative to average
        smoothing_period: Smoothing period for final score

    Returns:
        Series of divergence scores

    Formula:
        divergence = price_momentum * volume_ratio
        divergence_smoothed = MA(divergence, smoothing_period)

    Interpretation:
        High positive: Strong upward momentum with high volume (Banker)
        Moderate positive: Positive momentum with volume (Smart Money)
        Near zero: No clear directional bias (Neutral)
        Negative: Weak price with high volume (Retail distribution)
    """
    # Multiply price momentum by volume ratio
    # This amplifies signals when volume is high
    divergence = price_momentum * volume_ratio

    # Smooth the divergence to reduce noise
    divergence_smoothed = divergence.rolling(window=smoothing_period).mean()

    return divergence_smoothed
```

#### Step 4: Classify into Signals

```python
def classify_mcdx_signal(divergence_score: float,
                        threshold_banker: float = 0.10,
                        threshold_smart_money: float = 0.02,
                        threshold_retail: float = -0.05) -> str:
    """
    Classify divergence score into MCDX signal categories.

    Args:
        divergence_score: Calculated divergence score
        threshold_banker: Threshold for "Banker" signal
        threshold_smart_money: Threshold for "Smart Money" signal
        threshold_retail: Threshold for "Retail" signal (negative)

    Returns:
        Signal category: "Banker", "Smart Money", "Neutral", or "Retail"

    Thresholds (calibrated via backtesting):
        >= 0.10: Banker (strong institutional accumulation)
        >= 0.02: Smart Money (informed accumulation)
        > -0.05: Neutral (balanced)
        <= -0.05: Retail (distribution phase)
    """
    if pd.isna(divergence_score):
        return "Neutral"

    if divergence_score >= threshold_banker:
        return "Banker"
    elif divergence_score >= threshold_smart_money:
        return "Smart Money"
    elif divergence_score <= threshold_retail:
        return "Retail"
    else:
        return "Neutral"
```

---

### 9.3 Complete MCDX Implementation

```python
from dataclasses import dataclass
import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class MCDXIndicator(IIndicator):
    """
    MCDX (Multi-Color Divergence Index) Indicator.

    Identifies institutional accumulation vs retail distribution through
    volume-weighted price momentum analysis.

    Algorithm:
        1. Calculate price momentum (14-period ROC)
        2. Calculate volume ratio (volume / 20-period MA)
        3. Compute divergence: momentum * volume_ratio
        4. Smooth divergence (5-period MA)
        5. Classify into signals based on thresholds

    Signal Categories:
        - Banker: Strong institutional accumulation (score >= 0.10)
        - Smart Money: Informed accumulation (score >= 0.02)
        - Neutral: Balanced market (score -0.05 to 0.02)
        - Retail: Distribution phase (score <= -0.05)

    Performance:
        Target: <0.5 seconds for 200 data points
        Achieved via vectorized pandas operations
    """

    def __init__(self,
                 momentum_period: int = 14,
                 volume_ma_period: int = 20,
                 smoothing_period: int = 5,
                 threshold_banker: float = 0.10,
                 threshold_smart_money: float = 0.02,
                 threshold_retail: float = -0.05):
        """
        Initialize MCDX indicator with configurable parameters.

        Args:
            momentum_period: Period for price momentum calculation (default: 14)
            volume_ma_period: Period for volume moving average (default: 20)
            smoothing_period: Period for smoothing divergence (default: 5)
            threshold_banker: Threshold for Banker signal (default: 0.10)
            threshold_smart_money: Threshold for Smart Money signal (default: 0.02)
            threshold_retail: Threshold for Retail signal (default: -0.05)
        """
        self.momentum_period = momentum_period
        self.volume_ma_period = volume_ma_period
        self.smoothing_period = smoothing_period
        self.threshold_banker = threshold_banker
        self.threshold_smart_money = threshold_smart_money
        self.threshold_retail = threshold_retail

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate MCDX indicator values.

        Adds columns:
            - mcdx_price_momentum: Price rate of change
            - mcdx_volume_ratio: Volume relative to MA
            - mcdx_divergence: Raw divergence score
            - mcdx_score: Smoothed divergence score
            - mcdx_signal: Signal category (Banker, Smart Money, Neutral, Retail)

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added MCDX columns
        """
        # Validate input data
        self.validate_data(df)

        # Step 1: Calculate price momentum
        df['mcdx_price_momentum'] = df['close'].pct_change(periods=self.momentum_period)

        # Step 2: Calculate volume ratio
        volume_ma = df['volume'].rolling(window=self.volume_ma_period).mean()
        df['mcdx_volume_ratio'] = df['volume'] / volume_ma

        # Step 3: Calculate divergence
        df['mcdx_divergence'] = df['mcdx_price_momentum'] * df['mcdx_volume_ratio']

        # Step 4: Smooth divergence
        df['mcdx_score'] = df['mcdx_divergence'].rolling(window=self.smoothing_period).mean()

        # Step 5: Classify signals
        df['mcdx_signal'] = df['mcdx_score'].apply(self._classify_signal)

        # Log calculation summary
        logger.debug(
            f"MCDX calculated for {len(df)} periods. "
            f"Latest signal: {df['mcdx_signal'].iloc[-1]}, "
            f"score: {df['mcdx_score'].iloc[-1]:.4f}"
        )

        return df

    def _classify_signal(self, score: float) -> str:
        """Classify divergence score into signal category."""

        if pd.isna(score):
            return "Neutral"

        if score >= self.threshold_banker:
            return "Banker"
        elif score >= self.threshold_smart_money:
            return "Smart Money"
        elif score <= self.threshold_retail:
            return "Retail"
        else:
            return "Neutral"

    def get_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get current MCDX signal from most recent data point.

        Returns:
            Dictionary with signal information:
                - signal: Signal category (Banker, Smart Money, Neutral, Retail)
                - score: Divergence score (float)
                - volume_ratio: Current volume ratio (float)
                - momentum: Current price momentum (float)
                - timestamp: ISO timestamp (str)
        """
        # Calculate if not already done
        if 'mcdx_signal' not in df.columns:
            df = self.calculate(df)

        # Get latest row
        latest = df.iloc[-1]

        # Build signal dictionary
        signal = {
            "signal": latest['mcdx_signal'],
            "score": float(latest['mcdx_score']) if not pd.isna(latest['mcdx_score']) else None,
            "volume_ratio": float(latest['mcdx_volume_ratio']) if not pd.isna(latest['mcdx_volume_ratio']) else None,
            "momentum": float(latest['mcdx_price_momentum']) if not pd.isna(latest['mcdx_price_momentum']) else None,
            "timestamp": latest['date'].isoformat() if 'date' in df.columns else None
        }

        return signal

    def get_required_periods(self) -> int:
        """
        MCDX requires enough data for:
        - momentum_period for price momentum
        - volume_ma_period for volume moving average
        - smoothing_period for final smoothing

        Return max + buffer for edge cases.
        """
        required = max(
            self.momentum_period,
            self.volume_ma_period
        ) + self.smoothing_period

        return required + 5  # Buffer for warmup

    def get_name(self) -> str:
        return "mcdx"

    def get_metadata(self) -> IndicatorMetadata:
        return IndicatorMetadata(
            name="mcdx",
            display_name="MCDX (Multi-Color Divergence Index)",
            description="Volume-weighted indicator identifying institutional accumulation vs retail distribution",
            category="volume",
            required_periods=self.get_required_periods(),
            output_fields=["signal", "score", "volume_ratio", "momentum"],
            configuration_schema={
                "type": "object",
                "properties": {
                    "momentum_period": {
                        "type": "integer",
                        "minimum": 5,
                        "maximum": 30,
                        "default": 14,
                        "description": "Period for price momentum calculation"
                    },
                    "volume_ma_period": {
                        "type": "integer",
                        "minimum": 10,
                        "maximum": 50,
                        "default": 20,
                        "description": "Period for volume moving average"
                    },
                    "smoothing_period": {
                        "type": "integer",
                        "minimum": 3,
                        "maximum": 10,
                        "default": 5,
                        "description": "Smoothing period for divergence score"
                    },
                    "threshold_banker": {
                        "type": "number",
                        "minimum": 0.05,
                        "maximum": 0.20,
                        "default": 0.10,
                        "description": "Threshold for Banker signal"
                    },
                    "threshold_smart_money": {
                        "type": "number",
                        "minimum": 0.01,
                        "maximum": 0.10,
                        "default": 0.02,
                        "description": "Threshold for Smart Money signal"
                    },
                    "threshold_retail": {
                        "type": "number",
                        "minimum": -0.15,
                        "maximum": -0.02,
                        "default": -0.05,
                        "description": "Threshold for Retail signal (negative)"
                    }
                }
            },
            author="system",
            version="1.0"
        )


# Example usage
if __name__ == "__main__":
    # Sample data
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'date': dates,
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000000, 5000000, 100)
    })

    # Calculate MCDX
    mcdx = MCDXIndicator()
    df_with_mcdx = mcdx.calculate(df)

    # Get latest signal
    signal = mcdx.get_signal(df_with_mcdx)
    print(f"MCDX Signal: {signal['signal']}")
    print(f"Score: {signal['score']:.4f}")
    print(f"Volume Ratio: {signal['volume_ratio']:.2f}")
```

---

### 9.4 Testing and Validation

```python
import unittest
import pandas as pd
import numpy as np


class TestMCDXIndicator(unittest.TestCase):
    """Unit tests for MCDX indicator."""

    def setUp(self):
        """Create sample data for testing."""
        self.dates = pd.date_range('2024-01-01', periods=100, freq='D')
        self.df = pd.DataFrame({
            'date': self.dates,
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 102,
            'low': np.random.randn(100).cumsum() + 98,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000000, 5000000, 100)
        })

    def test_calculate_adds_required_columns(self):
        """Test that calculate() adds expected columns."""
        mcdx = MCDXIndicator()
        result = mcdx.calculate(self.df.copy())

        expected_columns = [
            'mcdx_price_momentum',
            'mcdx_volume_ratio',
            'mcdx_divergence',
            'mcdx_score',
            'mcdx_signal'
        ]

        for col in expected_columns:
            self.assertIn(col, result.columns, f"Missing column: {col}")

    def test_signal_categories(self):
        """Test that signals are valid categories."""
        mcdx = MCDXIndicator()
        result = mcdx.calculate(self.df.copy())

        valid_signals = {"Banker", "Smart Money", "Neutral", "Retail"}
        unique_signals = set(result['mcdx_signal'].dropna().unique())

        self.assertTrue(
            unique_signals.issubset(valid_signals),
            f"Invalid signals found: {unique_signals - valid_signals}"
        )

    def test_insufficient_data_raises_error(self):
        """Test that insufficient data raises InsufficientDataError."""
        mcdx = MCDXIndicator()
        short_df = self.df.head(10)  # Only 10 rows

        with self.assertRaises(InsufficientDataError):
            mcdx.calculate(short_df)

    def test_get_signal_returns_dict(self):
        """Test that get_signal() returns expected dictionary."""
        mcdx = MCDXIndicator()
        result = mcdx.calculate(self.df.copy())
        signal = mcdx.get_signal(result)

        self.assertIsInstance(signal, dict)
        self.assertIn('signal', signal)
        self.assertIn('score', signal)
        self.assertIn('volume_ratio', signal)
        self.assertIn('momentum', signal)

    def test_custom_thresholds(self):
        """Test custom threshold configuration."""
        mcdx = MCDXIndicator(
            threshold_banker=0.15,
            threshold_smart_money=0.05
        )

        self.assertEqual(mcdx.threshold_banker, 0.15)
        self.assertEqual(mcdx.threshold_smart_money, 0.05)

    def test_performance_target(self):
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

        mcdx = MCDXIndicator()

        start = time.time()
        mcdx.calculate(large_df)
        elapsed = time.time() - start

        self.assertLess(
            elapsed, 0.5,
            f"Performance target not met: {elapsed:.3f}s (target: <0.5s)"
        )


if __name__ == '__main__':
    unittest.main()
```

---

## Phase 10: B-XTrender Indicator Specification

### 10.1 Technical Overview

**B-XTrender** is a momentum-trend indicator that uses color coding (Green, Yellow, Red) to represent trend strength and direction. It combines exponential moving averages (EMAs) and momentum oscillators to identify sustained directional moves.

**Core Concept:**
- **Green:** Bullish momentum, confirmed uptrend (buy/hold zone)
- **Yellow:** Neutral/transitional, momentum weakening (caution zone)
- **Red:** Bearish momentum, confirmed downtrend (avoid/exit zone)

**Data Source:** TradingView Pine Script (B-XTrender or XTrender indicator)

---

### 10.2 Calculation Algorithm

#### Step 1: Calculate Fast and Slow EMAs

```python
def calculate_emas(df: pd.DataFrame,
                  fast_period: int = 12,
                  slow_period: int = 26) -> tuple[pd.Series, pd.Series]:
    """
    Calculate fast and slow exponential moving averages.

    Args:
        df: DataFrame with 'close' column
        fast_period: Period for fast EMA (default: 12)
        slow_period: Period for slow EMA (default: 26)

    Returns:
        Tuple of (ema_fast, ema_slow) Series
    """
    close = df['close']

    ema_fast = close.ewm(span=fast_period, adjust=False).mean()
    ema_slow = close.ewm(span=slow_period, adjust=False).mean()

    return ema_fast, ema_slow
```

#### Step 2: Calculate Momentum (EMA Difference)

```python
def calculate_momentum(ema_fast: pd.Series, ema_slow: pd.Series) -> pd.Series:
    """
    Calculate momentum as difference between fast and slow EMAs.

    Args:
        ema_fast: Fast EMA series
        ema_slow: Slow EMA series

    Returns:
        Momentum series

    Interpretation:
        Positive momentum: Fast EMA > Slow EMA (bullish)
        Negative momentum: Fast EMA < Slow EMA (bearish)
        Magnitude indicates strength
    """
    momentum = ema_fast - ema_slow
    return momentum
```

#### Step 3: Smooth Momentum (Signal Line)

```python
def smooth_momentum(momentum: pd.Series, signal_period: int = 9) -> pd.Series:
    """
    Apply smoothing to momentum using EMA.

    Args:
        momentum: Raw momentum series
        signal_period: Smoothing period (default: 9)

    Returns:
        Smoothed momentum (signal line)

    This reduces noise and provides clearer trend signals.
    """
    momentum_smooth = momentum.ewm(span=signal_period, adjust=False).mean()
    return momentum_smooth
```

#### Step 4: Classify into Color Zones

```python
def classify_xtrender_color(momentum_smooth: float,
                           threshold_green: float = 0.0,
                           threshold_red: float = -0.5) -> str:
    """
    Classify smoothed momentum into color zones.

    Args:
        momentum_smooth: Smoothed momentum value
        threshold_green: Threshold for green (bullish) zone
        threshold_red: Threshold for red (bearish) zone

    Returns:
        Color signal: "Green", "Yellow", or "Red"

    Thresholds (calibrated via backtesting):
        >= threshold_green (0.0): Green (bullish momentum)
        < threshold_green but > threshold_red: Yellow (neutral/weakening)
        <= threshold_red (-0.5): Red (bearish momentum)

    Note:
        Thresholds are relative to price scale. May need adjustment
        based on stock volatility (e.g., percentage-based thresholds).
    """
    if pd.isna(momentum_smooth):
        return "Yellow"

    if momentum_smooth >= threshold_green:
        return "Green"
    elif momentum_smooth <= threshold_red:
        return "Red"
    else:
        return "Yellow"
```

---

### 10.3 Complete B-XTrender Implementation

```python
class BXTrenderIndicator(IIndicator):
    """
    B-XTrender Momentum-Trend Indicator.

    Uses EMA-based momentum with color-coded signals to identify
    trend strength and direction.

    Algorithm:
        1. Calculate fast EMA (12-period) and slow EMA (26-period)
        2. Calculate momentum: fast_EMA - slow_EMA
        3. Smooth momentum with signal EMA (9-period)
        4. Classify into color zones based on thresholds

    Color Signals:
        - Green: Bullish momentum (momentum >= 0.0)
        - Yellow: Neutral/transitional (momentum -0.5 to 0.0)
        - Red: Bearish momentum (momentum <= -0.5)

    Performance:
        Target: <0.3 seconds for 200 data points
    """

    def __init__(self,
                 ema_fast_period: int = 12,
                 ema_slow_period: int = 26,
                 signal_period: int = 9,
                 threshold_green: float = 0.0,
                 threshold_red: float = -0.5):
        """
        Initialize B-XTrender indicator.

        Args:
            ema_fast_period: Fast EMA period (default: 12)
            ema_slow_period: Slow EMA period (default: 26)
            signal_period: Signal line smoothing period (default: 9)
            threshold_green: Threshold for green zone (default: 0.0)
            threshold_red: Threshold for red zone (default: -0.5)
        """
        self.ema_fast_period = ema_fast_period
        self.ema_slow_period = ema_slow_period
        self.signal_period = signal_period
        self.threshold_green = threshold_green
        self.threshold_red = threshold_red

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate B-XTrender indicator values.

        Adds columns:
            - xtrender_ema_fast: Fast EMA
            - xtrender_ema_slow: Slow EMA
            - xtrender_momentum: Raw momentum (fast - slow)
            - xtrender_momentum_smooth: Smoothed momentum (signal line)
            - xtrender_color: Color signal (Green, Yellow, Red)

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added B-XTrender columns
        """
        self.validate_data(df)

        # Step 1: Calculate EMAs
        df['xtrender_ema_fast'] = df['close'].ewm(
            span=self.ema_fast_period,
            adjust=False
        ).mean()

        df['xtrender_ema_slow'] = df['close'].ewm(
            span=self.ema_slow_period,
            adjust=False
        ).mean()

        # Step 2: Calculate momentum
        df['xtrender_momentum'] = df['xtrender_ema_fast'] - df['xtrender_ema_slow']

        # Step 3: Smooth momentum
        df['xtrender_momentum_smooth'] = df['xtrender_momentum'].ewm(
            span=self.signal_period,
            adjust=False
        ).mean()

        # Step 4: Classify color
        df['xtrender_color'] = df['xtrender_momentum_smooth'].apply(self._classify_color)

        logger.debug(
            f"B-XTrender calculated for {len(df)} periods. "
            f"Latest color: {df['xtrender_color'].iloc[-1]}, "
            f"momentum: {df['xtrender_momentum_smooth'].iloc[-1]:.4f}"
        )

        return df

    def _classify_color(self, momentum: float) -> str:
        """Classify momentum into color zone."""

        if pd.isna(momentum):
            return "Yellow"

        if momentum >= self.threshold_green:
            return "Green"
        elif momentum <= self.threshold_red:
            return "Red"
        else:
            return "Yellow"

    def get_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get current B-XTrender signal.

        Returns:
            Dictionary with signal information:
                - color: Color signal (Green, Yellow, Red)
                - momentum: Smoothed momentum value (float)
                - momentum_raw: Raw momentum (float)
                - trend_strength: Qualitative trend strength (strong, moderate, weak)
                - timestamp: ISO timestamp (str)
        """
        if 'xtrender_color' not in df.columns:
            df = self.calculate(df)

        latest = df.iloc[-1]

        # Calculate trend strength
        momentum_abs = abs(latest['xtrender_momentum_smooth'])
        if momentum_abs > 2.0:
            trend_strength = "strong"
        elif momentum_abs > 0.5:
            trend_strength = "moderate"
        else:
            trend_strength = "weak"

        signal = {
            "color": latest['xtrender_color'],
            "momentum": float(latest['xtrender_momentum_smooth']) if not pd.isna(latest['xtrender_momentum_smooth']) else None,
            "momentum_raw": float(latest['xtrender_momentum']) if not pd.isna(latest['xtrender_momentum']) else None,
            "trend_strength": trend_strength,
            "timestamp": latest['date'].isoformat() if 'date' in df.columns else None
        }

        return signal

    def get_required_periods(self) -> int:
        """
        B-XTrender requires enough data for:
        - slow EMA calculation
        - signal line smoothing

        Return slow_period + signal_period + buffer.
        """
        return self.ema_slow_period + self.signal_period + 5

    def get_name(self) -> str:
        return "b_xtrender"

    def get_metadata(self) -> IndicatorMetadata:
        return IndicatorMetadata(
            name="b_xtrender",
            display_name="B-XTrender",
            description="EMA-based momentum indicator with color-coded trend signals",
            category="momentum",
            required_periods=self.get_required_periods(),
            output_fields=["color", "momentum", "trend_strength"],
            configuration_schema={
                "type": "object",
                "properties": {
                    "ema_fast_period": {
                        "type": "integer",
                        "minimum": 5,
                        "maximum": 30,
                        "default": 12,
                        "description": "Fast EMA period"
                    },
                    "ema_slow_period": {
                        "type": "integer",
                        "minimum": 15,
                        "maximum": 50,
                        "default": 26,
                        "description": "Slow EMA period"
                    },
                    "signal_period": {
                        "type": "integer",
                        "minimum": 5,
                        "maximum": 20,
                        "default": 9,
                        "description": "Signal line smoothing period"
                    },
                    "threshold_green": {
                        "type": "number",
                        "minimum": -1.0,
                        "maximum": 1.0,
                        "default": 0.0,
                        "description": "Threshold for green (bullish) zone"
                    },
                    "threshold_red": {
                        "type": "number",
                        "minimum": -2.0,
                        "maximum": 0.0,
                        "default": -0.5,
                        "description": "Threshold for red (bearish) zone"
                    }
                }
            },
            author="system",
            version="1.0"
        )
```

---

## Phase 11: SMA and Additional Indicators

### 11.1 Simple Moving Average (SMA) Indicator

```python
class SMAIndicator(IIndicator):
    """
    Simple Moving Average (SMA) indicator.

    Calculates the arithmetic mean of closing prices over a specified period.

    Common Uses:
        - Trend identification (price above/below SMA)
        - Support/resistance levels
        - Golden Cross (SMA(50) crosses above SMA(200))
        - Death Cross (SMA(50) crosses below SMA(200))

    Common Periods:
        - SMA(20): Short-term trend (1 month)
        - SMA(50): Medium-term trend (2.5 months)
        - SMA(200): Long-term trend (1 year)
    """

    def __init__(self, period: int = 20):
        """
        Initialize SMA indicator.

        Args:
            period: Lookback period for moving average (default: 20)
        """
        if period < 1:
            raise ValueError("Period must be >= 1")

        self.period = period

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate SMA values.

        Adds columns:
            - sma_{period}: Simple moving average values

        Args:
            df: DataFrame with 'close' column

        Returns:
            DataFrame with added SMA column
        """
        self.validate_data(df)

        column_name = f"sma_{self.period}"
        df[column_name] = df['close'].rolling(window=self.period).mean()

        logger.debug(
            f"SMA({self.period}) calculated for {len(df)} periods. "
            f"Latest value: {df[column_name].iloc[-1]:.2f}"
        )

        return df

    def get_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get current SMA signal.

        Returns:
            Dictionary with:
                - value: SMA value
                - price: Current price
                - position: Price position relative to SMA ("above", "below", "at")
                - distance_pct: Percentage distance from SMA
                - timestamp: ISO timestamp
        """
        column_name = f"sma_{self.period}"

        if column_name not in df.columns:
            df = self.calculate(df)

        latest = df.iloc[-1]
        sma_value = latest[column_name]
        price = latest['close']

        # Determine position
        if pd.isna(sma_value):
            position = "unknown"
            distance_pct = None
        else:
            if price > sma_value:
                position = "above"
            elif price < sma_value:
                position = "below"
            else:
                position = "at"

            distance_pct = ((price - sma_value) / sma_value) * 100

        signal = {
            "value": float(sma_value) if not pd.isna(sma_value) else None,
            "price": float(price),
            "position": position,
            "distance_pct": float(distance_pct) if distance_pct is not None else None,
            "timestamp": latest['date'].isoformat() if 'date' in df.columns else None
        }

        return signal

    def get_required_periods(self) -> int:
        return self.period

    def get_name(self) -> str:
        return f"sma"

    def get_metadata(self) -> IndicatorMetadata:
        return IndicatorMetadata(
            name="sma",
            display_name=f"SMA({self.period})",
            description=f"Simple Moving Average over {self.period} periods",
            category="trend",
            required_periods=self.period,
            output_fields=["value", "position", "distance_pct"],
            configuration_schema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 500,
                        "default": 20,
                        "description": "Moving average period"
                    }
                }
            },
            author="system",
            version="1.0"
        )


# Helper function for Golden Cross detection
def detect_golden_cross(df: pd.DataFrame,
                       fast_period: int = 50,
                       slow_period: int = 200) -> bool:
    """
    Detect Golden Cross pattern (bullish signal).

    Golden Cross: Fast SMA crosses above Slow SMA

    Args:
        df: DataFrame with close prices
        fast_period: Fast SMA period (default: 50)
        slow_period: Slow SMA period (default: 200)

    Returns:
        True if Golden Cross detected in most recent period
    """
    if len(df) < slow_period + 1:
        return False

    # Calculate SMAs
    sma_fast = df['close'].rolling(window=fast_period).mean()
    sma_slow = df['close'].rolling(window=slow_period).mean()

    # Check last two periods
    cross_occurred = (
        sma_fast.iloc[-2] <= sma_slow.iloc[-2] and  # Was below/equal
        sma_fast.iloc[-1] > sma_slow.iloc[-1]       # Now above
    )

    return cross_occurred
```

---

### 11.2 Future Indicators (Phase 2 Specifications)

#### RSI (Relative Strength Index)

**Brief Specification:**
- **Purpose:** Momentum oscillator measuring overbought/oversold conditions
- **Calculation:** RSI = 100 - (100 / (1 + RS)), where RS = Avg Gain / Avg Loss
- **Periods:** Typically 14
- **Signals:** >70 overbought, <30 oversold
- **Implementation:** See extensibility example in Section 8.4

#### MACD (Moving Average Convergence Divergence)

**Brief Specification:**
- **Purpose:** Trend-following momentum indicator
- **Calculation:**
  - MACD Line = EMA(12) - EMA(26)
  - Signal Line = EMA(9) of MACD Line
  - Histogram = MACD Line - Signal Line
- **Signals:**
  - MACD crosses above signal: Bullish
  - MACD crosses below signal: Bearish
- **Implementation:** Similar to B-XTrender with additional signal line

---

## Phase 12: PortfolioService Interface (Complete)

```python
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PortfolioService:
    """
    Manages portfolio and holdings operations.

    Responsibilities:
    - Portfolio CRUD operations
    - Holdings management (add, update, remove)
    - Strategy validation on portfolio
    - Change detection between checks
    - Performance calculations
    - Portfolio export
    """

    def __init__(self,
                 portfolio_repository: 'IPortfolioRepository',
                 market_data_gateway: 'MarketDataGateway',
                 strategy_evaluator: 'StrategyEvaluator',
                 fundamental_gateway: 'FundamentalDataGateway'):
        self.repository = portfolio_repository
        self.market_gw = market_data_gateway
        self.strategy_eval = strategy_evaluator
        self.fundamental_gw = fundamental_gateway

    def create_portfolio(self, name: str) -> Portfolio:
        """
        Create a new portfolio.

        Args:
            name: Portfolio name (1-100 characters)

        Returns:
            Created Portfolio object

        Raises:
            ValueError: If name invalid

        Example:
            portfolio = service.create_portfolio("My Growth Portfolio")
        """
        if not name or len(name) > 100:
            raise ValueError("Portfolio name must be 1-100 characters")

        portfolio = Portfolio(name=name)
        saved = self.repository.save(portfolio)

        logger.info(f"Created portfolio: {saved.id} - {saved.name}")

        return saved

    def get_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        """
        Retrieve portfolio by ID with current market data.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            Portfolio with updated holding values, or None if not found

        Example:
            portfolio = service.get_portfolio("portfolio-id")
            print(f"Total value: ${portfolio.total_value}")
        """
        portfolio = self.repository.get(portfolio_id)

        if not portfolio:
            return None

        # Update holdings with current market data
        self._update_holdings_market_data(portfolio)

        return portfolio

    def list_portfolios(self) -> List[Portfolio]:
        """
        List all portfolios.

        Returns:
            List of Portfolio objects (sorted by creation date, newest first)
        """
        portfolios = self.repository.list_all()
        return sorted(portfolios, key=lambda p: p.created_at, reverse=True)

    def delete_portfolio(self, portfolio_id: str) -> bool:
        """
        Delete a portfolio and all its holdings.

        Args:
            portfolio_id: Portfolio ID to delete

        Returns:
            True if deleted, False if not found

        Example:
            success = service.delete_portfolio("portfolio-id")
        """
        success = self.repository.delete(portfolio_id)

        if success:
            logger.info(f"Deleted portfolio: {portfolio_id}")

        return success

    def add_holding(self,
                   portfolio_id: str,
                   ticker: str,
                   shares: int,
                   avg_cost: Decimal) -> Holding:
        """
        Add a stock holding to portfolio.

        Args:
            portfolio_id: Portfolio ID
            ticker: Stock ticker symbol
            shares: Number of shares
            avg_cost: Average cost per share

        Returns:
            Created Holding object

        Raises:
            PortfolioNotFoundException: If portfolio not found
            ValueError: If ticker already exists in portfolio or invalid params

        Example:
            holding = service.add_holding(
                portfolio_id="portfolio-id",
                ticker="AAPL",
                shares=100,
                avg_cost=Decimal("150.00")
            )
        """
        portfolio = self.repository.get(portfolio_id)
        if not portfolio:
            raise PortfolioNotFoundException(f"Portfolio not found: {portfolio_id}")

        # Create holding
        holding = Holding(
            ticker=ticker.upper(),
            shares=shares,
            avg_cost=avg_cost
        )

        # Add to portfolio (validates uniqueness)
        portfolio.add_holding(holding)

        # Save portfolio
        self.repository.update(portfolio)

        logger.info(
            f"Added holding to portfolio {portfolio_id}: "
            f"{ticker} - {shares} shares @ ${avg_cost}"
        )

        return holding

    def update_holding(self,
                      portfolio_id: str,
                      ticker: str,
                      shares: Optional[int] = None,
                      avg_cost: Optional[Decimal] = None) -> Holding:
        """
        Update an existing holding.

        Args:
            portfolio_id: Portfolio ID
            ticker: Stock ticker symbol
            shares: New share count (optional)
            avg_cost: New average cost (optional)

        Returns:
            Updated Holding object

        Raises:
            PortfolioNotFoundException: If portfolio not found
            HoldingNotFoundException: If holding not found

        Example:
            # Update share count
            holding = service.update_holding(
                portfolio_id="portfolio-id",
                ticker="AAPL",
                shares=150
            )
        """
        portfolio = self.repository.get(portfolio_id)
        if not portfolio:
            raise PortfolioNotFoundException(f"Portfolio not found: {portfolio_id}")

        holding = portfolio.get_holding(ticker.upper())
        if not holding:
            raise HoldingNotFoundException(
                f"Holding not found: {ticker} in portfolio {portfolio_id}"
            )

        # Update fields
        if shares is not None:
            object.__setattr__(holding, 'shares', shares)

        if avg_cost is not None:
            object.__setattr__(holding, 'avg_cost', avg_cost)

        # Save portfolio
        self.repository.update(portfolio)

        logger.info(f"Updated holding: {ticker} in portfolio {portfolio_id}")

        return holding

    def remove_holding(self, portfolio_id: str, ticker: str) -> bool:
        """
        Remove a holding from portfolio.

        Args:
            portfolio_id: Portfolio ID
            ticker: Stock ticker to remove

        Returns:
            True if removed, False if not found

        Example:
            success = service.remove_holding("portfolio-id", "AAPL")
        """
        portfolio = self.repository.get(portfolio_id)
        if not portfolio:
            return False

        removed = portfolio.remove_holding(ticker.upper())

        if removed:
            self.repository.update(portfolio)
            logger.info(f"Removed holding: {ticker} from portfolio {portfolio_id}")

        return removed

    def run_strategy_check(self,
                          portfolio_id: str,
                          strategy_id: str) -> 'PortfolioAnalysis':
        """
        Run strategy validation on all portfolio holdings.

        Args:
            portfolio_id: Portfolio ID
            strategy_id: Strategy ID to apply

        Returns:
            PortfolioAnalysis with categorized holdings and recommendations

        Raises:
            PortfolioNotFoundException: If portfolio not found
            StrategyNotFoundException: If strategy not found

        Example:
            analysis = service.run_strategy_check("portfolio-id", "default-strategy")
            print(f"Strong: {len(analysis.strong_holdings)}")
            print(f"Weakening: {len(analysis.weakening_holdings)}")
            print(f"Lost Signal: {len(analysis.lost_signal_holdings)}")
        """
        portfolio = self.repository.get(portfolio_id)
        if not portfolio:
            raise PortfolioNotFoundException(f"Portfolio not found: {portfolio_id}")

        # Update with current market data
        self._update_holdings_market_data(portfolio)

        # Analyze each holding
        strong = []
        weakening = []
        lost_signal = []

        for holding in portfolio.holdings:
            analysis = self._analyze_holding(holding, strategy_id, portfolio_id)

            if analysis.status == HoldingStatus.STRONG:
                strong.append(analysis)
            elif analysis.status == HoldingStatus.WEAKENING:
                weakening.append(analysis)
            elif analysis.status == HoldingStatus.LOST_SIGNAL:
                lost_signal.append(analysis)

        # Build portfolio analysis
        portfolio_analysis = PortfolioAnalysis(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio.name,
            strategy_id=strategy_id,
            check_date=datetime.now(),
            strong_holdings=strong,
            weakening_holdings=weakening,
            lost_signal_holdings=lost_signal,
            total_holdings=len(portfolio.holdings)
        )

        logger.info(
            f"Strategy check complete for portfolio {portfolio_id}: "
            f"{len(strong)} strong, {len(weakening)} weakening, {len(lost_signal)} lost"
        )

        return portfolio_analysis

    def get_portfolio_summary(self, portfolio_id: str) -> 'PortfolioSummary':
        """
        Get summary statistics for portfolio.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            PortfolioSummary with aggregate metrics

        Raises:
            PortfolioNotFoundException: If portfolio not found

        Example:
            summary = service.get_portfolio_summary("portfolio-id")
            print(f"Total Value: ${summary.total_value}")
            print(f"Total Gain/Loss: ${summary.total_gain_loss} ({summary.total_gain_loss_pct}%)")
            print(f"Top Performer: {summary.top_performer.ticker}")
        """
        portfolio = self.repository.get(portfolio_id)
        if not portfolio:
            raise PortfolioNotFoundException(f"Portfolio not found: {portfolio_id}")

        self._update_holdings_market_data(portfolio)

        # Calculate sector allocation
        sector_allocation = self._calculate_sector_allocation(portfolio)

        # Find top/bottom performers
        top_performer = max(
            portfolio.holdings,
            key=lambda h: h.gain_loss_pct if h.gain_loss_pct else 0
        )

        worst_performer = min(
            portfolio.holdings,
            key=lambda h: h.gain_loss_pct if h.gain_loss_pct else 0
        )

        summary = PortfolioSummary(
            portfolio_id=portfolio.id,
            portfolio_name=portfolio.name,
            total_holdings=len(portfolio.holdings),
            total_value=portfolio.total_value,
            total_cost=portfolio.total_cost,
            total_gain_loss=portfolio.total_gain_loss,
            total_gain_loss_pct=portfolio.total_gain_loss_pct,
            sector_allocation=sector_allocation,
            top_performer=top_performer,
            worst_performer=worst_performer,
            updated_at=datetime.now()
        )

        return summary

    def export_portfolio(self,
                        portfolio_id: str,
                        format: str = "csv",
                        output_path: Optional[Path] = None) -> Path:
        """
        Export portfolio to file.

        Args:
            portfolio_id: Portfolio ID to export
            format: Export format ("csv", "json", "xlsx")
            output_path: Optional custom output path

        Returns:
            Path to exported file

        Example:
            path = service.export_portfolio("portfolio-id", format="csv")
            print(f"Portfolio exported to {path}")
        """
        portfolio = self.repository.get(portfolio_id)
        if not portfolio:
            raise PortfolioNotFoundException(f"Portfolio not found: {portfolio_id}")

        self._update_holdings_market_data(portfolio)

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"portfolio_{portfolio.name}_{timestamp}.{format}"
            output_path = Path("exports") / filename

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "csv":
            self._export_csv(portfolio, output_path)
        elif format == "json":
            self._export_json(portfolio, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info(f"Exported portfolio {portfolio_id} to {output_path}")

        return output_path

    # Private helper methods

    def _update_holdings_market_data(self, portfolio: Portfolio):
        """Update all holdings with current market prices."""
        tickers = [h.ticker for h in portfolio.holdings]

        if not tickers:
            return

        # Fetch current prices in batch
        current_prices = self.market_gw.get_batch_current_prices(tickers)

        for holding in portfolio.holdings:
            price = current_prices.get(holding.ticker)
            if price:
                holding.update_market_data(price)

    def _analyze_holding(self,
                        holding: Holding,
                        strategy_id: str,
                        portfolio_id: str) -> 'HoldingAnalysis':
        """Analyze a single holding against strategy."""

        # Get previous check for change detection
        previous_check = self.repository.get_last_portfolio_check(
            portfolio_id, holding.ticker, strategy_id
        )

        # Evaluate current strategy
        is_match, signals = self.strategy_eval.evaluate_stock(holding.ticker, strategy_id)

        # Determine status
        if is_match:
            status = HoldingStatus.STRONG
            recommendation = "HOLD - All conditions met"
        else:
            # Check how many conditions failed
            strategy = self.strategy_eval.get_strategy(strategy_id)
            failed_conditions = sum(
                1 for condition in strategy.conditions
                if not condition.evaluate(signals.get(condition.indicator_name, {}))
            )

            if failed_conditions >= len(strategy.conditions) // 2:
                status = HoldingStatus.LOST_SIGNAL
                recommendation = "CONSIDER EXIT - Most conditions failed"
            else:
                status = HoldingStatus.WEAKENING
                recommendation = "MONITOR - Some conditions weakening"

        # Detect changes from previous check
        changes = []
        if previous_check:
            changes = self._detect_signal_changes(
                current_signals=signals,
                previous_signals=previous_check.signals
            )

        analysis = HoldingAnalysis(
            ticker=holding.ticker,
            company_name="",  # Populated from fundamental data
            status=status,
            signals=signals,
            changes=changes,
            recommendation=recommendation,
            check_date=datetime.now()
        )

        # Save check to database
        self.repository.save_portfolio_check(
            portfolio_id, strategy_id, holding.ticker, analysis
        )

        return analysis

    def _detect_signal_changes(self,
                              current_signals: Dict[str, Dict],
                              previous_signals: Dict[str, Dict]) -> List['SignalChange']:
        """Detect changes between current and previous signals."""

        changes = []

        for indicator_name, current_signal in current_signals.items():
            previous_signal = previous_signals.get(indicator_name, {})

            for field, current_value in current_signal.items():
                if field == 'timestamp':
                    continue

                previous_value = previous_signal.get(field)

                if previous_value != current_value:
                    severity = self._calculate_change_severity(
                        indicator_name, field, previous_value, current_value
                    )

                    change = SignalChange(
                        indicator=indicator_name,
                        field=field,
                        old_value=previous_value,
                        new_value=current_value,
                        severity=severity
                    )

                    changes.append(change)

        return changes

    def _calculate_change_severity(self,
                                   indicator: str,
                                   field: str,
                                   old_val: Any,
                                   new_val: Any) -> str:
        """Calculate severity of signal change (improvement, deterioration, neutral)."""

        if indicator == "mcdx" and field == "signal":
            ranking = {"Retail": 0, "Neutral": 1, "Smart Money": 2, "Banker": 3}
            old_rank = ranking.get(old_val, 1)
            new_rank = ranking.get(new_val, 1)

            if new_rank > old_rank:
                return "improvement"
            elif new_rank < old_rank:
                return "deterioration"

        elif indicator == "b_xtrender" and field == "color":
            ranking = {"Red": 0, "Yellow": 1, "Green": 2}
            old_rank = ranking.get(old_val, 1)
            new_rank = ranking.get(new_val, 1)

            if new_rank > old_rank:
                return "improvement"
            elif new_rank < old_rank:
                return "deterioration"

        return "neutral"

    def _calculate_sector_allocation(self, portfolio: Portfolio) -> Dict[str, Decimal]:
        """Calculate portfolio allocation by sector."""

        sector_values = {}

        for holding in portfolio.holdings:
            if holding.current_value is None:
                continue

            # Get sector from fundamental data
            fundamental = self.fundamental_gw.get_fundamental_data(holding.ticker)
            sector = fundamental.sector if fundamental else "Unknown"

            if sector not in sector_values:
                sector_values[sector] = Decimal("0.00")

            sector_values[sector] += holding.current_value

        # Convert to percentages
        total_value = portfolio.total_value
        sector_allocation = {
            sector: (value / total_value) * 100 if total_value > 0 else Decimal("0.00")
            for sector, value in sector_values.items()
        }

        return sector_allocation

    def _export_csv(self, portfolio: Portfolio, output_path: Path):
        """Export portfolio to CSV."""
        import csv

        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'Ticker', 'Shares', 'Avg Cost', 'Current Price',
                'Current Value', 'Gain/Loss $', 'Gain/Loss %', 'Added Date'
            ])

            # Data rows
            for holding in portfolio.holdings:
                writer.writerow([
                    holding.ticker,
                    holding.shares,
                    holding.avg_cost,
                    holding.current_price,
                    holding.current_value,
                    holding.gain_loss,
                    f"{holding.gain_loss_pct:.2f}%" if holding.gain_loss_pct else "N/A",
                    holding.added_at.strftime("%Y-%m-%d")
                ])

    def _export_json(self, portfolio: Portfolio, output_path: Path):
        """Export portfolio to JSON."""
        import json

        data = {
            "portfolio_id": portfolio.id,
            "portfolio_name": portfolio.name,
            "created_at": portfolio.created_at.isoformat(),
            "total_value": str(portfolio.total_value),
            "total_gain_loss": str(portfolio.total_gain_loss),
            "holdings": [
                {
                    "ticker": h.ticker,
                    "shares": h.shares,
                    "avg_cost": str(h.avg_cost),
                    "current_price": str(h.current_price) if h.current_price else None,
                    "current_value": str(h.current_value) if h.current_value else None,
                    "gain_loss": str(h.gain_loss) if h.gain_loss else None,
                    "gain_loss_pct": h.gain_loss_pct
                }
                for h in portfolio.holdings
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)


# Supporting data classes

from enum import Enum
from dataclasses import dataclass

class HoldingStatus(Enum):
    """Status of portfolio holding after strategy check."""
    STRONG = "strong"  # All conditions met
    WEAKENING = "weakening"  # Some conditions failing
    LOST_SIGNAL = "lost_signal"  # Most/all conditions failed


@dataclass
class SignalChange:
    """Detected change in indicator signal."""
    indicator: str
    field: str
    old_value: Any
    new_value: Any
    severity: str  # "improvement", "deterioration", "neutral"


@dataclass
class HoldingAnalysis:
    """Analysis result for a single holding."""
    ticker: str
    company_name: str
    status: HoldingStatus
    signals: Dict[str, Dict[str, Any]]
    changes: List[SignalChange]
    recommendation: str
    check_date: datetime


@dataclass
class PortfolioAnalysis:
    """Complete portfolio strategy check result."""
    portfolio_id: str
    portfolio_name: str
    strategy_id: str
    check_date: datetime
    strong_holdings: List[HoldingAnalysis]
    weakening_holdings: List[HoldingAnalysis]
    lost_signal_holdings: List[HoldingAnalysis]
    total_holdings: int


@dataclass
class PortfolioSummary:
    """Portfolio summary statistics."""
    portfolio_id: str
    portfolio_name: str
    total_holdings: int
    total_value: Decimal
    total_cost: Decimal
    total_gain_loss: Decimal
    total_gain_loss_pct: float
    sector_allocation: Dict[str, Decimal]
    top_performer: Holding
    worst_performer: Holding
    updated_at: datetime


# Custom exceptions
class PortfolioNotFoundException(Exception):
    """Raised when portfolio ID not found."""
    pass


class HoldingNotFoundException(Exception):
    """Raised when holding not found in portfolio."""
    pass
```

---

**End of Part 3: Indicator Architecture & Data Access Layer**

Part 3 is now complete with comprehensive indicator specifications, complete implementations of MCDX, B-XTrender, and SMA indicators, and the complete PortfolioService interface.

Proceed to **Part 4: Integration, Security & Performance** when ready. This will cover data access layer gateways (MarketDataGateway, ComplianceGateway, UniverseGateway), API integration patterns, rate limiting, caching, security, and performance optimization strategies.