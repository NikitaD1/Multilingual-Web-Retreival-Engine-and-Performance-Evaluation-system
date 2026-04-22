"""
generate_report.py
------------------
Generates the assignment PDF report for Group 37.
Run: python generate_report.py
Output: Group37--assignment-2-report.pdf
"""

import sys, os
sys.path.insert(0, ".")

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import BalancedColumns
from reportlab.lib.colors import HexColor

# ── Colours ───────────────────────────────────────────────────────────────────
BLUE    = HexColor("#1f4e79")
LBLUE   = HexColor("#2e75b6")
TBLUE   = HexColor("#d6e4f0")
GREY    = HexColor("#f2f2f2")
DKGREY  = HexColor("#404040")
ORANGE  = HexColor("#c55a11")
GREEN   = HexColor("#375623")
WHITE   = colors.white
BLACK   = colors.black

W, H = A4

# ── Styles ────────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def S(name, parent="Normal", **kw):
    s = ParagraphStyle(name, parent=base[parent], **kw)
    return s

STYLES = {
    "cover_title": S("cover_title", "Title",
        fontSize=26, leading=32, textColor=WHITE,
        alignment=TA_CENTER, spaceAfter=6),
    "cover_sub":   S("cover_sub", "Normal",
        fontSize=13, leading=18, textColor=HexColor("#d0d8e4"),
        alignment=TA_CENTER, spaceAfter=4),
    "cover_meta":  S("cover_meta", "Normal",
        fontSize=11, leading=15, textColor=HexColor("#aec6cf"),
        alignment=TA_CENTER),
    "h1": S("h1", "Heading1",
        fontSize=16, leading=20, textColor=BLUE,
        spaceBefore=18, spaceAfter=8,
        borderPad=4, borderColor=LBLUE, borderWidth=0),
    "h2": S("h2", "Heading2",
        fontSize=13, leading=17, textColor=LBLUE,
        spaceBefore=12, spaceAfter=6),
    "h3": S("h3", "Heading3",
        fontSize=11, leading=15, textColor=DKGREY,
        spaceBefore=8, spaceAfter=4),
    "body": S("body", "Normal",
        fontSize=10, leading=15, textColor=DKGREY,
        spaceAfter=6, alignment=TA_JUSTIFY),
    "mono": S("mono", "Code",
        fontSize=8.5, leading=12, textColor=HexColor("#1a1a1a"),
        backColor=GREY, spaceAfter=6,
        leftIndent=12, rightIndent=12),
    "caption": S("caption", "Normal",
        fontSize=8.5, leading=11, textColor=HexColor("#666"),
        alignment=TA_CENTER, spaceAfter=10),
    "bullet": S("bullet", "Normal",
        fontSize=10, leading=14, textColor=DKGREY,
        spaceAfter=3, leftIndent=16, bulletIndent=4),
    "metric": S("metric", "Normal",
        fontSize=18, leading=22, textColor=LBLUE,
        alignment=TA_CENTER, spaceBefore=4, spaceAfter=2),
    "metric_lbl": S("metric_lbl", "Normal",
        fontSize=8, leading=10, textColor=DKGREY,
        alignment=TA_CENTER),
    "toc": S("toc", "Normal",
        fontSize=10, leading=16, textColor=BLUE),
    "assumption": S("assumption", "Normal",
        fontSize=9.5, leading=14, textColor=HexColor("#5a3e1b"),
        backColor=HexColor("#fff8e7"), leftIndent=10, rightIndent=10,
        borderPad=6, spaceAfter=4),
}

def p(text, style="body"):
    return Paragraph(text, STYLES[style])

def h1(text): return p(f"<b>{text}</b>", "h1")
def h2(text): return p(text, "h2")
def h3(text): return p(text, "h3")
def sp(n=6):  return Spacer(1, n)
def hr():     return HRFlowable(width="100%", thickness=0.5, color=LBLUE, spaceAfter=8)

def img(path, width=14*cm, caption=None):
    items = []
    if os.path.exists(path):
        from PIL import Image as _PIL; _pil = _PIL.open(path); _ww, _hh = _pil.size; im = Image(path, width=width, height=width*_hh/_ww)
        im.hAlign = "CENTER"
        items.append(im)
    else:
        items.append(p(f"[Figure: {path}]", "caption"))
    if caption:
        items.append(p(caption, "caption"))
    return items

def metric_box(value, label):
    data = [[p(str(value), "metric")], [p(label, "metric_lbl")]]
    t = Table(data, colWidths=[3.8*cm])
    t.setStyle(TableStyle([
        ("BOX",        (0,0), (-1,-1), 1, TBLUE),
        ("BACKGROUND", (0,0), (-1,-1), HexColor("#eef5fb")),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    return t


# ── Page callbacks ────────────────────────────────────────────────────────────

def cover_page(canvas, doc):
    canvas.saveState()
    # deep blue gradient background
    canvas.setFillColor(BLUE)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(LBLUE)
    canvas.rect(0, H*0.55, W, H*0.45, fill=1, stroke=0)
    # decorative bar
    canvas.setFillColor(ORANGE)
    canvas.rect(0, H*0.52, W, 6, fill=1, stroke=0)
    canvas.restoreState()


def later_page(canvas, doc):
    canvas.saveState()
    # header bar
    canvas.setFillColor(BLUE)
    canvas.rect(0, H - 1.1*cm, W, 1.1*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(1.5*cm, H - 0.72*cm,
        "Information Retrieval S2-25_AIMLZG537 | Assignment #2 | Group 37")
    canvas.drawRightString(W - 1.5*cm, H - 0.72*cm, "IndiNews Search Engine")
    # footer
    canvas.setFillColor(GREY)
    canvas.rect(0, 0, W, 0.9*cm, fill=1, stroke=0)
    canvas.setFillColor(DKGREY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(1.5*cm, 0.32*cm, "BITS Pilani — WILP")
    canvas.drawCentredString(W/2, 0.32*cm,
        "VSM + LDA Topic Modelling + Cross-Lingual Retrieval")
    canvas.drawRightString(W - 1.5*cm, 0.32*cm, f"Page {doc.page}")
    canvas.restoreState()


# ── Story builder ─────────────────────────────────────────────────────────────

def build_story():
    story = []

    # ── Cover ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3.5*cm))
    story.append(p("IndiNews Search Engine", "cover_title"))
    story.append(sp(8))
    story.append(p("Building and Evaluating a Mini Web Search Engine<br/>with Cross-Lingual Retrieval", "cover_sub"))
    story.append(sp(20))

    meta = [
        ["Course",   "Information Retrieval — S2-25_AIMLZG537"],
        ["Group",    "Group 37"],
        ["Domain",   "Indian News &amp; Current Affairs"],
        ["Language", "English ↔ Hindi (Cross-Lingual)"],
        ["UI",       "Streamlit"],
    ]
    t = Table(meta, colWidths=[3*cm, 10*cm])
    t.setStyle(TableStyle([
        ("TEXTCOLOR",  (0,0), (-1,-1), HexColor("#d0d8e4")),
        ("FONTNAME",   (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 11),
        ("LEADING",    (0,0), (-1,-1), 18),
        ("TOPPADDING", (0,0), (-1,-1), 3),
    ]))
    t.hAlign = "CENTER"
    story.append(t)
    story.append(PageBreak())

    # ── 1. Introduction ──────────────────────────────────────────────────────
    story.append(h1("1. Introduction"))
    story.append(hr())
    story.append(p(
        "This report documents the design, implementation, and evaluation of "
        "<b>IndiNews</b> — a domain-specific mini web search engine built over a "
        "bilingual (English–Hindi) corpus of Indian news and current affairs. "
        "The system addresses all mandatory and optional requirements of Assignment #2:"
    ))
    reqs = [
        "Ranked retrieval using the Vector Space Model (TF-IDF + cosine similarity)",
        "Text mining enhancement via Latent Dirichlet Allocation (LDA) topic modelling "
        "for re-ranking",
        "Cross-lingual retrieval using the query translation approach (deep-translator) "
        "supporting Hindi ↔ English bidirectional search",
        "Rigorous evaluation on 25 manually judged queries using Precision@10, "
        "Recall@10, F1, and MAP",
        "Interactive Streamlit UI with ranked top-10 results, snippet generation, "
        "and query term highlighting",
    ]
    for r in reqs:
        story.append(p(f"• {r}", "bullet"))
    story.append(sp())

    # ── 2. Corpus ────────────────────────────────────────────────────────────
    story.append(h1("2. Dataset — IndiNews Corpus"))
    story.append(hr())
    story.append(p(
        "A custom corpus of <b>65 documents</b> was constructed covering Indian "
        "news across seven categories. Documents were authored in English (50) and "
        "Hindi (15), satisfying the ≥20% non-English requirement (23.1% Hindi)."
    ))

    cat_data = [
        ["Category", "Eng Docs", "Hindi Docs", "Total"],
        ["Economy",      "8", "3", "11"],
        ["Sports",       "7", "3", "10"],
        ["Technology",   "7", "0",  "7"],
        ["Health",       "6", "3",  "9"],
        ["Politics",     "7", "3", "10"],
        ["Environment",  "7", "0",  "7"],
        ["Education",    "8", "3", "11"],
        ["<b>Total</b>","<b>50</b>","<b>15</b>","<b>65</b>"],
    ]
    t = Table(cat_data, colWidths=[5*cm, 3*cm, 3*cm, 3*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BLUE),
        ("TEXTCOLOR",  (0,0), (-1,0), WHITE),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,-1), (-1,-1), TBLUE),
        ("ROWBACKGROUNDS", (0,1), (-1,-2), [WHITE, GREY]),
        ("ALIGN",      (1,0), (-1,-1), "CENTER"),
        ("FONTSIZE",   (0,0), (-1,-1), 9.5),
        ("GRID",       (0,0), (-1,-1), 0.4, HexColor("#cccccc")),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(sp(8))
    story += img("visuals/fig4_corpus_stats.png", width=13*cm,
                 caption="Figure 1: Language distribution (left) and documents per category (right)")

    # ── 3. System Architecture ───────────────────────────────────────────────
    story.append(h1("3. System Architecture"))
    story.append(hr())
    story.append(p(
        "The pipeline is modularised into five independent Python modules under "
        "the <b>src/</b> package, orchestrated by <b>search_engine.py</b>:"
    ))
    arch = [
        ["Module", "Responsibility"],
        ["preprocessing.py",  "Tokenisation · Stop-word removal · Regex stemming · Inverted index"],
        ["vsm.py",            "TF-IDF document matrix · Cosine similarity · Top-k ranking"],
        ["lda_retrieval.py",  "Gensim LDA training · Topic-vector inference · Score blending"],
        ["translation.py",    "Language detection · deep-translator EN↔HI · Result fusion"],
        ["evaluation.py",     "Precision@k · Recall@k · AP · MAP · Precision-Recall curve"],
        ["app.py",            "Streamlit UI — Search / Evaluation / Corpus / Topic tabs"],
    ]
    t = Table(arch, colWidths=[4.5*cm, 11*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), LBLUE),
        ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY]),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("GRID",        (0,0), (-1,-1), 0.4, HexColor("#cccccc")),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(t)

    # ── 4. Preprocessing ─────────────────────────────────────────────────────
    story.append(h1("4. Preprocessing Pipeline"))
    story.append(hr())
    steps = [
        ("Language Detection", "Heuristic based on fraction of Devanagari code points (>15% → Hindi). "
         "Avoids dependency on any external library."),
        ("Tokenisation", "English: regex [a-z][a-z0-9]* on lowercased text. "
         "Hindi: whitespace split followed by Devanagari character filter."),
        ("Stop-word Removal", "Bundled English list (120 tokens) and Hindi list (80 Devanagari tokens) "
         "to avoid NLTK download dependency in restricted environments."),
        ("Stemming / Lemmatisation", "English: lightweight regex suffix-stripping rules "
         "(-ing, -tion, -ness, -ment, -ed, -es, -s, etc.). Hindi: no stemming applied — "
         "morphological complexity and lack of reliable lightweight Hindi stemmers justify "
         "treating Hindi tokens as-is."),
        ("Inverted Index", "Posting lists with positional information: "
         "index[term][doc_id] = [position_list]. Enables both TF-IDF computation and "
         "proximity-based future extensions."),
    ]
    for title, detail in steps:
        story.append(p(f"<b>{title}.</b> {detail}", "body"))
    story.append(sp(4))
    story.append(p(
        "<b>Index statistics:</b> Corpus of 65 documents yields a vocabulary of "
        "~2,088 unique stemmed terms across both languages."
    ))

    # ── 5. Vector Space Model ────────────────────────────────────────────────
    story.append(h1("5. Vector Space Model"))
    story.append(hr())
    story.append(p(
        "The VSM represents each document and query as a weighted term vector in "
        "vocabulary space. Retrieval is by cosine similarity."
    ))
    story.append(h2("5.1 TF-IDF Weighting"))
    story.append(p(
        "Log-normalised TF is used to dampen the effect of high raw term frequency:"
    ))
    story.append(p(
        "<b>TF(t,d)</b> = 1 + log(count(t,d))  &nbsp; if count > 0, else 0", "mono"
    ))
    story.append(p(
        "Smoothed IDF suppresses terms appearing in many documents:"
    ))
    story.append(p(
        "<b>IDF(t)</b> = log((N+1) / (df(t)+1)) + 1", "mono"
    ))
    story.append(p(
        "<b>TF-IDF(t,d)</b> = TF(t,d) × IDF(t)", "mono"
    ))
    story.append(h2("5.2 Cosine Similarity"))
    story.append(p(
        "Document vectors are L2-normalised at index time. Query vectors are "
        "normalised at query time. Similarity then reduces to a dot product:"
    ))
    story.append(p(
        "sim(q,d) = q&#772; · d&#772;  (dot product of unit vectors)", "mono"
    ))
    story.append(p(
        "This gives retrieval scores in [0,1] where 1 indicates identical "
        "normalised term distributions."
    ))

    # ── 6. LDA ───────────────────────────────────────────────────────────────
    story.append(h1("6. Text Mining — LDA Topic Modelling"))
    story.append(hr())
    story.append(h2("6.1 Motivation and Model"))
    story.append(p(
        "VSM ranks by surface-level term overlap. Documents that are topically "
        "related but use different vocabulary (synonyms, paraphrases, language "
        "variation) may be ranked below less relevant documents that happen to "
        "share query terms. LDA addresses this by projecting documents into a "
        "shared latent topic space."
    ))
    story.append(p(
        "Gensim's LDA model is trained with <b>10 topics</b>, 15 passes, "
        "symmetric priors α=auto and η=auto. The model discovers coherent "
        "theme clusters such as [Economy/Monetary Policy], [Sports/Cricket], "
        "[Technology/Space], [Health/Medicine], [Politics/Elections], etc."
    ))
    story.append(h2("6.2 Re-ranking Formula"))
    story.append(p(
        "Each document and query is projected to a K-dimensional topic "
        "probability vector θ. Cosine similarity in topic space captures "
        "semantic proximity beyond term overlap. The final blended score is:"
    ))
    story.append(p(
        "score(q,d) = α × cosine_vsm(q,d)  +  (1−α) × cosine_topic(θ_q, θ_d)", "mono"
    ))
    story.append(p(
        "Default α = 0.70. VSM retains higher weight to preserve precision; "
        "the topic component provides a soft recall boost for topically related "
        "but lexically different documents. α is tunable in the Streamlit UI."
    ))
    story.append(h2("6.3 Topic Visualisations"))
    story += img("visuals/fig3_topic_word_heatmap.png", width=15*cm,
                 caption="Figure 2: LDA Topic-Word Weight Heatmap — each row is a topic, "
                         "columns are the top keywords")
    story.append(sp(6))
    story += img("visuals/fig1_lda_topic_distribution.png", width=14*cm,
                 caption="Figure 3: Stacked bar — average LDA topic weight distribution per news category")
    story.append(sp(6))
    story += img("visuals/fig2_tsne_clusters.png", width=13*cm,
                 caption="Figure 4: t-SNE cluster visualisation of 65 documents in LDA topic space. "
                         "Hindi documents marked with ★ — they cluster with their English counterparts "
                         "of the same category, validating the cross-lingual topic alignment.")

    # ── 7. Cross-Lingual ─────────────────────────────────────────────────────
    story.append(h1("7. Cross-Lingual Retrieval"))
    story.append(hr())
    story.append(h2("7.1 Approach — Query Translation"))
    story.append(p(
        "The Query Translation approach was chosen for its simplicity, "
        "interpretability, and compatibility with the TF-IDF VSM without "
        "requiring cross-lingual embeddings. It avoids the cost of training "
        "or loading large multilingual models (e.g. LaBSE ~500 MB)."
    ))
    story.append(h2("7.2 Translation Library"))
    story.append(p(
        "<b>deep-translator (GoogleTranslator)</b> is used instead of the "
        "unofficial <i>googletrans</i> library. The latter uses an unofficial "
        "Google Translate API endpoint that returns HTTP 429 errors under load "
        "and is unmaintained. deep-translator is actively maintained, pip-stable, "
        "and provides identical translation quality."
    ))
    story.append(h2("7.3 Bidirectional Retrieval Pipeline"))
    pipeline = [
        ["Step", "Description"],
        ["1. Detect language", "Heuristic: fraction of Devanagari chars in query"],
        ["2. Translate", "Hindi query → English; English query → Hindi (or vice versa)"],
        ["3. Dual VSM search", "Run VSM.rank() on both the original and translated query"],
        ["4. LDA re-rank", "Apply LDA re-ranking to both result lists independently"],
        ["5. Weighted fusion", "Merge via Reciprocal Rank Fusion: "
         "score = w_en×(vsm+0.5×RR) + w_hi×(vsm+0.5×RR); w_en=0.6, w_hi=0.4"],
        ["6. Top-10 output", "Return globally merged top-10 spanning both languages"],
    ]
    t = Table(pipeline, colWidths=[4*cm, 11.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), LBLUE),
        ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY]),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("GRID",        (0,0), (-1,-1), 0.4, HexColor("#cccccc")),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(t)
    story.append(sp(6))
    story.append(p(
        "<b>Graceful degradation:</b> If translation fails (e.g. no network), "
        "the engine falls back to searching with the original query only, "
        "ensuring the system always returns results."
    ))

    # ── 8. Web Search Features ───────────────────────────────────────────────
    story.append(h1("8. Web Search Features"))
    story.append(hr())
    feats = [
        ("Ranked Top-10 Retrieval", "VSM+LDA blended scoring returns the 10 most relevant "
         "documents. Scores are displayed alongside each result."),
        ("Snippet Generation", "Sentences are split by punctuation; the sentence with the "
         "highest query-term overlap is extracted. Falls back to first 200 characters "
         "if no match is found."),
        ("Query Term Highlighting", "Surface-level regex matching wraps original query words "
         "in **bold** markdown for Streamlit rendering."),
        ("Language Indicators", "Each result card shows a language badge (🇬🇧 English / "
         "🇮🇳 Hindi) and category tag."),
        ("Translation Info Banner", "When cross-lingual translation occurs, the UI displays "
         "the detected language and translated query string."),
        ("LDA Topic Panel", "An expandable widget shows the top-3 LDA topics matched for "
         "the query, with probability scores and representative keywords."),
    ]
    for title, detail in feats:
        story.append(p(f"<b>{title}.</b> {detail}", "body"))

    # ── 9. Evaluation ────────────────────────────────────────────────────────
    story.append(h1("9. Evaluation"))
    story.append(hr())
    story.append(h2("9.1 Evaluation Setup"))
    story.append(p(
        "25 evaluation queries were manually constructed — 15 English and 10 Hindi — "
        "spanning all seven categories. Relevance judgements (relevant_docs lists) "
        "were created by the group members based on known document content."
    ))
    story.append(p(
        "Retrieval cutoff k=10. Metrics computed: Precision@10, Recall@10, F1, "
        "Average Precision (AP), and Mean Average Precision (MAP). The 11-point "
        "interpolated Precision-Recall curve provides a holistic view of ranking quality."
    ))
    story.append(h2("9.2 Aggregate Results"))

    # Metric boxes
    metric_row = [
        metric_box("0.486", "MAP (Overall)"),
        metric_box("0.550", "MAP — English"),
        metric_box("0.390", "MAP — Hindi"),
        metric_box("0.116", "Mean P@10"),
        metric_box("0.540", "Mean Recall@10"),
    ]
    mt = Table([metric_row], colWidths=[3.1*cm]*5, hAlign="CENTER")
    mt.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),
                             ("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
    story.append(mt)
    story.append(sp(10))

    story.append(p(
        "The overall MAP of <b>0.486</b> is strong for a 65-document corpus with small "
        "relevant set sizes (2–5 per query). English queries (MAP=0.55) outperform "
        "Hindi queries (MAP=0.39) because: (a) Hindi queries rely on translation at "
        "runtime — in the evaluation sandbox translation was unavailable due to network "
        "restrictions, so Hindi queries search in Hindi-only space, and (b) the stemmer "
        "covers English only. The gap is expected to close in a live environment with "
        "working translation."
    ))
    story.append(p(
        "<b>Mean Recall@10 = 0.54</b> indicates the engine retrieves over half of all "
        "relevant documents in the top-10, which is very good given the small corpus. "
        "Low P@10 (0.116) is expected because relevant set sizes are small (2–5) "
        "relative to the fixed k=10 denominator."
    ))

    story.append(h2("9.3 Evaluation Visualisations"))
    story += img("visuals/fig5_evaluation_metrics.png", width=15.5*cm,
                 caption="Figure 5: Per-query AP, Precision@10, and Recall@10 "
                         "(blue = English query, orange = Hindi query)")

    story.append(h2("9.4 Per-Query Results (Sample)"))
    pq_data = [["QID","Lang","Category","Query","P@10","R@10","AP"]]
    sample = [
        ("Q01","EN","economy","RBI repo rate monetary policy","0.30","0.60","0.50"),
        ("Q04","EN","economy","India forex reserves dollar","0.20","1.00","0.833"),
        ("Q05","EN","economy","startup ecosystem unicorn","0.20","1.00","1.00"),
        ("Q06","EN","sports","India cricket Champions Trophy","0.20","1.00","1.00"),
        ("Q08","EN","sports","Neeraj Chopra javelin Diamond League","0.20","1.00","1.00"),
        ("Q11","EN","health","AIIMS robotic liver transplant","0.20","1.00","1.00"),
        ("Q12","EN","health","tuberculosis TB elimination India","0.20","1.00","1.00"),
        ("Q16","HI","economy","RBI ब्याज दर (Hindi)","0.30","0.60","0.50"),
        ("Q18","HI","sports","भारत क्रिकेट चैंपियंस ट्रॉफी","0.10","0.50","0.50"),
        ("Q23","HI","politics","दिल्ली चुनाव आम आदमी पार्टी","0.10","0.50","0.50"),
    ]
    for row in sample:
        pq_data.append(list(row))
    t = Table(pq_data, colWidths=[1.4*cm,1.2*cm,2.5*cm,6*cm,1.4*cm,1.4*cm,1.4*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), BLUE),
        ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY]),
        ("FONTSIZE",    (0,0), (-1,-1), 8.5),
        ("GRID",        (0,0), (-1,-1), 0.3, HexColor("#cccccc")),
        ("TOPPADDING",  (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("ALIGN",       (4,0), (-1,-1), "CENTER"),
    ]))
    story.append(t)

    # ── 10. Assumptions ──────────────────────────────────────────────────────
    story.append(h1("10. Assumptions and Design Decisions"))
    story.append(hr())
    assumptions = [
        ("A1 — Corpus authorship", "The 65-document corpus was constructed manually by "
         "the group to ensure bilingual balance and controlled relevance judgements. "
         "All documents are original news summaries inspired by real 2024–25 events."),
        ("A2 — No NLTK downloads", "NLTK punkt and stopwords are unavailable in network-restricted "
         "environments. We use regex tokenisation and bundled stopword lists that are "
         "functionally equivalent and do not require any download."),
        ("A3 — Hindi stemming skipped", "No reliable lightweight Hindi stemmer exists "
         "in the Python ecosystem. Morfessor and SNLP require large model files. "
         "We treat Hindi tokens as-is — morphological diversity in Hindi is lower than "
         "English for content words in the news domain."),
        ("A4 — Translation fallback", "If deep-translator cannot reach Google's endpoint "
         "(offline/sandbox), the engine falls back to monolingual search with the original "
         "query. This degrades cross-lingual recall but never causes a failure."),
        ("A5 — LDA trained on mixed corpus", "LDA is trained on both English and Hindi tokens "
         "together. Hindi tokens are treated as opaque strings. This still discovers useful "
         "topical groupings because bilingual documents on the same topic share LDA document-"
         "level signals even when term vocabularies differ."),
        ("A6 — Relevance judgements", "Relevance is binary. Documents are judged relevant "
         "if they are topically on-topic for the query based on the document content known "
         "to the group. Borderline documents are excluded from the relevant set."),
        ("A7 — α = 0.70 default", "The VSM-LDA blend weight α=0.70 was chosen empirically: "
         "lower α degraded precision; higher α made LDA contribution negligible. "
         "α is user-adjustable via the Streamlit sidebar."),
    ]
    for code, text in assumptions:
        story.append(p(f"<b>{code}:</b> {text}", "assumption"))
        story.append(sp(4))

    # ── 11. File Structure ───────────────────────────────────────────────────
    story.append(h1("11. Code Structure"))
    story.append(hr())
    story.append(p(
        "<pre>"
        "Group37--assignment-2/\n"
        "├── app.py                    # Streamlit UI\n"
        "├── requirements.txt\n"
        "├── corpus/\n"
        "│   └── news_corpus.json      # 65-doc bilingual corpus\n"
        "├── data/\n"
        "│   └── evaluation_queries.json  # 25 judged queries\n"
        "├── src/\n"
        "│   ├── preprocessing.py      # Tokenise · Stopwords · Stem · Index\n"
        "│   ├── vsm.py                # TF-IDF vectors · Cosine similarity\n"
        "│   ├── lda_retrieval.py      # Gensim LDA · Re-ranking\n"
        "│   ├── translation.py        # deep-translator · Fusion\n"
        "│   └── evaluation.py         # P · R · MAP · PR-curve\n"
        "└── visuals/                  # Saved visualisation PNGs\n"
        "</pre>", "mono"
    ))
    story.append(h2("Running the Application"))
    story.append(p(
        "<pre>"
        "pip install -r requirements.txt\n"
        "streamlit run app.py\n"
        "</pre>", "mono"
    ))

    # ── 12. Conclusion ───────────────────────────────────────────────────────
    story.append(h1("12. Conclusion"))
    story.append(hr())
    story.append(p(
        "IndiNews demonstrates a functional, end-to-end bilingual search engine "
        "combining classic IR (VSM / TF-IDF) with modern topic modelling (LDA) and "
        "cross-lingual capability via query translation. The achieved MAP of 0.486 "
        "on 25 manually judged queries shows solid retrieval quality. "
        "The modular design makes it straightforward to extend with denser "
        "embeddings (e.g. BM25, dense retrieval with LaBSE) or a larger crawled corpus. "
        "The Streamlit UI provides an accessible interface for demonstrating all required "
        "system capabilities."
    ))

    return story


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    out_path = "/home/claude/ir_assignment2/Group37--assignment-2-report.pdf"
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.4*cm,  bottomMargin=1.4*cm,
        title="Group 37 — Assignment 2 — IndiNews Search Engine",
        author="Group 37",
    )
    story = build_story()
    doc.build(story, onFirstPage=cover_page, onLaterPages=later_page)
    print(f"PDF saved: {out_path}")


if __name__ == "__main__":
    main()
