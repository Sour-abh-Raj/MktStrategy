"""
Meta-Portfolio Controller

Coordinates meta-portfolio AI with cluster allocation and monitoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

from freqtrade_project.meta_portfolio_layer.meta_portfolio_ai import (
    ClusterState,
    AllocationDecision,
    MetaPortfolioMetrics,
    ClusterFeatureExtractor,
    MetaPortfolioAI,
    create_cluster_feature_extractor,
    create_meta_portfolio_ai,
)


@dataclass
class MetaPortfolioDecision:
    """Complete meta-portfolio decision."""
    timestamp: str
    
    # Allocation decision
    allocations: Dict[str, float]
    method: str
    is_exploration: bool
    
    # Cluster states
    cluster_states: Dict[str, ClusterState]
    
    # Risk info
    risk_override: bool
    risk_message: str = ""


@dataclass
class ResearchFeedback:
    """Research guidance based on meta-portfolio performance."""
    cluster_priorities: Dict[str, float]  # Higher = more research needed
    recommendations: List[str]
    successful_clusters: List[str]
    underperforming_clusters: List[str]


class MetaPortfolioController:
    """
    Controller that manages the meta-portfolio AI.
    
    Coordinates:
    - Feature extraction
    - Allocation decision making
    - Risk constraints
    - Learning updates
    - Research feedback
    """
    
    def __init__(
        self,
        exploration_rate: float = 0.15,
        learning_rate: float = 0.1,
    ) -> None:
        self.feature_extractor = create_cluster_feature_extractor()
        self.ai = create_meta_portfolio_ai(exploration_rate, learning_rate)
        
        # Decision history
        self.decision_history: List[MetaPortfolioDecision] = []
        
        # Risk limits
        self.max_cluster_allocation = 0.40
        self.max_portfolio_drawdown = 0.25
    
    def make_allocation_decision(
        self,
        cluster_metrics: Dict[str, Dict],
        regime_signals: Dict,
    ) -> MetaPortfolioDecision:
        """
        Make allocation decision based on current cluster states and regime.
        """
        
        # Extract cluster states
        cluster_states = self.feature_extractor.extract_all_states(
            cluster_metrics, regime_signals
        )
        
        # Get allocation from AI
        allocation_decision = self.ai.allocate(cluster_states)
        
        # Apply risk checks
        risk_override, risk_message = self._check_risk_constraints(
            allocation_decision.allocations,
            cluster_states,
        )
        
        # Create decision
        decision = MetaPortfolioDecision(
            timestamp=datetime.now().isoformat(),
            allocations=allocation_decision.allocations,
            method=allocation_decision.method,
            is_exploration=allocation_decision.is_exploration,
            cluster_states=cluster_states,
            risk_override=risk_override,
            risk_message=risk_message,
        )
        
        self.decision_history.append(decision)
        
        return decision
    
    def _check_risk_constraints(
        self,
        allocations: Dict[str, float],
        states: Dict[str, ClusterState],
    ) -> tuple[bool, str]:
        """Check if allocations violate risk constraints."""
        
        # Check max cluster allocation
        for cluster, allocation in allocations.items():
            if allocation > self.max_cluster_allocation:
                return True, f"Max allocation exceeded for {cluster}: {allocation:.1%}"
        
        # Check extreme drawdown
        for state in states.values():
            if state.rolling_drawdown > self.max_portfolio_drawdown:
                return True, f"Extreme drawdown in {state.cluster_type}: {state.rolling_drawdown:.1%}"
        
        return False, ""
    
    def observe_performance(
        self,
        cluster_returns: Dict[str, float],
    ) -> float:
        """Observe cluster returns and update AI."""
        
        return self.ai.observe_return(cluster_returns)
    
    def get_research_feedback(
        self,
        cluster_metrics: Dict[str, Dict],
    ) -> ResearchFeedback:
        """Generate research guidance based on meta-portfolio performance."""
        
        # Analyze clusters
        priorities = {}
        successful = []
        underperforming = []
        
        for cluster_type, metrics in cluster_metrics.items():
            sharpe = metrics.get("sharpe", 0)
            stability = metrics.get("stability", 0)
            
            # Priority: low sharpe + low stability = high priority for research
            priority = 0.0
            if sharpe < 0.8:
                priority += (0.8 - sharpe) * 0.6
            if stability < 0.7:
                priority += (0.7 - stability) * 0.4
            
            priorities[cluster_type] = priority
            
            if priority > 0.4:
                underperforming.append(cluster_type)
            elif priority < 0.2:
                successful.append(cluster_type)
        
        # Generate recommendations
        recommendations = []
        
        for cluster in underperforming:
            recommendations.append(f"Increase strategy discovery in {cluster}")
        
        for cluster in successful:
            recommendations.append(f"Maintain {cluster} allocation")
        
        return ResearchFeedback(
            cluster_priorities=priorities,
            recommendations=recommendations,
            successful_clusters=successful,
            underperforming_clusters=underperforming,
        )
    
    def get_performance_summary(
        self,
        benchmark_returns: Dict[str, float],
    ) -> Dict:
        """Get performance summary."""
        
        metrics = self.ai.get_portfolio_metrics(benchmark_returns)
        
        return {
            "total_return": metrics.total_return,
            "sharpe_ratio": metrics.sharpe_ratio,
            "max_drawdown": metrics.max_drawdown,
            "volatility": metrics.volatility,
            "exploration_count": metrics.exploration_count,
            "exploitation_count": metrics.exploitation_count,
            "vs_static": metrics.vs_static,
            "vs_equal": metrics.vs_equal,
            "current_allocations": self.ai.current_allocations,
            "q_values": self.ai.allocation_model.get_q_values(),
        }
    
    def get_allocation_history(
        self,
        limit: int = 10,
    ) -> List[Dict]:
        """Get recent allocation history."""
        
        return [
            {
                "timestamp": d.timestamp,
                "allocations": d.allocations,
                "is_exploration": d.is_exploration,
            }
            for d in self.decision_history[-limit:]
        ]


def create_meta_portfolio_controller() -> MetaPortfolioController:
    """Create meta-portfolio controller."""
    return MetaPortfolioController()
