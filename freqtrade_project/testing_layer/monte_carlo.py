"""
Monte Carlo Robustness Testing

Tests strategy robustness via randomized simulations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random
import math


@dataclass
class SimulationResult:
    """Result from a single Monte Carlo simulation."""
    simulation_id: int
    
    # Metrics
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    
    # Execution metrics
    avg_slippage: float
    avg_latency_ms: float


@dataclass
class MonteCarloResult:
    """Complete Monte Carlo test results."""
    strategy_id: str
    num_simulations: int
    
    # Distribution statistics
    return_mean: float
    return_std: float
    return_ci_lower: float  # 95% CI
    return_ci_upper: float
    
    sharpe_mean: float
    sharpe_std: float
    sharpe_ci_lower: float
    sharpe_ci_upper: float
    
    drawdown_mean: float
    drawdown_std: float
    drawdown_ci_lower: float
    drawdown_ci_upper: float
    
    # Robustness assessment
    robustness_score: float  # 0-1
    is_robust: bool
    recommendation: str  # "accept", "review", "reject"


class MonteCarloSimulator:
    """
    Performs Monte Carlo simulations to test strategy robustness.
    
    Randomizes:
    - Trade order
    - Entry timing
    - Slippage levels
    - Execution delays
    """
    
    def __init__(
        self,
        num_simulations: int = 500,
        confidence_level: float = 0.95,
    ) -> None:
        self.num_simulations = num_simulations
        self.confidence_level = confidence_level
        self.z_score = 1.96  # 95% CI
    
    def run_simulation(
        self,
        strategy_id: str,
        base_trades: List[Dict],
        slippage_pct: float = 0.05,
        fee_pct: float = 0.1,
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulations for a strategy.
        
        Args:
            strategy_id: Strategy to test
            base_trades: Base trade list to randomize
            slippage_pct: Expected slippage (default 0.05%)
            fee_pct: Exchange fee (default 0.1%)
            
        Returns:
            MonteCarloResult with confidence intervals
        """
        returns = []
        sharpes = []
        drawdowns = []
        
        for sim_id in range(self.num_simulations):
            result = self._single_simulation(
                base_trades, slippage_pct, fee_pct
            )
            returns.append(result.total_return)
            sharpes.append(result.sharpe_ratio)
            drawdowns.append(result.max_drawdown)
        
        # Compute statistics
        return_mean = sum(returns) / len(returns)
        return_std = self._std(returns)
        return_ci_lower = return_mean - self.z_score * return_std
        return_ci_upper = return_mean + self.z_score * return_std
        
        sharpe_mean = sum(sharpes) / len(sharpes)
        sharpe_std = self._std(sharpes)
        sharpe_ci_lower = sharpe_mean - self.z_score * sharpe_std
        sharpe_ci_upper = sharpe_mean + self.z_score * sharpe_std
        
        drawdown_mean = sum(drawdowns) / len(drawdowns)
        drawdown_std = self._std(drawdowns)
        drawdown_ci_lower = drawdown_mean - self.z_score * drawdown_std
        drawdown_ci_upper = drawdown_mean + self.z_score * drawdown_std
        
        # Robustness score: higher is better
        # Based on coefficient of variation (lower = more robust)
        robustness = self._compute_robustness(returns, sharpes, drawdowns)
        
        is_robust = robustness >= 0.5 and sharpe_ci_lower > 0
        
        if is_robust and robustness >= 0.7:
            recommendation = "accept"
        elif is_robust:
            recommendation = "review"
        else:
            recommendation = "reject"
        
        return MonteCarloResult(
            strategy_id=strategy_id,
            num_simulations=self.num_simulations,
            return_mean=return_mean,
            return_std=return_std,
            return_ci_lower=return_ci_lower,
            return_ci_upper=return_ci_upper,
            sharpe_mean=sharpe_mean,
            sharpe_std=sharpe_std,
            sharpe_ci_lower=sharpe_ci_lower,
            sharpe_ci_upper=sharpe_ci_upper,
            drawdown_mean=drawdown_mean,
            drawdown_std=drawdown_std,
            drawdown_ci_lower=drawdown_ci_lower,
            drawdown_ci_upper=drawdown_ci_upper,
            robustness_score=robustness,
            is_robust=is_robust,
            recommendation=recommendation,
        )
    
    def _single_simulation(
        self,
        base_trades: List[Dict],
        slippage_pct: float,
        fee_pct: float,
    ) -> SimulationResult:
        """Run a single simulation with randomized parameters."""
        
        # Randomize parameters
        slippage_multiplier = random.uniform(0.5, 1.5)
        fee_multiplier = random.uniform(0.8, 1.2)
        
        # Randomize trade order
        trades = list(base_trades)
        random.shuffle(trades)
        
        # Apply costs
        total_return = 0
        equity = 1.0
        peak = 1.0
        max_dd = 0
        wins = 0
        
        for trade in trades:
            # Entry timing noise
            timing_noise = random.uniform(-0.01, 0.01)
            
            # Return after costs
            raw_return = trade.get("return_pct", 0)
            slippage_cost = slippage_pct * slippage_multiplier
            fee_cost = fee_pct * fee_multiplier
            
            net_return = raw_return - slippage_cost - fee_cost + timing_noise
            total_return += net_return
            
            # Track equity
            equity *= (1 + net_return)
            
            # Drawdown
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd
            
            # Win tracking
            if net_return > 0:
                wins += 1
        
        # Compute Sharpe (simplified)
        if len(trades) > 1:
            returns = [t.get("return_pct", 0) for t in trades]
            avg_ret = sum(returns) / len(returns)
            std_ret = self._std(returns)
            sharpe = avg_ret / std_ret if std_ret > 0 else 0
        else:
            sharpe = 0
        
        win_rate = wins / len(trades) if trades else 0
        
        return SimulationResult(
            simulation_id=0,
            total_return=total_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            win_rate=win_rate,
            total_trades=len(trades),
            avg_slippage=slippage_pct * slippage_multiplier,
            avg_latency_ms=random.uniform(50, 200),
        )
    
    def _std(self, values: List[float]) -> float:
        """Compute standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
        return math.sqrt(variance)
    
    def _compute_robustness(
        self,
        returns: List[float],
        sharpes: List[float],
        drawdowns: List[float],
    ) -> float:
        """Compute overall robustness score."""
        # Lower coefficient of variation = more robust
        
        # Return stability (inverse of CV)
        if returns:
            return_cv = abs(self._std(returns) / (sum(returns)/len(returns))) if sum(returns)/len(returns) != 0 else 999
            return_stability = 1 / (1 + return_cv)
        else:
            return_stability = 0
        
        # Sharpe stability
        sharpe_stability = 1 / (1 + abs(self._std(sharpes)))
        
        # Drawdown stability (inverse of mean)
        dd_stability = 1 / (1 + sum(drawdowns)/len(drawdowns))
        
        # Combined
        robustness = (
            0.4 * return_stability +
            0.4 * sharpe_stability +
            0.2 * dd_stability
        )
        
        return min(robustness, 1.0)


def create_monte_carlo_simulator() -> MonteCarloSimulator:
    """Create default Monte Carlo simulator."""
    return MonteCarloSimulator(num_simulations=500)


def simulate_base_trades(num_trades: int) -> List[Dict]:
    """Generate base trade list for simulation."""
    trades = []
    for i in range(num_trades):
        trades.append({
            "return_pct": random.uniform(-0.05, 0.08),
            "entry_time": 1700000000 + i * 3600,
            "exit_time": 1700000000 + i * 3600 + random.randint(600, 86400),
        })
    return trades
