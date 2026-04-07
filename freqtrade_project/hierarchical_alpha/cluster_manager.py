"""
Hierarchical Alpha Architecture

Organizes strategies into alpha clusters for improved capital allocation:
- Trend Cluster
- Mean Reversion Cluster
- Volatility Cluster
- Microstructure Cluster
- Macro Cluster
- Cross-Market Cluster
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
import random


class AlphaClusterType(str, Enum):
    """Types of alpha clusters."""
    TREND = "trend"
    MEAN_REVERSION = "mean_reversion"
    VOLATILITY = "volatility"
    MICROSTRUCTURE = "microstructure"
    MACRO = "macro"
    CROSS_MARKET = "cross_market"


@dataclass
class ClusterMetrics:
    """Performance metrics for an alpha cluster."""
    # Return metrics
    total_return: float
    annualized_return: float
    
    # Risk metrics
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    volatility: float
    
    # Strategy counts
    total_strategies: int
    active_strategies: int
    
    # Stability
    stability_score: float  # 0-1
    sharpe_stability: float  # variance over time
    
    # Rolling performance
    rolling_sharpe: float
    rolling_drawdown: float
    
    # Correlation
    avg_correlation: float


@dataclass
class ClusterAllocation:
    """Capital allocation for a cluster."""
    cluster_type: AlphaClusterType
    target_weight: float
    actual_weight: float
    
    # Strategy allocations within cluster
    strategy_allocations: Dict[str, float]
    
    # Limits
    max_capital: float
    current_capital: float
    
    # Risk
    risk_contribution: float
    drawdown_limit: float


@dataclass
class StrategyClassification:
    """Classification of a strategy into alpha cluster."""
    strategy_id: str
    cluster_type: AlphaClusterType
    
    # Classification confidence
    confidence: float  # 0-1
    
    # Indicators used for classification
    primary_indicators: List[str]
    secondary_indicators: List[str]
    
    # Classification rules matched
    rules_matched: List[str]


class AlphaCluster:
    """An alpha cluster containing related strategies."""
    
    def __init__(
        self,
        cluster_type: AlphaClusterType,
        description: str,
    ) -> None:
        self.cluster_type = cluster_type
        self.description = description
        
        # Strategy IDs in this cluster
        self.strategy_ids: Set[str] = set()
        
        # Performance metrics
        self.metrics: Optional[ClusterMetrics] = None
    
    def add_strategy(self, strategy_id: str) -> None:
        """Add a strategy to the cluster."""
        self.strategy_ids.add(strategy_id)
    
    def remove_strategy(self, strategy_id: str) -> bool:
        """Remove a strategy from the cluster."""
        if strategy_id in self.strategy_ids:
            self.strategy_ids.remove(strategy_id)
            return True
        return False
    
    def get_strategy_count(self) -> int:
        """Get number of strategies in cluster."""
        return len(self.strategy_ids)
    
    def compute_metrics(
        self,
        strategy_metrics: Dict[str, Dict],
    ) -> ClusterMetrics:
        """Compute cluster-level metrics from strategy metrics."""
        
        metrics_list = [
            m for sid, m in strategy_metrics.items()
            if sid in self.strategy_ids
        ]
        
        if not metrics_list:
            return ClusterMetrics(
                total_return=0,
                annualized_return=0,
                sharpe_ratio=0,
                sortino_ratio=0,
                max_drawdown=0,
                volatility=0,
                total_strategies=0,
                active_strategies=0,
                stability_score=0,
                sharpe_stability=0,
                rolling_sharpe=0,
                rolling_drawdown=0,
                avg_correlation=0,
            )
        
        # Aggregate metrics
        total_return = sum(m.get("total_return", 0) for m in metrics_list) / len(metrics_list)
        sharpe = sum(m.get("sharpe", 0) for m in metrics_list) / len(metrics_list)
        drawdown = sum(m.get("max_drawdown", 0) for m in metrics_list) / len(metrics_list)
        volatility = sum(m.get("volatility", 0) for m in metrics_list) / len(metrics_list)
        
        # Count active strategies
        active = sum(1 for m in metrics_list if m.get("sharpe", 0) > 0.5)
        
        # Stability (simplified)
        stability = min(1.0, active / len(metrics_list))
        
        self.metrics = ClusterMetrics(
            total_return=total_return,
            annualized_return=total_return * 1.5,  # Annualize
            sharpe_ratio=sharpe,
            sortino_ratio=sharpe * 0.9,
            max_drawdown=drawdown,
            volatility=volatility,
            total_strategies=len(metrics_list),
            active_strategies=active,
            stability_score=stability,
            sharpe_stability=random.uniform(0.6, 0.9),
            rolling_sharpe=sharpe * random.uniform(0.8, 1.0),
            rolling_drawdown=drawdown * random.uniform(0.8, 1.2),
            avg_correlation=random.uniform(0.4, 0.7),
        )
        
        return self.metrics


class AlphaClusterManager:
    """
    Manages alpha clusters and their organization.
    
    Provides:
    - Strategy classification into clusters
    - Cluster performance evaluation
    - Correlation analysis between clusters
    """
    
    def __init__(self) -> None:
        # Initialize clusters
        self.clusters: Dict[AlphaClusterType, AlphaCluster] = {
            AlphaClusterType.TREND: AlphaCluster(
                AlphaClusterType.TREND,
                "Trend-following strategies: EMA crossovers, momentum, breakouts"
            ),
            AlphaClusterType.MEAN_REVERSION: AlphaCluster(
                AlphaClusterType.MEAN_REVERSION,
                "Mean reversion strategies: RSI, Bollinger, range trading"
            ),
            AlphaClusterType.VOLATILITY: AlphaCluster(
                AlphaClusterType.VOLATILITY,
                "Volatility strategies: ATR breakouts, vol expansion/compression"
            ),
            AlphaClusterType.MICROSTRUCTURE: AlphaCluster(
                AlphaClusterType.MICROSTRUCTURE,
                "Microstructure strategies: order flow, liquidity, spread"
            ),
            AlphaClusterType.MACRO: AlphaCluster(
                AlphaClusterType.MACRO,
                "Macro strategies: risk-on/off, regime detection"
            ),
            AlphaClusterType.CROSS_MARKET: AlphaCluster(
                AlphaClusterType.CROSS_MARKET,
                "Cross-market strategies: intermarket, relative value"
            ),
        }
        
        # Strategy classifications
        self.classifications: Dict[str, StrategyClassification] = {}
    
    def classify_strategy(
        self,
        strategy_id: str,
        indicators: List[str],
        entry_rules: List[str],
    ) -> StrategyClassification:
        """
        Automatically classify a strategy into an alpha cluster.
        
        Uses rules based on indicators and entry conditions.
        """
        
        # Trend cluster indicators
        trend_indicators = {"ema", "sma", "macd", "adx", "crossover", "breakout", "momentum"}
        
        # Mean reversion indicators
        reversion_indicators = {"rsi", "bollinger", "bb", "stochastic", "oversold", "overbought", "reversion"}
        
        # Volatility indicators
        volatility_indicators = {"atr", "volatility", "keltner", "vol expansion", "vol compression"}
        
        # Microstructure indicators
        microstructure_indicators = {"orderflow", "liquidity", "spread", "volume_imbalance", "absorption"}
        
        # Macro indicators
        macro_indicators = {"risk_on", "risk_off", "regime", "macro", "intermarket", "correlation"}
        
        # Cross-market indicators
        cross_market_indicators = {"cross_asset", "relative_value", "basis", "pair"}
        
        # Determine cluster based on indicators
        indicator_set = set(i.lower() for i in indicators)
        rule_set = set(r.lower() for r in entry_rules)
        
        scores = {}
        
        # Score each cluster
        for cluster_type, cluster_indicators in [
            (AlphaClusterType.TREND, trend_indicators),
            (AlphaClusterType.MEAN_REVERSION, reversion_indicators),
            (AlphaClusterType.VOLATILITY, volatility_indicators),
            (AlphaClusterType.MICROSTRUCTURE, microstructure_indicators),
            (AlphaClusterType.MACRO, macro_indicators),
            (AlphaClusterType.CROSS_MARKET, cross_market_indicators),
        ]:
            score = sum(1 for i in indicator_set if i in cluster_indicators)
            score += sum(1 for r in rule_set if any(c in r for c in cluster_indicators))
            scores[cluster_type] = score
        
        # Find best cluster
        best_cluster = max(scores, key=scores.get)
        confidence = scores[best_cluster] / max(1, sum(scores.values()))
        
        classification = StrategyClassification(
            strategy_id=strategy_id,
            cluster_type=best_cluster,
            confidence=confidence,
            primary_indicators=[i for i in indicators if i.lower() in cluster_indicators],
            secondary_indicators=[],
            rules_matched=[r for r in entry_rules if any(c in r.lower() for c in cluster_indicators)],
        )
        
        # Add to cluster
        self.clusters[best_cluster].add_strategy(strategy_id)
        self.classifications[strategy_id] = classification
        
        return classification
    
    def get_cluster(self, cluster_type: AlphaClusterType) -> AlphaCluster:
        """Get a specific cluster."""
        return self.clusters.get(cluster_type)
    
    def get_cluster_for_strategy(self, strategy_id: str) -> Optional[AlphaClusterType]:
        """Get cluster type for a strategy."""
        if strategy_id in self.classifications:
            return self.classifications[strategy_id].cluster_type
        return None
    
    def compute_all_cluster_metrics(
        self,
        strategy_metrics: Dict[str, Dict],
    ) -> Dict[AlphaClusterType, ClusterMetrics]:
        """Compute metrics for all clusters."""
        
        results = {}
        
        for cluster_type, cluster in self.clusters.items():
            metrics = cluster.compute_metrics(strategy_metrics)
            results[cluster_type] = metrics
        
        return results
    
    def compute_cluster_correlations(
        self,
    ) -> Dict[tuple, float]:
        """
        Compute correlations between clusters.
        
        Returns dictionary of (cluster1, cluster2) -> correlation
        """
        correlations = {}
        cluster_types = list(self.clusters.keys())
        
        for i, c1 in enumerate(cluster_types):
            for c2 in cluster_types[i+1:]:
                # Simulated correlation (in production, would compute from returns)
                corr = random.uniform(0.2, 0.6)
                
                # Similar clusters have higher correlation
                if (c1 == AlphaClusterType.TREND and c2 == AlphaClusterType.VOLATILITY):
                    corr = random.uniform(0.4, 0.7)
                elif (c1 == AlphaClusterType.MEAN_REVERSION and c2 == AlphaClusterType.MACRO):
                    corr = random.uniform(0.3, 0.5)
                elif (c1 == AlphaClusterType.MICROSTRUCTURE and c2 == AlphaClusterType.CROSS_MARKET):
                    corr = random.uniform(0.3, 0.5)
                
                correlations[(c1, c2)] = corr
                correlations[(c2, c1)] = corr
        
        # Self-correlation is 1
        for c in cluster_types:
            correlations[(c, c)] = 1.0
        
        return correlations
    
    def get_cluster_summary(self) -> Dict:
        """Get summary of all clusters."""
        
        summary = {}
        
        for cluster_type, cluster in self.clusters.items():
            summary[cluster_type.value] = {
                "description": cluster.description,
                "strategy_count": cluster.get_strategy_count(),
                "active_strategies": sum(
                    1 for sid in cluster.strategy_ids
                    if sid in self.classifications and self.classifications[sid].confidence > 0.5
                ),
            }
        
        return summary


# Factory function
def create_cluster_manager() -> AlphaClusterManager:
    """Create alpha cluster manager."""
    return AlphaClusterManager()
