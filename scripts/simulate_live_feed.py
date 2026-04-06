import logging
import time
import random
import numpy as np
from typing import List, Dict
from freqtrade_project.pipeline import AdaptiveTradingSystem, CycleInput

logger = logging.getLogger(__name__)

def simulate_latency(mean_ms: float, packet_loss_prob: float) -> bool:
    """
    Sleeps for a random duration centered around mean_ms.
    Returns True if packet was lost, False otherwise.
    """
    if random.random() < packet_loss_prob:
        return True
    
    latency = max(5, np.random.normal(mean_ms, mean_ms/4))
    time.sleep(latency / 1000.0)
    return False

def run_realtime_simulation(config: dict) -> List[Dict]:
    """
    Simulates a live feed loop, processing ticks and logging adaptation latencies.
    """
    rt_config = config.get('real_time', {})
    sim_duration = rt_config.get('simulation_duration_seconds', 10)
    loss_prob = rt_config.get('packet_loss_probability', 0.05)
    mean_latency = rt_config.get('mean_latency_ms', 100)
    target_window_ms = rt_config.get('adaptation_target_window_ms', 2000)
    
    logger.info(f"Starting real-time simulation for {sim_duration}s...")
    system = AdaptiveTradingSystem()
    
    start_time = time.time()
    events = []
    tick_count = 0
    packet_drops = 0
    
    # Mock data window
    window = [{"timestamp": time.time(), "close": 50000 + i, "volume": 100} for i in range(30)]
    
    while time.time() - start_time < sim_duration:
        tick_start = time.time()
        tick_count += 1
        
        # 1. Simulate network arriving tick
        is_lost = simulate_latency(mean_latency, loss_prob)
        if is_lost:
            packet_drops += 1
            logger.debug("Simulated packet drop.")
            continue
            
        # Update window
        window.pop(0)
        window.append({"timestamp": time.time(), "close": 50000 + random.random()*10, "volume": 100})
        
        # 2. Process through pipeline
        pipeline_start = time.time()
        try:
            cycle = CycleInput(
                pair="BTC/USDT",
                timeframe="1m",
                raw_rows=window,
                tf_scores={"1m": 0.8},
                stress_metrics={"portfolio_drawdown": 0.0, "api_errors": 0},
                equity=10000.0
            )
            response = system.run_cycle(cycle)
            success = response.get('success', False)
        except Exception as e:
            logger.error(f"Pipeline error in RT sim: {e}")
            success = False
            
        pipeline_end = time.time()
        pipeline_latency_ms = (pipeline_end - pipeline_start) * 1000
        total_latency_ms = (pipeline_end - tick_start) * 1000
        
        events.append({
            "tick": tick_count,
            "success": success,
            "pipeline_latency_ms": pipeline_latency_ms,
            "total_latency_ms": total_latency_ms,
            "target_met": total_latency_ms <= target_window_ms,
            "loss": random.uniform(0.1, 0.5), # Mock convergence loss
            "kl_divergence": random.uniform(0.01, 0.1),
            "batch_size": 32,
            "learning_rate": 1e-4
        })
        
    logger.info(f"Simulation completed. {tick_count} ticks, {packet_drops} drops.")
    return events
