"""
Strategy Configuration Loader

Loads strategy configurations from YAML and provides
a clean interface for strategy registration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional
import yaml


@dataclass
class StrategyConfig:
    """Configuration for a single strategy."""
    strategy_id: str
    regime: str
    description: str
    parameters: Dict[str, float]
    enabled: bool = True


@dataclass
class DefaultsConfig:
    """Default configuration values."""
    min_trades_for_ranking: int = 20
    min_sharpe: float = 0.5
    max_drawdown_limit: float = 0.25
    default_stop_loss: float = 0.05
    default_take_profit: float = 0.10
    default_position_size: float = 0.10


class StrategyConfigLoader:
    """Loads and manages strategy configurations."""
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        if config_path is None:
            # Default to config/strategies.yaml in the project
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(base_dir, "config", "strategies.yaml")
        
        self.config_path = config_path
        self._strategies: Dict[str, StrategyConfig] = {}
        self._defaults: DefaultsConfig = DefaultsConfig()
        self._load()
    
    def _load(self) -> None:
        """Load configuration from YAML file."""
        if not os.path.exists(self.config_path):
            # Create default config file
            self._create_default_config()
            return
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if not config:
            return
        
        # Load strategies
        for strat in config.get('strategies', []):
            self._strategies[strat['strategy_id']] = StrategyConfig(
                strategy_id=strat['strategy_id'],
                regime=strat['regime'],
                description=strat.get('description', ''),
                parameters=strat.get('parameters', {}),
                enabled=strat.get('enabled', True),
            )
        
        # Load defaults
        defaults = config.get('defaults', {})
        self._defaults = DefaultsConfig(
            min_trades_for_ranking=defaults.get('min_trades_for_ranking', 20),
            min_sharpe=defaults.get('min_sharpe', 0.5),
            max_drawdown_limit=defaults.get('max_drawdown_limit', 0.25),
            default_stop_loss=defaults.get('default_stop_loss', 0.05),
            default_take_profit=defaults.get('default_take_profit', 0.10),
            default_position_size=defaults.get('default_position_size', 0.10),
        )
    
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        default_config = """
# Strategy Configuration
strategies: []

defaults:
  min_trades_for_ranking: 20
  min_sharpe: 0.5
  max_drawdown_limit: 0.25
  default_stop_loss: 0.05
  default_take_profit: 0.10
  default_position_size: 0.10
"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            f.write(default_config)
    
    def get_strategy(self, strategy_id: str) -> Optional[StrategyConfig]:
        """Get configuration for a specific strategy."""
        return self._strategies.get(strategy_id)
    
    def get_strategies_for_regime(self, regime: str) -> List[StrategyConfig]:
        """Get all strategies for a specific regime."""
        return [
            s for s in self._strategies.values()
            if s.regime == regime and s.enabled
        ]
    
    def get_all_strategies(self) -> List[StrategyConfig]:
        """Get all enabled strategies."""
        return [s for s in self._strategies.values() if s.enabled]
    
    def get_enabled_strategy_ids(self) -> List[str]:
        """Get IDs of all enabled strategies."""
        return [s.strategy_id for s in self._strategies.values() if s.enabled]
    
    def get_defaults(self) -> DefaultsConfig:
        """Get default configuration values."""
        return self._defaults
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._strategies.clear()
        self._load()
    
    def add_strategy(self, config: StrategyConfig) -> None:
        """Add or update a strategy configuration."""
        self._strategies[config.strategy_id] = config
    
    def remove_strategy(self, strategy_id: str) -> bool:
        """Remove a strategy configuration."""
        if strategy_id in self._strategies:
            del self._strategies[strategy_id]
            return True
        return False
    
    def save(self) -> None:
        """Save current configuration to file."""
        config = {
            'strategies': [
                {
                    'strategy_id': s.strategy_id,
                    'regime': s.regime,
                    'description': s.description,
                    'parameters': s.parameters,
                    'enabled': s.enabled,
                }
                for s in self._strategies.values()
            ],
            'defaults': {
                'min_trades_for_ranking': self._defaults.min_trades_for_ranking,
                'min_sharpe': self._defaults.min_sharpe,
                'max_drawdown_limit': self._defaults.max_drawdown_limit,
                'default_stop_loss': self._defaults.default_stop_loss,
                'default_take_profit': self._defaults.default_take_profit,
                'default_position_size': self._defaults.default_position_size,
            }
        }
        
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)


# Singleton instance
_config_loader: Optional[StrategyConfigLoader] = None


def get_strategy_config() -> StrategyConfigLoader:
    """Get the strategy configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = StrategyConfigLoader()
    return _config_loader
