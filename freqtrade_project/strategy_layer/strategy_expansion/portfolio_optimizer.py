"""
Portfolio Optimization Module

Advanced portfolio allocation methods:
- Risk parity
- Volatility scaling
- Sharpe-weighted allocation
- Hierarchical risk parity
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import random


@dataclass
class PortfolioMetrics:
    """Portfolio-level performance metrics."""
    expected_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    diversification_ratio: float
    
    # Component contributions
    risk_contributions: Dict[str, float]
    return_contributions: Dict[str, float]


@dataclass
class AllocationResult:
    """Result of portfolio optimization."""
    allocations: Dict[str, float]  # strategy_id -> weight
    portfolio_metrics: PortfolioMetrics
    method: str
    iteration: int


class PortfolioOptimizer:
    """
    Advanced portfolio optimization.
    
    Methods:
    - Risk parity: Equal risk contribution
    - Volatility scaling: Scale by inverse volatility
    - Sharpe-weighted: Weight by Sharpe ratio
    - Hierarchical: Cluster-based allocation
    """
    
    def __init__(self, target_volatility: float = 0.15) -> None:
        self.target_volatility = target_volatility
    
    def optimize_risk_parity(
        self,
        strategies: List[Dict],
        covariance: Dict[Tuple[str, str], float],
        risk_target: float = 1.0,
    ) -> AllocationResult:
        """
        Risk parity allocation.
        
        Each strategy contributes equally to portfolio risk.
        
        Formula: weight_i = risk_target / (vol_i * Σ(1/vol_j))
        """
        if not strategies:
            return AllocationResult({}, PortfolioMetrics(0, 0, 0, 0, 0, {}, {}), "risk_parity", 0)
        
        # Extract volatilities
        volatilities = {}
        for s in strategies:
            sid = s["strategy_id"]
            volatilities[sid] = s.get("volatility", 0.20)
        
        # Calculate risk parity weights
        inv_vols = {sid: 1 / max(vol, 0.01) for sid, vol in volatilities.items()}
        total_inv_vol = sum(inv_vols.values())
        
        if total_inv_vol == 0:
            equal_weight = 1.0 / len(strategies)
            weights = {s["strategy_id"]: equal_weight for s in strategies}
        else:
            weights = {
                sid: (inv_vol / total_inv_vol) * risk_target
                for sid, inv_vol in inv_vols.items()
            }
        
        # Normalize to sum to 1
        total = sum(weights.values())
        if total > 0:
            weights = {sid: w / total for sid, w in weights.items()}
        
        metrics = self._calculate_portfolio_metrics(strategies, weights, covariance)
        
        return AllocationResult(
            allocations=weights,
            portfolio_metrics=metrics,
            method="risk_parity",
            iteration=1,
        )
    
    def optimize_volatility_scaling(
        self,
        strategies: List[Dict],
        covariance: Dict[Tuple[str, str], float],
    ) -> AllocationResult:
        """
        Volatility-scaled allocation.
        
        Scale weights inversely proportional to volatility.
        Adjust to meet target portfolio volatility.
        """
        if not strategies:
            return AllocationResult({}, PortfolioMetrics(0, 0, 0, 0, 0, {}, {}), "volatility_scaling", 0)
        
        # Get volatilities and returns
        vols = {s["strategy_id"]: s.get("volatility", 0.20) for s in strategies}
        returns = {s["strategy_id"]: s.get("return", 0.10) for s in strategies}
        
        # Inverse volatility weights
        inv_vols = {sid: 1 / max(vol, 0.01) for sid, vol in vols.items()}
        total = sum(inv_vols.values())
        
        weights = {sid: inv_vol / total for sid, inv_vol in inv_vols.items()}
        
        # Scale to target volatility
        portfolio_vol = math.sqrt(sum(
            weights[i] * weights[j] * covariance.get((i, j), 0)
            for i in weights for j in weights
        ))
        
        if portfolio_vol > 0:
            scale = self.target_volatility / portfolio_vol
            weights = {sid: w * scale for sid, w in weights.items()}
        
        # Re-normalize
        total = sum(weights.values())
        if total > 0:
            weights = {sid: w / total for sid, w in weights.items()}
        
        metrics = self._calculate_portfolio_metrics(strategies, weights, covariance)
        
        return AllocationResult(
            allocations=weights,
            portfolio_metrics=metrics,
            method="volatility_scaling",
            iteration=1,
        )
    
    def optimize_sharpe_weighted(
        self,
        strategies: List[Dict],
        covariance: Dict[Tuple[str, str], float],
    ) -> AllocationResult:
        """
        Sharpe-weighted allocation.
        
        Weight strategies by their Sharpe ratios (risk-adjusted).
        """
        if not strategies:
            return AllocationResult({}, PortfolioMetrics(0, 0, 0, 0, 0, {}, {}), "sharpe_weighted", 0)
        
        # Get Sharpe ratios
        sharpes = {s["strategy_id"]: s.get("sharpe", 1.0) for s in strategies}
        
        # Use positive Sharpe values
        positive_sharpes = {sid: max(s, 0.01) for sid, s in sharpes.items()}
        total = sum(positive_sharpes.values())
        
        weights = {sid: s / total for sid, s in positive_sharpes.items()}
        
        metrics = self._calculate_portfolio_metrics(strategies, weights, covariance)
        
        return AllocationResult(
            allocations=weights,
            portfolio_metrics=metrics,
            method="sharpe_weighted",
            iteration=1,
        )
    
    def optimize_hierarchical(
        self,
        strategies: List[Dict],
        covariance: Dict[Tuple[str, str], float],
    ) -> AllocationResult:
        """
        Hierarchical risk parity.
        
        Cluster strategies by correlation, then allocate within clusters.
        """
        if not strategies:
            return AllocationResult({}, PortfolioMetrics(0, 0, 0, 0, 0, {}, {}), "hierarchical", 0)
        
        # Build correlation matrix
        strategy_ids = [s["strategy_id"] for s in strategies]
        
        # Simple clustering by correlation
        clusters = self._cluster_strategies(strategy_ids, covariance)
        
        # Allocate within clusters
        weights = {}
        for cluster in clusters:
            if len(cluster) == 1:
                weights[cluster[0]] = 1.0 / len(clusters)
            else:
                # Equal weight within cluster
                cluster_weight = 1.0 / len(clusters)
                for sid in cluster:
                    weights[sid] = cluster_weight / len(cluster)
        
        metrics = self._calculate_portfolio_metrics(strategies, weights, covariance)
        
        return AllocationResult(
            allocations=weights,
            portfolio_metrics=metrics,
            method="hierarchical",
            iteration=1,
        )
    
    def optimize_maximum_sharpe(
        self,
        strategies: List[Dict],
        covariance: Dict[Tuple[str, str], float],
        iterations: int = 100,
    ) -> AllocationResult:
        """
        Find portfolio weights that maximize Sharpe ratio.
        
        Uses random search with optimization.
        """
        if not strategies:
            return AllocationResult({}, PortfolioMetrics(0, 0, 0, 0, 0, {}, {}), "max_sharpe", 0)
        
        best_weights = {}
        best_sharpe = -float('inf')
        
        for it in range(iterations):
            # Random weights
            raw_weights = [random.random() for _ in strategies]
            total = sum(raw_weights)
            weights = {s["strategy_id"]: w / total for s, w in zip(strategies, raw_weights)}
            
            # Calculate Sharpe
            metrics = self._calculate_portfolio_metrics(strategies, weights, covariance)
            
            if metrics.sharpe_ratio > best_sharpe:
                best_sharpe = metrics.sharpe_ratio
                best_weights = weights
                best_metrics = metrics
        
        return AllocationResult(
            allocations=best_weights,
            portfolio_metrics=best_metrics,
            method="max_sharpe",
            iteration=iterations,
        )
    
    def _cluster_strategies(
        self,
        strategy_ids: List[str],
        covariance: Dict[Tuple[str, str], float],
        n_clusters: int = 3,
    ) -> List[List[str]]:
        """Simple clustering by correlation."""
        if len(strategy_ids) <= n_clusters:
            return [[sid] for sid in strategy_ids]
        
        # Calculate correlations from covariance
        vols = {}
        for (s1, s2), cov in covariance.items():
            if s1 not in vols:
                vols[s1] = math.sqrt(abs(cov)) if cov != 0 else 0.2
            if s2 not in vols:
                vols[s2] = math.sqrt(abs(cov)) if cov != 0 else 0.2
        
        # Simple heuristic clustering
        # Group strategies with similar volatility profiles
        clusters = [[] for _ in range(n_clusters)]
        for sid in strategy_ids:
            vol = vols.get(sid, 0.2)
            cluster_idx = min(int(vol * 10), n_clusters - 1)
            clusters[cluster_idx].append(sid)
        
        # Ensure no empty clusters
        return [c for c in clusters if c]
    
    def _calculate_portfolio_metrics(
        self,
        strategies: List[Dict],
        weights: Dict[str, float],
        covariance: Dict[Tuple[str, str], float],
    ) -> PortfolioMetrics:
        """Calculate portfolio-level metrics."""
        strategy_returns = {s["strategy_id"]: s.get("return", 0.10) for s in strategies}
        strategy_vols = {s["strategy_id"]: s.get("volatility", 0.20) for s in strategies}
        
        # Expected return
        expected_return = sum(
            weights[sid] * strategy_returns.get(sid, 0)
            for sid in weights
        )
        
        # Volatility (portfolio variance)
        portfolio_var = sum(
            weights[i] * weights[j] * covariance.get((i, j), 0)
            for i in weights for j in weights
        )
        volatility = math.sqrt(max(portfolio_var, 0))
        
        # Sharpe ratio
        sharpe = expected_return / volatility if volatility > 0 else 0
        
        # Max drawdown (simplified)
        max_dd = sum(weights[sid] * strategy_vols.get(sid, 0.2) for sid in weights) * 0.5
        
        # Diversification ratio
        weighted_vol = sum(weights[sid] * strategy_vols.get(sid, 0.2) for sid in weights)
        div_ratio = weighted_vol / volatility if volatility > 0 else 1
        
        # Risk contributions (simplified)
        risk_contributions = {
            sid: weights[sid] * strategy_vols.get(sid, 0.2) / weighted_vol
            for sid in weights
        } if weighted_vol > 0 else {}
        
        # Return contributions
        return_contributions = {
            sid: weights[sid] * strategy_returns.get(sid, 0)
            for sid in weights
        }
        
        return PortfolioMetrics(
            expected_return=expected_return,
            volatility=volatility,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            diversification_ratio=div_ratio,
            risk_contributions=risk_contributions,
            return_contributions=return_contributions,
        )
    
    def compare_methods(
        self,
        strategies: List[Dict],
        covariance: Dict[Tuple[str, str], float],
    ) -> List[AllocationResult]:
        """Compare all optimization methods."""
        methods = [
            self.optimize_risk_parity,
            self.optimize_volatility_scaling,
            self.optimize_sharpe_weighted,
            self.optimize_hierarchical,
            lambda s, c: self.optimize_maximum_sharpe(s, c, 50),
        ]
        
        results = []
        for method in methods:
            result = method(strategies, covariance)
            results.append(result)
        
        # Return best by Sharpe
        results.sort(key=lambda r: r.portfolio_metrics.sharpe_ratio, reverse=True)
        
        return results


def create_portfolio_optimizer(target_volatility: float = 0.15) -> PortfolioOptimizer:
    """Create portfolio optimizer."""
    return PortfolioOptimizer(target_volatility)
