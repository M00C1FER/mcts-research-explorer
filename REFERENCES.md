# Reference Projects

High-star open-source projects studied during the audit cycle.  
One concrete pattern from each is noted below.

---

## 1. [princeton-nlp/SWE-agent](https://github.com/princeton-nlp/SWE-agent) (⭐ 14k+, MIT)

**Pattern — Configurable exploration constants via dataclass config**  
SWE-agent centralises all hyperparameters (temperature, max iterations, budgets)
in a typed dataclass rather than scattered constructor kwargs.  This audit
adopted the same approach by adding `exploration_constant` to
`MCTSResearchExplorer.__init__` and propagating it to every `MCTSNode` at
creation time, keeping `ucb1` side-effect-free.

---

## 2. [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) (⭐ 18k+, Apache-2.0)

**Pattern — Pluggable, provider-agnostic search interface**  
GPT Researcher abstracts its web-search backend behind a single async callable,
letting users swap DuckDuckGo ↔ Tavily ↔ SearXNG without touching core logic.
`mcts-explorer` follows this pattern with the `search_fn` parameter; the
`fetcher` alias preserves backward compatibility for early adopters.

---

## 3. [stanford-oval/storm](https://github.com/stanford-oval/storm) (⭐ 7k+, MIT)

**Pattern — Multi-perspective query expansion**  
STORM generates diverse sub-queries from multiple "perspectives" (expert roles)
before synthesising a final answer.  The `_default_expand` heuristic in this
repo extracts novel key-terms from each result title to mimic the same breadth,
while `expand_fn` lets callers plug in an LLM-backed expander identical to
STORM's `QuestionAsker`.

---

## 4. [run-llama/llama_index](https://github.com/run-llama/llama_index) (⭐ 38k+, MIT)

**Pattern — CRAAP-style authority scoring in retrieval pipelines**  
LlamaIndex's `NodeWithScore` assigns domain-authority bonuses (academic,
government, documentation domains) and content-length bonuses during
re-ranking, matching the heuristic in `_default_score`.  Seeing the same
pattern validated in a production library confirms the approach is sound.

---

## 5. [microsoft/promptflow](https://github.com/microsoft/promptflow) (⭐ 10k+, MIT)

**Pattern — Pure-stdlib core with optional extras**  
PromptFlow keeps its core dependency-free and gates integrations behind
optional extras (`pip install promptflow[azure]`).  `mcts-explorer` mirrors
this: zero runtime dependencies in the default install, with `httpx` available
via `pip install "mcts-explorer[http]"`.
