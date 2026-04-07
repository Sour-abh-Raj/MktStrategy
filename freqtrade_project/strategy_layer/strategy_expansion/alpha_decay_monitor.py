"""
Alpha Decay Monitor

Monitors strategy performance over time and detects deterioration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Deque
from collections import deque
from datetime import datetime, timedelta
import random


@dataclass
class DecayMetrics:
    """Rolling performance metrics."""
    rolling_sharpe: float
    rolling_win_rate: float
    rolling_drawdown: float
    rolling_profit_factor: float
    trade_count: int
    
    # Trend
    sharpe_trend: str  # "improving", "stable", "declining"
    return_trend: str


@dataclass
class DecayAlert:
    """Alert when strategy shows decay."""
    strategy_id: str
    severity: str  # "warning", "critical"
    message: str
    detected_at: str
    
    # Metrics at detection
    current_sharpe: float
    baseline_sharpe: float
    decay_pct: float


@dataclass
class DecayReport:
    """Complete decay analysis."""
    strategy_id: str
    
    # Current state
    current_metrics: DecayMetrics
    
    # History
    metrics_history: List[DecayMetrics]
    
    # Detection
    alerts: List[DecayAlert]
    
    # Recommendation
    action: str  # "continue", "reduce_allocation", "retire"
    replacement_candidates: List[str]


class AlphaDecayMonitor:
    """
    Monitors alpha decay in strategies.
    
    Tracks rolling metrics and detects deterioration.
    """
    
    def __init__(
        self,
        window_size: int = 30,  # Rolling window in trades
        decay_threshold: float = 0.3,  # 30% decay triggers warning
        lookback_periods: int = 3,
    ) -> None:
        self.window_size = window_size
        self.decay_threshold = decay_threshold
        self.lookback_periods = lookback_periods
        
        # Rolling data per strategy
        self.strategy_data: Dict[str, Deque] = {}
        
        # Baseline performance (established when strategy enters library)
        self.baselines: Dict[str, Dict] = {}
    
    def register_strategy(
        self,
        strategy_id: str,
        sharpe: float,
        win_rate: float,
        profit_factor: float,
        max_drawdown: float,
    ) -> None:
        """Register a new strategy with baseline performance."""
        self.baselines[strategy_id] = {
            "sharpe": sharpe,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "registered_at": datetime.now().isoformat(),
        }
        self.strategy_data[strategy_id] = deque(maxlen=self.window_size)
    
    def record_trade(
        self,
        strategy_id: str,
        return_pct: float,
        won: bool,
        timestamp: Optional[str] = None,
    ) -> None:
        """Record a trade result for a strategy."""
        if strategy_id not in self.strategy_data:
            self.strategy_data[strategy_id] = deque(maxlen=self.window_size)
        
        self.strategy_data[strategy_id].append({
            "return": return_pct,
            "won": won,
            "timestamp": timestamp or datetime.now().isoformat(),
        })
    
    def analyze_strategy(self, strategy_id: str) -> DecayReport:
        """Analyze a strategy for decay."""
        if strategy_id not in self.strategy_data:
            return DecayReport(
                strategy_id=strategy_id,
                current_metrics=DecayMetrics(0, 0, 0, 0, 0, "stable", "stable"),
                metrics_history=[],
                alerts=[],
                action="continue",
                replacement_candidates=[],
            )
        
        trades = list(self.strategy_data[strategy_id])
        
        if len(trades) < 5:
            return DecayReport(
                strategy_id=strategy_id,
                current_metrics=self._calculate_metrics(trades),
                metrics_history=[],
                alerts=[],
                action="continue",
                replacement_candidates=[],
            )
        
        # Calculate current metrics
        current_metrics = self._calculate_metrics(trades)
        
        # Calculate historical metrics (in chunks)
        metrics_history = []
        chunk_size = max(5, len(trades) // 4)
        
        for i in range(0, len(trades), chunk_size):
            chunk = trades[i:i+chunk_size]
            if chunk:
                metrics_history.append(self._calculate_metrics(chunk))
        
        # Detect decay
        alerts = self._detect_decay(strategy_id, current_metrics, metrics_history)
        
        # Determine action
        action = self._determine_action(alerts, current_metrics)
        
        # Find replacement candidates
        replacements = self._find_replacements(strategy_id)
        
        return DecayReport(
            strategy_id=strategy_id,
            current_metrics=current_metrics,
            metrics_history=metrics_history,
            alerts=alerts,
            action=action,
            replacement_candidates=replacements,
        )
    
    def _calculate_metrics(self, trades: List[Dict]) -> DecayMetrics:
        """Calculate metrics from trades."""
        if not trades:
            return DecayMetrics(0, 0, 0, 0, 0, "stable", "stable")
        
        returns = [t["return"] for t in trades]
        wins = sum(1 for t in trades if t["won"])
        
        # Sharpe (simplified)
        avg_ret = sum(returns) / len(returns)
        std_ret = self._std(returns) if len(returns) > 1 else 0.01
        sharpe = avg_ret / std_ret if std_ret > 0 else 0
        
        # Win rate
        win_rate = wins / len(trades)
        
        # Drawdown (simplified)
        equity = 1.0
        peak = 1.0
        max_dd = 0
        for r in returns:
            equity *= (1 + r)
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd
        
        # Profit factor
        gross_win = sum(r for r in returns if r > 0)
        gross_loss = abs(sum(r for r in returns if r < 0))
        pf = gross_win / gross_loss if gross_loss > 0 else 999
        
        # Trends
        if len(returns) >= 10:
            recent = sum(returns[-5:]) / 5
            older = sum(returns[:5]) / 5
            sharpe_trend = "improving" if recent > older * 1.1 else "declining" if recent < older * 0.9 else "stable"
            return_trend = "improving" if recent > older else "declining"
        else:
            sharpe_trend = "stable"
            return_trend = "stable"
        
        return DecayMetrics(
            rolling_sharpe=sharpe,
            rolling_win_rate=win_rate,
            rolling_drawdown=max_dd,
            rolling_profit_factor=pf,
            trade_count=len(trades),
            sharpe_trend=sharpe_trend,
            return_trend=return_trend,
        )
    
    def _detect_decay(
        self,
        strategy_id: str,
        current: DecayMetrics,
        history: List[DecayMetrics],
    ) -> List[DecayAlert]:
        """Detect if strategy is decaying."""
        alerts = []
        
        if strategy_id not in self.baselines:
            return alerts
        
        baseline = self.baselines[strategy_id]
        
        # Sharpe decay
        baseline_sharpe = baseline["sharpe"]
        if baseline_sharpe > 0:
            decay_pct = (baseline_sharpe - current.rolling_sharpe) / baseline_sharpe
            
            if decay_pct > self.decay_threshold:
                if decay_pct > 0.5:
                    severity = "critical"
                else:
                    severity = "warning"
                
                alerts.append(DecayAlert(
                    strategy_id=strategy_id,
                    severity=severity,
                    message=f"Sharpe decayed {decay_pct:.1%} from baseline {baseline_sharpe:.2f} to {current.rolling_sharpe:.2f}",
                    detected_at=datetime.now().isoformat(),
                    current_sharpe=current.rolling_sharpe,
                    baseline_sharpe=baseline_sharpe,
                    decay_pct=decay_pct,
                ))
        
        # Win rate decay
        baseline_win = baseline["win_rate"]
        if current.rolling_win_rate < baseline_win * 0.8:
            alerts.append(DecayAlert(
                strategy_id=strategy_id,
                severity="warning",
                message=f"Win rate dropped from {baseline_win:.1%} to {current.rolling_win_rate:.1%}",
                detected_at=datetime.now().isoformat(),
                current_sharpe=current.rolling_sharpe,
                baseline_sharpe=baseline_sharpe,
                decay_pct=(baseline_win - current.rolling_win_rate) / baseline_win,
            ))
        
        # Drawdown increase
        baseline_dd = baseline["max_drawdown"]
        if current.rolling_drawdown > baseline_dd * 1.5:
            alerts.append(DecayAlert(
                strategy_id=strategy_id,
                severity="critical" if current.rolling_drawdown > baseline_dd * 2 else "warning",
                message=f"Drawdown increased from {baseline_dd:.1%} to {current.rolling_drawdown:.1%}",
                detected_at=datetime.now().isoformat(),
                current_sharpe=current.rolling_sharpe,
                baseline_sharpe=baseline_sharpe,
                decay_pct=(current.rolling_drawdown - baseline_dd) / baseline_dd,
            ))
        
        return alerts
    
    def _determine_action(
        self,
        alerts: List[DecayAlert],
        metrics: DecayMetrics,
    ) -> str:
        """Determine recommended action."""
        if not alerts:
            return "continue"
        
        critical_count = sum(1 for a in alerts if a.severity == "critical")
        warning_count = sum(1 for a in alerts if a.severity == "warning")
        
        if critical_count >= 2:
            return "retire"
        elif critical_count >= 1:
            return "reduce_allocation"
        elif warning_count >= 3:
            return "reduce_allocation"
        else:
            return "continue"
    
    def _find_replacements(self, current_id: str) -> List[str]:
        """Find replacement strategy candidates."""
        # Simple: return any strategy with positive metrics
        # In production: would query strategy library
        return [f"candidate_{i}" for i in range(3)]
    
    def _std(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
        return variance ** 0.5
    
    def get_portfolio_health(self) -> Dict:
        """Get overall portfolio health status."""
        total_strategies = len(self.strategy_data)
        
        if total_strategies == 0:
            return {
                "status": "no_data",
                "healthy_count": 0,
                "warning_count": 0,
                "critical_count": 0,
            }
        
        healthy = 0
        warning = 0
        critical = 0
        
        for sid in self.strategy_data:
            report = self.analyze_strategy(sid)
            if report.action == "retire":
                critical += 1
            elif report.action == "reduce_allocation":
                warning += 1
            else:
                healthy += 1
        
        status = "healthy" if critical == 0 else "warning" if critical < 3 else "critical"
        
        return {
            "status": status,
            "healthy_count": healthy,
            "warning_count": warning,
            "critical_count": critical,
            "total_strategies": total_strategies,
        }


def create_decay_monitor(window_size: int = 30) -> AlphaDecayMonitor:
    """Create decay monitor."""
    return AlphaDecayMonitor(window_size=window_size)
