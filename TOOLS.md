# Recommended Tools for mcts-explorer

This document lists tools that enhance `mcts-explorer` integrations. None are required for core functionality (pure stdlib).

---

## 1. Search Providers

### SearXNG — Self-Hosted Meta Search Engine

> Privacy-respecting, multi-engine search aggregator. Best default `search_fn` for production.

**Install:**
```bash
# Docker
docker run -d -p 8080:8080 searxng/searxng

# Termux (no Docker)
pip install searx   # or use public instance
```
**Use in mcts-explorer:**
```python
import httpx
def search(q): return httpx.get("http://localhost:8080/search", params={"q": q, "format": "json"}).json().get("results", [])
```

---

### ddgr — DuckDuckGo CLI

> Zero-browser terminal search. Great fallback when no search API is available.

**Install:**
```bash
# Linux
sudo apt-get install ddgr        # Debian/Ubuntu
sudo dnf install ddgr             # Fedora

# Termux
pkg install ddgr

# macOS
brew install ddgr
```
**Use in mcts-explorer:**
```python
import subprocess, json
def search(q):
    out = subprocess.run(["ddgr", "--json", q], capture_output=True, text=True, timeout=10)
    return json.loads(out.stdout or "[]")
```

---

### Brave Search API — REST API

> High-quality independent web index, separate from Google/Bing. Optional key.

**Sign up:** https://api.search.brave.com/  
**Install:** `pip install httpx`  
**Use:**
```python
import httpx, os
def search(q):
    resp = httpx.get("https://api.search.brave.com/res/v1/web/search",
        headers={"X-Subscription-Token": os.environ["BRAVE_SEARCH_API_KEY"]},
        params={"q": q, "count": 10}, timeout=10)
    return [{"url": r["url"], "title": r["title"], "content": r.get("description", "")}
            for r in resp.json().get("web", {}).get("results", [])]
```

---

## 2. HTTP Clients

### httpx — Async HTTP for Python

> Modern, async-capable HTTP client. Drop-in replacement for `requests`.

**Install:**
```bash
pip install httpx              # sync + async
pip install "httpx[http2]"     # HTTP/2 support
```

---

### trafilatura — Web Article Extraction

> Extracts main article content from web pages (strips ads, nav, footers).

**Install:**
```bash
pip install trafilatura

# Termux
pip install --user trafilatura
```
**Use:**
```python
import trafilatura
content = trafilatura.fetch_url("https://example.com")
text = trafilatura.extract(content)
```

---

## 3. Text Processing

### ripgrep (rg) — Ultra-fast Text Search

> Indexes local document collections for fast MCTS result retrieval.

**Install:**
```bash
sudo apt-get install ripgrep    # Debian/Ubuntu
pkg install ripgrep             # Termux
brew install ripgrep            # macOS
```

---

## 4. Visualization

### plotext — Terminal Plots

> Plot MCTS tree quality distributions directly in the terminal.

**Install:** `pip install plotext`  
**Use:**
```python
import plotext as plt
scores = [r["craap_score"] for r in results["results"]]
plt.hist(scores, bins=10)
plt.title("Source Quality Distribution")
plt.show()
```

---

## 5. Development / Testing

| Tool | Purpose | Install |
|------|---------|---------|
| `pytest` | Unit testing | `pip install pytest` |
| `pytest-cov` | Coverage reports | `pip install pytest-cov` |
| `ruff` | Fast Python linter | `pip install ruff` |
| `mypy` | Static type checking | `pip install mypy` |

---

## Platform Quick Reference

| Tool | Linux | WSL | Termux |
|------|-------|-----|--------|
| SearXNG | Docker | Docker | Public instance |
| ddgr | apt | apt | pkg |
| httpx | pip | pip | pip --user |
| trafilatura | pip | pip | pip --user |
| ripgrep | apt | apt | pkg |
| plotext | pip | pip | pip --user |
