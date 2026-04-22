"""
evaluation.py
-------------
Standard IR evaluation metrics:
  - Precision@k
  - Recall
  - Average Precision (AP)
  - Mean Average Precision (MAP)

Ground truth relevance judgements are loaded from
  data/evaluation_queries.json
"""

import json
import math
from pathlib import Path
from src.search_engine import SearchEngine

QUERIES_PATH = Path(__file__).parent.parent / "data" / "evaluation_queries.json"


# ── Metric functions ───────────────────────────────────────────────────────────

def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Fraction of top-k retrieved docs that are relevant."""
    if k == 0:
        return 0.0
    top_k = retrieved[:k]
    hits = sum(1 for d in top_k if d in relevant)
    return hits / k


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Fraction of relevant docs found in top-k retrieved."""
    if not relevant:
        return 0.0
    top_k = retrieved[:k]
    hits = sum(1 for d in top_k if d in relevant)
    return hits / len(relevant)


def average_precision(retrieved: list[str], relevant: set[str]) -> float:
    """
    Average Precision: average of precision values at each rank position
    where a relevant document is retrieved.
    """
    if not relevant:
        return 0.0
    hits = 0
    sum_prec = 0.0
    for i, doc_id in enumerate(retrieved, start=1):
        if doc_id in relevant:
            hits += 1
            sum_prec += hits / i
    return sum_prec / len(relevant) if relevant else 0.0


def mean_average_precision(aps: list[float]) -> float:
    """MAP = mean of AP values across all queries."""
    return sum(aps) / len(aps) if aps else 0.0


def f1_score(p: float, r: float) -> float:
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


# ── Evaluation runner ──────────────────────────────────────────────────────────

def run_evaluation(
    engine: SearchEngine,
    queries_path: str | Path = QUERIES_PATH,
    top_k: int = 10,
    use_lda: bool = True,
) -> dict:
    """
    Run all evaluation queries against the search engine and compute metrics.

    Parameters
    ----------
    engine      : built SearchEngine instance
    queries_path: path to evaluation_queries.json
    top_k       : cutoff for retrieval (default 10)
    use_lda     : whether to use LDA re-ranking

    Returns
    -------
    dict with per-query results and aggregate MAP / mean P / mean R
    """
    with open(queries_path, "r", encoding="utf-8") as f:
        eval_queries = json.load(f)

    per_query = []
    aps = []

    for q in eval_queries:
        qid = q["id"]
        query_text = q["query"]
        relevant_docs = set(q["relevant_docs"])

        try:
            result = engine.search(
                query_text,
                top_k=top_k,
                use_lda=use_lda,
                cross_lingual=True,
            )
            retrieved = [r["doc_id"] for r in result["results"]]
        except Exception as e:
            retrieved = []

        p_k = precision_at_k(retrieved, relevant_docs, top_k)
        r_k = recall_at_k(retrieved, relevant_docs, top_k)
        ap = average_precision(retrieved, relevant_docs)
        aps.append(ap)

        per_query.append({
            "id": qid,
            "query": query_text,
            "lang": q.get("lang", "en"),
            "category": q.get("category", ""),
            "relevant_count": len(relevant_docs),
            "retrieved": retrieved,
            "hits": [d for d in retrieved if d in relevant_docs],
            "precision": round(p_k, 4),
            "recall": round(r_k, 4),
            "f1": round(f1_score(p_k, r_k), 4),
            "ap": round(ap, 4),
        })

    # ── Aggregates ────────────────────────────────────────────────────────────
    map_score = mean_average_precision(aps)
    mean_p = sum(q["precision"] for q in per_query) / len(per_query)
    mean_r = sum(q["recall"] for q in per_query) / len(per_query)
    mean_f1 = f1_score(mean_p, mean_r)

    # Break down by language
    en_qs = [q for q in per_query if q["lang"] == "en"]
    hi_qs = [q for q in per_query if q["lang"] == "hi"]

    return {
        "map": round(map_score, 4),
        "mean_precision": round(mean_p, 4),
        "mean_recall": round(mean_r, 4),
        "mean_f1": round(mean_f1, 4),
        "en_map": round(mean_average_precision([q["ap"] for q in en_qs]), 4) if en_qs else 0,
        "hi_map": round(mean_average_precision([q["ap"] for q in hi_qs]), 4) if hi_qs else 0,
        "total_queries": len(per_query),
        "en_queries": len(en_qs),
        "hi_queries": len(hi_qs),
        "per_query": per_query,
    }
