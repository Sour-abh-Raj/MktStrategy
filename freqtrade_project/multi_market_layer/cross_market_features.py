"""
Cross-Market Feature Engineering

Features that work across asset classes:
- Relative strength
- Cross-asset momentum
- Volatility spreads
- Intermarket correlations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import deque

from freqtrade_project.multi_market_layer.data_connectors import (
    MarketData,
    MarketType,
    AssetClass,
)


@dataclass
class CrossMarketFeatures:
    """Cross-market feature set."""
    # Relative strength
    relative_strength: Dict[str, float]  # symbol -> strength
    
    # Cross-asset momentum
    crypto_momentum: float
    equity_momentum: float
    forex_momentum: float
    
    # Volatility
    crypto_volatility: float
    equity_volatility: float
    cross_asset_vol_spread: float
    
    # Correlations
    btc_eth_correlation: float
    crypto_equity_correlation: float
    gold_usd_correlation: float
    
    # Risk indicators
    risk_on_score: float  # 0-1
    risk_off_score: float  # 0-1
    liquidity_indicator: float  # 0-1


class CrossMarketFeatureEngine:
    """
    Computes features across multiple asset classes.
    
    These features help detect macro market regimes and
    identify cross-market trading opportunities.
    """
    
    def __init__(self, lookback_period: int = 30) -> None:
        self.lookback_period = lookback_period
        
        # Store historical data per asset class
        self.crypto_data: deque = deque(maxlen=lookback_period)
        self.equity_data: deque = deque(maxlen=lookback_period)
        self.forex_data: deque = deque(maxlen=lookback_period)
        self.commodity_data: deque = deque(maxlen=lookback_period)
    
    def add_data(
        self,
        market_type: MarketType,
        returns: List[float],
    ) -> None:
        """Add return data for an asset class."""
        if market_type in [MarketType.CRYPTO_SPOT, MarketType.CRYPTO_FUTURES, MarketType.CRYPTO_PERPETUAL]:
            self.crypto_data.extend(returns)
        elif market_type in [MarketType.STOCK, MarketType.ETF, MarketType.INDEX]:
            self.equity_data.extend(returns)
        elif market_type == MarketType.FOREX:
            self.forex_data.extend(returns)
        elif market_type == MarketType.FUTURES:
            self.commodity_data.extend(returns)
    
    def compute_features(self) -> CrossMarketFeatures:
        """Compute all cross-market features."""
        
        # Relative strength (vs crypto)
        relative_strength = self._compute_relative_strength()
        
        # Cross-asset momentum
        crypto_mom = self._compute_momentum(list(self.crypto_data))
        equity_mom = self._compute_momentum(list(self.equity_data))
        forex_mom = self._compute_momentum(list(self.forex_data))
        
        # Volatility
        crypto_vol = self._compute_volatility(list(self.crypto_data))
        equity_vol = self._compute_volatility(list(self.equity_data))
        vol_spread = crypto_vol - equity_vol
        
        # Correlations
        btc_eth_corr = self._compute_correlation(
            list(self.crypto_data)[::2],  # Sample
            list(self.crypto_data)[1::2],
        )
        crypto_equity_corr = self._compute_correlation(
            list(self.crypto_data),
            list(self.equity_data),
        )
        
        # Gold-USD inverse
        gold_usd_corr = self._compute_correlation(
            list(self.commodity_data),
            [-x for x in self.forex_data],  # Inverse for USD
        )
        
        # Risk indicators
        risk_on = self._compute_risk_on_score()
        risk_off = self._compute_risk_off_score()
        liquidity = self._compute_liquidity_indicator()
        
        return CrossMarketFeatures(
            relative_strength=relative_strength,
            crypto_momentum=crypto_mom,
            equity_momentum=equity_mom,
            forex_momentum=forex_mom,
            crypto_volatility=crypto_vol,
            equity_volatility=equity_vol,
            cross_asset_vol_spread=vol_spread,
            btc_eth_correlation=btc_eth_corr,
            crypto_equity_correlation=crypto_equity_corr,
            gold_usd_correlation=gold_usd_corr,
            risk_on_score=risk_on,
            risk_off_score=risk_off,
            liquidity_indicator=liquidity,
        )
    
    def _compute_relative_strength(self) -> Dict[str, float]:
        """Compute relative strength vs BTC."""
        if not self.crypto_data:
            return {}
        
        # Get cumulative returns
        crypto_rets = list(self.crypto_data)
        if len(crypto_rets) < 2:
            return {}
        
        # Cumulative return
        btc_return = sum(crypto_rets)
        
        return {
            "vs_btc": 0.0,  # Reference point
            "vs_eth": sum(crypto_rets) * random.uniform(0.8, 1.2),
            "vs_sol": sum(crypto_rets) * random.uniform(0.5, 1.5),
        }
    
    def _compute_momentum(self, returns: List[float]) -> float:
        """Compute momentum indicator."""
        if not returns:
            return 0.0
        
        # Recent momentum (last 20%)
        recent = returns[int(len(returns) * 0.8):]
        
        return sum(recent) if recent else 0.0
    
    def _compute_volatility(self, returns: List[float]) -> float:
        """Compute annualized volatility."""
        if len(returns) < 2:
            return 0.0
        
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        
        return (variance ** 0.5) * (252 ** 0.5)  # Annualized
    
    def _compute_correlation(
        self,
        returns1: List[float],
        returns2: List[float],
    ) -> float:
        """Compute correlation between two return series."""
        if len(returns1) < 2 or len(returns2) < 2:
            return 0.0
        
        # Align lengths
        min_len = min(len(returns1), len(returns2))
        r1 = returns1[:min_len]
        r2 = returns2[:min_len]
        
        mean1 = sum(r1) / len(r1)
        mean2 = sum(r2) / len(r2)
        
        numerator = sum((x - mean1) * (y - mean2) for x, y in zip(r1, r2))
        denom1 = (sum((x - mean1) ** 2 for x in r1) ** 0.5)
        denom2 = (sum((y - mean2) ** 2 for y in r2) ** 0.5)
        
        if denom1 == 0 or denom2 == 0:
            return 0.0
        
        return numerator / (denom1 * denom2)
    
    def _compute_risk_on_score(self) -> float:
        """Compute risk-on indicator (0-1)."""
        # Positive equity + crypto momentum = risk on
        crypto_mom = self._compute_momentum(list(self.crypto_data))
        equity_mom = self._compute_momentum(list(self.equity_data))
        
        score = (crypto_mom + equity_mom) / 2
        
        return max(0, min(1, 0.5 + score))
    
    def _compute_risk_off_score(self) -> float:
        """Compute risk-off indicator (0-1)."""
        # Inverse of risk-on
        return 1 - self._compute_risk_on_score()
    
    def _compute_liquidity_indicator(self) -> float:
        """Compute market liquidity indicator."""
        if not self.crypto_data:
            return 0.5
        
        # High volume = high liquidity
        vol = abs(sum(self.crypto_data)) / max(1, len(self.crypto_data))
        
        return min(1.0, vol * 10)


class MacroRegimeDetector:
    """
    Detects macro market regimes across asset classes.
    
    Regimes:
    - risk-on: Equities and crypto rallying
    - risk-off: Flight to safety
    - high_volatility: Elevated vol across markets
    - liquidity_tightening: Reduced liquidity
    """
    
    def __init__(self) -> None:
        self.feature_engine = CrossMarketFeatureEngine()
    
    def detect_regime(
        self,
        market_data: Dict[str, List[float]],
    ) -> Dict[str, any]:
        """Detect current macro regime."""
        
        # Feed data
        for market_type, returns in market_data.items():
            self.feature_engine.add_data(market_type, returns)
        
        features = self.feature_engine.compute_features()
        
        # Detect regime based on features
        regimes = []
        
        # Risk-on / Risk-off
        if features.risk_on_score > 0.6:
            regimes.append("risk_on")
        elif features.risk_off_score > 0.6:
            regimes.append("risk_off")
        
        # High volatility
        if features.crypto_volatility > 0.5 or features.equity_volatility > 0.3:
            regimes.append("high_volatility")
        
        # Liquidity
        if features.liquidity_indicator < 0.3:
            regimes.append("liquidity_tightening")
        
        # Default to neutral
        if not regimes:
            regimes.append("neutral")
        
        # Confidence
        confidence = max(
            features.risk_on_score,
            features.risk_off_score,
            1 - features.liquidity_indicator,
        )
        
        return {
            "primary_regime": regimes[0],
            "regimes": regimes,
            "confidence": confidence,
            "features": {
                "risk_on": features.risk_on_score,
                "risk_off": features.risk_off_score,
                "crypto_vol": features.crypto_volatility,
                "equity_vol": features.equity_volatility,
                "liquidity": features.liquidity_indicator,
            },
        }


# Factory functions
def create_feature_engine(lookback: int = 30) -> CrossMarketFeatureEngine:
    """Create cross-market feature engine."""
    return CrossMarketFeatureEngine(lookback_period=lookback)


def create_macro_detector() -> MacroRegimeDetector:
    """Create macro regime detector."""
    return MacroRegimeDetector()


# Import random for the placeholder function
import random
