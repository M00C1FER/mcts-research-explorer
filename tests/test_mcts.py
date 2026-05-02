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


def test_ucb1_visited():
    """UCB1 for a visited node must be finite and positive."""
    from mcts_explorer import MCTSNode
    parent = MCTSNode(query="parent")
    parent.visits = 5

    child = MCTSNode(query="child", parent=parent)
    child.visits = 2
    child.avg_quality = 0.6

    score = child.ucb1
    assert math.isfinite(score)
    assert score > 0
    # Exploitation part
    expected_exploit = 0.6
    expected_explore = 1.414 * math.sqrt(math.log(5) / 2)
    assert abs(score - (expected_exploit + expected_explore)) < 1e-9


def test_ucb1_custom_c():
    """Exploration constant stored on node is used by ucb1."""
    from mcts_explorer import MCTSNode
    parent = MCTSNode(query="parent")
    parent.visits = 4

    node = MCTSNode(query="child", parent=parent, c=2.0)
    node.visits = 1
    node.avg_quality = 0.5

    score = node.ucb1
    expected = 0.5 + 2.0 * math.sqrt(math.log(4) / 1)
    assert abs(score - expected) < 1e-9


def test_explorer_dry_run():
    from mcts_explorer import MCTSResearchExplorer
    def mock_fetcher(query):
        return [{"title": "Result", "url": "https://example.com", "score": 0.8}]
    explorer = MCTSResearchExplorer(fetcher=mock_fetcher, max_iterations=3)
    result = explorer.explore("test topic")
    assert result is not None
    assert result["queries_explored"] >= 1


def test_backprop_avg_quality_bounded():
    """avg_quality must stay in [0, 1] even with many results per node."""
    from mcts_explorer import MCTSResearchExplorer

    call_count = [0]

    def multi_result_search(query):
        # Return 5 results each with high authority (score ~0.8)
        call_count[0] += 1
        return [
            {"url": f"https://arxiv.org/abs/{i}{call_count[0]}",
             "title": f"Paper {i}",
             "content": "x" * 600}
            for i in range(5)
        ]

    explorer = MCTSResearchExplorer(search_fn=multi_result_search,
                                    max_nodes=10, max_depth=2)
    results = explorer.explore("multi result topic", budget=5)

    for node in explorer._all_nodes():
        assert node.avg_quality <= 1.0, (
            f"avg_quality {node.avg_quality:.3f} > 1.0 on node '{node.query}'"
        )


def test_explorer_all_branches_dead_end():
    """When all nodes are pruned / return no results, explore() must terminate."""
    from mcts_explorer import MCTSResearchExplorer

    def empty_search(query):
        return []  # Never returns results → quality stays 0 → pruned

    explorer = MCTSResearchExplorer(
        search_fn=empty_search,
        max_nodes=20,
        prune_threshold=0.40,
    )
    # Should not hang; budget acts as hard cap
    result = explorer.explore("dead end topic", budget=5)
    assert result is not None
    assert result["sources_found"] == 0


def test_exploration_constant_propagates():
    """MCTSResearchExplorer passes exploration_constant to every new node."""
    from mcts_explorer import MCTSResearchExplorer

    def stub_search(query):
        return [{"url": "https://example.com/a", "title": "A", "content": ""}]

    explorer = MCTSResearchExplorer(
        search_fn=stub_search,
        exploration_constant=2.5,
        max_nodes=10,
        max_depth=1,
    )
    explorer.explore("test", budget=3)

    for node in explorer._all_nodes():
        assert node.c == 2.5, f"Node '{node.query}' has c={node.c}, expected 2.5"


def test_no_search_fn_raises():
    """Constructing explorer without search_fn or fetcher raises ValueError."""
    from mcts_explorer import MCTSResearchExplorer
    with pytest.raises(ValueError, match="search_fn or fetcher"):
        MCTSResearchExplorer()
