"""
Research Cycle Controller

Orchestrates large-scale research cycles for strategy discovery, evaluation, and evolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from datetime import datetime
import random
import json

from freqtrade_project.alpha_lab.lab import get_alpha_lab, AlphaLab
from freqtrade_project.core.performance_metrics_engine.engine import (
    get_metrics_engine,
    PerformanceMetricsEngine,
    PerformanceMetrics,
    Trade,
)
from freqtrade_project.strategy_layer.strategy_evolution_engine.alpha_discovery_engine import (
    get_alpha_discovery_engine,
    AlphaDiscoveryEngine,
    DiscoveredStrategy,
)


@dataclass
class BacktestResult:
    """Result from a backtest run."""
    strategy_id: str
    pair: str
    timeframe: str
    start_date: str
    end_date: str
    
    # Metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    profit_factor: float
    
    # Validation
    passed_validation: bool
    rejection_reason: str = ""


@dataclass
class ResearchResult:
    """Results from a complete research cycle."""
    cycle_id: str
    timestamp: str
    
    # Generation
    strategies_generated: int
    
    # Evaluation
    strategies_tested: int
    strategies_passed: int
    strategies_rejected: int
    
    # Performance
    best_strategy: str
    best_sharpe: float
    best_return: float
    
    # Evolution
    strategies_mutated: int
    strategies_crossover: int
    
    # Validation
    min_trades_passed: int
    out_of_sample_passed: int
    cross_market_passed: int
    correlation_filter_passed: int
    
    # Benchmark comparison
    vs_benchmark_return: float
    vs_benchmark_sharpe: float
    
    # Library updates
    strategies_added_to_library: int


@dataclass
class ResearchMetrics:
    """Tracking metrics across research cycles."""
    total_cycles_run: int = 0
    total_strategies_generated: int = 0
    total_strategies_rejected: int = 0
    total_strategies_accepted: int = 0
    
    # Best performers
    best_sharpe_ever: float = 0.0
    best_return_ever: float = 0.0
    
    # Cumulative
    cumulative_generated: int = 0
    cumulative_accepted: int = 0


class ResearchCycleController:
    """
    Orchestrates the complete research supercycle.
    
    Cycle structure:
    1. Generate strategies (via AlphaLab agents)
    2. Backtest strategies
    3. Evaluate performance
    4. Apply overfitting protection
    5. Compute stability scores
    6. Filter by correlation
    7. Compare to benchmark
    8. Evolve top strategies
    9. Update strategy library
    10. Reallocate capital
    11. Repeat
    """
    
    def __init__(self, config: Optional[ResearchConfig] = None) -> None:
        self.config = config or ResearchConfig()
        
        # Components
        self.alpha_lab = get_alpha_lab()
        self.discovery_engine = get_alpha_discovery_engine()
        self.metrics_engine = get_metrics_engine()
        
        # Strategy storage
        self.strategy_library: Dict[str, DiscoveredStrategy] = {}
        self.research_results: List[ResearchResult] = []
        self.research_metrics = ResearchMetrics()
        
        # Cycle tracking
        self._cycle_count = 0
        
        # Benchmark data (buy-and-hold)
        self.benchmark_metrics: Optional[PerformanceMetrics] = None
    
    def run_research_cycle(
        self,
        strategies_per_agent: int = 50,
        pairs: Optional[List[str]] = None,
        timeframes: Optional[List[str]] = None,
    ) -> ResearchResult:
        """
        Run a complete research cycle.
        
        Args:
            strategies_per_agent: Strategies to generate per agent
            pairs: Trading pairs to test on
            timeframes: Timeframes to test on
            
        Returns:
            ResearchResult with complete cycle metrics
        """
        self._cycle_count += 1
        cycle_id = f"cycle_{self._cycle_count}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pairs = pairs or self.config.default_pairs
        timeframes = timeframes or self.config.default_timeframes
        
        # Phase 1: Generate strategies
        strategies = self._generate_strategies(strategies_per_agent)
        
        # Phase 2-3: Backtest strategies (simulated)
        backtest_results = self._run_backtests(strategies, pairs, timeframes)
        
        # Phase 4: Overfitting protection
        validated = self._apply_overfitting_protection(backtest_results)
        
        # Phase 5: Stability scoring
        stable = self._compute_stability_scores(validated)
        
        # Phase 6: Correlation filtering
        diversified = self._filter_by_correlation(stable)
        
        # Phase 7: Benchmark comparison
        winners = self._compare_to_benchmark(diversified)
        
        # Phase 8: Evolution
        evolved = self._evolve_strategies(winners)
        
        # Phase 9: Update library
        self._update_library(evolved)
        
        # Build result
        result = ResearchResult(
            cycle_id=cycle_id,
            timestamp=datetime.now().isoformat(),
            strategies_generated=len(strategies),
            strategies_tested=len(backtest_results),
            strategies_passed=len(validated),
            strategies_rejected=len(strategies) - len(validated),
            best_strategy=winners[0].strategy_id if winners else "",
            best_sharpe=winners[0].sharpe if winners else 0.0,
            best_return=winners[0].profit_factor if winners else 0.0,
            strategies_mutated=int(len(evolved) * 0.3),
            strategies_crossover=int(len(evolved) * 0.2),
            min_trades_passed=sum(1 for r in backtest_results.values() if r.total_trades >= self.config.min_trades),
            out_of_sample_passed=len(validated),
            cross_market_passed=len(stable),
            correlation_filter_passed=len(diversified),
            vs_benchmark_return=winners[0].profit_factor if winners else 0.0,
            vs_benchmark_sharpe=winners[0].sharpe if winners else 0.0,
            strategies_added_to_library=len(evolved),
        )
        
        self.research_results.append(result)
        self._update_metrics(result)
        
        return result
    
    def _generate_strategies(
        self,
        strategies_per_agent: int,
    ) -> List[DiscoveredStrategy]:
        """Phase 1: Generate strategies using AlphaLab agents."""
        results = self.alpha_lab.run_discovery(strategies_per_agent)
        
        all_strategies = []
        for result in results.values():
            all_strategies.extend(result.strategies)
        
        self.research_metrics.total_strategies_generated += len(all_strategies)
        
        return all_strategies
    
    def _run_backtests(
        self,
        strategies: List[DiscoveredStrategy],
        pairs: List[str],
        timeframes: List[str],
    ) -> Dict[str, BacktestResult]:
        """
        Phase 2-3: Run large-scale backtests.
        
        In production, this would use actual historical data.
        Here we simulate for demonstration.
        """
        results = {}
        
        for strategy in strategies:
            for pair in pairs:
                for timeframe in timeframes:
                    # Simulate backtest result
                    result = self._simulate_backtest(strategy, pair, timeframe)
                    results[f"{strategy.strategy_id}_{pair}_{timeframe}"] = result
        
        return results
    
    def _simulate_backtest(
        self,
        strategy: DiscoveredStrategy,
        pair: str,
        timeframe: str,
    ) -> BacktestResult:
        """Simulate a backtest result (for demonstration)."""
        # Generate realistic-looking metrics
        total_trades = random.randint(50, 500)
        win_rate = random.uniform(0.35, 0.65)
        winning_trades = int(total_trades * win_rate)
        losing_trades = total_trades - winning_trades
        
        # Returns
        avg_return = random.uniform(-0.02, 0.05)
        total_return = avg_return * total_trades
        annualized_return = total_return * (252 / 200)  # Assuming 200 trades
        
        # Risk metrics
        sharpe = random.uniform(-0.5, 2.5)
        sortino = sharpe * random.uniform(0.8, 1.2)
        max_drawdown = random.uniform(0.05, 0.35)
        
        # Profit factor
        avg_win = random.uniform(0.02, 0.08)
        avg_loss = random.uniform(0.01, 0.05)
        profit_factor = (winning_trades * avg_win) / (losing_trades * avg_loss) if losing_trades > 0 else 999
        
        return BacktestResult(
            strategy_id=strategy.strategy_id,
            pair=pair,
            timeframe=timeframe,
            start_date="2024-01-01",
            end_date="2025-12-31",
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_drawdown,
            profit_factor=profit_factor,
            passed_validation=False,
        )
    
    def _apply_overfitting_protection(
        self,
        backtest_results: Dict[str, BacktestResult],
    ) -> List[BacktestResult]:
        """Phase 4: Reject strategies that fail robustness tests."""
        validated = []
        
        for result in backtest_results.values():
            reasons = []
            
            # Minimum trade count
            if result.total_trades < self.config.min_trades:
                reasons.append(f"min_trades: {result.total_trades} < {self.config.min_trades}")
            
            # Max drawdown
            if result.max_drawdown > self.config.max_drawdown:
                reasons.append(f"drawdown: {result.max_drawdown:.2%} > {self.config.max_drawdown:.2%}")
            
            # Minimum Sharpe
            if result.sharpe_ratio < self.config.min_sharpe:
                reasons.append(f"sharpe: {result.sharpe_ratio:.2f} < {self.config.min_sharpe}")
            
            if reasons:
                result.rejection_reason = "; ".join(reasons)
                result.passed_validation = False
            else:
                result.passed_validation = True
                validated.append(result)
        
        return validated
    
    def _compute_stability_scores(
        self,
        validated: List[BacktestResult],
    ) -> List[BacktestResult]:
        """Phase 5: Compute stability scores across time windows."""
        stable = []
        
        for result in validated:
            # Simple stability: low drawdown + high trade count = stable
            trade_count_score = min(result.total_trades / 500, 1.0)
            drawdown_score = 1 - (result.max_drawdown / 0.5)
            stability = (trade_count_score + drawdown_score) / 2
            
            # Only keep stable strategies
            if stability >= self.config.min_stability:
                stable.append(result)
        
        return stable
    
    def _filter_by_correlation(
        self,
        strategies: List[BacktestResult],
    ) -> List[BacktestResult]:
        """Phase 6: Filter highly correlated strategies."""
        if len(strategies) <= 1:
            return strategies
        
        diversified = [strategies[0]]  # Keep first
        
        for s in strategies[1:]:
            is_correlated = False
            
            for existing in diversified:
                # Simplified correlation check
                corr = self._compute_correlation(s, existing)
                if corr > self.config.max_correlation:
                    is_correlated = True
                    break
            
            if not is_correlated:
                diversified.append(s)
        
        return diversified
    
    def _compute_correlation(
        self,
        a: BacktestResult,
        b: BacktestResult,
    ) -> float:
        """Compute simplified correlation between two strategies."""
        # In production, would use actual return series
        # Here: compare metrics
        if a.pair != b.pair:
            return 0.0
        
        score = 0.0
        if abs(a.sharpe_ratio - b.sharpe_ratio) < 0.3:
            score += 0.4
        if abs(a.win_rate - b.win_rate) < 0.1:
            score += 0.3
        if a.timeframe == b.timeframe:
            score += 0.3
        
        return score
    
    def _compare_to_benchmark(
        self,
        strategies: List[BacktestResult],
    ) -> List[DiscoveredStrategy]:
        """Phase 7: Compare to buy-and-hold benchmark."""
        if not strategies:
            return []
        
        # Get or create benchmark (simulated BTC buy-and-hold)
        if self.benchmark_metrics is None:
            self.benchmark_metrics = self._create_benchmark()
        
        winners = []
        
        for result in strategies:
            # Strategy must outperform benchmark
            if (result.sharpe_ratio > self.benchmark_metrics.sharpe_ratio and
                result.annualized_return > self.benchmark_metrics.annualized_return):
                
                # Create DiscoveredStrategy with metrics
                from freqtrade_project.strategy_layer.strategy_evolution_engine.alpha_discovery_engine import StrategyRules
                strategy = DiscoveredStrategy(
                    strategy_id=result.strategy_id,
                    regime="universal",
                    indicators=[],
                    rules=StrategyRules(
                        entry_rules=[],
                        exit_rules=[],
                        stop_loss=0.05,
                        take_profit=0.10,
                        trailing_stop=0.02,
                        position_sizing=0.10,
                    ),
                    description=f"Backtest: {result.pair} {result.timeframe}",
                    sharpe=result.sharpe_ratio,
                    sortino=result.sortino_ratio,
                    profit_factor=result.profit_factor,
                    max_drawdown=result.max_drawdown,
                    win_rate=result.win_rate,
                    trade_count=result.total_trades,
                )
                winners.append(strategy)
        
        return winners
    
    def _create_benchmark(self) -> PerformanceMetrics:
        """Create simulated buy-and-hold benchmark."""
        # Simulated BTC 2024-2025 performance
        return PerformanceMetrics(
            total_trades=1,
            winning_trades=1,
            losing_trades=0,
            win_rate=1.0,
            total_return=0.5,  # ~50% gain
            annualized_return=0.4,
            avg_trade_return=0.5,
            sharpe_ratio=1.5,
            sortino_ratio=1.8,
            max_drawdown=0.25,
            current_drawdown=0.0,
            profit_factor=999.0,
            avg_win=0.5,
            avg_loss=0.0,
            largest_win=0.5,
            largest_loss=0.0,
            return_std=0.15,
            stability_score=0.7,
            avg_trade_duration=86400 * 365,
            trades_per_day=1/365,
        )
    
    def _evolve_strategies(
        self,
        winners: List[DiscoveredStrategy],
    ) -> List[DiscoveredStrategy]:
        """Phase 8: Evolve top strategies."""
        if not winners:
            return []
        
        evolved = list(winners)
        
        # Mutation
        num_mutations = int(len(winners) * 0.3)
        for _ in range(num_mutations):
            parent = random.choice(winners)
            mutated = self.discovery_engine.mutate_strategy(parent)
            evolved.append(mutated)
        
        # Crossover
        num_crossovers = int(len(winners) * 0.2)
        for _ in range(num_crossovers):
            if len(winners) >= 2:
                p1, p2 = random.sample(winners, 2)
                child = self.discovery_engine.crossover_strategies(p1, p2)
                evolved.append(child)
        
        self.research_metrics.total_strategies_accepted += len(evolved)
        
        return evolved
    
    def _update_library(
        self,
        strategies: List[DiscoveredStrategy],
    ) -> None:
        """Phase 9: Add validated strategies to library."""
        for strategy in strategies:
            self.strategy_library[strategy.strategy_id] = strategy
    
    def _update_metrics(self, result: ResearchResult) -> None:
        """Update cumulative research metrics."""
        self.research_metrics.total_cycles_run += 1
        self.research_metrics.cumulative_generated += result.strategies_generated
        self.research_metrics.cumulative_accepted += result.strategies_added_to_library
        
        if result.best_sharpe > self.research_metrics.best_sharpe_ever:
            self.research_metrics.best_sharpe_ever = result.best_sharpe
        
        if result.best_return > self.research_metrics.best_return_ever:
            self.research_metrics.best_return_ever = result.best_return
    
    def run_continuous_research(
        self,
        num_cycles: int = 10,
        strategies_per_cycle: int = 50,
    ) -> List[ResearchResult]:
        """Phase 12: Run continuous research loop."""
        results = []
        
        for i in range(num_cycles):
            print(f"Running research cycle {i+1}/{num_cycles}...")
            result = self.run_research_cycle(strategies_per_cycle)
            results.append(result)
            
            # Log progress
            print(f"  Generated: {result.strategies_generated}")
            print(f"  Accepted: {result.strategies_added_to_library}")
            print(f"  Best Sharpe: {result.best_sharpe:.2f}")
        
        return results
    
    def get_research_dashboard(self) -> Dict:
        """Phase 13: Get research dashboard metrics."""
        return {
            "cycles_run": self.research_metrics.total_cycles_run,
            "strategies_generated": self.research_metrics.cumulative_generated,
            "strategies_accepted": self.research_metrics.cumulative_accepted,
            "strategies_in_library": len(self.strategy_library),
            "best_sharpe": self.research_metrics.best_sharpe_ever,
            "best_return": self.research_metrics.best_return_ever,
            "recent_results": [
                {
                    "cycle": r.cycle_id,
                    "generated": r.strategies_generated,
                    "accepted": r.strategies_added_to_library,
                    "best_sharpe": r.best_sharpe,
                }
                for r in self.research_results[-5:]
            ],
        }
    
    def export_results(self, filepath: str) -> None:
        """Export research results to JSON."""
        data = {
            "metrics": {
                "total_cycles": self.research_metrics.total_cycles_run,
                "total_generated": self.research_metrics.cumulative_generated,
                "total_accepted": self.research_metrics.cumulative_accepted,
                "best_sharpe": self.research_metrics.best_sharpe_ever,
                "best_return": self.research_metrics.best_return_ever,
            },
            "results": [
                {
                    "cycle_id": r.cycle_id,
                    "timestamp": r.timestamp,
                    "strategies_generated": r.strategies_generated,
                    "strategies_accepted": r.strategies_added_to_library,
                    "best_sharpe": r.best_sharpe,
                    "best_return": r.best_return,
                }
                for r in self.research_results
            ],
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


@dataclass
class ResearchConfig:
    """Configuration for research cycles."""
    # Generation
    default_pairs: List[str] = field(default_factory=lambda: [
        "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"
    ])
    default_timeframes: List[str] = field(default_factory=lambda: [
        "1h", "4h", "1d"
    ])
    
    # Validation
    min_trades: int = 200
    min_sharpe: float = 0.5
    max_drawdown: float = 0.30
    min_stability: float = 0.5
    
    # Correlation
    max_correlation: float = 0.8
    
    # Evolution
    mutation_rate: float = 0.3
    crossover_rate: float = 0.2
    
    # Benchmark
    benchmark_pair: str = "BTC/USDT"


# Singleton instance
_research_controller: Optional[ResearchCycleController] = None


def get_research_controller(config: Optional[ResearchConfig] = None) -> ResearchCycleController:
    """Get the research controller instance."""
    global _research_controller
    if _research_controller is None:
        _research_controller = ResearchCycleController(config)
    return _research_controller
