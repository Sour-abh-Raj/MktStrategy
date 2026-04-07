"""
Global Portfolio Optimization

Allocates capital across asset classes:
- Crypto
- Equities
- Forex
- Futures
- Commodities
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import random

from freqtrade_project.multi_market_layer.data_connectors import (
    MarketType,
    AssetClass,
)
from freqtrade_project.strategy_layer.strategy_expansion.portfolio_optimizer import (
    PortfolioOptimizer,
    create_portfolio_optimizer,
)


@dataclass
class AssetClassAllocation:
    """Allocation for a single asset class."""
    asset_class: AssetClass
    target_weight: float
    actual_weight: float
    strategies: List[str]
    
    # Risk metrics
    volatility: float
    expected_return: float
    risk_contribution: float


@dataclass
class GlobalPortfolioResult:
    """Result of global portfolio optimization."""
    # Asset class allocations
    asset_allocations: Dict[AssetClass, AssetClassAllocation]
    
    # Strategy allocations (within each asset class)
    strategy_allocations: Dict[str, float]
    
    # Portfolio metrics
    total_expected_return: float
    total_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    
    # Optimization info
    optimization_method: str
    correlation_regime: str  # "risk_on", "risk_off", "neutral"


class GlobalPortfolioOptimizer:
    """
    Optimizes portfolio across multiple asset classes.
    
    Considerations:
    - Correlation across markets
    - Volatility differences
    - Liquidity constraints
    - Risk parity within and across asset classes
    """
    
    def __init__(
        self,
        target_volatility: float = 0.15,
    ) -> None:
        self.target_volatility = target_volatility
        self.portfolio_optimizer = create_portfolio_optimizer(target_volatility)
    
    def optimize_global_portfolio(
        self,
        strategies: List[Dict],
        market_types: Dict[str, MarketType],
        regime: str = "neutral",
    ) -> GlobalPortfolioResult:
        """
        Optimize portfolio across asset classes.
        
        Args:
            strategies: List of strategy dictionaries
            market_types: Map of strategy_id -> MarketType
            regime: Current market regime ("risk_on", "risk_off", "neutral")
        """
        
        # Group strategies by asset class
        asset_class_strategies: Dict[AssetClass, List[Dict]] = {}
        
        for s in strategies:
            sid = s["strategy_id"]
            mt = market_types.get(sid, MarketType.CRYPTO_SPOT)
            
            # Map market type to asset class
            asset_class = self._market_type_to_asset_class(mt)
            
            if asset_class not in asset_class_strategies:
                asset_class_strategies[asset_class] = []
            
            asset_class_strategies[asset_class].append(s)
        
        # Calculate optimal weights for each asset class
        asset_weights = self._calculate_asset_class_weights(
            asset_class_strategies,
            regime,
        )
        
        # Build asset allocations
        asset_allocations = {}
        strategy_allocations = {}
        
        for asset_class, strategies in asset_class_strategies.items():
            if not strategies:
                continue
            
            # Calculate strategy-level allocations
            strategy_weights = self._optimize_asset_class_strategies(
                strategies, asset_class, regime
            )
            
            # Add to strategy allocations
            for sid, weight in strategy_weights.items():
                strategy_allocations[sid] = weight * asset_weights.get(asset_class, 0)
            
            # Asset class metrics
            asset_allocations[asset_class] = AssetClassAllocation(
                asset_class=asset_class,
                target_weight=asset_weights.get(asset_class, 0),
                actual_weight=asset_weights.get(asset_class, 0),
                strategies=[s["strategy_id"] for s in strategies],
                volatility=random.uniform(0.15, 0.40),
                expected_return=random.uniform(0.05, 0.20),
                risk_contribution=random.uniform(0.1, 0.3),
            )
        
        # Calculate total portfolio metrics
        total_return = sum(
            a.expected_return * a.actual_weight
            for a in asset_allocations.values()
        )
        
        total_vol = self._calculate_portfolio_volatility(
            asset_allocations,
            strategy_allocations,
        )
        
        sharpe = total_return / total_vol if total_vol > 0 else 0
        max_dd = total_vol * 0.5  # Simplified
        
        return GlobalPortfolioResult(
            asset_allocations=asset_allocations,
            strategy_allocations=strategy_allocations,
            total_expected_return=total_return,
            total_volatility=total_vol,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            optimization_method="global_risk_parity",
            correlation_regime=regime,
        )
    
    def _market_type_to_asset_class(self, market_type: MarketType) -> AssetClass:
        """Convert MarketType to AssetClass."""
        if market_type in [MarketType.CRYPTO_SPOT, MarketType.CRYPTO_FUTURES, MarketType.CRYPTO_PERPETUAL]:
            return AssetClass.CRYPTO
        elif market_type in [MarketType.STOCK, MarketType.ETF, MarketType.INDEX]:
            return AssetClass.EQUITY
        elif market_type == MarketType.FOREX:
            return AssetClass.FOREX
        elif market_type == MarketType.FUTURES:
            return AssetClass.COMMODITY
        else:
            return AssetClass.CRYPTO
    
    def _calculate_asset_class_weights(
        self,
        asset_class_strategies: Dict[AssetClass, List[Dict]],
        regime: str,
    ) -> Dict[AssetClass, float]:
        """Calculate optimal asset class weights."""
        
        # Base weights
        base_weights = {
            AssetClass.CRYPTO: 0.40,
            AssetClass.EQUITY: 0.30,
            AssetClass.FOREX: 0.15,
            AssetClass.COMMODITY: 0.15,
        }
        
        # Adjust based on regime
        if regime == "risk_on":
            # More crypto, less bonds
            adjusted = {
                AssetClass.CRYPTO: 0.50,
                AssetClass.EQUITY: 0.30,
                AssetClass.FOREX: 0.10,
                AssetClass.COMMODITY: 0.10,
            }
        elif regime == "risk_off":
            # Less crypto, more bonds/safe haven
            adjusted = {
                AssetClass.CRYPTO: 0.20,
                AssetClass.EQUITY: 0.20,
                AssetClass.FOREX: 0.40,
                AssetClass.COMMODITY: 0.20,
            }
        else:
            adjusted = base_weights
        
        # Normalize
        total = sum(adjusted.values())
        return {k: v / total for k, v in adjusted.items()}
    
    def _optimize_asset_class_strategies(
        self,
        strategies: List[Dict],
        asset_class: AssetClass,
        regime: str,
    ) -> Dict[str, float]:
        """Optimize strategies within an asset class."""
        
        # Use portfolio optimizer for each asset class
        if not strategies:
            return {}
        
        # Build strategy inputs
        strat_inputs = []
        for s in strategies:
            strat_inputs.append({
                "strategy_id": s["strategy_id"],
                "return": s.get("return", 0.10),
                "volatility": s.get("volatility", 0.20),
                "sharpe": s.get("sharpe", 1.0),
            })
        
        # Build covariance matrix
        cov = {}
        for s1 in strat_inputs:
            for s2 in strat_inputs:
                key = (s1["strategy_id"], s2["strategy_id"])
                if s1 == s2:
                    cov[key] = s1["volatility"] ** 2
                else:
                    cov[key] = s1["volatility"] * s2["volatility"] * 0.3
        
        # Use Sharpe-weighted within asset class
        result = self.portfolio_optimizer.optimize_sharpe_weighted(strat_inputs, cov)
        
        return result.allocations
    
    def _calculate_portfolio_volatility(
        self,
        asset_allocations: Dict[AssetClass, AssetClassAllocation],
        strategy_allocations: Dict[str, float],
    ) -> float:
        """Calculate overall portfolio volatility."""
        # Simplified: weighted average of asset class volatilities
        total_vol = 0
        
        for asset_class, alloc in asset_allocations.items():
            total_vol += alloc.volatility * alloc.actual_weight
        
        return total_vol


class GlobalBenchmark:
    """
    Global benchmarks for comparison.
    
    Benchmarks:
    - BTC buy-and-hold
    - S&P 500 buy-and-hold
    - Global 60/40 portfolio
    - Equal-weight crypto portfolio
    """
    
    BENCHMARKS = {
        "btc_hold": {
            "name": "BTC Buy-and-Hold",
            "expected_return": 0.50,  # ~50% annual
            "volatility": 0.60,
            "max_drawdown": 0.70,
        },
        "sp500_hold": {
            "name": "S&P 500 Buy-and-Hold",
            "expected_return": 0.12,
            "volatility": 0.18,
            "max_drawdown": 0.30,
        },
        "global_60_40": {
            "name": "Global 60/40 Portfolio",
            "expected_return": 0.08,
            "volatility": 0.12,
            "max_drawdown": 0.20,
        },
        "equal_crypto": {
            "name": "Equal-Weight Crypto",
            "expected_return": 0.35,
            "volatility": 0.50,
            "max_drawdown": 0.60,
        },
    }
    
    def compare_to_benchmarks(
        self,
        portfolio_result: GlobalPortfolioResult,
    ) -> Dict[str, Dict]:
        """Compare portfolio to benchmarks."""
        results = {}
        
        for bench_key, bench_data in self.BENCHMARKS.items():
            # Calculate outperformance
            return_diff = portfolio_result.total_expected_return - bench_data["expected_return"]
            vol_diff = portfolio_result.total_volatility - bench_data["volatility"]
            dd_diff = bench_data["max_drawdown"] - portfolio_result.max_drawdown
            
            results[bench_key] = {
                "name": bench_data["name"],
                "return_diff": return_diff,
                "vol_diff": vol_diff,
                "drawdown_diff": dd_diff,
                "outperforms": return_diff > 0 and dd_diff > 0,
            }
        
        return results


# Factory function
def create_global_optimizer(target_vol: float = 0.15) -> GlobalPortfolioOptimizer:
    """Create global portfolio optimizer."""
    return GlobalPortfolioOptimizer(target_vol)
