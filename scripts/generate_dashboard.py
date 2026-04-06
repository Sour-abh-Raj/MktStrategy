import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def generate_dashboard(backtest_results: dict, rt_events: list, sys_metrics: list, output_path: str = "dashboard.html"):
    """
    Generates an interactive HTML dashboard containing:
    1. Strategy performance metrics (Returns, Sharpe, Drawdown)
    2. System resource usage (CPU/Memory)
    3. RT Adaptation metrics (Latency, KL Divergence over time)
    """
    logger.info("Generating interactive dashboard...")
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            "Strategy Returns (%)", "Max Drawdown (%)", 
            "System CPU/Memory Usage", "RT Pipeline Latency (ms)",
            "Adaptation Loss", "Real-Time Success Rate"
        ),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "scatter"}, {"type": "scatter"}],
               [{"type": "scatter"}, {"type": "indicator"}]]
    )
    
    # 1. Backtest Results
    pairs = list(backtest_results.keys())
    returns = [res['total_return']*100 for res in backtest_results.values()]
    drawdowns = [res['max_drawdown']*100 for res in backtest_results.values()]
    
    ret_text = [f"{v:.2f}%" for v in returns]
    dd_text = [f"{v:.2f}%" for v in drawdowns]
    
    fig.add_trace(go.Bar(x=pairs, y=returns, name="Total Return", marker_color='green', text=ret_text, textposition='auto'), row=1, col=1)
    fig.add_trace(go.Bar(x=pairs, y=drawdowns, name="Max Drawdown", marker_color='red', text=dd_text, textposition='auto'), row=1, col=2)
    
    # 2. System Metrics
    if sys_metrics:
        df_sys = pd.DataFrame(sys_metrics)
        # normalize timestamps
        df_sys['time_offset'] = df_sys['timestamp'] - df_sys['timestamp'].iloc[0]
        fig.add_trace(go.Scatter(x=df_sys['time_offset'], y=df_sys['cpu_percent'], name="CPU %", line=dict(color='blue')), row=2, col=1)
        fig.add_trace(go.Scatter(x=df_sys['time_offset'], y=df_sys['memory_percent'], name="Mem %", line=dict(color='orange')), row=2, col=1)

    # 3. RT Adaptation Metrics
    if rt_events:
        df_rt = pd.DataFrame(rt_events)
        fig.add_trace(go.Scatter(x=df_rt['tick'], y=df_rt['total_latency_ms'], name="Total Latency", line=dict(color='purple')), row=2, col=2)
        fig.add_trace(go.Scatter(x=df_rt['tick'], y=df_rt['loss'], name="Convergence Loss", line=dict(color='brown')), row=3, col=1)
        
        success_rate = df_rt['success'].mean() * 100
        fig.add_trace(go.Indicator(
            mode = "number+gauge",
            value = success_rate,
            title = {"text": "Success Rate (%)"},
            gauge = {'axis': {'range': [None, 100]},
                     'bar': {'color': "darkblue"}}
        ), row=3, col=2)
    
    # Update layout
    fig.update_layout(height=1000, width=1200, title_text="Adaptive Trading System Audit Dashboard", showlegend=True)
    
    # Save
    fig.write_html(output_path)
    logger.info(f"Dashboard saved to {output_path}")

if __name__ == "__main__":
    # Test generation with dummy data
    generate_dashboard(
        {"BTC/USDT": {"total_return": 0.5, "max_drawdown": 0.1}, "ETH/USDT": {"total_return": 0.6, "max_drawdown": 0.15}},
        [{"tick": 1, "total_latency_ms": 150, "loss": 0.5, "success": True}],
        [{"timestamp": 0, "cpu_percent": 10, "memory_percent": 50}],
        "test_dashboard.html"
    )
