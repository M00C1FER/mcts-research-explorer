"""Smoke tests for mcts-explorer."""
import math
import pytest


def test_import():
    from mcts_explorer import MCTSNode, MCTSResearchExplorer
    assert MCTSNode is not None
    assert MCTSResearchExplorer is not None


def test_node_creation():
    from mcts_explorer import MCTSNode
    node = MCTSNode(query="test query")
    assert node.query == "test query"
    assert node.visits == 0
    assert node.depth == 0
    assert node.children == []


def test_ucb1_unvisited():
    from mcts_explorer import MCTSNode
    node = MCTSNode(query="unvisited")
    assert node.ucb1 == math.inf


def test_explorer_dry_run():
    from mcts_explorer import MCTSResearchExplorer
    def mock_fetcher(query):
        return [{"title": "Result", "url": "https://example.com", "score": 0.8}]
    explorer = MCTSResearchExplorer(fetcher=mock_fetcher, max_iterations=3)
    result = explorer.explore("test topic")
    assert result is not None
    assert result["queries_explored"] >= 1
