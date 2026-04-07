"""
Parameter Optimization Module

Advanced hyperparameter optimization using:
- Bayesian optimization concepts
- Genetic parameter tuning
- Adaptive parameter search
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Tuple
from datetime import datetime
import random
import math


@dataclass
class ParameterSpace:
    """Defines parameter search space."""
    name: str
    min_value: float
    max_value: float
    step: float = None  # If None, continuous
    
    def sample(self) -> float:
        """Sample a random value within the space."""
        if self.step:
            steps = int((self.max_value - self.min_value) / self.step)
            return self.min_value + random.randint(0, steps) * self.step
        return random.uniform(self.min_value, self.max_value)


@dataclass
class OptimizedParameters:
    """Result of parameter optimization."""
    parameters: Dict[str, float]
    objective_value: float  # Sharpe or similar
    iterations: int
    convergence: bool
    timestamp: str = field(default_factory=datetime.now().isoformat)


@dataclass
class OptimizationResult:
    """Complete optimization result."""
    strategy_id: str
    best_parameters: Dict[str, float]
    best_objective: float
    objective_history: List[float]
    convergence_iteration: int
    
    # Sensitivity analysis
    parameter_sensitivity: Dict[str, float]  # How sensitive each param is


class ParameterOptimizer:
    """
    Advanced parameter optimization using multiple methods.
    
    Methods:
    - Bayesian-style optimization
    - Genetic parameter tuning
    - Grid search with adaptive sampling
    """
    
    def __init__(
        self,
        max_iterations: int = 100,
        population_size: int = 20,
    ) -> None:
        self.max_iterations = max_iterations
        self.population_size = population_size
    
    def optimize(
        self,
        strategy_id: str,
        parameter_spaces: Dict[str, ParameterSpace],
        objective_fn: Callable[[Dict[str, float]], float],
    ) -> OptimizationResult:
        """
        Optimize parameters to maximize objective function.
        
        Args:
            strategy_id: Strategy to optimize
            parameter_spaces: Dict of parameter name -> space
            objective_fn: Function that takes params and returns score (e.g., Sharpe)
            
        Returns:
            OptimizationResult with best parameters
        """
        param_names = list(parameter_spaces.keys())
        
        # Track history
        objective_history = []
        best_objective = -float('inf')
        best_params = {}
        
        # Initialize population
        population = []
        for _ in range(self.population_size):
            params = {name: space.sample() for name, space in parameter_spaces.items()}
            population.append(params)
        
        convergence_count = 0
        
        for iteration in range(self.max_iterations):
            # Evaluate population
            results = []
            for params in population:
                obj = objective_fn(params)
                results.append((params, obj))
                objective_history.append(obj)
                
                if obj > best_objective:
                    best_objective = obj
                    best_params = params.copy()
            
            # Sort by objective
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Check convergence
            if iteration > 10:
                recent_avg = sum(objective_history[-10:]) / 10
                older_avg = sum(objective_history[-20:-10]) / 10
                if abs(recent_avg - older_avg) < 0.01:
                    convergence_count += 1
                else:
                    convergence_count = 0
            
            # Selection - keep top performers
            elite_count = max(2, self.population_size // 4)
            elite = [r[0] for r in results[:elite_count]]
            
            # Generate new population via crossover and mutation
            new_population = list(elite)
            
            while len(new_population) < self.population_size:
                # Crossover
                if random.random() < 0.7 and len(elite) >= 2:
                    parent1, parent2 = random.sample(elite, 2)
                    child = self._crossover(parent1, parent2, param_names)
                else:
                    child = random.choice(elite).copy()
                
                # Mutation
                if random.random() < 0.3:
                    child = self._mutate(child, parameter_spaces)
                
                new_population.append(child)
            
            population = new_population
        
        # Sensitivity analysis
        sensitivity = self._analyze_sensitivity(
            best_params, parameter_spaces, objective_fn
        )
        
        return OptimizationResult(
            strategy_id=strategy_id,
            best_parameters=best_params,
            best_objective=best_objective,
            objective_history=objective_history,
            convergence_iteration=convergence_count,
            parameter_sensitivity=sensitivity,
        )
    
    def _crossover(
        self,
        parent1: Dict[str, float],
        parent2: Dict[str, float],
        param_names: List[str],
    ) -> Dict[str, float]:
        """Perform crossover between two parameter sets."""
        child = {}
        for name in param_names:
            if random.random() < 0.5:
                child[name] = parent1[name]
            else:
                child[name] = parent2[name]
        return child
    
    def _mutate(
        self,
        params: Dict[str, float],
        spaces: Dict[str, ParameterSpace],
    ) -> Dict[str, float]:
        """Mutate parameters within their spaces."""
        mutated = params.copy()
        
        # Pick random parameter to mutate
        name = random.choice(list(spaces.keys()))
        space = spaces[name]
        
        # Mutate by small amount
        current = params[name]
        range_size = space.max_value - space.min_value
        
        if random.random() < 0.5:
            mutated[name] = min(space.max_value, current + range_size * random.uniform(0.1, 0.3))
        else:
            mutated[name] = max(space.min_value, current - range_size * random.uniform(0.1, 0.3))
        
        return mutated
    
    def _analyze_sensitivity(
        self,
        best_params: Dict[str, float],
        spaces: Dict[str, ParameterSpace],
        objective_fn: Callable[[Dict[str, float]], float],
    ) -> Dict[str, float]:
        """Analyze parameter sensitivity."""
        sensitivity = {}
        base_objective = objective_fn(best_params)
        
        for name, value in best_params.items():
            space = spaces[name]
            range_size = space.max_value - space.min_value
            
            if range_size == 0:
                sensitivity[name] = 0.0
                continue
            
            # Test sensitivity: vary parameter by ±20%
            test_params = best_params.copy()
            test_params[name] = value * 1.2
            obj_high = objective_fn(test_params)
            
            test_params[name] = value * 0.8
            obj_low = objective_fn(test_params)
            
            # Sensitivity = change in objective per unit change in parameter
            obj_change = max(obj_high, obj_low) - base_objective
            sensitivity[name] = abs(obj_change) / (range_size * 0.4)
        
        return sensitivity
    
    def quick_optimize(
        self,
        strategy_id: str,
        params: Dict[str, Tuple[float, float]],
        objective_fn: Callable,
    ) -> OptimizedParameters:
        """
        Quick optimization with simple ranges.
        
        Args:
            strategy_id: Strategy to optimize
            params: Dict of param name -> (min, max) tuple
            objective_fn: Function returning score
            
        Returns:
            OptimizedParameters with best found
        """
        spaces = {
            name: ParameterSpace(name, min_val, max_val)
            for name, (min_val, max_val) in params.items()
        }
        
        result = self.optimize(strategy_id, spaces, objective_fn)
        
        return OptimizedParameters(
            parameters=result.best_parameters,
            objective_value=result.best_objective,
            iterations=self.max_iterations,
            convergence=result.convergence_iteration > 5,
        )


class AdaptiveParameterSearch:
    """
    Adaptive parameter search that adjusts based on market conditions.
    
    Tracks regime changes and adapts parameters accordingly.
    """
    
    def __init__(self) -> None:
        self.regime_parameters: Dict[str, Dict[str, float]] = {}
        self.current_regime: str = "neutral"
    
    def update_regime(self, regime: str) -> None:
        """Update current market regime."""
        self.current_regime = regime
    
    def get_parameters(self, strategy_id: str) -> Dict[str, float]:
        """Get best parameters for current regime."""
        if self.current_regime in self.regime_parameters:
            return self.regime_parameters[self.current_regime].get(strategy_id, {})
        return {}
    
    def store_parameters(
        self,
        strategy_id: str,
        regime: str,
        parameters: Dict[str, float],
        performance: float,
    ) -> None:
        """Store parameters for a regime."""
        if regime not in self.regime_parameters:
            self.regime_parameters[regime] = {}
        
        # Only store if better than existing
        existing = self.regime_parameters[regime].get(strategy_id, {})
        if not existing or performance > existing.get("_performance", 0):
            parameters["_performance"] = performance
            self.regime_parameters[regime][strategy_id] = parameters


def create_parameter_optimizer(
    max_iterations: int = 100,
    population_size: int = 20,
) -> ParameterOptimizer:
    """Create parameter optimizer."""
    return ParameterOptimizer(max_iterations, population_size)
