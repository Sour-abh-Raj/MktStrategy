"""
Multi-Market Layer - Global Market Expansion

Modules:
- data_connectors.py: Multi-market data ingestion (crypto, stocks, forex, futures)
- cross_market_features.py: Cross-asset feature engineering
- cross_market_alpha.py: Cross-market strategy discovery
- global_portfolio.py: Global portfolio optimization across asset classes
"""

from freqtrade_project.multi_market_layer.data_connectors import (
    MarketType,
    AssetClass,
    MarketData,
    ExchangeConfig,
    DataConnector,
    CryptoDataConnector,
    StockDataConnector,
    ForexDataConnector,
    FuturesDataConnector,
    MultiMarketDataManager,
    create_crypto_connector,
    create_stock_connector,
    create_forex_connector,
    create_multi_market_manager,
)

from freqtrade_project.multi_market_layer.cross_market_features import (
    CrossMarketFeatures,
    CrossMarketFeatureEngine,
    MacroRegimeDetector,
    create_feature_engine,
    create_macro_detector,
)

from freqtrade_project.multi_market_layer.cross_market_alpha import (
    AlphaType,
    CrossMarketStrategy,
    IntermarketMomentumStrategy,
    RiskOnOffStrategy,
    CrossAssetArbitrageStrategy,
    CrossMarketAlphaDiscovery,
    create_cross_market_discovery,
)

from freqtrade_project.multi_market_layer.global_portfolio import (
    AssetClassAllocation,
    GlobalPortfolioResult,
    GlobalPortfolioOptimizer,
    GlobalBenchmark,
    create_global_optimizer,
)

__all__ = [
    # Data connectors
    "MarketType",
    "AssetClass",
    "MarketData",
    "ExchangeConfig",
    "DataConnector",
    "CryptoDataConnector",
    "StockDataConnector",
    "ForexDataConnector",
    "FuturesDataConnector",
    "MultiMarketDataManager",
    "create_crypto_connector",
    "create_stock_connector",
    "create_forex_connector",
    "create_multi_market_manager",
    
    # Cross-market features
    "CrossMarketFeatures",
    "CrossMarketFeatureEngine",
    "MacroRegimeDetector",
    "create_feature_engine",
    "create_macro_detector",
    
    # Cross-market alpha
    "AlphaType",
    "CrossMarketStrategy",
    "IntermarketMomentumStrategy",
    "RiskOnOffStrategy",
    "CrossAssetArbitrageStrategy",
    "CrossMarketAlphaDiscovery",
    "create_cross_market_discovery",
    
    # Global portfolio
    "AssetClassAllocation",
    "GlobalPortfolioResult",
    "GlobalPortfolioOptimizer",
    "GlobalBenchmark",
    "create_global_optimizer",
]
