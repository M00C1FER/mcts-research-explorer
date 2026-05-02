"""
mcts-explorer — MCTS-guided research query exploration.

Exports the main public API.
"""

from .explorer import MCTSNode, MCTSResearchExplorer

__all__ = ["MCTSNode", "MCTSResearchExplorer"]
__version__ = "1.0.0"
