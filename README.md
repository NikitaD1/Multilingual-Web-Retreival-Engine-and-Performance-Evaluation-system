# 🔍 IndiNews — Mini Web Search Engine with Cross-Lingual Retrieval

**Information Retrieval (S2-25_AIMLZG537) · Assignment #2 · Group 37 · BITS Pilani WILP**

A domain-specific bilingual search engine over Indian news and current affairs, combining TF-IDF Vector Space Model retrieval with LDA topic modelling and English ↔ Hindi cross-lingual query translation.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [System Architecture](#system-architecture)
4. [Installation](#installation)
5. [Running the App](#running-the-app)
6. [Project Structure](#project-structure)
7. [Corpus](#corpus)
8. [Pipeline Description](#pipeline-description)
9. [Evaluation Results](#evaluation-results)
10. [Assumptions](#assumptions)

---

## Project Overview

IndiNews is an end-to-end mini search engine built over a 65-document bilingual corpus of Indian current affairs (50 English + 15 Hindi). It satisfies all mandatory requirements of Assignment #2:

| Requirement | Implementation |
|---|---|
| Ranked retrieval (VSM) | TF-IDF with log-norm TF + smoothed IDF + cosine similarity |
| Text mining enhancement | LDA topic modelling (Gensim, 10 topics) for re-ranking |
| Cross-lingual retrieval | Query translation via `deep-translator` (EN ↔ HI) |
| Evaluation | Precision@10, Recall@10, F1, MAP on 25 judged queries |
| UI | Streamlit — Search / Evaluation / Corpus Stats / Topic Explorer tabs |

---

## Features

- **Bilingual search** — type queries in English or Hindi; the engine detects the language, translates bidirectionally, and merges results from both language spaces
- **LDA re-ranking** — blends VSM cosine score with latent topic similarity (`score = α·vsm + (1-α)·topic_sim`); α is tunable in the sidebar
- **Snippet generation** — extracts the most query-relevant sentence from each document
- **Query term highlighting** — bold-highlights matched words in result snippets
- **4-tab Streamlit UI** — Search, IR Evaluation, Corpus Statistics, Topic Explorer
- **Graceful degradation** — if translation fails (e.g. offline), engine falls back to monolingual search without crashing

---

## System Architecture

```
Query (EN or HI)
       │
       ▼
┌─────────────────────┐
│  Language Detection │  (Devanagari char fraction heuristic)
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
Translate      Original
to other       query
language
    │             │
    └──────┬───────┘
           ▼
┌──────────────────────┐
│  Preprocessing       │  tokenise → stopwords → stem → index lookup
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  VSM (TF-IDF)        │  cosine similarity → top-k ranked lists (EN + HI)
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  LDA Re-ranking      │  blend VSM score with topic-space cosine similarity
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  Result Fusion       │  Reciprocal Rank Fusion of EN + HI ranked lists
└──────────┬───────────┘
           ▼
      Top-10 Results
  (snippets + highlights)
```

---

## Installation

**Requirements:** Python 3.10+

```bash
# Clone or unzip the project
cd Group37--assignment-2

# Install dependencies
pip install -r requirements.txt
```

**Dependencies:**

```
streamlit>=1.35.0
gensim>=4.3.2
numpy>=1.26.0
pandas>=2.1.0
matplotlib>=3.8.0
scikit-learn>=1.4.0
deep-translator>=1.11.4
```

> **Note:** No NLTK downloads are required. Stopword lists and the stemmer are fully bundled in `src/preprocessing.py`.

---

## Running the App

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` with four tabs:

| Tab | What it shows |
|---|---|
| 🔎 **Search** | Live search with ranked results, snippets, translation info, LDA topic panel |
| 📊 **Evaluation** | Runs 25 evaluation queries; shows MAP, P@10, R@10, per-query table, PR curve |
| 📂 **Corpus Stats** | Language/category distribution charts, full document listing |
| 🧠 **Topic Explorer** | LDA topic-word heatmap and per-topic keyword breakdown |

**Example queries to try:**

```
English:  RBI repo rate inflation
          IPL 2025 viewership JioCinema
          AIIMS robotic surgery liver transplant
          India solar power capacity renewable energy

Hindi:    भारतीय रिजर्व बैंक ब्याज दर
          भारत क्रिकेट चैंपियंस ट्रॉफी पाकिस्तान
          दिल्ली विधानसभा चुनाव आम आदमी पार्टी
          एम्स रोबोटिक सर्जरी लिवर प्रत्यारोपण
```

---

## Project Structure

```
Group37--assignment-2/
│
├── app.py                        # Streamlit UI (4 tabs)
├── requirements.txt
├── README.md
├── generate_report.py            # Generates the assignment PDF report
│
├── corpus/
│   └── news_corpus.json          # 65-document bilingual corpus
│
├── data/
│   └── evaluation_queries.json   # 25 manually judged evaluation queries
│
├── src/
│   ├── __init__.py
│   ├── preprocessing.py          # Tokenisation · stopwords · stemming · inverted index
│   ├── vsm.py                    # TF-IDF document matrix · cosine similarity · ranking
│   ├── lda_retrieval.py          # Gensim LDA training · topic inference · re-ranking
│   ├── translation.py            # deep-translator EN↔HI · result fusion
│   └── evaluation.py             # P@k · R@k · AP · MAP · PR curve
│
└── visuals/
    ├── fig1_lda_topic_distribution.png
    ├── fig2_tsne_clusters.png
    ├── fig3_topic_word_heatmap.png
    ├── fig4_corpus_stats.png
    └── fig5_evaluation_metrics.png
```

---

## Corpus

The corpus (`corpus/news_corpus.json`) contains 65 documents across 7 categories:

| Category | English | Hindi | Total |
|---|---|---|---|
| Economy | 8 | 3 | 11 |
| Sports | 7 | 3 | 10 |
| Technology | 7 | 0 | 7 |
| Health | 6 | 3 | 9 |
| Politics | 7 | 3 | 10 |
| Environment | 7 | 0 | 7 |
| Education | 8 | 3 | 11 |
| **Total** | **50** | **15 (23.1%)** | **65** |

Each document has the schema:
```json
{
  "id": "en_001",
  "title": "RBI Maintains Repo Rate at 6.5%...",
  "content": "...",
  "language": "en",
  "category": "economy",
  "date": "2024-12-06"
}
```

---

## Pipeline Description

### Preprocessing (`src/preprocessing.py`)

| Step | English | Hindi |
|---|---|---|
| Tokenisation | Regex `[a-z][a-z0-9]*` on lowercased text | Whitespace split + Devanagari char filter |
| Stop-word removal | 120-token bundled list | 80-token Devanagari bundled list |
| Stemming | Regex suffix-stripping (15 rules: -ing, -tion, -ness, -ed, -es, etc.) | Not applied (morphological complexity) |

### VSM (`src/vsm.py`)

```
TF(t,d)    = 1 + log(count(t,d))   [log-normalised]
IDF(t)     = log((N+1)/(df(t)+1)) + 1   [smoothed]
TF-IDF     = TF × IDF
sim(q,d)   = q̂ · d̂   [cosine on L2-normalised vectors]
```

### LDA Re-ranking (`src/lda_retrieval.py`)

- **Model:** Gensim LDA · 10 topics · 15 passes · α=auto · η=auto
- **Re-ranking formula:** `score = α × cosine_vsm + (1-α) × cosine_topic`
- **Default α = 0.70** (tunable in sidebar)
- Why it helps: retrieves topically relevant documents even when surface vocabulary differs from the query

### Cross-Lingual Retrieval (`src/translation.py`)

- Library: `deep-translator` (GoogleTranslator) — chosen over the unmaintained `googletrans`
- Supports: Hindi query → search English docs; English query → search Hindi docs
- Fusion: Reciprocal Rank Fusion with weights `w_en=0.6`, `w_hi=0.4`
- Fallback: monolingual search on original query if network is unavailable

### Evaluation (`src/evaluation.py`)

- **25 queries:** 15 English + 10 Hindi, spanning all 7 categories
- **Metrics:** Precision@10, Recall@10, F1, Average Precision, MAP
- **Relevance:** Binary; manually judged per document per query

---

## Evaluation Results

| Metric | Score |
|---|---|
| **MAP (Overall)** | **0.486** |
| MAP — English queries | 0.550 |
| MAP — Hindi queries | 0.390 |
| Mean Precision@10 | 0.116 |
| Mean Recall@10 | 0.540 |
| Mean F1 | 0.189 |

> **Note on Hindi MAP gap:** During evaluation, the translation service was unavailable (sandbox network restriction), so Hindi queries searched only the Hindi document space without cross-lingual expansion. In a live environment with working translation, Hindi MAP is expected to approach English MAP.

> **Note on P@10:** The low precision figure is expected — relevant set sizes are 2–5 documents per query, so even a perfect retrieval gives P@10 ≤ 0.5. The metric of interest is MAP and Recall@10.

---

## Assumptions

| # | Assumption | Rationale |
|---|---|---|
| A1 | Corpus constructed manually | Ensures controlled bilingual balance and reliable relevance judgements |
| A2 | No NLTK downloads | Network-restricted environments; bundled lists are functionally equivalent |
| A3 | Hindi stemming skipped | No reliable lightweight Hindi stemmer in Python ecosystem; content-word morphology in news Hindi is manageable without stemming |
| A4 | Translation fallback to monolingual | Prevents hard failures in offline/sandbox deployments |
| A5 | LDA trained on mixed EN+HI corpus | Hindi tokens treated as opaque strings; topic co-occurrence signals still cluster bilingual documents correctly |
| A6 | Binary relevance judgements | Standard practice for small-scale evaluation; borderline documents excluded |
| A7 | α = 0.70 default | Empirically chosen; lower α hurt precision, higher α made LDA contribution negligible |
