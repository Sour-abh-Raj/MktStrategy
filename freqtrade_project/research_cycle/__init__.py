"""
Research Cycle - Autonomous Strategy Discovery & Validation

Modules:
- controller.py: Research cycle controller and orchestration
"""

from freqtrade_project.research_cycle.controller import (
    ResearchCycleController,
    ResearchConfig,
    ResearchResult,
    ResearchMetrics,
    BacktestResult,
    get_research_controller,
)

__all__ = [
    "ResearchCycleController",
    "ResearchConfig",
    "ResearchResult",
    "ResearchMetrics", 
    "BacktestResult",
    "get_research_controller",
]
