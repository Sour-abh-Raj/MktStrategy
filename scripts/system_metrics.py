import psutil
import time
import logging
from threading import Thread

logger = logging.getLogger(__name__)

class SystemMetricsMonitor:
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.is_running = False
        self.metrics = []
        self._thread = None
        
    def _monitor_loop(self):
        while self.is_running:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            
            self.metrics.append({
                "timestamp": time.time(),
                "cpu_percent": cpu,
                "memory_percent": mem
            })
            time.sleep(self.interval)
            
    def start(self):
        self.is_running = True
        # prime psutil cpu percent
        psutil.cpu_percent(interval=None)
        self._thread = Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("System metrics monitor started.")
        
    def stop(self):
        self.is_running = False
        if self._thread:
            self._thread.join()
        logger.info("System metrics monitor stopped.")
        return self.metrics

def get_snapshot():
    return {
        "cpu": psutil.cpu_percent(interval=0.1),
        "memory": psutil.virtual_memory().percent
    }
