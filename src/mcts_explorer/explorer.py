"""
MCTS Research Explorer
======================
Monte Carlo Tree Search for research query exploration.

Instead of linear search iteration, explores a TREE of queries:
  - Each node = a search query + its results + quality score
  - Children = refined/related queries generated from parent results
  - UCB1 selection balances explore (novel) vs exploit (high-quality)
  - CRAAP scores flow via backpropagation

Inspired by:
  - SWE-Search (MCTS for software engineering agents)
  - Perplexity's Test Time Compute framework
  - STORM's multi-perspective exploration
"""

import math
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MCTSNode:
    """A node in the research exploration tree."""
    query: str
    parent: Optional['MCTSNode'] = field(default=None, repr=False)
    children: List['MCTSNode'] = field(default_factory=list, repr=False)

    # Search results
    results: List[Dict[str, Any]] = field(default_factory=list, repr=False)
    result_count: int = 0

    # MCTS statistics
    visits: int = 0
    quality_sum: float = 0.0  # Sum of CRAAP scores from this node's own results
    avg_quality: float = 0.0  # Weighted-average quality for UCB1 / pruning

    # Metadata
    depth: int = 0
    expanded: bool = False
    pruned: bool = False

    # Exploration constant — set by MCTSResearchExplorer at node-creation time.
    # Stored per-node so UCB1 requires no external reference.
    c: float = field(default=1.414, repr=False)

    @property
    def ucb1(self) -> float:
        """Upper Confidence Bound 1 score for node selection.

        Returns +inf for unvisited nodes so they are always selected first.
        Uses ``max(parent_visits, 1)`` to guard against log(0) when the parent
        itself has not yet been visited.
        """
        if self.visits == 0:
            return float('inf')  # Unexplored nodes have infinite priority
        parent_visits = self.parent.visits if self.parent else self.visits
        exploitation = self.avg_quality
        exploration = self.c * math.sqrt(math.log(max(parent_visits, 1)) / self.visits)
        return exploitation + exploration


class MCTSResearchExplorer:
    """
    MCTS-guided research query exploration.

    Usage:
        explorer = MCTSResearchExplorer(
            search_fn=my_search_function,
            expand_fn=my_query_generator,
            max_nodes=200,
            max_depth=4
        )
        results = explorer.explore("topic", budget=50)
    """

    def __init__(
        self,
        search_fn: Optional[Callable[[str], List[Dict[str, Any]]]] = None,
        expand_fn: Optional[Callable[[str, List[Dict]], List[str]]] = None,
        score_fn: Optional[Callable[[Dict[str, Any]], float]] = None,
        max_nodes: int = 200,
        max_depth: int = 4,
        prune_threshold: float = 0.40,
        fetcher: Optional[Callable[[str], List[Dict[str, Any]]]] = None,
        max_iterations: Optional[int] = None,
        exploration_constant: float = 1.414,
    ):
        """
        Args:
            search_fn: Function(query) -> List[results]. Executes search.
            fetcher: Alias for search_fn (convenience parameter).
            expand_fn: Function(query, results) -> List[new_queries]. Generates child queries.
                       If None, uses simple keyword expansion.
            score_fn: Function(result) -> float. Scores result quality (CRAAP).
                      If None, uses default heuristic.
            max_nodes: Maximum nodes in tree (RAM bound).
            max_depth: Maximum tree depth.
            prune_threshold: Nodes with avg_quality below this are pruned.
            max_iterations: Default budget for explore() when budget not specified.
            exploration_constant: UCB1 exploration weight C (default sqrt(2) ≈ 1.414).
                Higher values favour exploration; lower values favour exploitation.
        """
        if search_fn is None and fetcher is not None:
            search_fn = fetcher
        if search_fn is None:
            raise ValueError("search_fn or fetcher must be provided")
        self.search_fn = search_fn
        self._default_budget: int = max_iterations if max_iterations is not None else 50
        self.expand_fn = expand_fn or self._default_expand
        self.score_fn = score_fn or self._default_score
        self.max_nodes = max_nodes
        self.max_depth = max_depth
        self.prune_threshold = prune_threshold
        self.exploration_constant = exploration_constant

        self.root: Optional[MCTSNode] = None
        self.node_count = 0
        self.all_results: List[Dict[str, Any]] = []
        self.seen_urls: set = set()
        self.seen_queries: set = set()

    def explore(self, topic: str, budget: Optional[int] = None,
                initial_queries: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run MCTS exploration on a topic.

        Args:
            topic: Root research topic
            budget: Number of search iterations (each = 1 node expansion)
            initial_queries: Optional pre-generated queries for Level 1

        Returns:
            {
                "results": List[Dict],  # All unique results, CRAAP-scored
                "tree_stats": {...},    # Tree statistics
                "queries_explored": int,
                "sources_found": int,
                "avg_quality": float,
            }
        """
        start = time.monotonic()
        if budget is None:
            budget = self._default_budget

        # Initialize root
        self.root = MCTSNode(query=topic, depth=0, c=self.exploration_constant)
        self.node_count = 1
        self.seen_queries.add(topic.lower())

        # Create Level 1 children from initial queries or topic
        if initial_queries:
            for q in initial_queries:
                if q.lower() not in self.seen_queries:
                    child = MCTSNode(query=q, parent=self.root, depth=1,
                                     c=self.exploration_constant)
                    self.root.children.append(child)
                    self.node_count += 1
                    self.seen_queries.add(q.lower())

        # Main MCTS loop
        iterations = 0
        while iterations < budget and self.node_count < self.max_nodes:
            # 1. SELECT — find most promising unexplored node
            node = self._select(self.root)
            if node is None:
                logger.debug("MCTS: all branches exhausted or pruned — stopping early")
                break  # No more expandable nodes

            # 2. EXPAND — generate child queries from this node's results
            if not node.expanded:
                self._simulate(node)  # Search first
                if node.depth < self.max_depth:
                    self._expand(node)
                node.expanded = True

            # 3. BACKPROPAGATE — update quality scores up the tree
            self._backpropagate(node)

            # 4. PRUNE — remove low-quality branches
            if iterations % 10 == 0 and iterations > 0:
                self._prune()

            iterations += 1

        # Collect all results sorted by CRAAP score
        self.all_results.sort(key=lambda x: x.get("craap_score", 0), reverse=True)

        elapsed = time.monotonic() - start
        stats = {
            "results": self.all_results,
            "tree_stats": {
                "total_nodes": self.node_count,
                "max_depth_reached": self._max_depth_reached(),
                "pruned_branches": sum(1 for n in self._all_nodes() if n.pruned),
                "avg_quality": self.root.avg_quality if self.root else 0,
            },
            "queries_explored": len(self.seen_queries),
            "sources_found": len(self.all_results),
            "avg_quality": (sum(r.get("craap_score", 0) for r in self.all_results)
                          / max(len(self.all_results), 1)),
            "elapsed": elapsed,
        }

        logger.info(f"MCTS: {iterations} iterations, {len(self.all_results)} sources, "
                    f"{self.node_count} nodes, {elapsed:.1f}s")
        return stats

    # ── MCTS Core Operations ─────────────────────────────────────────────

    def _select(self, node: MCTSNode) -> Optional[MCTSNode]:
        """Select the most promising node to explore next (UCB1)."""
        if node.pruned:
            return None

        # If this node hasn't been simulated yet, select it
        if not node.expanded and node.visits == 0:
            return node

        # If node has unexpanded children, pick the best one
        unexpanded = [c for c in node.children if not c.expanded and not c.pruned]
        if unexpanded:
            return max(unexpanded, key=lambda n: n.ucb1)

        # Recurse into best expanded child
        expanded = [c for c in node.children if c.expanded and not c.pruned]
        if expanded:
            best = max(expanded, key=lambda n: n.ucb1)
            return self._select(best)

        return None

    def _simulate(self, node: MCTSNode):
        """Execute search for this node's query and score results."""
        try:
            raw_results = self.search_fn(node.query)
        except Exception as e:
            logger.error(f"MCTS search failed for '{node.query}': {e}")
            raw_results = []

        for r in raw_results:
            url = r.get("url", "")
            if url and url not in self.seen_urls:
                self.seen_urls.add(url)
                r["craap_score"] = self.score_fn(r)
                r["discovery_query"] = node.query
                r["tree_depth"] = node.depth
                node.results.append(r)
                self.all_results.append(r)

        node.result_count = len(node.results)
        if node.results:
            node.quality_sum = sum(r.get("craap_score", 0) for r in node.results)
            node.avg_quality = node.quality_sum / len(node.results)
        node.visits = 1

    def _expand(self, node: MCTSNode):
        """Generate child queries from this node's results."""
        if self.node_count >= self.max_nodes:
            return
        if not node.results:
            return

        try:
            new_queries = self.expand_fn(node.query, node.results)
        except Exception as e:
            logger.error(f"MCTS expand failed: {e}")
            new_queries = []

        for q in new_queries:
            if self.node_count >= self.max_nodes:
                break
            q_lower = q.lower().strip()
            if q_lower and q_lower not in self.seen_queries:
                child = MCTSNode(query=q, parent=node, depth=node.depth + 1,
                                 c=self.exploration_constant)
                node.children.append(child)
                self.node_count += 1
                self.seen_queries.add(q_lower)

    def _backpropagate(self, node: MCTSNode):
        """Update quality scores from leaf to root.

        Each ancestor's avg_quality is a weighted average of its own simulation
        quality and its children's accumulated quality.  Using ``avg_quality``
        (already normalised to [0, 1]) rather than the raw ``quality_sum``
        (which scales with result_count) prevents the average from exceeding 1.
        """
        current = node
        while current is not None:
            if current.children:
                child_quality = sum(c.avg_quality * c.visits for c in current.children if not c.pruned)
                child_visits = sum(c.visits for c in current.children if not c.pruned)
                if child_visits > 0:
                    own_weight = max(current.visits, 1)
                    total_weight = own_weight + child_visits
                    # Use avg_quality (clamped to [0,1]) rather than quality_sum
                    # (which scales with result_count and can exceed 1.0 when a
                    # node has several results).
                    current.avg_quality = (
                        (current.avg_quality * own_weight + child_quality) / total_weight
                    )
            current.visits += 1
            current = current.parent

    def _prune(self):
        """Remove branches with consistently low quality."""
        for node in self._all_nodes():
            if (node.visits >= 2 and node.avg_quality < self.prune_threshold
                and node != self.root):
                node.pruned = True

    # ── Helper Methods ───────────────────────────────────────────────────

    def _all_nodes(self) -> List[MCTSNode]:
        """Breadth-first traversal of all nodes."""
        if not self.root:
            return []
        queue = [self.root]
        nodes = []
        while queue:
            node = queue.pop(0)
            nodes.append(node)
            queue.extend(node.children)
        return nodes

    def _max_depth_reached(self) -> int:
        """Return the maximum depth reached in the tree."""
        return max((n.depth for n in self._all_nodes()), default=0)

    def _default_expand(self, query: str, results: List[Dict]) -> List[str]:
        """Default query expansion: extract key terms from top results."""
        queries = []
        seen_words = set(query.lower().split())
        for r in results[:3]:
            title = r.get("title", "")
            words = [w for w in title.split() if len(w) > 4 and w.lower() not in seen_words]
            if words:
                refined = f"{query} {' '.join(words[:2])}"
                queries.append(refined)
                seen_words.update(w.lower() for w in words[:2])
        return queries[:3]

    def _default_score(self, result: Dict[str, Any]) -> float:
        """Default CRAAP scoring heuristic."""
        url = result.get("url", "")
        content = result.get("content", "") or result.get("snippet", "")

        score = 0.50  # Base

        # Authority bonus
        if any(d in url for d in [".gov", ".edu", ".mil", "arxiv.org", "ieee.org"]):
            score += 0.30
        elif any(d in url for d in ["github.com", "stackoverflow.com", "wikipedia.org"]):
            score += 0.15
        elif any(d in url for d in ["docs.", "developer.", "learn."]):
            score += 0.20

        # Content richness bonus
        if len(content) > 500:
            score += 0.10
        if len(content) > 1000:
            score += 0.05

        # Social media penalty
        if any(d in url for d in ["facebook.com", "twitter.com", "tiktok.com", "instagram.com"]):
            score -= 0.30

        return max(0.0, min(1.0, score))

    def get_tree_summary(self) -> str:
        """Generate a text summary of the exploration tree."""
        if not self.root:
            return "No tree built."

        lines = [f"MCTS Research Tree: {self.node_count} nodes, "
                f"{len(self.all_results)} sources\n"]

        def _render(node: MCTSNode, indent: int = 0):
            prefix = "  " * indent
            status = "✂" if node.pruned else ("✓" if node.expanded else "○")
            quality = f"Q={node.avg_quality:.2f}" if node.visits > 0 else "Q=?"
            lines.append(f"{prefix}{status} [{quality}, V={node.visits}, "
                        f"R={node.result_count}] {node.query[:60]}")
            for child in node.children[:5]:
                _render(child, indent + 1)
            if len(node.children) > 5:
                lines.append(f"{prefix}  ... +{len(node.children) - 5} more")

        _render(self.root)
        return "\n".join(lines)
