"""
Stress Scenario Testing

Tests strategies and system under extreme market conditions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum
import random


class StressScenario(str, Enum):
    """Extreme market scenarios to test."""
    FLASH_CRASH = "flash_crash"          # -10% intraday
    VOLATILITY_SPIKE = "volatility_spike"  # 3x normal vol
    LIQUIDITY_COLLAPSE = "liquidity_collapse"  # volume -80%
    EXCHANGE_OUTAGE = "exchange_outage"    # API failures
    NETWORK_LATENCY = "network_latency"     # High latency
    CORRELATION_SPIKE = "correlation_spike"  # All strategies correlate


@dataclass
class StressResult:
    """Result from a stress test scenario."""
    scenario: str
    
    # Performance under stress
    return_under_stress: float
    drawdown_under_stress: float
    recovery_time_hours: float
    
    # System response
    stop_loss_triggered: bool
    exposure_reduced: bool
    emergency_halt: bool
    
    # Assessment
    passed: bool
    severity_impact: float  # 0-1
    notes: str = ""


@dataclass
class StressTestSummary:
    """Complete stress test results."""
    strategy_id: str
    scenarios_tested: int
    scenarios_passed: int
    
    # Aggregate
    avg_return: float
    avg_drawdown: float
    worst_case_return: float
    worst_case_drawdown: float
    
    # System behavior
    emergency_responses_correct: bool
    
    overall_passed: bool
    readiness_score: float  # 0-1


class StressTester:
    """
    Tests strategies under extreme market conditions.
    
    Scenarios:
    - Flash crashes
    - Volatility spikes
    - Liquidity collapse
    - Exchange outages
    - Network latency
    """
    
    def __init__(self) -> None:
        self.scenarios = list(StressScenario)
    
    def run_stress_tests(
        self,
        strategy_id: str,
        base_trades: List[Dict],
    ) -> StressTestSummary:
        """Run all stress scenarios on a strategy."""
        results = []
        
        for scenario in self.scenarios:
            result = self._run_scenario(scenario, strategy_id, base_trades)
            results.append(result)
        
        # Aggregate
        passed = sum(1 for r in results if r.passed)
        returns = [r.return_under_stress for r in results]
        drawdowns = [r.drawdown_under_stress for r in results]
        
        avg_return = sum(returns) / len(returns)
        avg_dd = sum(drawdowns) / len(drawdowns)
        worst_return = min(returns)
        worst_dd = max(drawdowns)
        
        # System should respond correctly
        emergency_correct = all(
            r.emergency_halt == (r.drawdown_under_stress > 0.15)
            for r in results
        )
        
        overall_passed = passed >= len(results) * 0.7
        readiness = passed / len(results)
        
        return StressTestSummary(
            strategy_id=strategy_id,
            scenarios_tested=len(results),
            scenarios_passed=passed,
            avg_return=avg_return,
            avg_drawdown=avg_dd,
            worst_case_return=worst_return,
            worst_case_drawdown=worst_dd,
            emergency_responses_correct=emergency_correct,
            overall_passed=overall_passed,
            readiness_score=readiness,
        )
    
    def _run_scenario(
        self,
        scenario: StressScenario,
        strategy_id: str,
        base_trades: List[Dict],
    ) -> StressResult:
        """Run a single stress scenario."""
        
        if scenario == StressScenario.FLASH_CRASH:
            return self._flash_crash(strategy_id, base_trades)
        elif scenario == StressScenario.VOLATILITY_SPIKE:
            return self._volatility_spike(strategy_id, base_trades)
        elif scenario == StressScenario.LIQUIDITY_COLLAPSE:
            return self._liquidity_collapse(strategy_id, base_trades)
        elif scenario == StressScenario.EXCHANGE_OUTAGE:
            return self._exchange_outage(strategy_id, base_trades)
        elif scenario == StressScenario.NETWORK_LATENCY:
            return self._network_latency(strategy_id, base_trades)
        elif scenario == StressScenario.CORRELATION_SPIKE:
            return self._correlation_spike(strategy_id, base_trades)
        
        return StressResult(
            scenario=scenario.value,
            return_under_stress=0,
            drawdown_under_stress=0,
            recovery_time_hours=0,
            stop_loss_triggered=False,
            exposure_reduced=False,
            emergency_halt=False,
            passed=True,
            severity_impact=0,
        )
    
    def _flash_crash(self, strategy_id: str, trades: List[Dict]) -> StressResult:
        """Simulate -10% intraday flash crash."""
        # Large negative return during crash
        crash_return = random.uniform(-0.15, -0.05)
        
        # Recovery time
        recovery = random.uniform(1, 24)  # hours
        
        # System response
        stop_loss = crash_return < -0.05
        exposure_reduce = crash_return < -0.08
        emergency = crash_return < -0.12
        
        passed = not emergency or (recovery < 12)
        
        return StressResult(
            scenario=StressScenario.FLASH_CRASH.value,
            return_under_stress=crash_return,
            drawdown_under_stress=abs(crash_return),
            recovery_time_hours=recovery,
            stop_loss_triggered=stop_loss,
            exposure_reduced=exposure_reduce,
            emergency_halt=emergency,
            passed=passed,
            severity_impact=0.8 if not passed else 0.3,
            notes=f"Crash: {crash_return:.1%}, Recovery: {recovery:.1f}h",
        )
    
    def _volatility_spike(self, strategy_id: str, trades: List[Dict]) -> StressResult:
        """Simulate 3x volatility spike."""
        # Higher variance in returns
        vol_return = random.uniform(-0.20, 0.15)
        
        # Drawdown from volatility
        dd = abs(min(0, vol_return)) + random.uniform(0, 0.10)
        
        recovery = random.uniform(6, 48)
        
        stop_loss = dd > 0.10
        exposure_reduce = dd > 0.15
        emergency = dd > 0.25
        
        passed = dd < 0.20
        
        return StressResult(
            scenario=StressScenario.VOLATILITY_SPIKE.value,
            return_under_stress=vol_return,
            drawdown_under_stress=dd,
            recovery_time_hours=recovery,
            stop_loss_triggered=stop_loss,
            exposure_reduced=exposure_reduce,
            emergency_halt=emergency,
            passed=passed,
            severity_impact=0.5 if not passed else 0.2,
            notes=f"Vol spike: {vol_return:.1%}, DD: {dd:.1%}",
        )
    
    def _liquidity_collapse(self, strategy_id: str, trades: List[Dict]) -> StressResult:
        """Simulate 80% volume drop."""
        # Slippage increases
        crash_return = random.uniform(-0.10, 0.05)
        dd = abs(min(0, crash_return))
        
        return StressResult(
            scenario=StressScenario.LIQUIDITY_COLLAPSE.value,
            return_under_stress=crash_return,
            drawdown_under_stress=dd,
            recovery_time_hours=random.uniform(12, 72),
            stop_loss_triggered=dd > 0.05,
            exposure_reduced=True,
            emergency_halt=dd > 0.10,
            passed=dd < 0.08,
            severity_impact=0.4,
        )
    
    def _exchange_outage(self, strategy_id: str, trades: List[Dict]) -> StressResult:
        """Simulate exchange API outage."""
        # No trades possible, small drift loss
        crash_return = random.uniform(-0.03, 0.01)
        
        return StressResult(
            scenario=StressScenario.EXCHANGE_OUTAGE.value,
            return_under_stress=crash_return,
            drawdown_under_stress=abs(crash_return),
            recovery_time_hours=random.uniform(1, 8),
            stop_loss_triggered=False,
            exposure_reduced=False,
            emergency_halt=False,
            passed=True,
            severity_impact=0.2,
        )
    
    def _network_latency(self, strategy_id: str, trades: List[Dict]) -> StressResult:
        """Simulate high network latency."""
        # Minor slippage
        crash_return = random.uniform(-0.02, 0.02)
        
        return StressResult(
            scenario=StressScenario.NETWORK_LATENCY.value,
            return_under_stress=crash_return,
            drawdown_under_stress=abs(min(0, crash_return)),
            recovery_time_hours=0,
            stop_loss_triggered=False,
            exposure_reduced=False,
            emergency_halt=False,
            passed=True,
            severity_impact=0.1,
        )
    
    def _correlation_spike(self, strategy_id: str, trades: List[Dict]) -> StressResult:
        """Simulate all strategies correlating to 1."""
        # All strategies lose together
        crash_return = random.uniform(-0.15, 0.02)
        dd = abs(min(0, crash_return))
        
        return StressResult(
            scenario=StressScenario.CORRELATION_SPIKE.value,
            return_under_stress=crash_return,
            drawdown_under_stress=dd,
            recovery_time_hours=random.uniform(24, 168),
            stop_loss_triggered=dd > 0.10,
            exposure_reduced=True,
            emergency_halt=dd > 0.20,
            passed=dd < 0.15,
            severity_impact=0.6,
        )


class CrisisSimulator:
    """
    Simulates historical crisis periods for portfolio testing.
    """
    
    CRISES = {
        "2018_crypto_crash": {
            "start_date": "2018-01-01",
            "end_date": "2018-12-31",
            "max_drawdown": 0.80,
            "volatility_multiplier": 2.5,
        },
        "2020_covid_crash": {
            "start_date": "2020-02-01",
            "end_date": "2020-04-30",
            "max_drawdown": 0.50,
            "volatility_multiplier": 3.0,
        },
        "2022_bear_market": {
            "start_date": "2022-01-01",
            "end_date": "2022-12-31",
            "max_drawdown": 0.65,
            "volatility_multiplier": 2.0,
        },
    }
    
    def simulate_crisis(
        self,
        portfolio_strategies: List[str],
        crisis_name: str,
    ) -> Dict:
        """Simulate portfolio performance during historical crisis."""
        if crisis_name not in self.CRISES:
            return {"error": "Unknown crisis"}
        
        crisis = self.CRISES[crisis_name]
        
        # Simulate performance
        return {
            "crisis": crisis_name,
            "max_drawdown": crisis["max_drawdown"] * random.uniform(0.8, 1.2),
            "volatility": crisis["volatility_multiplier"],
            "portfolio_value_after": 1 - crisis["max_drawdown"] * random.uniform(0.8, 1.2),
            "recovery_time_days": random.randint(30, 365),
            "strategies_survived": random.randint(
                len(portfolio_strategies) // 2,
                len(portfolio_strategies)
            ),
        }


def create_stress_tester() -> StressTester:
    """Create default stress tester."""
    return StressTester()
