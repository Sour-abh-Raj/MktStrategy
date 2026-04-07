"""
Market Microstructure Layer

Analyzes market microstructure for improved trade execution and signal quality.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import deque


@dataclass
class OrderFlowMetrics:
    """Order flow analysis results."""
    imbalance: float           # -1 to 1 (sell to buy pressure)
    aggressive_buying: float    # 0 to 1
    aggressive_selling: float  # 0 to 1
    cumulative_delta: float    # Cumulative volume delta
    absorption_ratio: float    # How much volume is being absorbed


@dataclass
class LiquidityMetrics:
    """Liquidity monitoring results."""
    bid_depth: float           # Total bid volume
    ask_depth: float           # Total ask volume
    depth_imbalance: float     # -1 to 1
    liquidity_shock: bool      # True if liquidity collapsed
    depth_ratio: float         # bid/ask ratio


@dataclass
class SpreadMetrics:
    """Spread tracking results."""
    spread: float              # Current spread
    spread_change: float      # Change from average
    spread_volatility: float  # Volatility of spread
    widening: bool             # True if spread is widening


@dataclass
class ImbalanceMetrics:
    """Order book imbalance results."""
    bid_ask_ratio: float       # Bid to ask ratio
    price_pressure: float      # Upward/downward pressure
    volume_imbalance: float     # Volume imbalance
    imbalance_trend: str       # "increasing", "decreasing", "stable"


@dataclass
class MicrostructureFeatures:
    """Combined microstructure features for intelligence layer."""
    order_flow: OrderFlowMetrics
    liquidity: LiquidityMetrics
    spread: SpreadMetrics
    imbalance: ImbalanceMetrics
    
    # Composite signals
    execution_risk: float      # 0 to 1 (higher = riskier execution)
    signal_quality: float       # 0 to 1 (higher = better signal)


class OrderFlowAnalyzer:
    """Analyzes order flow to detect buying/selling pressure."""
    
    def __init__(self, window_size: int = 100) -> None:
        self.window_size = window_size
        self._trade_deltas: deque = deque(maxlen=window_size)
        self._volumes: deque = deque(maxlen=window_size)
    
    def update(self, price: float, volume: float, trade_side: str) -> None:
        """
        Update with new trade data.
        
        Args:
            price: Trade price
            volume: Trade volume
            trade_side: "buy" or "sell"
        """
        # Delta: positive for buys, negative for sells
        delta = volume if trade_side == "buy" else -volume
        self._trade_deltas.append(delta)
        self._volumes.append(volume)
    
    def analyze(self) -> OrderFlowMetrics:
        """Compute order flow metrics."""
        if not self._trade_deltas:
            return OrderFlowMetrics(
                imbalance=0,
                aggressive_buying=0,
                aggressive_selling=0,
                cumulative_delta=0,
                absorption_ratio=0,
            )
        
        deltas = list(self._trade_deltas)
        volumes = list(self._volumes)
        
        # Imbalance: ratio of buy to total volume
        total_delta = sum(deltas)
        total_volume = sum(volumes)
        imbalance = total_delta / total_volume if total_volume > 0 else 0
        
        # Aggressive buying/selling
        buys = sum(d for d in deltas if d > 0)
        sells = abs(sum(d for d in deltas if d < 0))
        
        aggressive_buying = buys / total_volume if total_volume > 0 else 0
        aggressive_selling = sells / total_volume if total_volume > 0 else 0
        
        # Cumulative delta
        cumulative_delta = total_delta
        
        # Absorption ratio (simplified)
        absorption = 1.0 - abs(imbalance)  # More balanced = more absorption
        
        return OrderFlowMetrics(
            imbalance=imbalance,
            aggressive_buying=aggressive_buying,
            aggressive_selling=aggressive_selling,
            cumulative_delta=cumulative_delta,
            absorption_ratio=absorption,
        )
    
    def reset(self) -> None:
        """Reset the analyzer."""
        self._trade_deltas.clear()
        self._volumes.clear()


class LiquidityMonitor:
    """Monitors order book depth and liquidity conditions."""
    
    def __init__(self, baseline_depth: float = 1000000.0) -> None:
        self.baseline_depth = baseline_depth
        self._depth_history: deque = deque(maxlen=100)
    
    def update(self, bid_depth: float, ask_depth: float) -> None:
        """
        Update with order book depth.
        
        Args:
            bid_depth: Total bid volume at top levels
            ask_depth: Total ask volume at top levels
        """
        total_depth = bid_depth + ask_depth
        self._depth_history.append(total_depth)
    
    def analyze(self) -> LiquidityMetrics:
        """Compute liquidity metrics."""
        if not self._depth_history:
            return LiquidityMetrics(
                bid_depth=0,
                ask_depth=0,
                depth_imbalance=0,
                liquidity_shock=False,
                depth_ratio=0,
            )
        
        current_depth = self._depth_history[-1]
        avg_depth = np.mean(self._depth_history)
        
        # Liquidity shock detection
        liquidity_shock = current_depth < (self.baseline_depth * 0.2)
        
        # Depth ratio
        depth_ratio = current_depth / self.baseline_depth
        
        return LiquidityMetrics(
            bid_depth=current_depth * 0.5,  # Estimate
            ask_depth=current_depth * 0.5,
            depth_imbalance=0,  # Would need bid/ask separately
            liquidity_shock=liquidity_shock,
            depth_ratio=depth_ratio,
        )
    
    def reset(self) -> None:
        """Reset the monitor."""
        self._depth_history.clear()


class SpreadTracker:
    """Tracks bid-ask spread changes."""
    
    def __init__(self, window_size: int = 100) -> None:
        self.window_size = window_size
        self._spreads: deque = deque(maxlen=window_size)
    
    def update(self, bid: float, ask: float) -> None:
        """
        Update with new bid/ask prices.
        
        Args:
            bid: Best bid price
            ask: Best ask price
        """
        spread = (ask - bid) / bid if bid > 0 else 0
        self._spreads.append(spread)
    
    def analyze(self) -> SpreadMetrics:
        """Compute spread metrics."""
        if len(self._spreads) < 2:
            return SpreadMetrics(
                spread=0,
                spread_change=0,
                spread_volatility=0,
                widening=False,
            )
        
        spreads = list(self._spreads)
        current = spreads[-1]
        avg = np.mean(spreads)
        
        # Spread change
        spread_change = (current - avg) / avg if avg > 0 else 0
        
        # Spread volatility
        spread_volatility = np.std(spreads)
        
        # Widening detection
        widening = current > (avg * 1.5)
        
        return SpreadMetrics(
            spread=current,
            spread_change=spread_change,
            spread_volatility=spread_volatility,
            widening=widening,
        )
    
    def reset(self) -> None:
        """Reset the tracker."""
        self._spreads.clear()


class ImbalanceDetector:
    """Detects order book imbalance patterns."""
    
    def __init__(self, window_size: int = 50) -> None:
        self.window_size = window_size
        self._imbalances: deque = deque(maxlen=window_size)
    
    def update(self, bid_volume: float, ask_volume: float) -> None:
        """
        Update with order book volumes.
        
        Args:
            bid_volume: Total bid volume
            ask_volume: Total ask volume
        """
        total = bid_volume + ask_volume
        if total > 0:
            imbalance = (bid_volume - ask_volume) / total
            self._imbalances.append(imbalance)
    
    def analyze(self) -> ImbalanceMetrics:
        """Compute imbalance metrics."""
        if len(self._imbalances) < 2:
            return ImbalanceMetrics(
                bid_ask_ratio=1.0,
                price_pressure=0,
                volume_imbalance=0,
                imbalance_trend="stable",
            )
        
        imbalances = list(self._imbalances)
        current = imbalances[-1]
        
        # Bid-ask ratio
        bid_ask_ratio = (1 + current) / (1 - current) if current != 1 else float('inf')
        
        # Price pressure (scaled imbalance)
        price_pressure = current
        
        # Volume imbalance
        volume_imbalance = abs(current)
        
        # Trend detection
        if len(imbalances) >= 10:
            recent = np.mean(imbalances[-10:-5])
            older = np.mean(imbalances[-15:-10])
            diff = recent - older
            
            if diff > 0.1:
                trend = "increasing"
            elif diff < -0.1:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        return ImbalanceMetrics(
            bid_ask_ratio=bid_ask_ratio,
            price_pressure=price_pressure,
            volume_imbalance=volume_imbalance,
            imbalance_trend=trend,
        )
    
    def reset(self) -> None:
        """Reset the detector."""
        self._imbalances.clear()


class MicrostructureAnalyzer:
    """Combined analyzer for all microstructure signals."""
    
    def __init__(self) -> None:
        self.order_flow = OrderFlowAnalyzer()
        self.liquidity = LiquidityMonitor()
        self.spread = SpreadTracker()
        self.imbalance = ImbalanceDetector()
    
    def update(
        self,
        bid_price: float,
        ask_price: float,
        last_price: float,
        volume: float,
        trade_side: str,
        bid_volume: float = 0,
        ask_volume: float = 0,
    ) -> None:
        """
        Update all analyzers with new market data.
        
        Args:
            bid_price: Best bid price
            ask_price: Best ask price
            last_price: Last traded price
            volume: Trade volume
            trade_side: "buy" or "sell"
            bid_volume: Total bid volume (optional)
            ask_volume: Total ask volume (optional)
        """
        # Update spread tracker
        self.spread.update(bid_price, ask_price)
        
        # Update order flow
        self.order_flow.update(last_price, volume, trade_side)
        
        # Update liquidity
        if bid_volume > 0 and ask_volume > 0:
            self.liquidity.update(bid_volume, ask_volume)
            self.imbalance.update(bid_volume, ask_volume)
        else:
            # Estimate from spread
            self.liquidity.update(1000, 1000)
    
    def analyze(self) -> MicrostructureFeatures:
        """Analyze all microstructure components."""
        order_flow = self.order_flow.analyze()
        liquidity = self.liquidity.analyze()
        spread = self.spread.analyze()
        imbalance = self.imbalance.analyze()
        
        # Execution risk assessment
        execution_risk = 0.0
        
        # High spread = higher execution risk
        if spread.widening:
            execution_risk += 0.3
        elif spread.spread_volatility > 0.001:
            execution_risk += 0.1
        
        # Liquidity shock = high risk
        if liquidity.liquidity_shock:
            execution_risk += 0.4
        
        # High order flow imbalance = higher risk
        if abs(order_flow.imbalance) > 0.8:
            execution_risk += 0.2
        
        execution_risk = min(execution_risk, 1.0)
        
        # Signal quality (inverse of risk)
        signal_quality = 1.0 - execution_risk
        
        # Adjust for absorption (high absorption = better quality)
        signal_quality += order_flow.absorption_ratio * 0.2
        signal_quality = min(signal_quality, 1.0)
        
        return MicrostructureFeatures(
            order_flow=order_flow,
            liquidity=liquidity,
            spread=spread,
            imbalance=imbalance,
            execution_risk=execution_risk,
            signal_quality=signal_quality,
        )
    
    def get_features(self) -> Dict[str, float]:
        """
        Get microstructure features as dictionary for intelligence layer.
        
        Returns:
            Dictionary of feature_name: value
        """
        analysis = self.analyze()
        
        return {
            # Order flow features
            "orderflow_imbalance": analysis.order_flow.imbalance,
            "aggressive_buying": analysis.order_flow.aggressive_buying,
            "aggressive_selling": analysis.order_flow.aggressive_selling,
            "absorption_ratio": analysis.order_flow.absorption_ratio,
            
            # Liquidity features
            "depth_ratio": analysis.liquidity.depth_ratio,
            "liquidity_shock": 1.0 if analysis.liquidity.liquidity_shock else 0.0,
            
            # Spread features
            "spread": analysis.spread.spread,
            "spread_change": analysis.spread.spread_change,
            "spread_widening": 1.0 if analysis.spread.widening else 0.0,
            
            # Imbalance features
            "volume_imbalance": analysis.imbalance.volume_imbalance,
            "price_pressure": analysis.imbalance.price_pressure,
            
            # Composite features
            "execution_risk": analysis.execution_risk,
            "signal_quality": analysis.signal_quality,
        }
    
    def reset(self) -> None:
        """Reset all analyzers."""
        self.order_flow.reset()
        self.liquidity.reset()
        self.spread.reset()
        self.imbalance.reset()


# Singleton instance
_analyzer: Optional[MicrostructureAnalyzer] = None


def get_microstructure_analyzer() -> MicrostructureAnalyzer:
    """Get the default microstructure analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = MicrostructureAnalyzer()
    return _analyzer
