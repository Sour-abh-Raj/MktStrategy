import logging
import pandas as pd
import numpy as np
import time

logger = logging.getLogger(__name__)

def generate_synthetic_data(pair: str, years: int, timeframe: str = '1m', seed: int = 42) -> pd.DataFrame:
    """
    Generates realistic looking synthetic OHLCV data to simulate 5+ years of market data
    without hitting API limits or taking hours to download.
    """
    logger.info(f"Generating synthetic data for {pair} ({years} years, {timeframe})...")
    np.random.seed(seed)
    
    # 1 minute -> ~525,600 rows per year
    rows_per_year = 365 * 24 * 60
    total_rows = years * rows_per_year
    
    start_time = pd.Timestamp.utcnow() - pd.Timedelta(days=years*365)
    timestamps = pd.date_range(start=start_time, periods=total_rows, freq='min')
    
    # Simulate a geometric brownian motion for price
    mu = 0.00001
    sigma = 0.005 # per minute volatility
    
    returns = np.random.normal(loc=mu, scale=sigma, size=total_rows)
    # Starting price
    start_price = 50000 if 'BTC' in pair else 3000
    price_series = start_price * np.exp(np.cumsum(returns))
    
    # Build OHLCV
    close_price = price_series
    open_price = price_series.copy()
    open_price[1:] = close_price[:-1]
    
    # Add some noise for high/low
    high_price = np.maximum(open_price, close_price) * (1 + np.random.uniform(0, 0.002, total_rows))
    low_price = np.minimum(open_price, close_price) * (1 - np.random.uniform(0, 0.002, total_rows))
    
    volume = np.random.lognormal(mean=1, sigma=1, size=total_rows) * 100
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': open_price,
        'high': high_price,
        'low': low_price,
        'close': close_price,
        'volume': volume
    })
    
    logger.info(f"Generated {len(df)} rows of synthetic data for {pair}.")
    return df

def get_market_data(config: dict) -> dict:
    """
    Returns a dictionary mapping pair names to their DataFrame data.
    """
    data_config = config.get('data', {})
    pairs = data_config.get('pairs', ['BTC/USDT'])
    years = data_config.get('years', 5)
    timeframe = data_config.get('timeframe', '1m')
    use_synthetic = data_config.get('use_synthetic', True)
    
    data_dict = {}
    
    if use_synthetic:
        seed = data_config.get('seed', 42)
        for i, pair in enumerate(pairs):
            df = generate_synthetic_data(pair, years, timeframe, seed + i)
            data_dict[pair] = df
    else:
        for i, pair in enumerate(pairs):
            if pair == "BTC/USDT":
                logger.info(f"Loading local CSV for {pair}...")
                df = pd.read_csv('data/Bitcoin_4_6_2025-4_6_2026_historical_data_coinmarketcap.csv', sep=';')
                if 'timestamp' in df.columns:
                    df = df.drop(columns=['timestamp'])
                df = df.rename(columns={'timeOpen': 'timestamp'})
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp').reset_index(drop=True)
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                data_dict[pair] = df
            else:
                logger.warning(f"No local data for {pair}. Using synthetic.")
                data_dict[pair] = generate_synthetic_data(pair, years, timeframe, 42 + i)
            
    return data_dict

if __name__ == "__main__":
    import yaml
    with open('audit_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print("Testing data generation...")
    data = get_market_data(config)
    for p, df in data.items():
        print(f"{p}: {df.shape}")
