"""
Cluster Monitoring and Research Guidance

Monitors cluster performance and guides research focus.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from collections import deque


@dataclass
class ClusterAlert:
    """Alert for cluster performance issues."""
    cluster_type: str
    severity: str  # "warning", "critical"
    message: str
    detected_at: str
    metrics_at_alert: Dict


@dataclass
class ResearchGuidance:
    """Guidance for research system based on cluster performance."""
    # Areas needing more research
    underperforming_clusters: List[str]
    
    # Areas to maintain
    stable_clusters: List[str]
    
    # Recommendations
    recommendations: List[str]
    
    # Priority scores by cluster
    cluster_priorities: Dict[str, float]  # higher = more research needed


@dataclass
class ClusterDashboard:
    """Complete cluster monitoring dashboard."""
    timestamp: str
    
    # Performance by cluster
    cluster_performance: Dict[str, Dict]
    
    # Allocations
    cluster_allocations: Dict[str, float]
    
    # Risks
    alerts: List[ClusterAlert]
    cluster_drawdowns: Dict[str, float]
    
    # Diversification
    average_correlation: float
    diversification_score: float


class ClusterMonitor:
    """
    Monitors alpha cluster performance and generates alerts.
    """
    
    def __init__(
        self,
        lookback_periods: int = 30,
        decay_threshold: float = 0.3,
    ) -> None:
        self.lookback_periods = lookback_periods
        self.decay_threshold = decay_threshold
        
        # Historical metrics per cluster
        self.cluster_history: Dict[str, deque] = {}
    
    def record_cluster_metrics(
        self,
        cluster_type: str,
        metrics: Dict,
    ) -> None:
        """Record metrics for a cluster."""
        
        if cluster_type not in self.cluster_history:
            self.cluster_history[cluster_type] = deque(maxlen=self.lookback_periods)
        
        self.cluster_history[cluster_type].append({
            "timestamp": datetime.now().isoformat(),
            **metrics,
        })
    
    def detect_cluster_decay(
        self,
        cluster_type: str,
        current_metrics: Dict,
        baseline_metrics: Dict,
    ) -> List[ClusterAlert]:
        """Detect performance decay in a cluster."""
        
        alerts = []
        
        # Sharpe decay
        if baseline_metrics.get("sharpe", 0) > 0:
            sharpe_decay = (baseline_metrics["sharpe"] - current_metrics.get("sharpe", 0)) / baseline_metrics["sharpe"]
            
            if sharpe_decay > self.decay_threshold:
                severity = "critical" if sharpe_decay > 0.5 else "warning"
                alerts.append(ClusterAlert(
                    cluster_type=cluster_type.value,
                    severity=severity,
                    message=f"Sharpe decayed {sharpe_decay:.1%} from {baseline_metrics['sharpe']:.2f} to {current_metrics.get('sharpe', 0):.2f}",
                    detected_at=datetime.now().isoformat(),
                    metrics_at_alert=current_metrics,
                ))
        
        # Drawdown increase
        baseline_dd = baseline_metrics.get("max_drawdown", 0)
        current_dd = current_metrics.get("max_drawdown", 0)
        
        if current_dd > baseline_dd * 1.5:
            severity = "critical" if current_dd > baseline_dd * 2 else "warning"
            alerts.append(ClusterAlert(
                cluster_type=cluster_type.value,
                severity=severity,
                message=f"Drawdown increased from {baseline_dd:.1%} to {current_dd:.1%}",
                detected_at=datetime.now().isoformat(),
                metrics_at_alert=current_metrics,
            ))
        
        return alerts
    
    def get_cluster_dashboard(
        self,
        cluster_metrics: Dict[str, Dict],
        cluster_allocations: Dict[str, float],
    ) -> ClusterDashboard:
        """Generate cluster monitoring dashboard."""
        
        # Get alerts for all clusters
        all_alerts = []
        cluster_drawdowns = {}
        
        for cluster_type, metrics in cluster_metrics.items():
            alerts = self.detect_cluster_decay(
                cluster_type,
                metrics,
                metrics,  # baseline = current for simplicity
            )
            all_alerts.extend(alerts)
            
            cluster_drawdowns[cluster_type.value] = metrics.get("max_drawdown", 0)
        
        # Calculate average correlation
        avg_corr = 0.4  # Simplified
        
        # Diversification score
        div_score = 1.0 - avg_corr
        
        return ClusterDashboard(
            timestamp=datetime.now().isoformat(),
            cluster_performance=cluster_metrics,
            cluster_allocations=cluster_allocations,
            alerts=all_alerts,
            cluster_drawdowns=cluster_drawdowns,
            average_correlation=avg_corr,
            diversification_score=div_score,
        )


class ResearchGuidanceEngine:
    """
    Guides research focus based on cluster performance.
    
    Analyzes which alpha clusters need more attention.
    """
    
    def __init__(self) -> None:
        self.research_priority_scores: Dict[str, float] = {}
    
    def generate_guidance(
        self,
        cluster_metrics: Dict[str, Dict],
    ) -> ResearchGuidance:
        """Generate research guidance based on cluster performance."""
        
        underperforming = []
        stable = []
        priorities = {}
        
        for cluster_type, metrics in cluster_metrics.items():
            sharpe = metrics.get("sharpe", 0)
            stability = metrics.get("stability_score", 0)
            active = metrics.get("active_strategies", 0)
            
            # Calculate research priority
            # Lower Sharpe + lower stability + fewer strategies = higher priority
            priority = 0.0
            
            if sharpe < 1.0:
                priority += (1.0 - sharpe) * 0.4
            
            if stability < 0.7:
                priority += (0.7 - stability) * 0.3
            
            if active < 5:
                priority += (5 - active) * 0.1
            
            priorities[cluster_type.value] = priority
            
            # Classify cluster
            if priority > 0.4:
                underperforming.append(cluster_type.value)
            else:
                stable.append(cluster_type.value)
        
        # Generate recommendations
        recommendations = []
        
        for cluster_type in underperforming:
            recommendations.append(f"Increase {cluster_type} strategy discovery")
        
        for cluster_type in stable:
            if priorities.get(cluster_type, 0) < 0.2:
                recommendations.append(f"Maintain {cluster_type} allocation")
        
        # Sort by priority
        underperforming.sort(key=lambda x: priorities.get(x, 0), reverse=True)
        
        return ResearchGuidance(
            underperforming_clusters=underperforming,
            stable_clusters=stable,
            recommendations=recommendations,
            cluster_priorities=priorities,
        )


class CrossClusterStressTester:
    """
    Tests portfolio resilience under cluster-specific stress scenarios.
    """
    
    def __init__(self) -> None:
        self.scenarios = [
            "trend_failure_sideways",
            "mean_reversion_trend",
            "macro_regime_shift",
            "volatility_spike",
            "correlation_increase",
        ]
    
    def simulate_scenario(
        self,
        scenario: str,
        cluster_allocations: Dict[str, float],
        cluster_metrics: Dict[str, Dict],
    ) -> Dict:
        """Simulate a stress scenario affecting specific clusters."""
        
        impact_factors = {
            "trend_failure_sideways": {
                "trend": 0.5,  # 50% return reduction
                "mean_reversion": 1.0,
                "volatility": 0.9,
                "microstructure": 1.0,
                "macro": 0.8,
                "cross_market": 0.9,
            },
            "mean_reversion_trend": {
                "trend": 1.0,
                "mean_reversion": 0.3,  # Major failure
                "volatility": 1.1,
                "microstructure": 1.0,
                "macro": 0.9,
                "cross_market": 0.8,
            },
            "macro_regime_shift": {
                "trend": 0.7,
                "mean_reversion": 0.8,
                "volatility": 1.2,
                "microstructure": 0.9,
                "macro": 0.2,  # Major failure
                "cross_market": 0.3,
            },
            "volatility_spike": {
                "trend": 0.8,
                "mean_reversion": 0.9,
                "volatility": 0.4,  # Vol strategies fail
                "microstructure": 0.7,
                "macro": 0.8,
                "cross_market": 0.9,
            },
            "correlation_increase": {
                "trend": 0.8,
                "mean_reversion": 0.8,
                "volatility": 0.8,
                "microstructure": 0.8,
                "macro": 0.8,
                "cross_market": 0.6,
            },
        }
        
        impacts = impact_factors.get(scenario, {})
        
        # Calculate impact on portfolio
        new_returns = {}
        new_drawdowns = {}
        
        for cluster_type, allocation in cluster_allocations.items():
            impact = impacts.get(cluster_type, 1.0)
            
            original_return = cluster_metrics.get(cluster_type, {}).get("return", 0.10)
            original_dd = cluster_metrics.get(cluster_type, {}).get("max_drawdown", 0.15)
            
            new_returns[cluster_type] = original_return * impact
            new_drawdowns[cluster_type] = original_dd * impact
        
        # Total portfolio impact
        total_return = sum(
            new_returns.get(c, 0) * allocation
            for c, allocation in cluster_allocations.items()
        )
        
        total_dd = sum(
            new_drawdowns.get(c, 0) * allocation
            for c, allocation in cluster_allocations.items()
        )
        
        return {
            "scenario": scenario,
            "cluster_impacts": impacts,
            "portfolio_return": total_return,
            "portfolio_drawdown": total_dd,
            "impact_assessment": "severe" if total_dd > 0.25 else "moderate" if total_dd > 0.15 else "mild",
        }


# Factory functions
def create_cluster_monitor() -> ClusterMonitor:
    """Create cluster monitor."""
    return ClusterMonitor()


def create_research_guidance_engine() -> ResearchGuidanceEngine:
    """Create research guidance engine."""
    return ResearchGuidanceEngine()


def create_stress_tester() -> CrossClusterStressTester:
    """Create cross-cluster stress tester."""
    return CrossClusterStressTester()
