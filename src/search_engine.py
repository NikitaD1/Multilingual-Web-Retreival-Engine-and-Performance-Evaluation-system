"""
search_engine.py
----------------
Orchestrates the full retrieval pipeline:
  1. Cross-lingual query processing (translation)
  2. VSM cosine similarity ranking
  3. LDA topic-based re-ranking
  4. Snippet generation with highlighted query terms
"""

import re
import json
import logging
from pathlib import Path

from src.preprocessing import build_index, preprocess, detect_language, InvertedIndex
from src.vsm import VectorSpaceModel
from src.lda_retrieval import LDARetrieval
from src.translation import CrossLingualProcessor, merge_results

logger = logging.getLogger(__name__)

CORPUS_PATH = Path(__file__).parent.parent / "corpus" / "news_corpus.json"


# ── Snippet generation ─────────────────────────────────────────────────────────

def generate_snippet(content: str, query_terms: list[str], window: int = 35) -> str:
    """
    Extract the most relevant sentence/window from *content* that contains
    the most query term matches.  Falls back to first 200 chars.
    """
    sentences = re.split(r"(?<=[।.!?])\s+", content)
    if not sentences:
        return content[:200]

    query_stems = set(query_terms)
    best_sentence, best_score = sentences[0], 0

    for sent in sentences:
        words = sent.lower().split()
        score = sum(1 for w in words if any(qt in w for qt in query_stems))
        if score > best_score:
            best_score = score
            best_sentence = sent

    # Trim to ~200 chars from the match point
    snip = best_sentence[:220]
    if len(best_sentence) > 220:
        snip += "…"
    return snip


def highlight_terms(text: str, query_terms: list[str]) -> str:
    """
    Wrap query terms in **bold** markers for Streamlit markdown rendering.
    Works on surface-level word matching (not stemmed) for readability.
    """
    for term in query_terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        text = pattern.sub(lambda m: f"**{m.group(0)}**", text)
    return text


# ── Search Engine ──────────────────────────────────────────────────────────────

class SearchEngine:
    """
    End-to-end mini search engine.

    Usage
    -----
    engine = SearchEngine()
    engine.build()
    results = engine.search("RBI repo rate", top_k=10, use_lda=True)
    """

    def __init__(self, corpus_path: str | Path = CORPUS_PATH):
        self.corpus_path = Path(corpus_path)
        self.index: InvertedIndex | None = None
        self.documents: list[dict] = []
        self.doc_map: dict[str, dict] = {}
        self.vsm: VectorSpaceModel | None = None
        self.lda: LDARetrieval | None = None
        self.clp = CrossLingualProcessor()
        self.ready = False

    def build(self, n_topics: int = 10) -> None:
        """Build all components from the corpus."""
        logger.info("Building inverted index …")
        self.index, self.documents = build_index(str(self.corpus_path))
        self.doc_map = {d["id"]: d for d in self.documents}

        logger.info("Building VSM …")
        self.vsm = VectorSpaceModel(self.index)

        logger.info("Training LDA …")
        self.lda = LDARetrieval(n_topics=n_topics)
        self.lda.train(self.index)

        self.ready = True
        logger.info(
            f"Engine ready | docs={len(self.documents)} "
            f"vocab={len(self.index.vocabulary())} topics={n_topics}"
        )

    # ── Core search ───────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 10,
        use_lda: bool = True,
        cross_lingual: bool = True,
    ) -> dict:
        """
        Main search entry point.

        Returns
        -------
        dict:
            query_info   : translation details
            results      : list of result dicts (ranked)
            topics       : top LDA topics for the query
            vsm_scores   : raw VSM-only scores (for comparison)
        """
        if not self.ready:
            raise RuntimeError("Call engine.build() first.")

        # 1. Cross-lingual processing
        qinfo = self.clp.process(query) if cross_lingual else {
            "original": query, "detected_lang": detect_language(query),
            "en_query": query, "hi_query": query, "was_translated": False,
        }

        detected_lang = qinfo["detected_lang"]
        en_query = qinfo["en_query"]
        hi_query = qinfo["hi_query"]

        # 2. VSM search — English side
        en_vsm = self.vsm.rank(en_query, top_k=top_k * 2, lang="en")
        # VSM search — Hindi side
        hi_vsm = self.vsm.rank(hi_query, top_k=top_k * 2, lang="hi")

        # Keep all unique VSM results for comparison output
        vsm_combined = merge_results(en_vsm, hi_vsm, top_k=top_k)
        vsm_doc_ids = [doc_id for doc_id, _ in vsm_combined]

        # 3. LDA re-ranking
        if use_lda and self.lda is not None:
            en_reranked = self.lda.rerank(en_vsm, en_query, lang="en")
            hi_reranked = self.lda.rerank(hi_vsm, hi_query, lang="hi")
            final_scores = merge_results(en_reranked, hi_reranked, top_k=top_k)
        else:
            final_scores = vsm_combined

        # 4. Build result dicts with snippets
        query_terms_en = preprocess(en_query, "en")
        query_terms_hi = preprocess(hi_query, "hi")
        all_query_terms = list(set(query_terms_en + query_terms_hi))

        # Also keep original surface words for highlighting
        surface_terms = query.split() + en_query.split()

        results = []
        for doc_id, score in final_scores:
            doc = self.doc_map.get(doc_id, {})
            if not doc:
                continue
            content = doc.get("content", "")
            snippet = generate_snippet(content, all_query_terms)
            snippet_highlighted = highlight_terms(snippet, surface_terms)

            results.append({
                "doc_id": doc_id,
                "title": doc.get("title", ""),
                "language": doc.get("language", "en"),
                "category": doc.get("category", ""),
                "date": doc.get("date", ""),
                "score": round(score, 4),
                "snippet": snippet_highlighted,
                "snippet_plain": snippet,
            })

        # 5. Topic analysis for query
        topics = []
        if self.lda is not None:
            try:
                topics = self.lda.top_topics(en_query, top_n=3, lang="en")
            except Exception:
                topics = []

        return {
            "query_info": qinfo,
            "results": results,
            "topics": topics,
            "vsm_doc_ids": vsm_doc_ids,   # for baseline comparison
        }

    # ── Utility ───────────────────────────────────────────────────────────────

    def corpus_stats(self) -> dict:
        en_docs = sum(1 for d in self.documents if d["language"] == "en")
        hi_docs = sum(1 for d in self.documents if d["language"] == "hi")
        categories = {}
        for d in self.documents:
            categories[d["category"]] = categories.get(d["category"], 0) + 1
        return {
            "total": len(self.documents),
            "english": en_docs,
            "hindi": hi_docs,
            "hindi_pct": round(100 * hi_docs / max(len(self.documents), 1), 1),
            "vocabulary_size": len(self.index.vocabulary()) if self.index else 0,
            "categories": categories,
        }

    def topic_words(self) -> list[dict]:
        if self.lda is None:
            return []
        return self.lda.topic_word_matrix()
