"""
Meta-Portfolio AI Layer

Modules:
- meta_portfolio_ai.py: Core AI allocation model
- portfolio_controller.py: Controller for coordination
"""

from freqtrade_project.meta_portfolio_layer.meta_portfolio_ai import (
    ClusterState,
    AllocationDecision,
    MetaPortfolioMetrics,
    ClusterFeatureExtractor,
    MetaPortfolioAI,
    create_cluster_feature_extractor,
    create_meta_portfolio_ai,
)

from freqtrade_project.meta_portfolio_layer.portfolio_controller import (
    MetaPortfolioDecision,
    ResearchFeedback,
    MetaPortfolioController,
    create_meta_portfolio_controller,
)

__all__ = [
    # Core AI
    "ClusterState",
    "AllocationDecision",
    "MetaPortfolioMetrics",
    "ClusterFeatureExtractor",
    "MetaPortfolioAI",
    "create_cluster_feature_extractor",
    "create_meta_portfolio_ai",
    
    # Controller
    "MetaPortfolioDecision",
    "ResearchFeedback",
    "MetaPortfolioController",
    "create_meta_portfolio_controller",
]
