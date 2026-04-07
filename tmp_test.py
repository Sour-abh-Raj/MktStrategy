import yaml
import traceback
from scripts.download_market_data import get_market_data
from freqtrade_project.pipeline import AdaptiveTradingSystem, CycleInput

with open('audit_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

print("Getting market data...")
try:
    data = get_market_data(config)
    df = data['BTC/USDT']

    print("Running single cycle with 60 rows...")
    system = AdaptiveTradingSystem()

    window = []
    for i in range(60):
        row = df.iloc[i].to_dict()
        row['timestamp'] = row['timestamp'].timestamp()
        window.append(row)

    cycle = CycleInput(
        pair="BTC/USDT",
        timeframe="1d",
        raw_rows=window,
        tf_scores={"1m": 0.8, "5m": 0.6, "1h": 0.2},
        stress_metrics={"portfolio_drawdown": 0.05, "api_errors": 0},
        equity=10000.0
    )

    import pprint
    resp = system.run_cycle(cycle)
    pprint.pprint(resp)
except Exception as e:
    traceback.print_exc()
