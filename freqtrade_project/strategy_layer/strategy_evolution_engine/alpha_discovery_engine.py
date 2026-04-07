"""
Enhanced Alpha Discovery Engine

Generates strategies using full indicator combinations.
Supports Trend, Momentum, Volatility, and Volume indicators.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


class IndicatorCategory(str, Enum):
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"


@dataclass
class IndicatorConfig:
    """Configuration for a single indicator."""
    name: str
    category: IndicatorCategory
    params: Dict[str, float]
    signal_type: str  # "oscillator", "crossover", "breakout", "reversion"


# Define available indicators by category
TREND_INDICATORS: List[IndicatorConfig] = [
    IndicatorConfig("ema", IndicatorCategory.TREND, {"period": 12}, "crossover"),
    IndicatorConfig("ema", IndicatorCategory.TREND, {"period": 26}, "crossover"),
    IndicatorConfig("ema", IndicatorCategory.TREND, {"period": 50}, "crossover"),
    IndicatorConfig("sma", IndicatorCategory.TREND, {"period": 20}, "crossover"),
    IndicatorConfig("sma", IndicatorCategory.TREND, {"period": 50}, "crossover"),
    IndicatorConfig("sma", IndicatorCategory.TREND, {"period": 200}, "crossover"),
    IndicatorConfig("macd", IndicatorCategory.TREND, {"fast": 12, "slow": 26, "signal": 9}, "crossover"),
    IndicatorConfig("adx", IndicatorCategory.TREND, {"period": 14}, "breakout"),
]

MOMENTUM_INDICATORS: List[IndicatorConfig] = [
    IndicatorConfig("rsi", IndicatorCategory.MOMENTUM, {"period": 14}, "oscillator"),
    IndicatorConfig("rsi", IndicatorCategory.MOMENTUM, {"period": 7}, "oscillator"),
    IndicatorConfig("rsi", IndicatorCategory.MOMENTUM, {"period": 21}, "oscillator"),
    IndicatorConfig("stochastic", IndicatorCategory.MOMENTUM, {"k_period": 14, "d_period": 3}, "oscillator"),
    IndicatorConfig("roc", IndicatorCategory.MOMENTUM, {"period": 12}, "oscillator"),
    IndicatorConfig("momentum", IndicatorCategory.MOMENTUM, {"period": 10}, "oscillator"),
]

VOLATILITY_INDICATORS: List[IndicatorConfig] = [
    IndicatorConfig("atr", IndicatorCategory.VOLATILITY, {"period": 14}, "breakout"),
    IndicatorConfig("bollinger", IndicatorCategory.VOLATILITY, {"period": 20, "std_mult": 2.0}, "reversion"),
    IndicatorConfig("bollinger", IndicatorCategory.VOLATILITY, {"period": 20, "std_mult": 1.5}, "reversion"),
    IndicatorConfig("keltner", IndicatorCategory.VOLATILITY, {"period": 20, "multiplier": 2.0}, "breakout"),
]

VOLUME_INDICATORS: List[IndicatorConfig] = [
    IndicatorConfig("vwap", IndicatorCategory.VOLUME, {}, "cumulative"),
    IndicatorConfig("obv", IndicatorCategory.VOLUME, {}, "cumulative"),
    IndicatorConfig("volume_sma", IndicatorCategory.VOLUME, {"period": 20}, "crossover"),
]

ALL_INDICATORS = (
    TREND_INDICATORS + MOMENTUM_INDICATORS + VOLATILITY_INDICATORS + VOLUME_INDICATORS
)


@dataclass
class EntryRule:
    """Entry rule for a strategy."""
    indicator: str
    condition: str  # "gt", "lt", "cross_above", "cross_below"
    threshold: float
    secondary: Optional[str] = None
    secondary_threshold: Optional[float] = None


@dataclass
class ExitRule:
    """Exit rule for a strategy."""
    indicator: str
    condition: str
    threshold: float


@dataclass
class StrategyRules:
    """Complete rule set for a strategy."""
    entry_rules: List[EntryRule]
    exit_rules: List[ExitRule]
    stop_loss: float
    take_profit: float
    trailing_stop: float
    position_sizing: float


@dataclass
class DiscoveredStrategy:
    """A fully defined trading strategy discovered by the engine."""
    strategy_id: str
    regime: str
    indicators: List[IndicatorConfig]
    rules: StrategyRules
    description: str
    
    # Performance metrics (set after backtesting)
    sharpe: float = 0.0
    sortino: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    trade_count: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "strategy_id": self.strategy_id,
            "regime": self.regime,
            "indicators": [
                {"name": i.name, "category": i.category.value, "params": i.params}
                for i in self.indicators
            ],
            "entry_rules": [
                {
                    "indicator": r.indicator,
                    "condition": r.condition,
                    "threshold": r.threshold,
                }
                for r in self.rules.entry_rules
            ],
            "exit_rules": [
                {
                    "indicator": r.indicator,
                    "condition": r.condition,
                    "threshold": r.threshold,
                }
                for r in self.rules.exit_rules
            ],
            "stop_loss": self.rules.stop_loss,
            "take_profit": self.rules.take_profit,
            "trailing_stop": self.rules.trailing_stop,
            "position_sizing": self.rules.position_sizing,
            "description": self.description,
            "metrics": {
                "sharpe": self.sharpe,
                "sortino": self.sortino,
                "profit_factor": self.profit_factor,
                "max_drawdown": self.max_drawdown,
                "win_rate": self.win_rate,
                "trade_count": self.trade_count,
            },
        }


class AlphaDiscoveryEngine:
    """
    Advanced alpha discovery engine using full indicator combinations.
    
    Generates hundreds/thousands of candidate strategies with:
    - Multiple indicator combinations
    - Entry/exit rule generation
    - Risk parameter assignment
    - Regime optimization
    """
    
    # Parameter ranges for random generation
    PARAM_RANGES = {
        "ema_period": (5, 50),
        "sma_period": (10, 200),
        "rsi_period": (7, 21),
        "rsi_oversold": (20, 40),
        "rsi_overbought": (60, 80),
        "stoch_period": (7, 21),
        "bb_period": (10, 30),
        "bb_std": (1.5, 3.0),
        "atr_period": (7, 21),
        "atr_multiplier": (1.5, 3.0),
        "stop_loss": (0.02, 0.10),
        "take_profit": (0.05, 0.20),
        "trailing_stop": (0.01, 0.05),
        "position_sizing": (0.05, 0.20),
    }
    
    def __init__(self, random_seed: Optional[int] = None) -> None:
        self.random_seed = random_seed
        if random_seed is not None:
            random.seed(random_seed)
        
        # Available rule templates
        self._entry_templates = self._build_entry_templates()
        self._exit_templates = self._build_exit_templates()
    
    def _build_entry_templates(self) -> List[Tuple[str, str, float]]:
        """Build entry rule templates."""
        return [
            ("rsi", "lt", 30),       # RSI oversold
            ("rsi", "lt", 40),       # RSI weak
            ("rsi", "gt", 60),       # RSI strong
            ("rsi", "cross_below", 30),  # RSI crosses above oversold
            ("macd", "gt", 0),       # MACD positive
            ("macd", "cross_above", 0),  # MACD crosses above zero
            ("ema_fast", "gt", 0),   # EMA above (need price)
            ("stoch_k", "lt", 20),   # Stochastic oversold
            ("stoch_k", "gt", 80),   # Stochastic overbought
            ("bb_lower", "lt", 0),   # Below lower BB (need price)
            ("atr", "gt", 0),        # ATR breakout (need threshold)
        ]
    
    def _build_exit_templates(self) -> List[Tuple[str, str, float]]:
        """Build exit rule templates."""
        return [
            ("rsi", "gt", 70),       # RSI overbought
            ("rsi", "gt", 60),      # RSI strong
            ("rsi", "cross_above", 70),  # RSI crosses above overbought
            ("macd", "lt", 0),       # MACD negative
            ("macd", "cross_below", 0),  # MACD crosses below zero
            ("stoch_k", "gt", 80),   # Stochastic overbought
            ("bb_upper", "gt", 0),   # Above upper BB (need price)
        ]
    
    def generate_strategy_population(
        self,
        population_size: int = 100,
        regime: str = "universal",
    ) -> List[DiscoveredStrategy]:
        """
        Generate a population of diverse strategies.
        
        Args:
            population_size: Number of strategies to generate
            regime: Target market regime
            
        Returns:
            List of discovered strategies
        """
        population = []
        
        for i in range(population_size):
            strategy = self._generate_single_strategy(f"{regime}_{i:04d}", regime)
            population.append(strategy)
        
        return population
    
    def _generate_single_strategy(
        self,
        strategy_id: str,
        regime: str,
    ) -> DiscoveredStrategy:
        """Generate a single strategy with full indicator combinations."""
        # Select indicators based on regime
        indicators = self._select_indicators_for_regime(regime)
        
        # Generate entry rules
        entry_rules = self._generate_entry_rules(indicators)
        
        # Generate exit rules
        exit_rules = self._generate_exit_rules(indicators)
        
        # Generate risk parameters
        rules = StrategyRules(
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            stop_loss=self._random_param("stop_loss"),
            take_profit=self._random_param("take_profit"),
            trailing_stop=self._random_param("trailing_stop"),
            position_sizing=self._random_param("position_sizing"),
        )
        
        # Build description
        desc = self._build_description(indicators, entry_rules, rules)
        
        return DiscoveredStrategy(
            strategy_id=strategy_id,
            regime=regime,
            indicators=indicators,
            rules=rules,
            description=desc,
        )
    
    def _select_indicators_for_regime(self, regime: str) -> List[IndicatorConfig]:
        """Select indicators appropriate for a regime."""
        # Always include at least one trend indicator
        trend_count = random.randint(1, 2)
        
        # Regime-specific selection
        if regime in ["bullish", "bearish"]:
            # Focus on trend + momentum
            momentum_count = 2
            volatility_count = 1
            volume_count = 1
        elif regime == "sideways":
            # Focus on volatility + momentum (reversion)
            momentum_count = 2
            volatility_count = 2
            volume_count = 0
        elif regime == "high_volatility":
            # Focus on volatility
            momentum_count = 1
            volatility_count = 3
            volume_count = 1
        elif regime == "low_volatility":
            # Focus on trend
            trend_count = 2
            momentum_count = 1
            volatility_count = 1
            volume_count = 1
        else:
            # Universal: balanced
            momentum_count = 1
            volatility_count = 1
            volume_count = 1
        
        selected = []
        
        # Select from each category
        for _ in range(trend_count):
            selected.append(random.choice(TREND_INDICATORS))
        
        for _ in range(momentum_count):
            selected.append(random.choice(MOMENTUM_INDICATORS))
        
        for _ in range(volatility_count):
            selected.append(random.choice(VOLATILITY_INDICATORS))
        
        for _ in range(volume_count):
            selected.append(random.choice(VOLUME_INDICATORS))
        
        return selected
    
    def _generate_entry_rules(
        self,
        indicators: List[IndicatorConfig],
    ) -> List[EntryRule]:
        """Generate entry rules from selected indicators."""
        rules = []
        
        # Create 1-3 entry rules
        num_rules = random.randint(1, 3)
        
        for _ in range(num_rules):
            indicator = random.choice(indicators)
            
            if indicator.name == "rsi":
                threshold = random.choice([30, 35, 40])
                condition = "lt"
            elif indicator.name == "macd":
                threshold = 0
                condition = random.choice(["gt", "cross_above"])
            elif indicator.name == "stochastic":
                threshold = random.choice([20, 25, 30])
                condition = "lt"
            elif indicator.name == "atr":
                threshold = self._random_param("atr_multiplier")
                condition = "gt"
            else:
                threshold = 0.5
                condition = "gt"
            
            rules.append(EntryRule(
                indicator=indicator.name,
                condition=condition,
                threshold=threshold,
            ))
        
        return rules
    
    def _generate_exit_rules(
        self,
        indicators: List[IndicatorConfig],
    ) -> List[ExitRule]:
        """Generate exit rules from selected indicators."""
        rules = []
        
        # Create 1-2 exit rules
        num_rules = random.randint(1, 2)
        
        for _ in range(num_rules):
            indicator = random.choice(indicators)
            
            if indicator.name == "rsi":
                threshold = random.choice([65, 70, 75])
                condition = "gt"
            elif indicator.name == "macd":
                threshold = 0
                condition = "lt"
            elif indicator.name == "stochastic":
                threshold = random.choice([70, 75, 80])
                condition = "gt"
            else:
                threshold = 0.5
                condition = "lt"
            
            rules.append(ExitRule(
                indicator=indicator.name,
                condition=condition,
                threshold=threshold,
            ))
        
        return rules
    
    def _build_description(
        self,
        indicators: List[IndicatorConfig],
        entry_rules: List[EntryRule],
        rules: Optional[StrategyRules],
    ) -> str:
        """Build human-readable description."""
        ind_names = ", ".join(set(i.name for i in indicators))
        
        entry_desc = "; ".join(
            f"{r.indicator} {r.condition} {r.threshold}"
            for r in entry_rules
        ) if entry_rules else "none"
        
        sl = rules.stop_loss if rules else 0.05
        tp = rules.take_profit if rules else 0.10
        pos = rules.position_sizing if rules else 0.10
        
        return (
            f"Indicators: {ind_names}. "
            f"Entry: {entry_desc}. "
            f"SL: {sl:.1%}, TP: {tp:.1%}, "
            f"Pos: {pos:.1%}"
        )
    
    def _random_param(self, param_name: str) -> float:
        """Generate random parameter value."""
        low, high = self.PARAM_RANGES.get(param_name, (0.01, 0.1))
        return round(random.uniform(low, high), 3)
    
    def generate_targeted_strategies(
        self,
        target_regime: str,
        num_strategies: int = 50,
    ) -> List[DiscoveredStrategy]:
        """Generate strategies specifically optimized for a market regime."""
        return self.generate_strategy_population(num_strategies, target_regime)
    
    def generate_all_regimes(
        self,
        strategies_per_regime: int = 100,
    ) -> Dict[str, List[DiscoveredStrategy]]:
        """Generate strategies for all market regimes."""
        regimes = ["bullish", "bearish", "sideways", "high_volatility", "low_volatility"]
        
        result = {}
        for regime in regimes:
            result[regime] = self.generate_strategy_population(
                strategies_per_regime, regime
            )
        
        return result
    
    def mutate_strategy(
        self,
        strategy: DiscoveredStrategy,
    ) -> DiscoveredStrategy:
        """
        Mutate an existing strategy to create variation.
        
        Operations:
        - Modify indicator parameters
        - Adjust thresholds
        - Add/remove indicators
        - Change risk parameters
        """
        mutation_type = random.choice(["param", "threshold", "risk", "add_indicator"])
        
        if mutation_type == "param":
            # Modify indicator parameter
            if strategy.indicators:
                ind = random.choice(strategy.indicators)
                if ind.name == "rsi":
                    ind.params["period"] = random.randint(7, 21)
                elif ind.name in ["ema", "sma"]:
                    ind.params["period"] = random.randint(5, 200)
        
        elif mutation_type == "threshold":
            # Adjust rule thresholds
            if strategy.rules and strategy.rules.entry_rules:
                rule = random.choice(strategy.rules.entry_rules)
                rule.threshold += random.uniform(-0.05, 0.05)
                rule.threshold = max(0, min(1, rule.threshold))
        
        elif mutation_type == "risk":
            # Change risk parameters
            if strategy.rules:
                rp = strategy.rules
                rp.stop_loss = self._random_param("stop_loss")
                rp.take_profit = self._random_param("take_profit")
        
        elif mutation_type == "add_indicator":
            # Add a new indicator
            all_indicators = TREND_INDICATORS + MOMENTUM_INDICATORS + VOLATILITY_INDICATORS + VOLUME_INDICATORS
            new_ind = random.choice(all_indicators)
            if new_ind not in strategy.indicators:
                strategy.indicators.append(new_ind)
        
        # Update description
        strategy.description = self._build_description(
            strategy.indicators,
            strategy.rules.entry_rules if strategy.rules else [],
            strategy.rules if strategy.rules else None,
        )
        
        # New ID
        strategy.strategy_id = f"{strategy.regime}_mutated_{random.randint(0, 99999)}"
        
        return strategy
    
    def crossover_strategies(
        self,
        parent1: DiscoveredStrategy,
        parent2: DiscoveredStrategy,
    ) -> DiscoveredStrategy:
        """
        Combine two strategies to create offspring.
        
        Operations:
        - Combine indicator sets
        - Blend rule sets
        - Mix risk parameters
        """
        # Combine indicators (take unique from both)
        combined_indicators = parent1.indicators + parent2.indicators
        # Deduplicate by name
        seen = set()
        unique_indicators = []
        for ind in combined_indicators:
            if ind.name not in seen:
                seen.add(ind.name)
                unique_indicators.append(ind)
        
        # Mix entry rules
        combined_entries = []
        if parent1.rules and parent1.rules.entry_rules:
            combined_entries.append(random.choice(parent1.rules.entry_rules))
        if parent2.rules and parent2.rules.entry_rules:
            combined_entries.append(random.choice(parent2.rules.entry_rules))
        
        # Mix exit rules
        combined_exits = []
        if parent1.rules and parent1.rules.exit_rules:
            combined_exits.append(random.choice(parent1.rules.exit_rules))
        if parent2.rules and parent2.rules.exit_rules:
            combined_exits.append(random.choice(parent2.rules.exit_rules))
        
        # Get parent rules or defaults
        rp1 = parent1.rules or StrategyRules([], [], 0.05, 0.10, 0.02, 0.10)
        rp2 = parent2.rules or StrategyRules([], [], 0.05, 0.10, 0.02, 0.10)
        
        # Average risk parameters
        new_rules = StrategyRules(
            entry_rules=combined_entries or [],
            exit_rules=combined_exits or [],
            stop_loss=(rp1.stop_loss + rp2.stop_loss) / 2,
            take_profit=(rp1.take_profit + rp2.take_profit) / 2,
            trailing_stop=(rp1.trailing_stop + rp2.trailing_stop) / 2,
            position_sizing=(rp1.position_sizing + rp2.position_sizing) / 2,
        )
        
        child = DiscoveredStrategy(
            strategy_id=f"crossover_{random.randint(0, 99999)}",
            regime=parent1.regime,
            indicators=unique_indicators[:5],  # Limit to 5 indicators
            rules=new_rules,
            description=f"Crossover of {parent1.strategy_id} x {parent2.strategy_id}",
        )
        
        return child


# Singleton instance
_discovery_engine: Optional[AlphaDiscoveryEngine] = None


def get_alpha_discovery_engine(seed: Optional[int] = None) -> AlphaDiscoveryEngine:
    """Get the alpha discovery engine instance."""
    global _discovery_engine
    if _discovery_engine is None:
        _discovery_engine = AlphaDiscoveryEngine(seed)
    return _discovery_engine
