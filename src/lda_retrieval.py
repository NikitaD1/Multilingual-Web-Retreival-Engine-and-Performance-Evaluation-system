"""
lda_retrieval.py
----------------
Latent Dirichlet Allocation for retrieval enhancement.

How LDA improves retrieval:
  The VSM ranks by exact-term overlap (TF-IDF cosine).  If a document is
  topically relevant but uses different vocabulary (synonyms, paraphrases)
  it may rank poorly.  LDA captures latent topic structure: documents and
  queries are projected into a shared low-dimensional topic space.  A
  blended score
        final = α * cosine_sim  +  (1-α) * topic_sim
  boosts documents that share the same latent topic as the query even when
  surface-level term overlap is low, improving recall.
"""

import numpy as np
from gensim import corpora
from gensim.models import LdaModel
from src.preprocessing import InvertedIndex, preprocess, detect_language


class LDARetrieval:
    """
    Wraps a Gensim LDA model and provides topic-similarity scoring
    for re-ranking VSM results.
    """

    def __init__(self, n_topics: int = 10, passes: int = 15, random_state: int = 42):
        self.n_topics = n_topics
        self.passes = passes
        self.random_state = random_state
        self.dictionary: corpora.Dictionary | None = None
        self.model: LdaModel | None = None
        self._doc_topic_vectors: dict[str, np.ndarray] = {}

    # ── Training ──────────────────────────────────────────────────────────────

    def train(self, index: InvertedIndex) -> None:
        """Train LDA on the preprocessed corpus tokens."""
        corpus_tokens = list(index.doc_tokens.values())
        doc_ids = list(index.doc_tokens.keys())

        self.dictionary = corpora.Dictionary(corpus_tokens)
        self.dictionary.filter_extremes(no_below=2, no_above=0.9)
        bow_corpus = [self.dictionary.doc2bow(tokens) for tokens in corpus_tokens]

        self.model = LdaModel(
            corpus=bow_corpus,
            id2word=self.dictionary,
            num_topics=self.n_topics,
            passes=self.passes,
            random_state=self.random_state,
            alpha="auto",
            eta="auto",
            minimum_probability=0.0,
        )

        # Pre-compute document topic distributions
        for doc_id, bow in zip(doc_ids, bow_corpus):
            self._doc_topic_vectors[doc_id] = self._to_dense(
                self.model.get_document_topics(bow, minimum_probability=0.0)
            )

    # ── Inference ─────────────────────────────────────────────────────────────

    def _to_dense(self, topic_dist: list[tuple[int, float]]) -> np.ndarray:
        vec = np.zeros(self.n_topics, dtype=np.float32)
        for topic_id, prob in topic_dist:
            vec[topic_id] = prob
        return vec

    def query_topic_vector(self, query: str, lang: str | None = None) -> np.ndarray:
        if self.model is None or self.dictionary is None:
            raise RuntimeError("LDA model not trained yet.")
        if lang is None:
            lang = detect_language(query)
        tokens = preprocess(query, lang)
        bow = self.dictionary.doc2bow(tokens)
        return self._to_dense(
            self.model.get_document_topics(bow, minimum_probability=0.0)
        )

    @staticmethod
    def _topic_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        """Cosine similarity between two topic distribution vectors."""
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    def rerank(
        self,
        vsm_scores: list[tuple[str, float]],
        query: str,
        alpha: float = 0.7,
        lang: str | None = None,
    ) -> list[tuple[str, float]]:
        """
        Blend VSM cosine scores with LDA topic similarity.
        alpha=0.7 weights VSM higher; topic similarity acts as soft boost.

        Parameters
        ----------
        vsm_scores : list of (doc_id, vsm_score) — from VectorSpaceModel.rank()
        query      : raw query string
        alpha      : weight for VSM (1-alpha goes to topic similarity)

        Returns
        -------
        Re-ranked list of (doc_id, blended_score)
        """
        if self.model is None:
            return vsm_scores

        q_topic = self.query_topic_vector(query, lang)
        blended = []
        for doc_id, vsm_score in vsm_scores:
            d_topic = self._doc_topic_vectors.get(doc_id, np.zeros(self.n_topics))
            ts = self._topic_similarity(q_topic, d_topic)
            blended_score = alpha * vsm_score + (1 - alpha) * ts
            blended.append((doc_id, blended_score))

        blended.sort(key=lambda x: x[1], reverse=True)
        return blended

    def get_doc_topic_vector(self, doc_id: str) -> np.ndarray:
        return self._doc_topic_vectors.get(doc_id, np.zeros(self.n_topics))

    # ── Interpretability ──────────────────────────────────────────────────────

    def top_topics(self, query: str, top_n: int = 3, lang: str | None = None) -> list[dict]:
        """Return top topics for a query with their representative keywords."""
        q_topic = self.query_topic_vector(query, lang)
        top_indices = np.argsort(q_topic)[::-1][:top_n]
        results = []
        for idx in top_indices:
            if q_topic[idx] < 0.01:
                continue
            keywords = [
                word for word, _ in self.model.show_topic(int(idx), topn=8)
            ]
            results.append({
                "topic_id": int(idx),
                "probability": float(q_topic[idx]),
                "keywords": keywords,
            })
        return results

    def topic_word_matrix(self) -> list[dict]:
        """Return all topics with their top 10 words (for visualisation)."""
        if self.model is None:
            return []
        topics = []
        for i in range(self.n_topics):
            words = self.model.show_topic(i, topn=10)
            topics.append({
                "topic_id": i,
                "words": [w for w, _ in words],
                "weights": [round(p, 4) for _, p in words],
            })
        return topics
