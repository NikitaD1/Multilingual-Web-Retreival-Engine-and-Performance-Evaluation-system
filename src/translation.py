"""
translation.py
--------------
Cross-lingual retrieval via query translation.

Approach chosen: Query Translation
  - Hindi query → translate to English → search English corpus
  - English query → translate to Hindi  → search Hindi corpus
  - Bidirectional retrieval: run BOTH and merge results

Library: deep-translator (GoogleTranslator)
  Chosen over googletrans (unofficial, unreliable) for its stability
  and active maintenance.

Assumption: Network access available at runtime. A graceful fallback
  returns the original text if translation fails (e.g., offline environment).
"""

import re
import logging
from src.preprocessing import detect_language

logger = logging.getLogger(__name__)

try:
    from deep_translator import GoogleTranslator
    _TRANSLATOR_AVAILABLE = True
except ImportError:
    _TRANSLATOR_AVAILABLE = False
    logger.warning("deep-translator not installed. Translation will be skipped.")


# ── Translation helpers ────────────────────────────────────────────────────────

def translate(text: str, source: str, target: str) -> str:
    """
    Translate *text* from *source* to *target* language code.
    Returns original text on failure.
    """
    if not _TRANSLATOR_AVAILABLE:
        return text
    if source == target:
        return text
    try:
        translator = GoogleTranslator(source=source, target=target)
        translated = translator.translate(text)
        return translated if translated else text
    except Exception as e:
        logger.warning(f"Translation failed ({source}→{target}): {e}")
        return text


def translate_hi_to_en(text: str) -> str:
    return translate(text, source="hi", target="en")


def translate_en_to_hi(text: str) -> str:
    return translate(text, source="en", target="hi")


# ── Cross-lingual query processor ─────────────────────────────────────────────

class CrossLingualProcessor:
    """
    Given a query, produces both an English version and a Hindi version
    for use in bilingual retrieval.
    """

    def process(self, query: str) -> dict:
        """
        Detect language, translate bidirectionally.

        Returns
        -------
        dict with keys:
            original       : original query
            detected_lang  : 'en' or 'hi'
            en_query       : English version (translated if original was Hindi)
            hi_query       : Hindi version  (translated if original was English)
            was_translated : bool
        """
        detected = detect_language(query)

        if detected == "hi":
            en_query = translate_hi_to_en(query)
            hi_query = query
            was_translated = en_query.strip().lower() != query.strip().lower()
        else:
            hi_query = translate_en_to_hi(query)
            en_query = query
            was_translated = True  # always translated for EN→HI

        return {
            "original": query,
            "detected_lang": detected,
            "en_query": en_query,
            "hi_query": hi_query,
            "was_translated": was_translated,
        }


def merge_results(
    en_results: list[tuple[str, float]],
    hi_results: list[tuple[str, float]],
    en_weight: float = 0.6,
    hi_weight: float = 0.4,
    top_k: int = 10,
) -> list[tuple[str, float]]:
    """
    Combine ranked lists from English and Hindi searches using weighted fusion.
    Reciprocal Rank Fusion blended with normalised scores.
    """
    score_map: dict[str, float] = {}

    def _add(results, weight):
        for rank, (doc_id, score) in enumerate(results):
            # Reciprocal rank component for position signal
            rr = 1.0 / (rank + 1)
            combined = weight * (score + 0.5 * rr)
            score_map[doc_id] = score_map.get(doc_id, 0.0) + combined

    _add(en_results, en_weight)
    _add(hi_results, hi_weight)

    merged = sorted(score_map.items(), key=lambda x: x[1], reverse=True)
    return merged[:top_k]
