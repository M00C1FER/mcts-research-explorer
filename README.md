# MCTS Research Explorer

> Intelligent research query exploration using Monte Carlo Tree Search — balancing exploitation of high-quality sources with exploration of novel query branches.

## What It Does

Traditional research pipelines iterate linearly through queries. `mcts-explorer` builds a **tree** of queries using UCB1 selection, expanding the most promising branches and pruning dead-ends automatically.

```
root: "quantum computing"
├── ✓ "quantum computing error correction" [Q=0.72, R=8]
│   ├── ✓ "quantum computing error correction surface codes" [Q=0.81, R=6]
│   └── ✓ "quantum computing error correction threshold" [Q=0.68, R=4]
├── ✓ "quantum computing hardware comparison" [Q=0.65, R=5]
└── ✂ "quantum computing movies" [Q=0.12, pruned]
```

**Key capabilities:**
- UCB1 balances explore/exploit across query branches
- CRAAP scoring (Currency, Relevance, Authority, Accuracy, Purpose) rates source quality
- Automatic pruning of low-quality branches
- Pluggable search, expansion, and scoring functions
- Zero runtime dependencies (pure Python stdlib)

## Installation

```bash
git clone https://github.com/M00C1FER/mcts-research-explorer
cd mcts-research-explorer
./install.sh
```

## Quick Start

```python
from mcts_explorer import MCTSResearchExplorer

def my_search(query: str):
    # Return list of dicts with "url", "title", "content" keys
    return [{"url": "https://example.com", "title": "...", "content": "..."}]

explorer = MCTSResearchExplorer(search_fn=my_search, max_nodes=100, max_depth=3)
results = explorer.explore("your research topic", budget=30)

print(f"Found {results['sources_found']} sources")
print(f"Average quality: {results['avg_quality']:.2f}")
print(explorer.get_tree_summary())
```

## API Reference

### `MCTSResearchExplorer(search_fn, expand_fn=None, score_fn=None, max_nodes=200, max_depth=4, prune_threshold=0.40, exploration_constant=1.414)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `search_fn` | `Callable[[str], List[Dict]]` | Required. Execute a search query, return results with `url`, `title`, `content` |
| `expand_fn` | `Callable[[str, List[Dict]], List[str]]` | Optional. Generate child queries from parent + results |
| `score_fn` | `Callable[[Dict], float]` | Optional. Score result quality 0.0–1.0 (CRAAP) |
| `max_nodes` | `int` | Maximum tree nodes (memory bound) |
| `max_depth` | `int` | Maximum query depth |
| `prune_threshold` | `float` | Remove branches below this quality score |
| `exploration_constant` | `float` | UCB1 `C` weight (default `√2 ≈ 1.414`). Higher → more exploration |

### `explorer.explore(topic, budget=50, initial_queries=None) -> Dict`

Returns:
```python
{
    "results": List[Dict],        # All unique results, sorted by CRAAP score
    "tree_stats": {
        "total_nodes": int,
        "max_depth_reached": int,
        "pruned_branches": int,
        "avg_quality": float,
    },
    "queries_explored": int,
    "sources_found": int,
    "avg_quality": float,
    "elapsed": float,             # seconds
}
```

### `explorer.get_tree_summary() -> str`

Human-readable ASCII tree of the exploration structure.

## Search Function Interface

Your `search_fn` must accept a query string and return a list of dicts:

```python
def search_fn(query: str) -> List[Dict[str, Any]]:
    return [
        {
            "url": "https://arxiv.org/abs/...",
            "title": "Paper title",
            "content": "Abstract or full text...",
            # any additional fields are preserved
        }
    ]
```

## Integrating with SearXNG

```python
import httpx

def searxng_search(query: str):
    import os
    searxng_url = os.environ.get("SEARXNG_URL", "http://localhost:8080")
    resp = httpx.get(
        f"{searxng_url}/search",
        params={"q": query, "format": "json"},
        timeout=10
    )
    resp.raise_for_status()
    return resp.json().get("results", [])

explorer = MCTSResearchExplorer(search_fn=searxng_search)
results = explorer.explore("machine learning optimization", budget=40)
```

## Architecture

```
MCTSResearchExplorer
├── _select()       — UCB1 traversal to find best unexplored node
├── _simulate()     — Execute search_fn, score with score_fn
├── _expand()       — Generate children via expand_fn
├── _backpropagate()— Propagate quality scores to root
└── _prune()        — Remove low-quality branches
```

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Debian 12/13, Ubuntu 22.04/24.04 | ✅ | Full support — `apt` auto-install |
| Arch / Manjaro | ✅ | Full support — `pacman` auto-install |
| Fedora / RHEL / Rocky | ✅ | Full support — `dnf` auto-install |
| Alpine Linux | ✅ | Full support — `apk` auto-install (`py3-pip`) |
| WSL 2 (Ubuntu base) | ✅ | Full support — no EFI or OS-specific assumptions |
| Termux (Android arm64) | ✅ | No sudo required; uses `--user` pip install |
| macOS | ✅ | Full support |

### Termux (Android) Quick Install

```bash
pkg install python git
git clone https://github.com/M00C1FER/mcts-research-explorer
cd mcts-research-explorer
./install.sh          # detects Termux automatically; no sudo needed
python3 examples/demo.py
```

### Alpine Quick Install

```bash
apk add python3 py3-pip git
git clone https://github.com/M00C1FER/mcts-research-explorer
cd mcts-research-explorer
./install.sh
source .venv/bin/activate
python examples/demo.py
```

## License

MIT — see [LICENSE](LICENSE)
