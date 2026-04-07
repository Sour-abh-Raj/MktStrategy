"""
Hierarchical Alpha Architecture

Modules:
- cluster_manager.py: Alpha cluster organization and classification
- hierarchical_allocation.py: Two-stage capital allocation
- cluster_monitoring.py: Cluster monitoring and research guidance
"""

from freqtrade_project.hierarchical_alpha.cluster_manager import (
    AlphaClusterType,
    AlphaCluster,
    ClusterMetrics,
    ClusterAllocation,
    StrategyClassification,
    AlphaClusterManager,
    create_cluster_manager,
)

from freqtrade_project.hierarchical_alpha.hierarchical_allocation import (
    HierarchicalAllocation,
    HierarchicalAllocator,
    ClusterRiskController,
    create_hierarchical_allocator,
)

from freqtrade_project.hierarchical_alpha.cluster_monitoring import (
    ClusterAlert,
    ResearchGuidance,
    ClusterDashboard,
    ClusterMonitor,
    ResearchGuidanceEngine,
    CrossClusterStressTester,
    create_cluster_monitor,
    create_research_guidance_engine,
    create_stress_tester,
)

__all__ = [
    # Cluster types
    "AlphaClusterType",
    
    # Cluster management
    "AlphaCluster",
    "ClusterMetrics",
    "ClusterAllocation",
    "StrategyClassification",
    "AlphaClusterManager",
    "create_cluster_manager",
    
    # Hierarchical allocation
    "HierarchicalAllocation",
    "HierarchicalAllocator",
    "ClusterRiskController",
    "create_hierarchical_allocator",
    
    # Monitoring
    "ClusterAlert",
    "ResearchGuidance",
    "ClusterDashboard",
    "ClusterMonitor",
    "ResearchGuidanceEngine",
    "CrossClusterStressTester",
    "create_cluster_monitor",
    "create_research_guidance_engine",
    "create_stress_tester",
]
