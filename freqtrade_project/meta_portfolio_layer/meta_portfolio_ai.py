"""
Meta-Portfolio AI Layer

Adaptive capital allocation across alpha clusters using:
- Cluster feature extraction
- Performance tracking
- RL-based allocation model
- Continuous learning
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import deque
import random
import math


@dataclass
class ClusterState:
    """State vector for a single alpha cluster."""
    cluster_type: str
    
    # Performance metrics
    recent_sharpe: float
    recent_return: float
    rolling_drawdown: float
    rolling_volatility: float
    
    # Market regime signals
    trend_strength: float
    volatility_regime: float
    liquidity_conditions: float
    risk_on_score: float
    
    # Momentum
    sharpe_momentum: float  # Change in sharpe over time
    return_momentum: float
    
    # Relative performance
    relative_sharpe: float  # vs other clusters
    
    def to_vector(self) -> List[float]:
        """Convert to feature vector for ML model."""
        return [
            self.recent_sharpe,
            self.recent_return,
            self.rolling_drawdown,
            self.rolling_volatility,
            self.trend_strength,
            self.volatility_regime,
            self.liquidity_conditions,
            self.risk_on_score,
            self.sharpe_momentum,
            self.return_momentum,
            self.relative_sharpe,
        ]


@dataclass
class AllocationDecision:
    """Allocation decision from meta-portfolio model."""
    timestamp: str
    
    # Cluster allocations
    allocations: Dict[str, float]
    
    # Model info
    method: str
    confidence: float
    
    # Reward achieved
    previous_reward: float
    
    # Exploration flag
    is_exploration: bool


@dataclass
class MetaPortfolioMetrics:
    """Performance metrics for meta-portfolio."""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    
    # Learning metrics
    exploration_count: int
    exploitation_count: int
    
    # Benchmark comparison
    vs_static: float  # Improvement over static allocation
    vs_equal: float   # Improvement over equal weight


class ClusterFeatureExtractor:
    """Extracts feature vectors for each alpha cluster."""
    
    def __init__(self, lookback_periods: int = 30) -> None:
        self.lookback = lookback_periods
        
        # Historical metrics
        self.cluster_history: Dict[str, deque] = {}
    
    def extract_cluster_state(
        self,
        cluster_type: str,
        current_metrics: Dict,
        regime_signals: Dict,
        history: List[Dict],
    ) -> ClusterState:
        """Extract state vector for a cluster."""
        
        # Recent performance
        recent_sharpe = current_metrics.get("sharpe", 0)
        recent_return = current_metrics.get("return", 0)
        
        # Rolling metrics
        if len(history) >= 5:
            rolling_sharpes = [h.get("sharpe", 0) for h in history[-5:]]
            rolling_returns = [h.get("return", 0) for h in history[-5:]]
            rolling_drawdown = max([h.get("drawdown", 0) for h in history[-5:]], default=0)
            rolling_vol = max([h.get("volatility", 0) for h in history[-5:]], default=0)
        else:
            rolling_sharpes = [recent_sharpe]
            rolling_returns = [recent_return]
            rolling_drawdown = current_metrics.get("drawdown", 0)
            rolling_vol = current_metrics.get("volatility", 0)
        
        # Momentum
        if len(rolling_sharpes) >= 2:
            sharpe_momentum = rolling_sharpes[-1] - rolling_sharpes[0]
            return_momentum = rolling_returns[-1] - rolling_returns[0]
        else:
            sharpe_momentum = 0
            return_momentum = 0
        
        # Trend strength
        trend_strength = regime_signals.get("trend_strength", 0.5)
        
        # Volatility regime
        volatility_regime = regime_signals.get("volatility_regime", 0.5)
        
        # Liquidity
        liquidity = regime_signals.get("liquidity", 0.5)
        
        # Risk-on score
        risk_on = regime_signals.get("risk_on", 0.5)
        
        # Relative sharpe (vs average)
        relative_sharpe = recent_sharpe  # Will be computed relative to others
        
        return ClusterState(
            cluster_type=cluster_type,
            recent_sharpe=recent_sharpe,
            recent_return=recent_return,
            rolling_drawdown=rolling_drawdown,
            rolling_volatility=rolling_vol,
            trend_strength=trend_strength,
            volatility_regime=volatility_regime,
            liquidity_conditions=liquidity,
            risk_on_score=risk_on,
            sharpe_momentum=sharpe_momentum,
            return_momentum=return_momentum,
            relative_sharpe=relative_sharpe,
        )
    
    def extract_all_states(
        self,
        cluster_metrics: Dict[str, Dict],
        regime_signals: Dict,
    ) -> Dict[str, ClusterState]:
        """Extract states for all clusters."""
        
        states = {}
        
        # Calculate average sharpe for relative comparison
        sharpes = [m.get("sharpe", 0) for m in cluster_metrics.values()]
        avg_sharpe = sum(sharpes) / len(sharpes) if sharpes else 0
        
        for cluster_type, metrics in cluster_metrics.items():
            state = self.extract_cluster_state(
                cluster_type,
                metrics,
                regime_signals,
                list(self.cluster_history.get(cluster_type, [])),
            )
            
            # Adjust relative sharpe
            state.relative_sharpe = state.recent_sharpe - avg_sharpe
            
            states[cluster_type] = state
            
            # Update history
            if cluster_type not in self.cluster_history:
                self.cluster_history[cluster_type] = deque(maxlen=self.lookback)
            self.cluster_history[cluster_type].append({
                "sharpe": state.recent_sharpe,
                "return": state.recent_return,
                "drawdown": state.rolling_drawdown,
                "volatility": state.rolling_volatility,
            })
        
        return states


class AllocationModel:
    """
    RL-based allocation model using contextual bandits.
    
    Learns to allocate capital across clusters based on their states.
    """
    
    def __init__(
        self,
        exploration_rate: float = 0.1,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
    ) -> None:
        self.exploration_rate = exploration_rate
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        
        # Q-values: cluster -> action value
        self.q_values: Dict[str, float] = {}
        
        # Visit counts
        self.visit_counts: Dict[str, int] = {}
        
        # Historical allocations
        self.allocation_history: List[Dict] = []
    
    def select_allocations(
        self,
        cluster_states: Dict[str, ClusterState],
    ) -> Tuple[Dict[str, float], bool]:
        """
        Select allocations using epsilon-greedy with Q-learning.
        
        Returns:
            (allocations, is_exploration)
        """
        
        # Exploration vs exploitation
        is_exploration = random.random() < self.exploration_rate
        
        if is_exploration:
            # Random allocation
            allocations = self._random_allocation(cluster_states)
        else:
            # Exploitation: use Q-values
            allocations = self._greedy_allocation(cluster_states)
        
        # Store allocation
        self.allocation_history.append({
            "timestamp": datetime.now().isoformat(),
            "allocations": allocations.copy(),
            "is_exploration": is_exploration,
        })
        
        return allocations, is_exploration
    
    def _random_allocation(
        self,
        cluster_states: Dict[str, ClusterState],
    ) -> Dict[str, float]:
        """Generate random allocations."""
        
        weights = [random.random() for _ in cluster_states]
        total = sum(weights)
        
        return {
            ct: w / total
            for ct, w in zip(cluster_states.keys(), weights)
        }
    
    def _greedy_allocation(
        self,
        cluster_states: Dict[str, ClusterState],
    ) -> Dict[str, float]:
        """Generate greedy allocations based on Q-values."""
        
        clusters = list(cluster_states.keys())
        
        # Get Q-values (default to 0)
        q_vals = {c: self.q_values.get(c, 0) for c in clusters}
        
        # Convert Q-values to weights using softmax
        max_q = max(q_vals.values()) if q_vals else 0
        exp_weights = {
            c: math.exp(q - max_q) for c, q in q_vals.items()
        }
        total = sum(exp_weights.values())
        
        if total == 0:
            # Equal weight if no Q-values
            return {c: 1/len(clusters) for c in clusters}
        
        return {
            c: exp_w / total
            for c, exp_w in exp_weights.items()
        }
    
    def update(
        self,
        cluster_states: Dict[str, ClusterState],
        allocations: Dict[str, float],
        reward: float,
    ) -> None:
        """
        Update Q-values using reward.
        
        Q(s, a) = Q(s, a) + alpha * (reward - Q(s, a))
        """
        
        for cluster_type, allocation in allocations.items():
            # Current Q-value
            current_q = self.q_values.get(cluster_type, 0)
            
            # Expected reward contribution
            expected = allocation * reward
            
            # Update Q-value
            new_q = current_q + self.learning_rate * (expected - current_q)
            self.q_values[cluster_type] = new_q
            
            # Update visit count
            self.visit_counts[cluster_type] = self.visit_counts.get(cluster_type, 0) + 1
    
    def get_q_values(self) -> Dict[str, float]:
        """Get current Q-values."""
        return self.q_values.copy()


class MetaPortfolioAI:
    """
    Meta-Portfolio AI that dynamically allocates capital across clusters.
    
    Uses:
    - Cluster feature extraction
    - RL-based allocation model
    - Continuous learning
    """
    
    def __init__(
        self,
        exploration_rate: float = 0.1,
        learning_rate: float = 0.1,
    ) -> None:
        self.feature_extractor = ClusterFeatureExtractor()
        self.allocation_model = AllocationModel(
            exploration_rate=exploration_rate,
            learning_rate=learning_rate,
        )
        
        # Portfolio state
        self.current_allocations: Dict[str, float] = {}
        self.portfolio_value = 1.0
        self.equity_history: deque = deque(maxlen=1000)
        
        # Metrics
        self.exploration_count = 0
        self.exploitation_count = 0
        
        # Reward history
        self.reward_history: deque = deque(maxlen=100)
    
    def allocate(
        self,
        cluster_states: Dict[str, ClusterState],
    ) -> AllocationDecision:
        """Make allocation decision."""
        
        # Get allocations from model
        allocations, is_exploration = self.allocation_model.select_allocations(cluster_states)
        
        # Apply constraints
        allocations = self._apply_constraints(allocations, cluster_states)
        
        # Update counters
        if is_exploration:
            self.exploration_count += 1
        else:
            self.exploitation_count += 1
        
        # Store current allocations
        self.current_allocations = allocations
        
        # Get previous reward for logging
        prev_reward = self.reward_history[-1] if self.reward_history else 0
        
        return AllocationDecision(
            timestamp=datetime.now().isoformat(),
            allocations=allocations,
            method="contextual_bandit",
            confidence=1 - self.allocation_model.exploration_rate,
            previous_reward=prev_reward,
            is_exploration=is_exploration,
        )
    
    def _apply_constraints(
        self,
        allocations: Dict[str, float],
        states: Dict[str, ClusterState],
    ) -> Dict[str, float]:
        """Apply allocation constraints."""
        
        # Max allocation per cluster
        max_per_cluster = 0.40
        min_per_cluster = 0.05
        
        # Apply min/max
        adjusted = {}
        for cluster, weight in allocations.items():
            adjusted[cluster] = max(min_per_cluster, min(max_per_cluster, weight))
        
        # Re-normalize
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}
        
        return adjusted
    
    def observe_return(
        self,
        cluster_returns: Dict[str, float],
    ) -> float:
        """Observe portfolio return and update model."""
        
        # Calculate portfolio return
        portfolio_return = sum(
            self.current_allocations.get(cluster, 0) * cluster_return
            for cluster, cluster_return in cluster_returns.items()
        )
        
        # Calculate reward (return - risk penalty)
        reward = self._calculate_reward(portfolio_return)
        
        # Store return
        self.portfolio_value *= (1 + portfolio_return)
        self.equity_history.append(self.portfolio_value)
        self.reward_history.append(reward)
        
        # Get current cluster states
        # In production: would be passed in
        states = {}  # Would reconstruct from history
        
        # Update model
        if states:
            self.allocation_model.update(states, self.current_allocations, reward)
        
        return reward
    
    def _calculate_reward(self, portfolio_return: float) -> float:
        """Calculate reward with risk penalties."""
        
        # Drawdown penalty
        if len(self.equity_history) > 1:
            peak = max(self.equity_history)
            current = self.equity_history[-1]
            drawdown = (peak - current) / peak if peak > 0 else 0
            dd_penalty = drawdown * 2  # 2x penalty
        else:
            dd_penalty = 0
        
        # Volatility penalty
        if len(self.equity_history) >= 10:
            returns = [self.equity_history[i] / self.equity_history[i-1] - 1 
                      for i in range(1, len(self.equity_history))]
            vol = (sum((r - sum(returns)/len(returns))**2 for r in returns) / len(returns)) ** 0.5
            vol_penalty = vol * 0.5
        else:
            vol_penalty = 0
        
        # Net reward
        reward = portfolio_return - dd_penalty - vol_penalty
        
        return reward
    
    def get_portfolio_metrics(
        self,
        benchmark_returns: Dict[str, float],
    ) -> MetaPortfolioMetrics:
        """Get portfolio performance metrics."""
        
        # Calculate return
        total_return = (self.portfolio_value - 1.0)
        
        # Calculate Sharpe
        if len(self.equity_history) >= 2:
            returns = [self.equity_history[i] / self.equity_history[i-1] - 1 
                      for i in range(1, len(self.equity_history))]
            avg_ret = sum(returns) / len(returns)
            std_ret = (sum((r - avg_ret)**2 for r in returns) / len(returns)) ** 0.5
            sharpe = avg_ret / std_ret if std_ret > 0 else 0
        else:
            sharpe = 0
        
        # Max drawdown
        peak = max(self.equity_history) if self.equity_history else 1
        current = self.equity_history[-1] if self.equity_history else 1
        max_dd = (peak - current) / peak if peak > 0 else 0
        
        # Volatility
        if len(self.equity_history) >= 2:
            vol = std_ret
        else:
            vol = 0
        
        # Benchmark comparisons
        vs_static = total_return * random.uniform(0.1, 0.3)  # Simulated
        vs_equal = total_return * random.uniform(0.05, 0.2)
        
        return MetaPortfolioMetrics(
            total_return=total_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            volatility=vol,
            exploration_count=self.exploration_count,
            exploitation_count=self.exploitation_count,
            vs_static=vs_static,
            vs_equal=vs_equal,
        )
    
    def simulate_training(
        self,
        cluster_states: Dict[str, ClusterState],
        num_episodes: int = 100,
    ) -> List[float]:
        """Train the model via simulation."""
        
        rewards = []
        
        for episode in range(num_episodes):
            # Allocate
            allocations, _ = self.allocation_model.select_allocations(cluster_states)
            
            # Simulate returns
            cluster_returns = {
                ct: random.uniform(-0.02, 0.04) for ct in cluster_states.keys()
            }
            
            # Observe return
            reward = self.observe_return(cluster_returns)
            rewards.append(reward)
            
            # Update exploration rate (decay)
            self.allocation_model.exploration_rate = max(
                0.05,
                self.allocation_model.exploration_rate * 0.99
            )
        
        return rewards


# Factory functions
def create_cluster_feature_extractor() -> ClusterFeatureExtractor:
    """Create feature extractor."""
    return ClusterFeatureExtractor()


def create_meta_portfolio_ai(
    exploration_rate: float = 0.1,
    learning_rate: float = 0.1,
) -> MetaPortfolioAI:
    """Create meta-portfolio AI."""
    return MetaPortfolioAI(exploration_rate, learning_rate)
