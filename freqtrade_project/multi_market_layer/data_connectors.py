"""
Multi-Market Data Layer

Extends data layer to support multiple asset classes:
- Crypto (existing + new exchanges)
- Stocks/ETFs
- Futures
- Forex
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import random


class MarketType(str, Enum):
    """Asset class / market types."""
    CRYPTO_SPOT = "crypto_spot"
    CRYPTO_FUTURES = "crypto_futures"
    CRYPTO_PERPETUAL = "crypto_perpetual"
    STOCK = "stock"
    ETF = "etf"
    INDEX = "index"
    FUTURES = "futures"
    FOREX = "forex"
    COMMODITY = "commodity"


class AssetClass(str, Enum):
    """Broader asset classification."""
    CRYPTO = "crypto"
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    COMMODITY = "commodity"
    FOREX = "forex"


@dataclass
class MarketData:
    """Standardized market data format across all asset classes."""
    symbol: str
    market_type: MarketType
    asset_class: AssetClass
    
    # Price data
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    # Timestamp
    timestamp: int
    timeframe: str
    
    # Exchange info
    exchange: str
    
    # Additional fields for specific asset types
    open_interest: Optional[float] = None  # For futures
    funding_rate: Optional[float] = None    # For perpetals
    bid_ask_spread: Optional[float] = None


@dataclass
class ExchangeConfig:
    """Configuration for an exchange."""
    name: str
    api_endpoint: str
    fee_tier: float  # maker fee
    min_order_size: float
    latency_ms: float
    
    # Supported markets
    supported_market_types: List[MarketType] = field(default_factory=list)


class DataConnector:
    """Base class for market data connectors."""
    
    def __init__(self, exchange: str, api_key: Optional[str] = None) -> None:
        self.exchange = exchange
        self.api_key = api_key
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[MarketData]:
        """Fetch OHLCV data."""
        raise NotImplementedError
    
    def fetch_orderbook(
        self,
        symbol: str,
        depth: int = 20,
    ) -> Dict:
        """Fetch order book."""
        raise NotImplementedError
    
    def fetch_ticker(self, symbol: str) -> Dict:
        """Fetch current ticker."""
        raise NotImplementedError


class CryptoDataConnector(DataConnector):
    """Data connector for crypto exchanges."""
    
    EXCHANGES = {
        "binance": ExchangeConfig(
            name="binance",
            api_endpoint="https://api.binance.com",
            fee_tier=0.001,  # 0.1%
            min_order_size=0.00001,
            latency_ms=50,
            supported_market_types=[MarketType.CRYPTO_SPOT, MarketType.CRYPTO_FUTURES, MarketType.CRYPTO_PERPETUAL],
        ),
        "bybit": ExchangeConfig(
            name="bybit",
            api_endpoint="https://api.bybit.com",
            fee_tier=0.001,
            min_order_size=0.0001,
            latency_ms=60,
            supported_market_types=[MarketType.CRYPTO_SPOT, MarketType.CRYPTO_PERPETUAL],
        ),
        "okx": ExchangeConfig(
            name="okx",
            api_endpoint="https://www.okx.com",
            fee_tier=0.0008,
            min_order_size=0.0001,
            latency_ms=70,
            supported_market_types=[MarketType.CRYPTO_SPOT, MarketType.CRYPTO_PERPETUAL],
        ),
        "coinbase": ExchangeConfig(
            name="coinbase",
            api_endpoint="https://api.coinbase.com",
            fee_tier=0.006,  # 0.6%
            min_order_size=0.0001,
            latency_ms=80,
            supported_market_types=[MarketType.CRYPTO_SPOT],
        ),
    }
    
    def __init__(self, exchange: str = "binance", api_key: Optional[str] = None) -> None:
        super().__init__(exchange, api_key)
        self.config = self.EXCHANGES.get(exchange)
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[MarketData]:
        """Fetch crypto OHLCV data."""
        # In production: would call exchange API
        # Simulated for demo
        return self._generate_mock_data(symbol, timeframe, start_time, end_time)
    
    def _generate_mock_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[int],
        end_time: Optional[int],
    ) -> List[MarketData]:
        """Generate mock data for demonstration."""
        # Determine market type from symbol
        if "PERP" in symbol or "USDT" in symbol:
            market_type = MarketType.CRYPTO_PERPETUAL
        elif "QUART" in symbol or "MONTH" in symbol:
            market_type = MarketType.CRYPTO_FUTURES
        else:
            market_type = MarketType.CRYPTO_SPOT
        
        # Generate sample data
        base_price = 1000.0 if "BTC" in symbol else 100.0
        data = []
        now = int(datetime.now().timestamp())
        
        for i in range(100):
            ts = now - (100 - i) * 3600  # hourly
            
            # Random walk price
            change = random.uniform(-0.02, 0.02)
            base_price *= (1 + change)
            
            data.append(MarketData(
                symbol=symbol,
                market_type=market_type,
                asset_class=AssetClass.CRYPTO,
                open=base_price * random.uniform(0.99, 1.01),
                high=base_price * random.uniform(1.00, 1.02),
                low=base_price * random.uniform(0.98, 1.00),
                close=base_price,
                volume=random.uniform(1000000, 10000000),
                timestamp=ts,
                timeframe=timeframe,
                exchange=self.exchange,
            ))
        
        return data


class StockDataConnector(DataConnector):
    """Data connector for stock/equity markets."""
    
    SOURCES = {
        "yahoo": "Yahoo Finance",
        "polygon": "Polygon.io",
        "alpha_vantage": "Alpha Vantage",
    }
    
    def __init__(self, source: str = "yahoo", api_key: Optional[str] = None) -> None:
        super().__init__(source, api_key)
        self.source = source
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[MarketData]:
        """Fetch stock OHLCV data."""
        return self._generate_mock_stock_data(symbol, timeframe, start_time, end_time)
    
    def _generate_mock_stock_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[int],
        end_time: Optional[int],
    ) -> List[MarketData]:
        """Generate mock stock data."""
        market_type = MarketType.STOCK if symbol not in ["SPY", "QQQ", "IWM"] else MarketType.ETF
        
        base_price = 100.0
        data = []
        now = int(datetime.now().timestamp())
        
        for i in range(100):
            ts = now - (100 - i) * 86400  # daily
            
            change = random.uniform(-0.03, 0.03)
            base_price *= (1 + change)
            
            data.append(MarketData(
                symbol=symbol,
                market_type=market_type,
                asset_class=AssetClass.EQUITY,
                open=base_price * random.uniform(0.99, 1.01),
                high=base_price * random.uniform(1.00, 1.02),
                low=base_price * random.uniform(0.98, 1.00),
                close=base_price,
                volume=random.uniform(1000000, 50000000),
                timestamp=ts,
                timeframe=timeframe,
                exchange=self.source,
            ))
        
        return data


class ForexDataConnector(DataConnector):
    """Data connector for forex markets."""
    
    PAIRS = ["EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD", "USD/CAD"]
    
    def __init__(self, source: str = "yahoo", api_key: Optional[str] = None) -> None:
        super().__init__(source, api_key)
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[MarketData]:
        """Fetch forex OHLCV data."""
        return self._generate_mock_forex_data(symbol, timeframe, start_time, end_time)
    
    def _generate_mock_forex_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[int],
        end_time: Optional[int],
    ) -> List[MarketData]:
        """Generate mock forex data."""
        # Base rates
        base_rates = {
            "EUR/USD": 1.08,
            "USD/JPY": 150.0,
            "GBP/USD": 1.26,
        }
        
        base_price = base_rates.get(symbol, 1.0)
        data = []
        now = int(datetime.now().timestamp())
        
        for i in range(100):
            ts = now - (100 - i) * 3600
            
            change = random.uniform(-0.005, 0.005)
            base_price *= (1 + change)
            
            data.append(MarketData(
                symbol=symbol,
                market_type=MarketType.FOREX,
                asset_class=AssetClass.FOREX,
                open=base_price * random.uniform(0.9995, 1.0005),
                high=base_price * random.uniform(1.0000, 1.0010),
                low=base_price * random.uniform(0.9990, 1.0000),
                close=base_price,
                volume=random.uniform(100000, 1000000),
                timestamp=ts,
                timeframe=timeframe,
                exchange=self.exchange,
            ))
        
        return data


class FuturesDataConnector(DataConnector):
    """Data connector for futures markets."""
    
    CONTRACTS = {
        "BTC-PERPETUAL": "BTC/USDT",
        "ETH-PERPETUAL": "ETH/USDT",
        "ES": "SPX",  # S&P 500
        "NQ": "NDX",  # Nasdaq
        "CL": "WTI",  # Oil
        "GC": "GOLD", # Gold
    }
    
    def __init__(self, exchange: str = "cme", api_key: Optional[str] = None) -> None:
        super().__init__(exchange, api_key)
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[MarketData]:
        """Fetch futures OHLCV data."""
        return self._generate_mock_futures_data(symbol, timeframe, start_time, end_time)
    
    def _generate_mock_futures_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[int],
        end_time: Optional[int],
    ) -> List[MarketData]:
        """Generate mock futures data."""
        is_perpetual = "PERPETUAL" in symbol
        
        base_price = 45000.0 if "BTC" in symbol else 2500.0
        market_type = MarketType.CRYPTO_PERPETUAL if is_perpetual else MarketType.FUTURES
        asset_class = AssetClass.CRYPTO if is_perpetual else AssetClass.COMMODITY
        
        data = []
        now = int(datetime.now().timestamp())
        
        for i in range(100):
            ts = now - (100 - i) * 3600
            
            change = random.uniform(-0.02, 0.02)
            base_price *= (1 + change)
            
            data.append(MarketData(
                symbol=symbol,
                market_type=market_type,
                asset_class=asset_class,
                open=base_price * random.uniform(0.99, 1.01),
                high=base_price * random.uniform(1.00, 1.02),
                low=base_price * random.uniform(0.98, 1.00),
                close=base_price,
                volume=random.uniform(100000, 1000000),
                timestamp=ts,
                timeframe=timeframe,
                exchange=self.exchange,
                open_interest=random.uniform(10000, 100000),
                funding_rate=0.0001 if is_perpetual else None,
            ))
        
        return data


class MultiMarketDataManager:
    """
    Unified data manager for all asset classes.
    
    Provides a single interface to fetch and normalize data
    across crypto, stocks, forex, and futures.
    """
    
    def __init__(self) -> None:
        self.connectors: Dict[str, DataConnector] = {}
        
        # Initialize default connectors
        self._setup_default_connectors()
    
    def _setup_default_connectors(self) -> None:
        """Setup default data connectors."""
        # Crypto
        self.connectors["binance"] = CryptoDataConnector("binance")
        
        # Stocks
        self.connectors["yahoo"] = StockDataConnector("yahoo")
        
        # Forex
        self.connectors["forex"] = ForexDataConnector("yahoo")
        
        # Futures
        self.connectors["futures"] = FuturesDataConnector("cme")
    
    def add_connector(self, connector: DataConnector) -> None:
        """Add a custom data connector."""
        self.connectors[connector.exchange] = connector
    
    def fetch_data(
        self,
        symbol: str,
        market_type: MarketType,
        timeframe: str = "1h",
        exchange: str = "binance",
    ) -> List[MarketData]:
        """Fetch data for a symbol."""
        connector = self.connectors.get(exchange)
        
        if connector:
            return connector.fetch_ohlcv(symbol, timeframe)
        
        return []
    
    def fetch_multiple(
        self,
        symbols: List[Dict],  # List of {symbol, market_type, exchange}
        timeframe: str = "1h",
    ) -> Dict[str, List[MarketData]]:
        """Fetch data for multiple symbols."""
        results = {}
        
        for item in symbols:
            symbol = item["symbol"]
            market_type = item.get("market_type", MarketType.CRYPTO_SPOT)
            exchange = item.get("exchange", "binance")
            
            data = self.fetch_data(symbol, market_type, timeframe, exchange)
            results[symbol] = data
        
        return results
    
    def get_supported_markets(self) -> Dict[str, List[str]]:
        """Get list of supported markets."""
        return {
            "crypto": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"],
            "stocks": ["AAPL", "MSFT", "GOOGL", "AMZN"],
            "etfs": ["SPY", "QQQ", "IWM"],
            "forex": ["EUR/USD", "USD/JPY", "GBP/USD"],
            "futures": ["BTC-PERPETUAL", "ES", "CL", "GC"],
        }


# Factory functions
def create_crypto_connector(exchange: str = "binance") -> CryptoDataConnector:
    """Create crypto data connector."""
    return CryptoDataConnector(exchange)


def create_stock_connector(source: str = "yahoo") -> StockDataConnector:
    """Create stock data connector."""
    return StockDataConnector(source)


def create_forex_connector(source: str = "yahoo") -> ForexDataConnector:
    """Create forex data connector."""
    return ForexDataConnector(source)


def create_multi_market_manager() -> MultiMarketDataManager:
    """Create multi-market data manager."""
    return MultiMarketDataManager()
