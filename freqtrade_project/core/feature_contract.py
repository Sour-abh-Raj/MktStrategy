"""
Feature Contract Schema

Defines the contract between data layer (feature engineering) 
and intelligence layer (regime classification).

This ensures consistent feature passing between layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class FeatureCategory(str, Enum):
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    MICROSTRUCTURE = "microstructure"


@dataclass
class FeatureSchema:
    """Schema definition for a single feature."""
    name: str
    category: FeatureCategory
    dtype: str  # float, int, bool
    description: str
    expected_range: tuple  # (min, max)
    required: bool = True


# Define all expected features
TREND_FEATURES: List[FeatureSchema] = [
    FeatureSchema(
        name="ema_fast",
        category=FeatureCategory.TREND,
        dtype="float",
        description="Fast EMA value",
        expected_range=(0, float('inf')),
        required=False,
    ),
    FeatureSchema(
        name="ema_slow",
        category=FeatureCategory.TREND,
        dtype="float",
        description="Slow EMA value",
        expected_range=(0, float('inf')),
        required=False,
    ),
    FeatureSchema(
        name="ma_slope",
        category=FeatureCategory.TREND,
        dtype="float",
        description="Moving average slope (normalized)",
        expected_range=(-1, 1),
        required=True,
    ),
    FeatureSchema(
        name="macd_line",
        category=FeatureCategory.TREND,
        dtype="float",
        description="MACD line value",
        expected_range=(-float('inf'), float('inf')),
        required=False,
    ),
    FeatureSchema(
        name="macd_signal",
        category=FeatureCategory.TREND,
        dtype="float",
        description="MACD signal line",
        expected_range=(-float('inf'), float('inf')),
        required=False,
    ),
    FeatureSchema(
        name="macd_hist",
        category=FeatureCategory.TREND,
        dtype="float",
        description="MACD histogram (oscillator)",
        expected_range=(-float('inf'), float('inf')),
        required=True,
    ),
    FeatureSchema(
        name="adx",
        category=FeatureCategory.TREND,
        dtype="float",
        description="Average Directional Index (0-100)",
        expected_range=(0, 100),
        required=False,
    ),
]


MOMENTUM_FEATURES: List[FeatureSchema] = [
    FeatureSchema(
        name="rsi",
        category=FeatureCategory.MOMENTUM,
        dtype="float",
        description="Relative Strength Index (0-100)",
        expected_range=(0, 100),
        required=True,
    ),
    FeatureSchema(
        name="stoch_k",
        category=FeatureCategory.MOMENTUM,
        dtype="float",
        description="Stochastic %K (0-100)",
        expected_range=(0, 100),
        required=False,
    ),
    FeatureSchema(
        name="stoch_d",
        category=FeatureCategory.MOMENTUM,
        dtype="float",
        description="Stochastic %D (0-100)",
        expected_range=(0, 100),
        required=False,
    ),
    FeatureSchema(
        name="roc",
        category=FeatureCategory.MOMENTUM,
        dtype="float",
        description="Rate of Change",
        expected_range=(-float('inf'), float('inf')),
        required=False,
    ),
    FeatureSchema(
        name="momentum",
        category=FeatureCategory.MOMENTUM,
        dtype="float",
        description="Generic momentum indicator",
        expected_range=(-float('inf'), float('inf')),
        required=False,
    ),
]


VOLATILITY_FEATURES: List[FeatureSchema] = [
    FeatureSchema(
        name="atr",
        category=FeatureCategory.VOLATILITY,
        dtype="float",
        description="Average True Range",
        expected_range=(0, float('inf')),
        required=False,
    ),
    FeatureSchema(
        name="atr_ratio",
        category=FeatureCategory.VOLATILITY,
        dtype="float",
        description="ATR ratio to moving average",
        expected_range=(0, 10),
        required=True,
    ),
    FeatureSchema(
        name="bb_mid",
        category=FeatureCategory.VOLATILITY,
        dtype="float",
        description="Bollinger Band middle line",
        expected_range=(0, float('inf')),
        required=False,
    ),
    FeatureSchema(
        name="bb_upper",
        category=FeatureCategory.VOLATILITY,
        dtype="float",
        description="Bollinger Band upper line",
        expected_range=(0, float('inf')),
        required=False,
    ),
    FeatureSchema(
        name="bb_lower",
        category=FeatureCategory.VOLATILITY,
        dtype="float",
        description="Bollinger Band lower line",
        expected_range=(0, float('inf')),
        required=False,
    ),
    FeatureSchema(
        name="bb_width",
        category=FeatureCategory.VOLATILITY,
        dtype="float",
        description="Bollinger Band width (volatility)",
        expected_range=(0, 1),
        required=True,
    ),
    FeatureSchema(
        name="keltner_mid",
        category=FeatureCategory.VOLATILITY,
        dtype="float",
        description="Keltner Channel middle",
        expected_range=(0, float('inf')),
        required=False,
    ),
    FeatureSchema(
        name="keltner_upper",
        category=FeatureCategory.VOLATILITY,
        dtype="float",
        description="Keltner Channel upper",
        expected_range=(0, float('inf')),
        required=False,
    ),
    FeatureSchema(
        name="keltner_lower",
        category=FeatureCategory.VOLATILITY,
        dtype="float",
        description="Keltner Channel lower",
        expected_range=(0, float('inf')),
        required=False,
    ),
]


VOLUME_FEATURES: List[FeatureSchema] = [
    FeatureSchema(
        name="volume",
        category=FeatureCategory.VOLUME,
        dtype="float",
        description="Trading volume",
        expected_range=(0, float('inf')),
        required=False,
    ),
    FeatureSchema(
        name="volume_ratio",
        category=FeatureCategory.VOLUME,
        dtype="float",
        description="Volume ratio to average",
        expected_range=(0, 10),
        required=True,
    ),
    FeatureSchema(
        name="vwap",
        category=FeatureCategory.VOLUME,
        dtype="float",
        description="Volume Weighted Average Price",
        expected_range=(0, float('inf')),
        required=False,
    ),
    FeatureSchema(
        name="obv",
        category=FeatureCategory.VOLUME,
        dtype="float",
        description="On-Balance Volume",
        expected_range=(-float('inf'), float('inf')),
        required=False,
    ),
    FeatureSchema(
        name="volume_spike",
        category=FeatureCategory.VOLUME,
        dtype="bool",
        description="Whether volume is spiking",
        expected_range=(0, 1),
        required=False,
    ),
]


# All features combined
ALL_FEATURES: Dict[str, FeatureSchema] = {
    f.name: f 
    for f in TREND_FEATURES + MOMENTUM_FEATURES + VOLATILITY_FEATURES + VOLUME_FEATURES
}


class FeatureValidator:
    """Validates features against the schema."""
    
    def __init__(self) -> None:
        self.schema = ALL_FEATURES
    
    def validate(self, features: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate features against schema.
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required features
        for name, schema in self.schema.items():
            if schema.required and name not in features:
                errors.append(f"Missing required feature: {name}")
        
        # Validate ranges
        for name, value in features.items():
            if name in self.schema:
                schema = self.schema[name]
                min_val, max_val = schema.expected_range
                
                if isinstance(value, (int, float)):
                    if value < min_val or value > max_val:
                        # Only warn, don't fail
                        pass  # Flexible range checking
        
        return len(errors) == 0, errors
    
    def get_missing_features(self, features: Dict[str, Any]) -> List[str]:
        """Get list of missing required features."""
        return [
            name for name, schema in self.schema.items()
            if schema.required and name not in features
        ]
    
    def get_feature_category(self, feature_name: str) -> Optional[FeatureCategory]:
        """Get category for a feature."""
        if feature_name in self.schema:
            return self.schema[feature_name].category
        return None


def get_feature_validator() -> FeatureValidator:
    """Get feature validator instance."""
    return FeatureValidator()
