"""
app.py
------
Streamlit UI for the Mini Web Search Engine
Group 37 | Information Retrieval S2-25_AIMLZG537 | Assignment #2
"""

import sys
import json
import time
import logging
import threading
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.WARNING)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IndiNews Search Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.result-card {
    background: #f8f9fa;
    border-left: 4px solid #1f77b4;
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 14px;
}
.result-title { font-size: 1.05rem; font-weight: 700; color: #1a1a2e; }
.result-meta  { font-size: 0.80rem; color: #666; margin: 2px 0 6px 0; }
.result-snip  { font-size: 0.92rem; color: #333; line-height: 1.5; }
.score-badge  {
    display: inline-block;
    background: #1f77b4; color: white;
    font-size: 0.75rem; border-radius: 12px;
    padding: 2px 8px; margin-left: 8px;
}
.lang-badge {
    display: inline-block;
    background: #ff7f0e; color: white;
    font-size: 0.72rem; border-radius: 10px;
    padding: 1px 7px; margin-right: 4px;
}
.metric-card {
    text-align: center;
    background: #eef2ff;
    border-radius: 8px;
    padding: 16px;
    margin: 4px;
}
.metric-val  { font-size: 1.8rem; font-weight: 700; color: #1f77b4; }
.metric-lbl  { font-size: 0.82rem; color: #555; }
</style>
""", unsafe_allow_html=True)


# ── Engine singleton ──────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_engine():
    from src.search_engine import SearchEngine
    engine = SearchEngine()
    engine.build(n_topics=10)
    return engine


# ── Helpers ───────────────────────────────────────────────────────────────────

def flag(lang: str) -> str:
    return "🇮🇳 Hindi" if lang == "hi" else "🇬🇧 English"


def render_result(rank: int, r: dict) -> None:
    lang_badge = f'<span class="lang-badge">{flag(r["language"])}</span>'
    score_badge = f'<span class="score-badge">score: {r["score"]}</span>'
    meta = f'{lang_badge} {r["category"].title()} &nbsp;·&nbsp; {r["date"]} {score_badge}'
    st.markdown(
        f"""<div class="result-card">
        <div class="result-title">{rank}. {r["title"]}</div>
        <div class="result-meta">{meta}</div>
        <div class="result-snip">{r["snippet"]}</div>
        </div>""",
        unsafe_allow_html=True,
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/d/d3/BITS_Pilani-Logo.svg", width=120)
    st.markdown("## ⚙️ Engine Settings")
    use_lda = st.toggle("LDA Re-ranking", value=True,
                        help="Blend topic similarity with VSM cosine score")
    top_k = st.slider("Results per query", 5, 10, 10)
    alpha_lda = st.slider("VSM weight (α)", 0.4, 0.9, 0.7, 0.05,
                          help="α=VSM weight; (1-α)=LDA topic weight")
    st.markdown("---")
    st.markdown("**Group 37**  \nS2-25_AIMLZG537  \nAssignment #2")


# ── Header ────────────────────────────────────────────────────────────────────

st.title("🔍 IndiNews — Mini Web Search Engine")
st.caption("Indian Current Affairs · English ↔ Hindi · VSM + LDA + Cross-Lingual Retrieval")

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_search, tab_eval, tab_corpus, tab_topics = st.tabs([
    "🔎 Search", "📊 Evaluation", "📂 Corpus Stats", "🧠 Topic Explorer"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: SEARCH
# ══════════════════════════════════════════════════════════════════════════════

with tab_search:
    st.subheader("Search Indian News (English or Hindi)")

    col_q, col_btn = st.columns([5, 1])
    with col_q:
        query = st.text_input(
            "Query",
            placeholder="e.g.  RBI repo rate inflation  |  भारतीय रिजर्व बैंक ब्याज दर",
            label_visibility="collapsed",
        )
    with col_btn:
        search_clicked = st.button("Search 🔍", use_container_width=True)

    # Example queries
    st.markdown(
        "**Try:** &nbsp;"
        "`RBI repo rate inflation` &nbsp;|&nbsp; "
        "`IPL 2025 viewership` &nbsp;|&nbsp; "
        "`भारत क्रिकेट चैंपियंस ट्रॉफी` &nbsp;|&nbsp; "
        "`AIIMS robotic surgery` &nbsp;|&nbsp; "
        "`डिजिटल इंडिया यूपीआई`"
    )

    if search_clicked and query.strip():
        with st.spinner("Searching …"):
            engine = load_engine()
            t0 = time.time()
            out = engine.search(query, top_k=top_k, use_lda=use_lda, cross_lingual=True)
            elapsed = time.time() - t0

        qinfo = out["query_info"]
        results = out["results"]
        topics = out["topics"]

        # ── Translation info ──────────────────────────────────────────────────
        if qinfo["was_translated"]:
            if qinfo["detected_lang"] == "hi":
                st.info(
                    f"🌐 Hindi query detected.  "
                    f"Translated to English: **\"{qinfo['en_query']}\"**  "
                    f"— searching both English and Hindi documents."
                )
            else:
                st.info(
                    f"🌐 English query detected.  "
                    f"Translated to Hindi: **\"{qinfo['hi_query']}\"**  "
                    f"— searching both English and Hindi documents."
                )

        st.markdown(
            f"**{len(results)}** results &nbsp;·&nbsp; "
            f"{'LDA + VSM' if use_lda else 'VSM only'} &nbsp;·&nbsp; "
            f"⏱ {elapsed*1000:.0f} ms"
        )
        st.markdown("---")

        if not results:
            st.warning("No results found. Try a different query.")
        else:
            for i, r in enumerate(results, 1):
                render_result(i, r)

        # ── LDA topic panel ───────────────────────────────────────────────────
        if use_lda and topics:
            with st.expander("🧠 LDA Topics matched for this query"):
                for t in topics:
                    st.markdown(
                        f"**Topic {t['topic_id']}** "
                        f"(probability: `{t['probability']:.3f}`)  \n"
                        f"Keywords: {', '.join(t['keywords'])}"
                    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: EVALUATION
# ══════════════════════════════════════════════════════════════════════════════

with tab_eval:
    st.subheader("📊 IR Evaluation — Precision · Recall · MAP")
    st.markdown(
        "Evaluates the engine on **25 manually judged queries** (15 English + 10 Hindi) "
        "using Precision@10, Recall@10, and Mean Average Precision (MAP)."
    )

    run_eval = st.button("▶ Run Evaluation", key="run_eval")

    if run_eval:
        with st.spinner("Running evaluation on 25 queries …"):
            from src.evaluation import run_evaluation
            engine = load_engine()
            ev = run_evaluation(engine, use_lda=use_lda)

        # ── Aggregate metrics ─────────────────────────────────────────────────
        st.markdown("### Aggregate Metrics")
        cols = st.columns(5)
        metrics = [
            ("MAP", ev["map"]),
            ("Mean Precision@10", ev["mean_precision"]),
            ("Mean Recall@10", ev["mean_recall"]),
            ("EN MAP", ev["en_map"]),
            ("HI MAP", ev["hi_map"]),
        ]
        for col, (label, val) in zip(cols, metrics):
            col.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-val">{val:.3f}</div>'
                f'<div class="metric-lbl">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # ── Per-query table ───────────────────────────────────────────────────
        st.markdown("### Per-Query Results")
        rows = []
        for q in ev["per_query"]:
            rows.append({
                "ID": q["id"],
                "Lang": flag(q["lang"]),
                "Category": q["category"],
                "Query": q["query"][:55] + ("…" if len(q["query"]) > 55 else ""),
                "Relevant": q["relevant_count"],
                "P@10": q["precision"],
                "R@10": q["recall"],
                "F1": q["f1"],
                "AP": q["ap"],
            })
        df = pd.DataFrame(rows)
        st.dataframe(
            df.style.background_gradient(subset=["P@10", "R@10", "AP"], cmap="Blues"),
            use_container_width=True,
            hide_index=True,
        )

        # ── Charts ────────────────────────────────────────────────────────────
        st.markdown("### Visualisations")
        c1, c2 = st.columns(2)

        with c1:
            fig, ax = plt.subplots(figsize=(6, 3.5))
            x = range(len(ev["per_query"]))
            ids = [q["id"] for q in ev["per_query"]]
            aps = [q["ap"] for q in ev["per_query"]]
            colors = ["#1f77b4" if q["lang"] == "en" else "#ff7f0e"
                      for q in ev["per_query"]]
            ax.bar(ids, aps, color=colors)
            ax.axhline(ev["map"], color="red", linestyle="--", label=f"MAP={ev['map']:.3f}")
            ax.set_xlabel("Query ID")
            ax.set_ylabel("Average Precision")
            ax.set_title("AP per Query (🔵 EN | 🟠 HI)")
            ax.set_xticks(list(ids))
            ax.set_xticklabels(list(ids), rotation=90, fontsize=7)
            ax.legend(fontsize=8)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        with c2:
            fig2, ax2 = plt.subplots(figsize=(6, 3.5))
            cats = {}
            for q in ev["per_query"]:
                c = q["category"]
                cats.setdefault(c, []).append(q["ap"])
            cat_names = list(cats.keys())
            cat_maps = [sum(v) / len(v) for v in cats.values()]
            ax2.barh(cat_names, cat_maps, color="#2ca02c")
            ax2.set_xlabel("Mean AP")
            ax2.set_title("Mean AP by Category")
            plt.tight_layout()
            st.pyplot(fig2)
            plt.close()

        # ── Precision-Recall curve ────────────────────────────────────────────
        st.markdown("### Precision–Recall Curve (interpolated, 11-point)")
        recall_levels = [i / 10 for i in range(11)]
        all_pr_curves = []
        for q in ev["per_query"]:
            relevant = set()
            # reconstruct from hits
            relevant = set(q["hits"])
            if not relevant:
                continue
            retrieved = q["retrieved"]
            pr_curve = []
            for rl in recall_levels:
                # find precision at recall ≥ rl
                max_p = 0.0
                hits = 0
                for rank, doc_id in enumerate(retrieved, 1):
                    if doc_id in relevant:
                        hits += 1
                    r = hits / max(len(relevant), 1)
                    if r >= rl:
                        max_p = max(max_p, hits / rank)
                pr_curve.append(max_p)
            all_pr_curves.append(pr_curve)

        if all_pr_curves:
            mean_pr = [sum(c[i] for c in all_pr_curves) / len(all_pr_curves)
                       for i in range(11)]
            fig3, ax3 = plt.subplots(figsize=(7, 3.5))
            ax3.plot(recall_levels, mean_pr, "b-o", markersize=4)
            ax3.fill_between(recall_levels, mean_pr, alpha=0.15)
            ax3.set_xlabel("Recall")
            ax3.set_ylabel("Precision")
            ax3.set_title("Interpolated 11-Point Precision–Recall Curve")
            ax3.set_xlim(0, 1); ax3.set_ylim(0, 1.05)
            ax3.grid(True, alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig3)
            plt.close()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: CORPUS STATS
# ══════════════════════════════════════════════════════════════════════════════

with tab_corpus:
    st.subheader("📂 Corpus Statistics")
    engine = load_engine()
    stats = engine.corpus_stats()

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total Documents", stats["total"])
    s2.metric("English", stats["english"])
    s3.metric("Hindi", stats["hindi"])
    s4.metric("Hindi %", f"{stats['hindi_pct']}%")
    st.metric("Vocabulary Size (unique stems)", stats["vocabulary_size"])

    # Language distribution pie
    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(
            [stats["english"], stats["hindi"]],
            labels=["English", "Hindi"],
            colors=["#1f77b4", "#ff7f0e"],
            autopct="%1.1f%%",
            startangle=90,
        )
        ax.set_title("Language Distribution")
        st.pyplot(fig)
        plt.close()

    with c2:
        fig2, ax2 = plt.subplots(figsize=(5, 4))
        cats = stats["categories"]
        ax2.barh(list(cats.keys()), list(cats.values()), color="#17becf")
        ax2.set_xlabel("Number of Documents")
        ax2.set_title("Documents per Category")
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()

    st.markdown("---")
    st.markdown("### Raw Corpus")
    with open(engine.corpus_path, "r", encoding="utf-8") as f:
        docs = json.load(f)
    df = pd.DataFrame([
        {"ID": d["id"], "Language": flag(d["language"]),
         "Category": d["category"], "Date": d["date"],
         "Title": d["title"][:70]}
        for d in docs
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: TOPIC EXPLORER
# ══════════════════════════════════════════════════════════════════════════════

with tab_topics:
    st.subheader("🧠 LDA Topic Explorer")
    st.markdown(
        "Displays the 10 latent topics discovered by LDA on the corpus.  \n"
        "Each topic is described by its top 10 contributing words.  \n"
        "**How LDA improves retrieval:** by projecting documents and queries "
        "into topic space, the engine can retrieve topically similar documents "
        "even when they do not share exact vocabulary with the query."
    )

    engine = load_engine()
    topics = engine.topic_words()

    if not topics:
        st.warning("LDA model not ready.")
    else:
        # Heatmap-style topic-word matrix
        topic_labels = [f"T{t['topic_id']}" for t in topics]
        all_words = []
        for t in topics:
            all_words.extend(t["words"])
        unique_words = list(dict.fromkeys(all_words))[:40]

        matrix = np.zeros((len(topics), len(unique_words)))
        for i, t in enumerate(topics):
            for word, weight in zip(t["words"], t["weights"]):
                if word in unique_words:
                    j = unique_words.index(word)
                    matrix[i, j] = weight

        fig, ax = plt.subplots(figsize=(14, 5))
        im = ax.imshow(matrix, aspect="auto", cmap="Blues")
        ax.set_xticks(range(len(unique_words)))
        ax.set_xticklabels(unique_words, rotation=75, ha="right", fontsize=7)
        ax.set_yticks(range(len(topics)))
        ax.set_yticklabels(topic_labels, fontsize=9)
        ax.set_title("Topic–Word Weight Heatmap (LDA)")
        plt.colorbar(im, ax=ax, fraction=0.02)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        st.markdown("---")
        st.markdown("### Per-Topic Keywords")
        cols = st.columns(2)
        for i, t in enumerate(topics):
            with cols[i % 2]:
                st.markdown(
                    f"**Topic {t['topic_id']}:** "
                    + " · ".join(
                        f"`{w}`" for w, wt in zip(t["words"], t["weights"])
                    )
                )
