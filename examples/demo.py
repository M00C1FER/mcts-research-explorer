"""
Demo: MCTS Research Explorer with a mock search function.

Run:
    python examples/demo.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcts_explorer import MCTSResearchExplorer

# ── Mock search function (replace with real search_fn) ────────────────────

MOCK_CORPUS = {
    "quantum computing": [
        {"url": "https://arxiv.org/abs/1234", "title": "Quantum Error Correction Survey", "content": "Comprehensive survey of surface codes and threshold theorems."},
        {"url": "https://ibm.com/quantum", "title": "IBM Quantum Systems", "content": "IBM quantum processors and Qiskit SDK overview."},
        {"url": "https://en.wikipedia.org/wiki/Quantum_computing", "title": "Quantum Computing - Wikipedia", "content": "Quantum computation fundamentals."},
    ],
    "quantum computing error correction": [
        {"url": "https://nature.com/articles/s41586-023-error", "title": "Nature: Real-time error correction", "content": "Logical qubit demonstration with real-time error correction."},
        {"url": "https://arxiv.org/abs/5678", "title": "Surface Code Implementation", "content": "Topological codes for fault-tolerant quantum computation."},
    ],
    "quantum computing hardware comparison": [
        {"url": "https://ieee.org/spectrum/quantum-race", "title": "IEEE: Quantum Hardware Race 2024", "content": "Comparison of superconducting, trapped-ion, and photonic systems."},
    ],
    "quantum computing IBM superconducting": [
        {"url": "https://arxiv.org/abs/9012", "title": "Superconducting Qubit Coherence", "content": "T1, T2 coherence times in transmon qubits."},
    ],
}

def mock_search(query: str):
    """Return mock results matching query keywords."""
    q_lower = query.lower()
    for key, results in MOCK_CORPUS.items():
        if any(word in q_lower for word in key.split()):
            return [dict(r) for r in results]
    return []


# ── Run MCTS exploration ──────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("MCTS Research Explorer — Demo")
    print("=" * 60)
    print()

    explorer = MCTSResearchExplorer(
        search_fn=mock_search,
        max_nodes=30,
        max_depth=3,
        prune_threshold=0.30,
    )

    results = explorer.explore(
        "quantum computing",
        budget=10,
        initial_queries=["quantum computing error correction", "quantum computing hardware comparison"]
    )

    print("EXPLORATION COMPLETE")
    print("-" * 40)
    print(f"Queries explored : {results['queries_explored']}")
    print(f"Sources found    : {results['sources_found']}")
    print(f"Average quality  : {results['avg_quality']:.2f}")
    print(f"Elapsed          : {results['elapsed']:.2f}s")
    print()

    print("TOP 5 SOURCES (by CRAAP score):")
    print("-" * 40)
    for i, r in enumerate(results["results"][:5], 1):
        print(f"  {i}. [{r.get('craap_score', 0):.2f}] {r['title']}")
        print(f"       {r['url']}")
    print()

    print("EXPLORATION TREE:")
    print("-" * 40)
    print(explorer.get_tree_summary())


if __name__ == "__main__":
    main()
