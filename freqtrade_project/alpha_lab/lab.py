"""
Alpha Lab - Multi-Agent Alpha Discovery System

Each agent specializes in discovering strategies for different types of alpha:
- Trend Agent: EMA crossovers, MACD, trend breakouts
- Mean Reversion Agent: RSI, Bollinger reversions, range trading
- Volatility Agent: ATR breakouts, volatility expansion/compression
- Microstructure Agent: Order flow, liquidity, spread changes
- Portfolio Agent: Strategy ranking, correlation, capital allocation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
import random

from freqtrade_project.strategy_layer.strategy_evolution_engine.alpha_discovery_engine import (
    AlphaDiscoveryEngine,
    DiscoveredStrategy,
    IndicatorConfig,
    IndicatorCategory,
)


@dataclass
class AgentResult:
    """Result from an alpha agent."""
    agent_name: str
    strategies: List[DiscoveredStrategy]
    generation_time_ms: float
    best_metrics: Dict[str, float] = field(default_factory=dict)


class BaseAlphaAgent:
    """Base class for all alpha discovery agents."""
    
    def __init__(self, name: str, regime: str) -> None:
        self.name = name
        self.regime = regime
        self.discovery_engine = AlphaDiscoveryEngine()
    
    def discover(
        self,
        num_strategies: int = 50,
    ) -> List[DiscoveredStrategy]:
        """Discover alpha strategies."""
        raise NotImplementedError
    
    def evaluate(
        self,
        strategies: List[DiscoveredStrategy],
    ) -> Dict[str, float]:
        """Evaluate discovered strategies."""
        if not strategies:
            return {}
        
        # Simple evaluation based on strategy diversity
        return {
            "count": len(strategies),
            "diversity": self._calculate_diversity(strategies),
        }
    
    def _calculate_diversity(self, strategies: List[DiscoveredStrategy]) -> float:
        """Calculate diversity of strategy set."""
        if len(strategies) <= 1:
            return 0.0
        
        indicator_sets = []
        for s in strategies:
            ind_names = tuple(sorted(set(i.name for i in s.indicators)))
            indicator_sets.append(ind_names)
        
        unique = len(set(indicator_sets))
        return unique / len(strategies)


class TrendAgent(BaseAlphaAgent):
    """Agent specializing in trend-following strategies."""
    
    def discover(self, num_strategies: int = 50) -> List[DiscoveredStrategy]:
        """Discover trend-based strategies."""
        # Generate strategies specifically for trend
        strategies = self.discovery_engine.generate_strategy_population(
            num_strategies, "bullish"
        )
        
        # Add trend-specific modifications
        for s in strategies:
            # Ensure EMA or MACD is included
            has_trend = any(i.category == IndicatorCategory.TREND for i in s.indicators)
            if not has_trend:
                s.indicators.append(IndicatorConfig(
                    "ema", IndicatorCategory.TREND, {"period": 12}, "crossover"
                ))
        
        return strategies


class MeanReversionAgent(BaseAlphaAgent):
    """Agent specializing in mean reversion strategies."""
    
    def discover(self, num_strategies: int = 50) -> List[DiscoveredStrategy]:
        """Discover mean reversion strategies."""
        # Generate for sideways regime
        strategies = self.discovery_engine.generate_strategy_population(
            num_strategies, "sideways"
        )
        
        # Add reversion-specific indicators
        for s in strategies:
            # Ensure volatility indicators for reversion
            has_vol = any(i.category == IndicatorCategory.VOLATILITY for i in s.indicators)
            if not has_vol:
                s.indicators.append(IndicatorConfig(
                    "bollinger", IndicatorCategory.VOLATILITY, 
                    {"period": 20, "std_mult": 2.0}, "reversion"
                ))
        
        return strategies


class VolatilityAgent(BaseAlphaAgent):
    """Agent specializing in volatility-based strategies."""
    
    def discover(self, num_strategies: int = 50) -> List[DiscoveredStrategy]:
        """Discover volatility-based strategies."""
        # High volatility strategies
        strategies = self.discovery_engine.generate_strategy_population(
            num_strategies, "high_volatility"
        )
        
        # Add volatility indicators
        for s in strategies:
            has_vol = any(i.category == IndicatorCategory.VOLATILITY for i in s.indicators)
            if not has_vol:
                s.indicators.append(IndicatorConfig(
                    "atr", IndicatorCategory.VOLATILITY, {"period": 14}, "breakout"
                ))
        
        return strategies


class MicrostructureAgent(BaseAlphaAgent):
    """Agent specializing in microstructure-based strategies."""
    
    def __init__(self, name: str = "microstructure", regime: str = "universal") -> None:
        super().__init__(name, regime)
    
    def discover(self, num_strategies: int = 50) -> List[DiscoveredStrategy]:
        """Discover microstructure-informed strategies."""
        # These strategies will incorporate microstructure signals
        strategies = self.discovery_engine.generate_strategy_population(
            num_strategies, "universal"
        )
        
        # Add volume indicators
        for s in strategies:
            has_volume = any(i.category == IndicatorCategory.VOLUME for i in s.indicators)
            if not has_volume:
                s.indicators.append(IndicatorConfig(
                    "vwap", IndicatorCategory.VOLUME, {}, "cumulative"
                ))
            s.description += " [Microstructure-informed]"
        
        return strategies


class PortfolioAgent:
    """
    Agent responsible for evaluating and allocating capital to strategies.
    
    Responsibilities:
    - Rank strategies by performance
    - Compute strategy correlations
    - Allocate capital to top strategies
    """
    
    def __init__(self) -> None:
        self.discovery_engine = AlphaDiscoveryEngine()
    
    def rank_strategies(
        self,
        strategies: List[DiscoveredStrategy],
    ) -> List[DiscoveredStrategy]:
        """Rank strategies by performance metrics."""
        if not strategies:
            return []
        
        # Sort by composite score (sharpe-weighted)
        scored = []
        for s in strategies:
            score = (
                s.sharpe * 0.35 +
                s.sortino * 0.25 +
                s.profit_factor * 0.20 -
                s.max_drawdown * 0.15 +
                s.win_rate * 0.10
            )
            scored.append((s, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in scored]
    
    def compute_correlation(
        self,
        strategy_a: DiscoveredStrategy,
        strategy_b: DiscoveredStrategy,
    ) -> float:
        """
        Compute correlation between two strategies.
        
        Simplified: Based on indicator overlap.
        """
        ind_a = set(i.name for i in strategy_a.indicators)
        ind_b = set(i.name for i in strategy_b.indicators)
        
        overlap = len(ind_a & ind_b)
        union = len(ind_a | ind_b)
        
        if union == 0:
            return 0.0
        
        return overlap / union
    
    def filter_by_correlation(
        self,
        strategies: List[DiscoveredStrategy],
        max_correlation: float = 0.8,
    ) -> List[DiscoveredStrategy]:
        """
        Filter strategies to reduce correlation.
        
        Keeps first strategy, removes highly correlated subsequent ones.
        """
        if len(strategies) <= 1:
            return strategies
        
        filtered = [strategies[0]]
        
        for s in strategies[1:]:
            is_correlated = False
            for existing in filtered:
                corr = self.compute_correlation(s, existing)
                if corr > max_correlation:
                    is_correlated = True
                    break
            
            if not is_correlated:
                filtered.append(s)
        
        return filtered
    
    def allocate_capital(
        self,
        strategies: List[DiscoveredStrategy],
        total_capital: float = 1.0,
        max_position: float = 0.2,
    ) -> Dict[str, float]:
        """
        Allocate capital to strategies.
        
        Args:
            strategies: Ranked strategies
            total_capital: Total capital to allocate
            max_position: Maximum position size per strategy
            
        Returns:
            Dictionary of strategy_id: allocation
        """
        if not strategies:
            return {}
        
        # Top strategies get more capital
        allocations = {}
        num_positions = min(len(strategies), 5)  # Max 5 positions
        
        for i, s in enumerate(strategies[:num_positions]):
            # Decreasing allocation for lower-ranked
            weight = 1.0 / (i + 1)
            allocation = min(total_capital * weight * 0.5, max_position)
            allocations[s.strategy_id] = round(allocation, 4)
        
        # Normalize to total capital
        total = sum(allocations.values())
        if total > 0:
            for sid in allocations:
                allocations[sid] = round(allocations[sid] / total * total_capital, 4)
        
        return allocations


class AlphaLab:
    """
    Multi-Agent Alpha Discovery Laboratory.
    
    Coordinates all agents to discover, evaluate, and allocate capital to strategies.
    """
    
    def __init__(self) -> None:
        # Initialize agents
        self.trend_agent = TrendAgent("trend", "bullish")
        self.mean_reversion_agent = MeanReversionAgent("mean_reversion", "sideways")
        self.volatility_agent = VolatilityAgent("volatility", "high_volatility")
        self.microstructure_agent = MicrostructureAgent()
        self.portfolio_agent = PortfolioAgent()
        
        self.agents = [
            self.trend_agent,
            self.mean_reversion_agent,
            self.volatility_agent,
            self.microstructure_agent,
        ]
    
    def run_discovery(
        self,
        strategies_per_agent: int = 50,
    ) -> Dict[str, AgentResult]:
        """
        Run discovery across all agents.
        
        Returns:
            Dictionary of agent_name: AgentResult
        """
        results = {}
        
        for agent in self.agents:
            strategies = agent.discover(strategies_per_agent)
            metrics = agent.evaluate(strategies)
            
            results[agent.name] = AgentResult(
                agent_name=agent.name,
                strategies=strategies,
                generation_time_ms=0.0,  # Would measure in production
                best_metrics=metrics,
            )
        
        return results
    
    def run_competition(
        self,
        results: Dict[str, AgentResult],
    ) -> List[DiscoveredStrategy]:
        """
        Run strategies through competition pipeline.
        
        Process:
        1. Collect all strategies from agents
        2. Rank by performance metrics
        3. Filter by correlation
        4. Return top strategies
        """
        all_strategies = []
        
        for result in results.values():
            all_strategies.extend(result.strategies)
        
        # Rank strategies
        ranked = self.portfolio_agent.rank_strategies(all_strategies)
        
        # Filter by correlation
        filtered = self.portfolio_agent.filter_by_correlation(ranked, max_correlation=0.8)
        
        return filtered
    
    def allocate(
        self,
        strategies: List[DiscoveredStrategy],
        total_capital: float = 1.0,
    ) -> Dict[str, float]:
        """
        Allocate capital to winning strategies.
        
        Returns:
            Dictionary of strategy_id: allocation
        """
        return self.portfolio_agent.allocate_capital(
            strategies, total_capital
        )
    
    def run_full_cycle(
        self,
        strategies_per_agent: int = 50,
        total_capital: float = 1.0,
    ) -> Dict[str, any]:
        """
        Run complete alpha discovery cycle.
        
        Returns:
            Complete results including strategies and allocations
        """
        # Discovery phase
        results = self.run_discovery(strategies_per_agent)
        
        # Competition phase
        winners = self.run_competition(results)
        
        # Allocation phase
        allocations = self.allocate(winners, total_capital)
        
        return {
            "discovery_results": {
                name: {
                    "strategy_count": len(r.strategies),
                    "metrics": r.best_metrics,
                }
                for name, r in results.items()
            },
            "competed_strategies": [
                {"strategy_id": s.strategy_id, "regime": s.regime}
                for s in winners
            ],
            "allocations": allocations,
            "total_strategies_discovered": sum(
                len(r.strategies) for r in results.values()
            ),
        }


# Singleton instance
_alpha_lab: Optional[AlphaLab] = None


def get_alpha_lab() -> AlphaLab:
    """Get the alpha lab instance."""
    global _alpha_lab
    if _alpha_lab is None:
        _alpha_lab = AlphaLab()
    return _alpha_lab
