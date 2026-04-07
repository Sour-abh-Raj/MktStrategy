"""
Cross-Market Alpha Discovery

Agents that discover strategies across multiple asset classes:
- Intermarket momentum strategies
- Risk-on/risk-off strategies
- Cross-asset arbitrage
- Global macro strategies
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from freqtrade_project.multi_market_layer.data_connectors import (
    MarketType,
    AssetClass,
)


class AlphaType(str, Enum):
    """Types of cross-market alpha."""
    INTERMARKET_MOMENTUM = "intermarket_momentum"
    RISK_ON_OFF = "risk_on_off"
    CROSS_ASSET_ARBITRAGE = "cross_asset_arbitrage"
    GLOBAL_MACRO = "global_macro"
    RELATIVE_VALUE = "relative_value"


@dataclass
class CrossMarketStrategy:
    """Strategy that operates across multiple markets."""
    strategy_id: str
    alpha_type: AlphaType
    
    # Market targeting
    primary_market: MarketType
    secondary_markets: List[MarketType]
    asset_classes: List[AssetClass]
    
    # Strategy logic
    entry_conditions: List[Dict]  # Cross-market conditions
    exit_conditions: List[Dict]
    
    # Risk parameters
    stop_loss: float
    take_profit: float
    position_sizing: float
    
    # Performance
    sharpe: float = 0.0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    
    # Status
    active: bool = True


@dataclass
class IntermarketMomentumStrategy(CrossMarketStrategy):
    """Momentum strategy across asset classes."""
    
    def __init__(self) -> None:
        super().__init__(
            strategy_id=f"intermarket_mom_{random.randint(0, 999)}",
            alpha_type=AlphaType.INTERMARKET_MOMENTUM,
            primary_market=MarketType.CRYPTO_SPOT,
            secondary_markets=[MarketType.CRYPTO_SPOT, MarketType.STOCK],
            asset_classes=[AssetClass.CRYPTO, AssetClass.EQUITY],
            entry_conditions=[
                {"condition": "btc_momentum_above", "threshold": 0.05},
                {"condition": "altcoin_strength_above", "threshold": 0.03},
            ],
            exit_conditions=[
                {"condition": "btc_momentum_below", "threshold": 0.0},
            ],
            stop_loss=0.05,
            take_profit=0.10,
            position_sizing=0.10,
        )


@dataclass
class RiskOnOffStrategy(CrossMarketStrategy):
    """Risk-on/risk-off strategy."""
    
    def __init__(self) -> None:
        super().__init__(
            strategy_id=f"riskonoff_{random.randint(0, 999)}",
            alpha_type=AlphaType.RISK_ON_OFF,
            primary_market=MarketType.CRYPTO_SPOT,
            secondary_markets=[MarketType.STOCK, MarketType.FOREX],
            asset_classes=[AssetClass.CRYPTO, AssetClass.EQUITY],
            entry_conditions=[
                {"condition": "risk_on_signal", "threshold": 0.6},
                {"condition": "equity_rally", "threshold": 0.02},
            ],
            exit_conditions=[
                {"condition": "risk_off_signal", "threshold": 0.6},
            ],
            stop_loss=0.08,
            take_profit=0.15,
            position_sizing=0.15,
        )


@dataclass
class CrossAssetArbitrageStrategy(CrossMarketStrategy):
    """Cross-asset arbitrage strategy."""
    
    def __init__(self) -> None:
        super().__init__(
            strategy_id=f"arb_{random.randint(0, 999)}",
            alpha_type=AlphaType.CROSS_ASSET_ARBITRAGE,
            primary_market=MarketType.CRYPTO_SPOT,
            secondary_markets=[MarketType.CRYPTO_PERPETUAL],
            asset_classes=[AssetClass.CRYPTO],
            entry_conditions=[
                {"condition": "basis_above_threshold", "threshold": 0.02},
                {"condition": "basis_reversion_mean", "threshold": 0.0},
            ],
            exit_conditions=[
                {"condition": "basis_zero", "threshold": 0.001},
            ],
            stop_loss=0.02,
            take_profit=0.03,
            position_sizing=0.20,  # Lower for arb
        )


class CrossMarketAlphaDiscovery:
    """
    Discovers alpha across multiple asset classes.
    
    Generates strategies that:
    - Exploit intermarket momentum
    - Trade risk-on/risk-off regimes
    - Find cross-asset arbitrages
    - Respond to global macro conditions
    """
    
    def __init__(self) -> None:
        self.strategies: List[CrossMarketStrategy] = []
    
    def generate_intermarket_momentum(
        self,
        count: int = 10,
    ) -> List[CrossMarketStrategy]:
        """Generate intermarket momentum strategies."""
        strategies = []
        
        # Leader-follower strategies
        patterns = [
            # BTC leads, alts follow
            {"leader": "BTC", "followers": ["ETH", "SOL", "BNB"]},
            # ETH leads
            {"leader": "ETH", "followers": ["MATIC", "LINK", "DOT"]},
            # SOL leads
            {"leader": "SOL", "followers": ["APT", "ARB", "OP"]},
        ]
        
        for pattern in patterns[:count]:
            strategy = CrossMarketStrategy(
                strategy_id=f"intermarket_{pattern['leader']}_{len(strategies)}",
                alpha_type=AlphaType.INTERMARKET_MOMENTUM,
                primary_market=MarketType.CRYPTO_SPOT,
                secondary_markets=[MarketType.CRYPTO_SPOT],
                asset_classes=[AssetClass.CRYPTO],
                entry_conditions=[
                    {"condition": f"{pattern['leader']}_momentum", "threshold": 0.05},
                    {"condition": "relative_strength", "threshold": 0.03},
                ],
                exit_conditions=[
                    {"condition": "momentum_reversal", "threshold": 0.0},
                ],
                stop_loss=random.uniform(0.04, 0.08),
                take_profit=random.uniform(0.08, 0.15),
                position_sizing=random.uniform(0.08, 0.15),
            )
            strategies.append(strategy)
        
        self.strategies.extend(strategies)
        return strategies
    
    def generate_risk_on_off(
        self,
        count: int = 10,
    ) -> List[CrossMarketStrategy]:
        """Generate risk-on/risk-off strategies."""
        strategies = []
        
        for i in range(count):
            strategy = CrossMarketStrategy(
                strategy_id=f"riskonoff_{i}",
                alpha_type=AlphaType.RISK_ON_OFF,
                primary_market=MarketType.CRYPTO_SPOT,
                secondary_markets=[MarketType.STOCK, MarketType.FOREX],
                asset_classes=[AssetClass.CRYPTO, AssetClass.EQUITY, AssetClass.FOREX],
                entry_conditions=[
                    {"condition": "sp500_rally", "threshold": 0.02},
                    {"condition": "vix_declining", "threshold": -0.05},
                    {"condition": "btc_correlation", "threshold": 0.7},
                ],
                exit_conditions=[
                    {"condition": "risk_off_trigger", "threshold": 0.6},
                ],
                stop_loss=random.uniform(0.05, 0.10),
                take_profit=random.uniform(0.10, 0.20),
                position_sizing=random.uniform(0.10, 0.20),
            )
            strategies.append(strategy)
        
        self.strategies.extend(strategies)
        return strategies
    
    def generate_cross_asset_arbitrage(
        self,
        count: int = 10,
    ) -> List[CrossMarketStrategy]:
        """Generate cross-asset arbitrage strategies."""
        strategies = []
        
        arbitrage_patterns = [
            # BTC spot vs futures basis
            {"type": "basis", "pair": "BTC", "markets": [MarketType.CRYPTO_SPOT, MarketType.CRYPTO_PERPETUAL]},
            # ETH/BTC relative value
            {"type": "relative_value", "pair": "ETH", "markets": [MarketType.CRYPTO_SPOT]},
            # Gold/USD inverse
            {"type": "inverse", "pair": "GOLD", "markets": [MarketType.COMMODITY, MarketType.FOREX]},
        ]
        
        for pattern in arbitrage_patterns[:count]:
            strategy = CrossMarketStrategy(
                strategy_id=f"arb_{pattern['type']}_{len(strategies)}",
                alpha_type=AlphaType.CROSS_ASSET_ARBITRAGE,
                primary_market=pattern["markets"][0],
                secondary_markets=pattern["markets"],
                asset_classes=[AssetClass.CRYPTO, AssetClass.COMMODITY],
                entry_conditions=[
                    {"condition": f"{pattern['type']}_deviation", "threshold": 0.02},
                    {"condition": "mean_reversion_signal", "threshold": 2.0},
                ],
                exit_conditions=[
                    {"condition": "deviation_zero", "threshold": 0.001},
                ],
                stop_loss=random.uniform(0.01, 0.03),
                take_profit=random.uniform(0.02, 0.05),
                position_sizing=random.uniform(0.15, 0.25),
            )
            strategies.append(strategy)
        
        self.strategies.extend(strategies)
        return strategies
    
    def generate_global_macro(
        self,
        count: int = 10,
    ) -> List[CrossMarketStrategy]:
        """Generate global macro strategies."""
        strategies = []
        
        macro_strategies = [
            # High vol macro
            {"regime": "high_volatility", "action": "reduce_risk"},
            # Risk-on macro
            {"regime": "risk_on", "action": "increase_risk"},
            # Liquidity tightening
            {"regime": "liquidity_tight", "action": "rotate_assets"},
        ]
        
        for macro in macro_strategies[:count]:
            strategy = CrossMarketStrategy(
                strategy_id=f"macro_{macro['regime']}_{len(strategies)}",
                alpha_type=AlphaType.GLOBAL_MACRO,
                primary_market=MarketType.CRYPTO_SPOT,
                secondary_markets=[MarketType.STOCK, MarketType.FUTURES],
                asset_classes=[AssetClass.CRYPTO, AssetClass.EQUITY, AssetClass.COMMODITY],
                entry_conditions=[
                    {"condition": f"macro_regime_{macro['regime']}", "threshold": 0.7},
                ],
                exit_conditions=[
                    {"condition": "regime_change", "threshold": 0.5},
                ],
                stop_loss=random.uniform(0.05, 0.12),
                take_profit=random.uniform(0.10, 0.25),
                position_sizing=random.uniform(0.05, 0.15),
            )
            strategies.append(strategy)
        
        self.strategies.extend(strategies)
        return strategies
    
    def generate_all(
        self,
        strategies_per_type: int = 10,
    ) -> Dict[AlphaType, List[CrossMarketStrategy]]:
        """Generate all types of cross-market strategies."""
        return {
            AlphaType.INTERMARKET_MOMENTUM: self.generate_intermarket_momentum(strategies_per_type),
            AlphaType.RISK_ON_OFF: self.generate_risk_on_off(strategies_per_type),
            AlphaType.CROSS_ASSET_ARBITRAGE: self.generate_cross_asset_arbitrage(strategies_per_type),
            AlphaType.GLOBAL_MACRO: self.generate_global_macro(strategies_per_type),
        }
    
    def get_strategies_by_type(
        self,
        alpha_type: AlphaType,
    ) -> List[CrossMarketStrategy]:
        """Get all strategies of a specific type."""
        return [s for s in self.strategies if s.alpha_type == alpha_type]
    
    def get_strategies_by_market(
        self,
        market_type: MarketType,
    ) -> List[CrossMarketStrategy]:
        """Get all strategies that trade a specific market."""
        return [s for s in self.strategies if s.primary_market == market_type]


# Factory function
def create_cross_market_discovery() -> CrossMarketAlphaDiscovery:
    """Create cross-market alpha discovery."""
    return CrossMarketAlphaDiscovery()


# Import random
import random
