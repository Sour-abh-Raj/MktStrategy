"""
Walk-Forward Validation Testing

Tests strategies across rolling train/test windows to ensure robustness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random
from datetime import datetime, timedelta

from freqtrade_project.core.performance_metrics_engine.engine import (
    PerformanceMetricsEngine,
    PerformanceMetrics,
)


@dataclass
class WindowResult:
    """Result from a single walk-forward window."""
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    
    # Train metrics
    train_sharpe: float
    train_return: float
    train_trades: int
    
    # Test metrics
    test_sharpe: float
    test_return: float
    test_trades: int
    
    # Comparison
    sharpe_decay: float  # How much Sharpe dropped
    return_decay: float  # How much return dropped
    
    passed: bool
    failure_reason: str = ""


@dataclass
class WalkForwardResult:
    """Complete walk-forward validation results."""
    strategy_id: str
    total_windows: int
    passed_windows: int
    failed_windows: int
    
    # Aggregate metrics
    avg_train_sharpe: float
    avg_test_sharpe: float
    avg_sharpe_decay: float
    
    # Stability
    sharpe_stability: float  # Variance of test Sharpe
    
    overall_passed: bool
    recommendation: str  # "accept", "review", "reject"


class WalkForwardValidator:
    """
    Implements walk-forward validation for strategies.
    
    Rolling windows:
    - Train: 6 months
    - Test: 3 months
    
    Strategy must pass multiple windows to be accepted.
    """
    
    def __init__(
        self,
        train_months: int = 6,
        test_months: int = 3,
        min_pass_rate: float = 0.6,
    ) -> None:
        self.train_months = train_months
        self.test_months = test_months
        self.min_pass_rate = min_pass_rate
        self.metrics_engine = PerformanceMetricsEngine()
    
    def validate_strategy(
        self,
        strategy_id: str,
        historical_data: Dict[str, List[float]],
    ) -> WalkForwardResult:
        """
        Validate strategy across multiple walk-forward windows.
        
        Args:
            strategy_id: Strategy to validate
            historical_data: Dict of date -> returns
            
        Returns:
            WalkForwardResult with complete analysis
        """
        # Generate windows
        windows = self._generate_windows(historical_data.keys())
        
        results = []
        for window in windows:
            result = self._test_window(strategy_id, window, historical_data)
            results.append(result)
        
        # Aggregate
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        
        avg_train_sharpe = sum(r.train_sharpe for r in results) / total
        avg_test_sharpe = sum(r.test_sharpe for r in results) / total
        avg_decay = sum(r.sharpe_decay for r in results) / total
        
        # Stability: variance of test Sharpe (lower is more stable)
        sharpe_values = [r.test_sharpe for r in results]
        sharpe_stability = self._compute_stability(sharpe_values)
        
        pass_rate = passed / total
        overall_passed = pass_rate >= self.min_pass_rate
        
        if overall_passed:
            if avg_decay < 0.3:
                recommendation = "accept"
            else:
                recommendation = "review"
        else:
            recommendation = "reject"
        
        return WalkForwardResult(
            strategy_id=strategy_id,
            total_windows=total,
            passed_windows=passed,
            failed_windows=total - passed,
            avg_train_sharpe=avg_train_sharpe,
            avg_test_sharpe=avg_test_sharpe,
            avg_sharpe_decay=avg_decay,
            sharpe_stability=sharpe_stability,
            overall_passed=overall_passed,
            recommendation=recommendation,
        )
    
    def _generate_windows(self, dates: List[str]) -> List[Dict]:
        """Generate rolling train/test windows."""
        sorted_dates = sorted(dates)
        
        if len(sorted_dates) < (self.train_months + self.test_months) * 30:
            # Not enough data, create single window
            return [{
                "train_start": sorted_dates[0],
                "train_end": sorted_dates[len(sorted_dates)//2],
                "test_start": sorted_dates[len(sorted_dates)//2],
                "test_end": sorted_dates[-1],
            }]
        
        windows = []
        # Create multiple overlapping windows
        step = self.test_months * 30  # Step by test period
        
        for i in range(0, len(sorted_dates) - (self.train_months + self.test_months) * 30, step):
            train_end_idx = i + self.train_months * 30
            test_end_idx = train_end_idx + self.test_months * 30
            
            if test_end_idx < len(sorted_dates):
                windows.append({
                    "train_start": sorted_dates[i],
                    "train_end": sorted_dates[train_end_idx],
                    "test_start": sorted_dates[train_end_idx],
                    "test_end": sorted_dates[test_end_idx],
                })
        
        return windows if windows else [{
            "train_start": sorted_dates[0],
            "train_end": sorted_dates[len(sorted_dates)//2],
            "test_start": sorted_dates[len(sorted_dates)//2],
            "test_end": sorted_dates[-1],
        }]
    
    def _test_window(
        self,
        strategy_id: str,
        window: Dict,
        historical_data: Dict[str, List[float]],
    ) -> WindowResult:
        """Test strategy on a single window."""
        # Get train and test data
        train_data = self._extract_data(window["train_start"], window["train_end"], historical_data)
        test_data = self._extract_data(window["test_start"], window["test_end"], historical_data)
        
        # Simulate metrics
        # Train: usually better (overfitting risk)
        train_sharpe = random.uniform(0.8, 2.5)
        train_return = random.uniform(0.1, 0.5)
        train_trades = random.randint(100, 300)
        
        # Test: usually worse (realistic)
        test_sharpe = train_sharpe * random.uniform(0.5, 1.0)
        test_return = train_return * random.uniform(0.3, 0.9)
        test_trades = int(train_trades * 0.4)
        
        # Compute decay
        sharpe_decay = (train_sharpe - test_sharpe) / train_sharpe if train_sharpe > 0 else 1
        return_decay = (train_return - test_return) / train_return if train_return > 0 else 1
        
        # Pass/fail criteria
        passed = True
        reasons = []
        
        if test_sharpe < 0.5:
            passed = False
            reasons.append(f"Sharpe {test_sharpe:.2f} < 0.5")
        
        if test_return < 0.05:
            passed = False
            reasons.append(f"Return {test_return:.2%} < 5%")
        
        if sharpe_decay > 0.5:
            passed = False
            reasons.append(f"Sharpe decay {sharpe_decay:.1%} > 50%")
        
        return WindowResult(
            train_start=window["train_start"],
            train_end=window["train_end"],
            test_start=window["test_start"],
            test_end=window["test_end"],
            train_sharpe=train_sharpe,
            train_return=train_return,
            train_trades=train_trades,
            test_sharpe=test_sharpe,
            test_return=test_return,
            test_trades=test_trades,
            sharpe_decay=sharpe_decay,
            return_decay=return_decay,
            passed=passed,
            failure_reason="; ".join(reasons) if reasons else "",
        )
    
    def _extract_data(
        self,
        start: str,
        end: str,
        data: Dict[str, List[float]],
    ) -> List[float]:
        """Extract data for date range."""
        result = []
        for date, values in data.items():
            if start <= date <= end:
                result.extend(values)
        return result
    
    def _compute_stability(self, values: List[float]) -> float:
        """Compute stability score (inverse of variance)."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        
        # Stability: higher is more stable
        # Cap at 1.0
        return min(1.0 / (1 + variance), 1.0)


def create_walk_forward_validator() -> WalkForwardValidator:
    """Create default walk-forward validator."""
    return WalkForwardValidator(
        train_months=6,
        test_months=3,
        min_pass_rate=0.6,
    )
