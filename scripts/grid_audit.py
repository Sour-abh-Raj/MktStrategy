import argparse
import yaml
import logging
import sys
import pandas as pd
from scripts.download_market_data import get_market_data
from scripts.run_backtests import run_backtest
from scripts.simulate_live_feed import run_realtime_simulation
from scripts.system_metrics import SystemMetricsMonitor
from scripts.generate_dashboard import generate_dashboard

def setup_logging(level, verbose):
    if verbose:
        level = logging.DEBUG
    elif level:
        level = getattr(logging, level.upper(), logging.INFO)
    else:
        level = logging.INFO
        
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def main():
    parser = argparse.ArgumentParser(description="Grid Audit CLI Tool")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug logging")
    parser.add_argument("--log-level", type=str, help="Set log level (INFO, DEBUG, WARNING, ERROR)")
    parser.add_argument("--output", type=str, help="Override output directory for dashboard and reports")
    
    args = parser.parse_args()
    setup_logging(args.log_level, args.verbose)
    logger = logging.getLogger("grid_audit")
    
    logger.info(f"Starting audit using config: {args.config}")
    
    try:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
        
    output_dash = args.output + "/dashboard.html" if args.output else config.get('logging', {}).get('dashboard_output', 'dashboard.html')
    
    # Start system metrics collection
    monitor = SystemMetricsMonitor(interval=0.5)
    monitor.start()
    
    try:
        # 1. Download / Generate Data
        logger.info("--- Phase 1: Market Data Generation ---")
        market_data = get_market_data(config)
        
        # 2. Run Backtests
        logger.info("--- Phase 2: System Strategy Backtests ---")
        bt_results = run_backtest(config, market_data)
        
        # 3. Simulate Live Feed
        logger.info("--- Phase 3: Real-Time Live Feed Simulation ---")
        rt_events = run_realtime_simulation(config)
        
    finally:
        sys_metrics = monitor.stop()
        
    # 4. Generate Dashboard
    logger.info("--- Phase 4: Generating Dashboards ---")
    generate_dashboard(bt_results, rt_events, sys_metrics, output_dash)
    
    # 5. Output Summary Table
    print("\n" + "="*50)
    print("                AUDIT SUMMARY TABLE                ")
    print("="*50)
    
    df_bt = pd.DataFrame(bt_results).T
    if not df_bt.empty:
        df_bt['total_return'] = df_bt['total_return'].map('{:.2%}'.format)
        df_bt['max_drawdown'] = df_bt['max_drawdown'].map('{:.2%}'.format)
        df_bt['sharpe_ratio'] = df_bt['sharpe_ratio'].map('{:.2f}'.format)
        print("Strategy Backtest Performance:")
        print(df_bt.to_string())
    
    if rt_events:
        df_rt = pd.DataFrame(rt_events)
        avg_latency = df_rt['total_latency_ms'].mean()
        max_latency = df_rt['total_latency_ms'].max()
        success = df_rt['success'].mean() * 100
        print("\nReal-Time Adaptation Metrics:")
        print(f"  Average Pipeline Latency:  {avg_latency:.2f} ms")
        print(f"  Maximum Pipeline Latency:  {max_latency:.2f} ms")
        print(f"  System Success Rate:       {success:.1f}%")
        
    
    report_output = config.get('logging', {}).get('report_output', 'audit_report.md')
    report_str = "\n## Grid Audit CLI Run Results\n```text\n"
    report_str += "Strategy Backtest Performance:\n" + df_bt.to_string() + "\n\n"
    if rt_events:
        report_str += "Real-Time Adaptation Metrics:\n"
        report_str += f"  Average Pipeline Latency:  {avg_latency:.2f} ms\n"
        report_str += f"  Maximum Pipeline Latency:  {max_latency:.2f} ms\n"
        report_str += f"  System Success Rate:       {success:.1f}%\n"
    report_str += "```\n"

    try:
        with open(report_output, "a") as f:
            f.write(report_str)
        print(f"\nAppended results back into {report_output}")
    except Exception as e:
        logger.error(f"Could not write to report file: {e}")

    print(f"\nDashboard generated at: {output_dash}")
    print("="*50)
    
if __name__ == "__main__":
    main()
