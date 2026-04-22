"""
vsm.py
------
Vector Space Model:
  - TF-IDF document matrix
  - Cosine similarity computation
  - Ranked retrieval (top-k)
"""

import math
import numpy as np
from collections import Counter
from src.preprocessing import InvertedIndex, preprocess, detect_language


class VectorSpaceModel:
    """
    Builds a TF-IDF matrix from an InvertedIndex and supports
    cosine-similarity ranked retrieval.
    """

    def __init__(self, index: InvertedIndex):
        self.index = index
        self.vocab: list[str] = sorted(index.vocabulary())
        self.term_to_idx: dict[str, int] = {t: i for i, t in enumerate(self.vocab)}
        self.V = len(self.vocab)                     # vocabulary size
        self.doc_ids: list[str] = index.all_doc_ids
        self._doc_vectors: dict[str, np.ndarray] = {}
        self._build_doc_vectors()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_doc_vectors(self) -> None:
        for doc_id in self.doc_ids:
            vec = np.zeros(self.V, dtype=np.float32)
            tokens = self.index.doc_tokens[doc_id]
            tf_counts = Counter(tokens)
            for term, cnt in tf_counts.items():
                if term in self.term_to_idx:
                    idx = self.term_to_idx[term]
                    tf = 1 + math.log(cnt) if cnt > 0 else 0
                    idf = self.index.idf(term)
                    vec[idx] = tf * idf
            norm = np.linalg.norm(vec)
            self._doc_vectors[doc_id] = vec / norm if norm > 0 else vec

    # ── Query ─────────────────────────────────────────────────────────────────

    def query_vector(self, query: str, lang: str | None = None) -> np.ndarray:
        """Convert a raw query string to a normalised TF-IDF vector."""
        if lang is None:
            lang = detect_language(query)
        tokens = preprocess(query, lang)
        tf_counts = Counter(tokens)
        vec = np.zeros(self.V, dtype=np.float32)
        for term, cnt in tf_counts.items():
            if term in self.term_to_idx:
                idx = self.term_to_idx[term]
                tf = 1 + math.log(cnt) if cnt > 0 else 0
                idf = self.index.idf(term)
                vec[idx] = tf * idf
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def cosine_similarity(self, q_vec: np.ndarray, doc_id: str) -> float:
        """Dot product of pre-normalised vectors."""
        return float(np.dot(q_vec, self._doc_vectors[doc_id]))

    def rank(
        self,
        query: str,
        top_k: int = 10,
        lang: str | None = None,
    ) -> list[tuple[str, float]]:
        """
        Return list of (doc_id, score) sorted descending by cosine similarity.
        """
        q_vec = self.query_vector(query, lang)
        scores = [
            (doc_id, self.cosine_similarity(q_vec, doc_id))
            for doc_id in self.doc_ids
        ]
        scores.sort(key=lambda x: x[1], reverse=True)
        return [(d, s) for d, s in scores[:top_k] if s > 0]

    def get_doc_vector(self, doc_id: str) -> np.ndarray:
        return self._doc_vectors.get(doc_id, np.zeros(self.V, dtype=np.float32))

    def get_query_terms(self, query: str, lang: str | None = None) -> list[str]:
        """Return the preprocessed query terms (used for snippet highlighting)."""
        if lang is None:
            lang = detect_language(query)
        return preprocess(query, lang)
