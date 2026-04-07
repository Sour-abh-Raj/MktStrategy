"""
Hierarchical Capital Allocation

Two-stage allocation:
1. Cluster Allocation (between alpha clusters)
2. Strategy Allocation (within each cluster)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import math

from freqtrade_project.hierarchical_alpha.cluster_manager import (
    AlphaClusterType,
    AlphaClusterManager,
    ClusterMetrics,
    ClusterAllocation,
)


@dataclass
class HierarchicalAllocation:
    """Complete hierarchical allocation result."""
    
    # Stage 1: Cluster allocations
    cluster_allocations: Dict[AlphaClusterType, ClusterAllocation]
    
    # Stage 2: Strategy allocations
    strategy_allocations: Dict[str, float]
    
    # Portfolio metrics
    portfolio_expected_return: float
    portfolio_volatility: float
    portfolio_sharpe: float
    portfolio_max_drawdown: float
    
    # Diversification
    diversification_ratio: float
    
    # Optimization info
    optimization_method: str
    correlation_regime: str


class HierarchicalAllocator:
    """
    Performs hierarchical capital allocation.
    
    Stage 1: Allocate between clusters (risk parity, Sharpe weighting, etc.)
    Stage 2: Allocate within clusters (strategy ranking, diversification)
    """
    
    def __init__(
        self,
        cluster_manager: AlphaClusterManager,
        target_portfolio_volatility: float = 0.20,
    ) -> None:
        self.cluster_manager = cluster_manager
        self.target_volatility = target_portfolio_volatility
    
    def allocate(
        self,
        cluster_metrics: Dict[AlphaClusterType, ClusterMetrics],
        strategy_metrics: Dict[str, Dict],
        method: str = "cluster_risk_parity",
    ) -> HierarchicalAllocation:
        """
        Perform hierarchical capital allocation.
        
        Args:
            cluster_metrics: Performance metrics per cluster
            strategy_metrics: Performance metrics per strategy
            method: Allocation method
            
        Returns:
            HierarchicalAllocation with all allocations
        """
        
        # Stage 1: Cluster allocation
        cluster_weights = self._allocate_to_clusters(cluster_metrics, method)
        
        # Stage 2: Strategy allocation within clusters
        strategy_allocations = self._allocate_to_strategies(
            cluster_weights, strategy_metrics
        )
        
        # Build cluster allocations
        cluster_allocations = {}
        for cluster_type, weight in cluster_weights.items():
            strategies = [
                sid for sid, m in strategy_metrics.items()
                if self.cluster_manager.get_cluster_for_strategy(sid) == cluster_type
            ]
            
            cluster_allocations[cluster_type] = ClusterAllocation(
                cluster_type=cluster_type,
                target_weight=weight,
                actual_weight=weight,
                strategy_allocations={},
                max_capital=weight,
                current_capital=weight,
                risk_contribution=weight * cluster_metrics.get(cluster_type, ClusterMetrics(0,0,0,0,0,0,0,0,0,0,0,0,0)).volatility,
                drawdown_limit=0.30,
            )
        
        # Calculate portfolio metrics
        portfolio_return = sum(
            weight * cluster_metrics.get(ct, ClusterMetrics(0,0,0,0,0,0,0,0,0,0,0,0,0)).annualized_return
            for ct, weight in cluster_weights.items()
        )
        
        portfolio_vol = self._calculate_portfolio_volatility(
            cluster_weights, cluster_metrics
        )
        
        portfolio_sharpe = portfolio_return / portfolio_vol if portfolio_vol > 0 else 0
        
        # Max drawdown (simplified)
        max_dd = sum(
            weight * cluster_metrics.get(ct, ClusterMetrics(0,0,0,0,0,0,0,0,0,0,0,0,0)).max_drawdown
            for ct, weight in cluster_weights.items()
        )
        
        # Diversification ratio
        div_ratio = 1.0 - sum(
            cluster_weights[c1] * cluster_weights[c2] * 0.5
            for c1 in cluster_weights for c2 in cluster_weights
            if c1 != c2
        )
        
        return HierarchicalAllocation(
            cluster_allocations=cluster_allocations,
            strategy_allocations=strategy_allocations,
            portfolio_expected_return=portfolio_return,
            portfolio_volatility=portfolio_vol,
            portfolio_sharpe=portfolio_sharpe,
            portfolio_max_drawdown=max_dd,
            diversification_ratio=div_ratio,
            optimization_method=method,
            correlation_regime="neutral",
        )
    
    def _allocate_to_clusters(
        self,
        cluster_metrics: Dict[AlphaClusterType, ClusterMetrics],
        method: str,
    ) -> Dict[AlphaClusterType, float]:
        """Stage 1: Allocate capital between clusters."""
        
        if method == "cluster_risk_parity":
            return self._risk_parity_allocation(cluster_metrics)
        elif method == "cluster_sharpe_weighted":
            return self._sharpe_weighted_allocation(cluster_metrics)
        elif method == "cluster_volatility_scaling":
            return self._volatility_scaled_allocation(cluster_metrics)
        elif method == "cluster_equal":
            return self._equal_allocation(cluster_metrics)
        else:
            return self._risk_parity_allocation(cluster_metrics)
    
    def _risk_parity_allocation(
        self,
        cluster_metrics: Dict[AlphaClusterType, ClusterMetrics],
    ) -> Dict[AlphaClusterType, float]:
        """
        Risk parity allocation across clusters.
        
        Each cluster contributes equally to portfolio risk.
        """
        
        # Get volatilities
        volatilities = {}
        for ct, metrics in cluster_metrics.items():
            volatilities[ct] = metrics.volatility if metrics.volatility > 0 else 0.20
        
        # Inverse volatility weights
        inv_vols = {ct: 1 / max(v, 0.01) for ct, v in volatilities.items()}
        total = sum(inv_vols.values())
        
        if total == 0:
            # Equal weight if no volatility data
            n = len(cluster_metrics) if cluster_metrics else 1
            return {ct: 1/n for ct in cluster_metrics}
        
        weights = {ct: inv_v / total for ct, inv_v in inv_vols.items()}
        
        return weights
    
    def _sharpe_weighted_allocation(
        self,
        cluster_metrics: Dict[AlphaClusterType, ClusterMetrics],
    ) -> Dict[AlphaClusterType, float]:
        """
        Allocate based on Sharpe ratios.
        
        Higher Sharpe clusters get more capital.
        """
        
        # Get Sharpe ratios
        sharpes = {}
        for ct, metrics in cluster_metrics.items():
            sharpes[ct] = max(metrics.sharpe_ratio, 0.01)
        
        # Normalize
        total = sum(sharpes.values())
        
        if total == 0:
            n = len(cluster_metrics) if cluster_metrics else 1
            return {ct: 1/n for ct in cluster_metrics}
        
        weights = {ct: s / total for ct, s in sharpes.items()}
        
        return weights
    
    def _volatility_scaled_allocation(
        self,
        cluster_metrics: Dict[AlphaClusterType, ClusterMetrics],
    ) -> Dict[AlphaClusterType, float]:
        """
        Scale allocation to target volatility.
        """
        
        volatilities = {}
        returns = {}
        
        for ct, metrics in cluster_metrics.items():
            volatilities[ct] = metrics.volatility if metrics.volatility > 0 else 0.20
            returns[ct] = metrics.annualized_return
        
        # Scale by inverse volatility to target vol
        weights = {}
        for ct in cluster_metrics:
            # Scale factor to achieve target vol
            scale = self.target_volatility / max(volatilities[ct], 0.01)
            weights[ct] = returns[ct] * scale
        
        # Normalize
        total = sum(weights.values())
        if total == 0:
            n = len(cluster_metrics) if cluster_metrics else 1
            return {ct: 1/n for ct in cluster_metrics}
        
        return {ct: w / total for ct, w in weights.items()}
    
    def _equal_allocation(
        self,
        cluster_metrics: Dict[AlphaClusterType, ClusterMetrics],
    ) -> Dict[AlphaClusterType, float]:
        """Equal weight allocation."""
        
        n = len(cluster_metrics) if cluster_metrics else 1
        return {ct: 1/n for ct in cluster_metrics}
    
    def _allocate_to_strategies(
        self,
        cluster_weights: Dict[AlphaClusterType, float],
        strategy_metrics: Dict[str, Dict],
    ) -> Dict[str, float]:
        """
        Stage 2: Allocate within each cluster.
        
        Uses Sharpe-weighted allocation within clusters.
        """
        
        allocations = {}
        
        for cluster_type, cluster_weight in cluster_weights.items():
            # Get strategies in this cluster
            strategies_in_cluster = [
                sid for sid, m in strategy_metrics.items()
                if self.cluster_manager.get_cluster_for_strategy(sid) == cluster_type
            ]
            
            if not strategies_in_cluster:
                continue
            
            # Sharpe-weight within cluster
            sharpes = {
                sid: max(m.get("sharpe", 0.5), 0.01)
                for sid, m in strategy_metrics.items()
                if sid in strategies_in_cluster
            }
            
            total = sum(sharpes.values())
            
            if total == 0:
                # Equal weight
                weight_per_strategy = cluster_weight / len(strategies_in_cluster)
            else:
                weight_per_strategy = cluster_weight
            
            for sid in strategies_in_cluster:
                strategy_weight = (sharpes[sid] / total) * weight_per_strategy if total > 0 else weight_per_strategy / len(strategies_in_cluster)
                allocations[sid] = strategy_weight
        
        return allocations
    
    def _calculate_portfolio_volatility(
        self,
        cluster_weights: Dict[AlphaClusterType, float],
        cluster_metrics: Dict[AlphaClusterType, ClusterMetrics],
    ) -> float:
        """Calculate portfolio volatility."""
        
        # Get cluster correlations
        correlations = self.cluster_manager.compute_cluster_correlations()
        
        # Calculate weighted volatility
        vol = 0.0
        
        for c1, w1 in cluster_weights.items():
            for c2, w2 in cluster_weights.items():
                m1 = cluster_metrics.get(c1)
                m2 = cluster_metrics.get(c2)
                
                if m1 and m2:
                    corr = correlations.get((c1, c2), 0.5)
                    vol += w1 * w2 * m1.volatility * m2.volatility * corr
        
        return math.sqrt(vol)


class ClusterRiskController:
    """
    Risk controls for alpha clusters.
    
    Enforces limits on cluster allocation and drawdowns.
    """
    
    def __init__(
        self,
        max_cluster_allocation: float = 0.40,
        max_cluster_drawdown: float = 0.30,
    ) -> None:
        self.max_cluster_allocation = max_cluster_allocation
        self.max_cluster_drawdown = max_cluster_drawdown
    
    def apply_risk_limits(
        self,
        allocation: HierarchicalAllocation,
        cluster_metrics: Dict[AlphaClusterType, ClusterMetrics],
    ) -> HierarchicalAllocation:
        """Apply risk limits to cluster allocations."""
        
        # Check each cluster
        for cluster_type, alloc in allocation.cluster_allocations.items():
            metrics = cluster_metrics.get(cluster_type)
            
            if not metrics:
                continue
            
            # Check drawdown limit
            if metrics.max_drawdown > self.max_cluster_drawdown:
                # Reduce allocation
                reduction_factor = self.max_cluster_drawdown / metrics.max_drawdown
                alloc.actual_weight = alloc.target_weight * reduction_factor
            
            # Check max allocation
            if alloc.target_weight > self.max_cluster_allocation:
                alloc.actual_weight = self.max_cluster_allocation
        
        # Re-normalize weights
        total = sum(a.actual_weight for a in allocation.cluster_allocations.values())
        
        if total > 0:
            for alloc in allocation.cluster_allocations.values():
                alloc.actual_weight = alloc.actual_weight / total
        
        return allocation


# Factory function
def create_hierarchical_allocator(
    cluster_manager: AlphaClusterManager,
) -> HierarchicalAllocator:
    """Create hierarchical allocator."""
    return HierarchicalAllocator(cluster_manager)
