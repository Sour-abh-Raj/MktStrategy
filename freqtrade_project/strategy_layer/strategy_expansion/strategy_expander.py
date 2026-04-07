"""
Strategy Expansion - New Strategy Families

Additional strategy types for expanded alpha discovery:
- Breakout Strategies
- Market Structure Strategies
- Statistical Arbitrage Signals
- Multi-Timeframe Strategies
- Regime-Specific Strategies
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import random


class StrategyFamily(str, Enum):
    """Expanded strategy families."""
    BREAKOUT = "breakout"
    MARKET_STRUCTURE = "market_structure"
    STAT_ARBITRAGE = "stat_arbitrage"
    MULTI_TIMEFRAME = "multi_timeframe"
    REGIME_SPECIFIC = "regime_specific"


@dataclass
class BreakoutConfig:
    """Breakout strategy configuration."""
    channel_period: int = 20
    breakout_threshold: float = 0.02
    volume_confirmation: bool = True
    volume_threshold: float = 1.5


@dataclass
class MarketStructureConfig:
    """Market structure strategy configuration."""
    lookback_period: int = 50
    support_resistance_levels: int = 5
    trendline_period: int = 20
    swing_lookback: int = 10


@dataclass
class StatArbConfig:
    """Statistical arbitrage strategy configuration."""
    z_score_entry: float = 2.0
    z_score_exit: float = 0.5
    lookback_period: int = 30
    pair_correlation: float = 0.8


@dataclass
class MultiTimeframeConfig:
    """Multi-timeframe strategy configuration."""
    trend_timeframe: str = "4h"
    entry_timeframe: str = "15m"
    trend_indicators: List[str] = field(default_factory=lambda: ["ema", "adx"])
    entry_indicators: List[str] = field(default_factory=lambda: ["rsi", "macd"])


@dataclass
class RegimeSpecificConfig:
    """Regime-specific strategy configuration."""
    target_regime: str = "high_volatility"
    adaptive_params: bool = True
    regime_indicators: List[str] = field(default_factory=lambda: ["atr", "rsi"])


@dataclass
class ExpandedStrategy:
    """Expanded strategy with full configuration."""
    strategy_id: str
    family: StrategyFamily
    regime: str
    
    # Core components
    indicators: List[Dict]
    entry_rules: List[Dict]
    exit_rules: List[Dict]
    
    # Risk parameters
    stop_loss: float
    take_profit: float
    trailing_stop: float
    position_sizing: float
    
    # Timeframes
    timeframes: List[str]
    
    # Performance (filled after testing)
    sharpe: float = 0.0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    profit_factor: float = 0.0


class StrategyExpander:
    """
    Expands strategy discovery to new families.
    
    Generates strategies across:
    - Breakout strategies
    - Market structure strategies
    - Statistical arbitrage
    - Multi-timeframe strategies
    - Regime-specific strategies
    """
    
    def __init__(self, random_seed: Optional[int] = None) -> None:
        if random_seed:
            random.seed(random_seed)
    
    def generate_breakout_strategies(
        self,
        num_strategies: int = 20,
        regime: str = "bullish",
    ) -> List[ExpandedStrategy]:
        """Generate breakout strategies."""
        strategies = []
        
        for i in range(num_strategies):
            config = BreakoutConfig(
                channel_period=random.randint(10, 40),
                breakout_threshold=random.uniform(0.01, 0.05),
                volume_confirmation=random.choice([True, False]),
                volume_threshold=random.uniform(1.2, 2.0),
            )
            
            indicators = [
                {"name": "donchian", "params": {"period": config.channel_period}},
                {"name": "atr", "params": {"period": 14}},
                {"name": "volume", "params": {}},
            ]
            
            if config.volume_confirmation:
                indicators.append({"name": "volume_sma", "params": {"period": 20}})
            
            entry_rules = [
                {"condition": "price_above_donchian", "threshold": config.breakout_threshold},
            ]
            
            if config.volume_confirmation:
                entry_rules.append({"condition": "volume_above_threshold", "threshold": config.volume_threshold})
            
            exit_rules = [
                {"condition": "price_below_donchian", "threshold": config.breakout_threshold * 0.5},
                {"condition": "rsi_overbought", "threshold": 70},
            ]
            
            strategy = ExpandedStrategy(
                strategy_id=f"breakout_{regime}_{i:03d}",
                family=StrategyFamily.BREAKOUT,
                regime=regime,
                indicators=indicators,
                entry_rules=entry_rules,
                exit_rules=exit_rules,
                stop_loss=random.uniform(0.03, 0.08),
                take_profit=random.uniform(0.08, 0.15),
                trailing_stop=random.uniform(0.015, 0.03),
                position_sizing=random.uniform(0.05, 0.15),
                timeframes=["1h", "4h"],
            )
            strategies.append(strategy)
        
        return strategies
    
    def generate_market_structure_strategies(
        self,
        num_strategies: int = 20,
        regime: str = "sideways",
    ) -> List[ExpandedStrategy]:
        """Generate market structure strategies."""
        strategies = []
        
        for i in range(num_strategies):
            config = MarketStructureConfig(
                lookback_period=random.randint(20, 100),
                support_resistance_levels=random.randint(3, 8),
                trendline_period=random.randint(10, 40),
                swing_lookback=random.randint(5, 20),
            )
            
            indicators = [
                {"name": "sma", "params": {"period": config.lookback_period}},
                {"name": "swing_high", "params": {"period": config.swing_lookback}},
                {"name": "swing_low", "params": {"period": config.swing_lookback}},
            ]
            
            entry_rules = [
                {"condition": "price_near_support", "threshold": 0.01},
                {"condition": "rsi_oversold", "threshold": 35},
            ]
            
            exit_rules = [
                {"condition": "price_near_resistance", "threshold": 0.01},
                {"condition": "rsi_overbought", "threshold": 65},
            ]
            
            strategy = ExpandedStrategy(
                strategy_id=f"mktstructure_{regime}_{i:03d}",
                family=StrategyFamily.MARKET_STRUCTURE,
                regime=regime,
                indicators=indicators,
                entry_rules=entry_rules,
                exit_rules=exit_rules,
                stop_loss=random.uniform(0.02, 0.05),
                take_profit=random.uniform(0.05, 0.12),
                trailing_stop=random.uniform(0.01, 0.025),
                position_sizing=random.uniform(0.05, 0.15),
                timeframes=["1h", "4h", "1d"],
            )
            strategies.append(strategy)
        
        return strategies
    
    def generate_stat_arb_strategies(
        self,
        num_strategies: int = 15,
        regime: str = "universal",
    ) -> List[ExpandedStrategy]:
        """Generate statistical arbitrage strategies."""
        strategies = []
        
        for i in range(num_strategies):
            config = StatArbConfig(
                z_score_entry=random.uniform(1.5, 2.5),
                z_score_exit=random.uniform(0.3, 0.7),
                lookback_period=random.randint(20, 50),
                pair_correlation=random.uniform(0.7, 0.95),
            )
            
            indicators = [
                {"name": "z_score", "params": {"period": config.lookback_period}},
                {"name": "spread_ma", "params": {"period": config.lookback_period}},
                {"name": "correlation", "params": {"period": 20}},
            ]
            
            entry_rules = [
                {"condition": "z_score_below_neg", "threshold": -config.z_score_entry},
                {"condition": "z_score_above_pos", "threshold": config.z_score_entry},
            ]
            
            exit_rules = [
                {"condition": "z_score_near_zero", "threshold": config.z_score_exit},
            ]
            
            strategy = ExpandedStrategy(
                strategy_id=f"statarb_{regime}_{i:03d}",
                family=StrategyFamily.STAT_ARBITRAGE,
                regime=regime,
                indicators=indicators,
                entry_rules=entry_rules,
                exit_rules=exit_rules,
                stop_loss=random.uniform(0.02, 0.04),
                take_profit=random.uniform(0.04, 0.08),
                trailing_stop=random.uniform(0.01, 0.02),
                position_sizing=random.uniform(0.03, 0.08),  # Lower for stat arb
                timeframes=["15m", "1h", "4h"],
            )
            strategies.append(strategy)
        
        return strategies
    
    def generate_multi_timeframe_strategies(
        self,
        num_strategies: int = 20,
        regime: str = "bullish",
    ) -> List[ExpandedStrategy]:
        """Generate multi-timeframe strategies."""
        timeframe_pairs = [
            ("4h", "15m"),
            ("1h", "5m"),
            ("1d", "1h"),
            ("4h", "30m"),
            ("1h", "15m"),
        ]
        
        strategies = []
        
        for i in range(num_strategies):
            tf_pair = random.choice(timeframe_pairs)
            
            config = MultiTimeframeConfig(
                trend_timeframe=tf_pair[0],
                entry_timeframe=tf_pair[1],
            )
            
            # Trend indicators on higher timeframe
            trend_indicators = [
                {"name": "ema", "params": {"period": 50}, "timeframe": config.trend_timeframe},
                {"name": "adx", "params": {"period": 14}, "timeframe": config.trend_timeframe},
            ]
            
            # Entry indicators on lower timeframe
            entry_indicators = [
                {"name": "rsi", "params": {"period": 14}, "timeframe": config.entry_timeframe},
                {"name": "macd", "params": {"fast": 12, "slow": 26}, "timeframe": config.entry_timeframe},
            ]
            
            indicators = trend_indicators + entry_indicators
            
            entry_rules = [
                {"condition": "trend_ema_bullish", "timeframe": config.trend_timeframe},
                {"condition": "entry_rsi_oversold", "timeframe": config.entry_timeframe, "threshold": 35},
            ]
            
            exit_rules = [
                {"condition": "trend_reversal", "timeframe": config.trend_timeframe},
                {"condition": "entry_rsi_overbought", "timeframe": config.entry_timeframe, "threshold": 65},
            ]
            
            strategy = ExpandedStrategy(
                strategy_id=f"multitf_{regime}_{i:03d}",
                family=StrategyFamily.MULTI_TIMEFRAME,
                regime=regime,
                indicators=indicators,
                entry_rules=entry_rules,
                exit_rules=exit_rules,
                stop_loss=random.uniform(0.03, 0.07),
                take_profit=random.uniform(0.06, 0.12),
                trailing_stop=random.uniform(0.015, 0.03),
                position_sizing=random.uniform(0.05, 0.12),
                timeframes=[config.trend_timeframe, config.entry_timeframe],
            )
            strategies.append(strategy)
        
        return strategies
    
    def generate_regime_specific_strategies(
        self,
        num_strategies: int = 25,
    ) -> List[ExpandedStrategy]:
        """Generate strategies optimized for specific regimes."""
        strategies = []
        regimes = ["high_volatility", "low_volatility", "trending", "ranging"]
        
        for regime in regimes:
            for i in range(num_strategies // len(regimes)):
                config = RegimeSpecificConfig(
                    target_regime=regime,
                    adaptive_params=random.choice([True, False]),
                )
                
                # Different indicators based on regime
                if regime == "high_volatility":
                    inds = [
                        {"name": "atr", "params": {"period": 10}},
                        {"name": "bollinger", "params": {"period": 20, "std": 2.5}},
                        {"name": "adx", "params": {"period": 14}},
                    ]
                elif regime == "low_volatility":
                    inds = [
                        {"name": "ema", "params": {"period": 21}},
                        {"name": "keltner", "params": {"period": 20}},
                        {"name": "rsi", "params": {"period": 21}},
                    ]
                elif regime == "trending":
                    inds = [
                        {"name": "ema", "params": {"period": 50}},
                        {"name": "macd", "params": {"fast": 12, "slow": 26}},
                        {"name": "adx", "params": {"period": 14}},
                    ]
                else:  # ranging
                    inds = [
                        {"name": "bb", "params": {"period": 20}},
                        {"name": "rsi", "params": {"period": 14}},
                        {"name": "stochastic", "params": {"k": 14, "d": 3}},
                    ]
                
                entry_rules = [
                    {"condition": "atr_above_threshold", "threshold": 0.02 if regime == "high_volatility" else 0.01},
                ]
                
                exit_rules = [
                    {"condition": "rsi_extreme", "threshold": 70 if regime == "ranging" else 60},
                ]
                
                strategy = ExpandedStrategy(
                    strategy_id=f"regime_{regime}_{i:03d}",
                    family=StrategyFamily.REGIME_SPECIFIC,
                    regime=regime,
                    indicators=inds,
                    entry_rules=entry_rules,
                    exit_rules=exit_rules,
                    stop_loss=random.uniform(0.04, 0.10) if regime == "high_volatility" else random.uniform(0.02, 0.05),
                    take_profit=random.uniform(0.08, 0.15),
                    trailing_stop=random.uniform(0.02, 0.04),
                    position_sizing=random.uniform(0.05, 0.15),
                    timeframes=["1h", "4h"],
                )
                strategies.append(strategy)
        
        return strategies
    
    def generate_all_families(
        self,
        strategies_per_family: int = 20,
    ) -> Dict[StrategyFamily, List[ExpandedStrategy]]:
        """Generate strategies across all families."""
        return {
            StrategyFamily.BREAKOUT: self.generate_breakout_strategies(strategies_per_family),
            StrategyFamily.MARKET_STRUCTURE: self.generate_market_structure_strategies(strategies_per_family),
            StrategyFamily.STAT_ARBITRAGE: self.generate_stat_arb_strategies(strategies_per_family),
            StrategyFamily.MULTI_TIMEFRAME: self.generate_multi_timeframe_strategies(strategies_per_family),
            StrategyFamily.REGIME_SPECIFIC: self.generate_regime_specific_strategies(strategies_per_family),
        }
    
    def get_total_count(
        self,
        strategies_per_family: int = 20,
    ) -> int:
        """Get total strategy count across all families."""
        return strategies_per_family * 5  # 5 families


def create_strategy_expander(seed: Optional[int] = None) -> StrategyExpander:
    """Create strategy expander."""
    return StrategyExpander(seed)
