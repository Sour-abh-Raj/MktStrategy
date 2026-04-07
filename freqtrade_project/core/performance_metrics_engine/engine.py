"""
Unified Performance Metrics Engine

Single source of truth for computing all performance metrics.
Replaces PerformanceAnalyzer and PerformanceValidator with consistent logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np
from statistics import mean, stdev


@dataclass
class Trade:
    """Individual trade record."""
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: int  # timestamp
    exit_time: int   # timestamp
    side: str = "long"  # "long" or "short"
    
    @property
    def return_pct(self) -> float:
        """Return as percentage."""
        if self.side == "long":
            return (self.exit_price - self.entry_price) / self.entry_price
        return (self.entry_price - self.exit_price) / self.entry_price
    
    @property
    def profit(self) -> float:
        """Profit/loss in absolute terms."""
        return self.return_pct * self.quantity * self.entry_price
    
    @property
    def duration(self) -> int:
        """Trade duration in seconds."""
        return self.exit_time - self.entry_time


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""
    # Core metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Return metrics
    total_return: float
    annualized_return: float
    avg_trade_return: float
    
    # Risk metrics
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    current_drawdown: float
    
    # Profit metrics
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    
    # Stability metrics
    return_std: float
    stability_score: float
    
    # Trade analysis
    avg_trade_duration: float
    trades_per_day: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization."""
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": self.win_rate,
            "total_return": self.total_return,
            "annualized_return": self.annualized_return,
            "avg_trade_return": self.avg_trade_return,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self.max_drawdown,
            "current_drawdown": self.current_drawdown,
            "profit_factor": self.profit_factor,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "largest_win": self.largest_win,
            "largest_loss": self.largest_loss,
            "return_std": self.return_std,
            "stability_score": self.stability_score,
            "avg_trade_duration": self.avg_trade_duration,
            "trades_per_day": self.trades_per_day,
        }


class PerformanceMetricsEngine:
    """
    Unified engine for computing all strategy performance metrics.
    
    Replaces:
    - PerformanceAnalyzer
    - PerformanceValidator
    """
    
    def __init__(self, risk_free_rate: float = 0.0):
        """
        Initialize the metrics engine.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe calculation
        """
        self.risk_free_rate = risk_free_rate
    
    def compute_metrics(
        self,
        trades: List[Trade],
        equity_curve: List[float],
        timestamps: List[int],
    ) -> PerformanceMetrics:
        """
        Compute all performance metrics from trade history.
        
        Args:
            trades: List of completed trades
            equity_curve: Equity curve values
            timestamps: Timestamps corresponding to equity values
            
        Returns:
            Comprehensive PerformanceMetrics
        """
        if not trades:
            return self._empty_metrics()
        
        # Sort trades by exit time
        sorted_trades = sorted(trades, key=lambda t: t.exit_time)
        
        # Basic counts
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.profit > 0)
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Returns
        returns = [t.return_pct for t in trades]
        total_return = sum(returns)
        avg_trade_return = mean(returns) if returns else 0
        
        # Annualized return (assuming ~252 trading days)
        if len(timestamps) >= 2:
            time_span_days = (timestamps[-1] - timestamps[0]) / 86400
            if time_span_days > 0:
                periods_per_year = 252 / max(time_span_days, 1)
                annualized_return = (1 + total_return) ** periods_per_year - 1
            else:
                annualized_return = total_return
        else:
            annualized_return = total_return
        
        # Drawdown
        max_dd, current_dd = self._compute_drawdown(equity_curve)
        
        # Sharpe ratio
        sharpe = self._compute_sharpe(returns, annualized_return)
        
        # Sortino ratio (downside deviation)
        sortino = self._compute_sortino(returns, annualized_return)
        
        # Profit metrics
        profits = [t.profit for t in trades]
        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p < 0]
        
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        
        avg_win = mean(wins) if wins else 0
        avg_loss = mean(losses) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = min(losses) if losses else 0
        
        # Stability
        return_std = stdev(returns) if len(returns) > 1 else 0
        stability = self._compute_stability(returns)
        
        # Trade timing
        durations = [t.duration for t in trades]
        avg_duration = mean(durations) if durations else 0
        
        # Trades per day
        if len(timestamps) >= 2:
            days = max((timestamps[-1] - timestamps[0]) / 86400, 1)
            trades_per_day = total_trades / days
        else:
            trades_per_day = 0
        
        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return=total_return,
            annualized_return=annualized_return,
            avg_trade_return=avg_trade_return,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            current_drawdown=current_dd,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            return_std=return_std,
            stability_score=stability,
            avg_trade_duration=avg_duration,
            trades_per_day=trades_per_day,
        )
    
    def compute_from_equity(
        self,
        equity_curve: List[float],
        timestamps: List[int],
    ) -> PerformanceMetrics:
        """
        Compute metrics from equity curve only (for buy-and-hold benchmarks).
        
        Args:
            equity_curve: List of equity values
            timestamps: Timestamps for each equity value
            
        Returns:
            PerformanceMetrics
        """
        if len(equity_curve) < 2:
            return self._empty_metrics()
        
        # Compute returns from equity curve
        returns = []
        for i in range(1, len(equity_curve)):
            ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
            returns.append(ret)
        
        # Create synthetic trades for compatibility
        trades = []
        for i in range(len(returns)):
            trades.append(Trade(
                entry_price=equity_curve[i],
                exit_price=equity_curve[i+1],
                quantity=1.0,
                entry_time=timestamps[i],
                exit_time=timestamps[i+1],
            ))
        
        return self.compute_metrics(trades, equity_curve, timestamps)
    
    def compute_from_returns(
        self,
        returns: List[float],
        timestamps: Optional[List[int]] = None,
    ) -> PerformanceMetrics:
        """
        Compute metrics from a list of periodic returns.
        
        Args:
            returns: List of period returns (e.g., daily returns)
            timestamps: Optional timestamps for each return
            
        Returns:
            PerformanceMetrics
        """
        if not returns:
            return self._empty_metrics()
        
        # Create synthetic equity curve
        equity = [1.0]
        for r in returns:
            equity.append(equity[-1] * (1 + r))
        
        if timestamps is None:
            timestamps = list(range(len(returns)))
        
        # Create synthetic trades
        trades = [
            Trade(
                entry_price=equity[i],
                exit_price=equity[i+1],
                quantity=1.0,
                entry_time=timestamps[i],
                exit_time=timestamps[i+1],
            )
            for i in range(len(returns))
        ]
        
        return self.compute_metrics(trades, equity, timestamps)
    
    def _empty_metrics(self) -> PerformanceMetrics:
        """Return empty metrics for no-data case."""
        return PerformanceMetrics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_return=0.0,
            annualized_return=0.0,
            avg_trade_return=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown=0.0,
            current_drawdown=0.0,
            profit_factor=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            largest_win=0.0,
            largest_loss=0.0,
            return_std=0.0,
            stability_score=0.0,
            avg_trade_duration=0.0,
            trades_per_day=0.0,
        )
    
    def _compute_drawdown(self, equity: List[float]) -> Tuple[float, float]:
        """Compute max and current drawdown."""
        if not equity:
            return 0.0, 0.0
        
        peak = equity[0]
        max_dd = 0.0
        
        for value in equity:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        
        # Current drawdown
        current_dd = (peak - equity[-1]) / peak if peak > 0 else 0
        
        return max_dd, current_dd
    
    def _compute_sharpe(self, returns: List[float], annualized_return: float) -> float:
        """Compute Sharpe ratio."""
        if not returns or len(returns) < 2:
            return 0.0
        
        avg_return = mean(returns)
        std_return = stdev(returns)
        
        if std_return == 0:
            return 0.0
        
        # Annualize if returns are not already annualized
        # Assuming returns are per-trade
        return (annualized_return - self.risk_free_rate) / std_return
    
    def _compute_sortino(self, returns: List[float], annualized_return: float) -> float:
        """Compute Sortino ratio using downside deviation."""
        if not returns:
            return 0.0
        
        # Downside returns only
        downside = [r for r in returns if r < 0]
        
        if not downside:
            return float('inf') if annualized_return > 0 else 0.0
        
        downside_std = stdev(downside) if len(downside) > 1 else 0
        
        if downside_std == 0:
            return 0.0
        
        return (annualized_return - self.risk_free_rate) / downside_std
    
    def _compute_stability(self, returns: List[float]) -> float:
        """
        Compute stability score based on return consistency.
        
        Returns value between 0-1 where 1 is most stable.
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        # Coefficient of variation
        avg = mean(returns)
        std = stdev(returns)
        
        if avg == 0:
            return 0.0
        
        cv = abs(std / avg)
        
        # Invert CV: lower CV = higher stability
        return max(0, 1 - cv)
    
    def compare_to_benchmark(
        self,
        strategy_metrics: PerformanceMetrics,
        benchmark_metrics: PerformanceMetrics,
    ) -> Dict[str, any]:
        """
        Compare strategy performance to benchmark.
        
        Args:
            strategy_metrics: Strategy performance metrics
            benchmark_metrics: Benchmark (e.g., buy-and-hold) metrics
            
        Returns:
            Comparison dictionary
        """
        return {
            "return_diff": strategy_metrics.annualized_return - benchmark_metrics.annualized_return,
            "sharpe_diff": strategy_metrics.sharpe_ratio - benchmark_metrics.sharpe_ratio,
            "drawdown_diff": benchmark_metrics.max_drawdown - strategy_metrics.max_drawdown,  # Positive is good
            "outperforms_return": strategy_metrics.annualized_return > benchmark_metrics.annualized_return,
            "outperforms_sharpe": strategy_metrics.sharpe_ratio > benchmark_metrics.sharpe_ratio,
            "lower_drawdown": strategy_metrics.max_drawdown < benchmark_metrics.max_drawdown,
        }
    
    def compute_ranking_score(
        self,
        metrics: PerformanceMetrics,
        weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Compute overall ranking score from metrics.
        
        Args:
            metrics: Performance metrics
            weights: Custom weights for scoring
            
        Returns:
            Overall score
        """
        if weights is None:
            weights = {
                "sharpe": 0.25,
                "sortino": 0.20,
                "profit_factor": 0.20,
                "max_drawdown": -0.15,
                "win_rate": 0.10,
                "stability": 0.10,
            }
        
        score = 0.0
        
        # Normalize Sharpe to 0-1 range (cap at 3.0)
        sharpe_norm = min(metrics.sharpe_ratio / 3.0, 1.0)
        score += weights.get("sharpe", 0) * sharpe_norm
        
        # Sortino
        sortino_norm = min(metrics.sortino_ratio / 3.0, 1.0)
        score += weights.get("sortino", 0) * sortino_norm
        
        # Profit factor (normalize 1.0-3.0 range)
        pf_norm = min(max((metrics.profit_factor - 1.0) / 2.0, 0), 1.0)
        score += weights.get("profit_factor", 0) * pf_norm
        
        # Drawdown (penalize)
        dd_norm = metrics.max_drawdown / 0.25  # Normalize to 0-25%
        score += weights.get("max_drawdown", 0) * min(dd_norm, 1.0)
        
        # Win rate
        score += weights.get("win_rate", 0) * metrics.win_rate
        
        # Stability
        score += weights.get("stability", 0) * metrics.stability_score
        
        return score


# Singleton instance
_metrics_engine: Optional[PerformanceMetricsEngine] = None


def get_metrics_engine() -> PerformanceMetricsEngine:
    """Get the default metrics engine instance."""
    global _metrics_engine
    if _metrics_engine is None:
        _metrics_engine = PerformanceMetricsEngine()
    return _metrics_engine
