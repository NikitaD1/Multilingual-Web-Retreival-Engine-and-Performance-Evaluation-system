"""
preprocessing.py
----------------
Language-aware preprocessing pipeline:
  - Tokenisation
  - Stop-word removal (English + Hindi — bundled, no network required)
  - Stemming (regex rules, no NLTK download needed)
  - Inverted index construction
"""

import re
import json
import math
from collections import defaultdict

_EN_STOPS = {
    "i","me","my","myself","we","our","ours","ourselves","you","your","yours",
    "yourself","yourselves","he","him","his","himself","she","her","hers",
    "herself","it","its","itself","they","them","their","theirs","themselves",
    "what","which","who","whom","this","that","these","those","am","is","are",
    "was","were","be","been","being","have","has","had","having","do","does",
    "did","doing","a","an","the","and","but","if","or","because","as","until",
    "while","of","at","by","for","with","about","against","between","into",
    "through","during","before","after","above","below","to","from","up","down",
    "in","out","on","off","over","under","again","further","then","once","here",
    "there","when","where","why","how","all","both","each","few","more","most",
    "other","some","such","no","nor","not","only","own","same","so","than",
    "too","very","s","t","can","will","just","don","should","now","d","ll","m",
    "o","re","ve","y","ain","also","said","would","could","one","two","new",
    "may","per","cent","including","according","however","among","well",
}

_HI_STOPS = {
    "का","की","के","में","है","हैं","और","को","से","पर","यह","वह","एक","इस",
    "इन","उन","जो","जब","तो","भी","नहीं","तक","लिए","कि","था","थी","थे","हो",
    "हुआ","हुई","हुए","जा","रहा","रही","रहे","कर","किया","किए","किसी","कोई",
    "सभी","ने","द्वारा","बाद","पहले","अब","यहां","वहां","जैसे","या","लेकिन",
    "अगर","तथा","साथ","बहुत","अधिक","कम","ही","तब","जहां","वहीं","जिस","जिन",
    "उस","उन्हें","उसे","उसकी","उसका","उसके","इसका","इसकी","इसके","इसे",
    "इन्हें","इनका","हमारे","आपके","उनके","व","एवं","आदि","जैसा","जैसी",
    "इसी","उसी","जिसे","जिसका","दो","तीन","कई","सकता","सकती","सकते","होता",
    "होती","होते","गया","गई","गए","करने","होने","करना","होना","अपने","अपनी",
    "अपना","हम","आप","वे","ये","फिर","अभी","नए","नई","नया","हर","कुछ",
}

_SUFFIX_RULES = [
    (r"ing$",""), (r"tion$","t"), (r"tions$","t"), (r"ational$","ate"),
    (r"alism$","al"), (r"ness$",""), (r"ment$",""), (r"ments$",""),
    (r"ities$","ity"), (r"ity$",""), (r"ful$",""), (r"ous$",""),
    (r"ive$",""), (r"ize$",""), (r"ise$",""), (r"ers$","er"),
    (r"ies$","y"), (r"es$",""), (r"ed$",""), (r"s$",""),
]

def _stem_en(word):
    if len(word) <= 3:
        return word
    for pattern, replacement in _SUFFIX_RULES:
        new = re.sub(pattern, replacement, word)
        if new != word and len(new) >= 3:
            return new
    return word

def detect_language(text):
    devanagari = sum(1 for ch in text if "\u0900" <= ch <= "\u097f")
    return "hi" if devanagari / max(len(text), 1) > 0.15 else "en"

def tokenise(text, lang="en"):
    if lang == "hi":
        text = re.sub(r"[^\u0900-\u097f\s]", " ", text)
        return [t for t in text.split() if t.strip()]
    text = text.lower()
    return re.findall(r"[a-z][a-z0-9]*", text)

def remove_stopwords(tokens, lang="en"):
    stops = _HI_STOPS if lang == "hi" else _EN_STOPS
    return [t for t in tokens if t not in stops]

def stem(tokens, lang="en"):
    if lang == "en":
        return [_stem_en(t) for t in tokens]
    return tokens

def preprocess(text, lang=None):
    if lang is None:
        lang = detect_language(text)
    tokens = tokenise(text, lang)
    tokens = remove_stopwords(tokens, lang)
    tokens = stem(tokens, lang)
    return [t for t in tokens if len(t) > 1]


class InvertedIndex:
    def __init__(self):
        self.index = defaultdict(lambda: defaultdict(list))
        self.doc_tokens = {}
        self.doc_lengths = {}
        self.num_docs = 0

    def build(self, documents):
        self.num_docs = len(documents)
        for doc in documents:
            doc_id = doc["id"]
            lang = doc.get("language", "en")
            raw_text = doc["title"] + " " + doc["content"]
            tokens = preprocess(raw_text, lang)
            self.doc_tokens[doc_id] = tokens
            self.doc_lengths[doc_id] = len(tokens)
            for pos, term in enumerate(tokens):
                self.index[term][doc_id].append(pos)

    def term_freq(self, term, doc_id):
        return len(self.index.get(term, {}).get(doc_id, []))

    def doc_freq(self, term):
        return len(self.index.get(term, {}))

    def idf(self, term):
        df = self.doc_freq(term)
        if df == 0:
            return 0.0
        return math.log((self.num_docs + 1) / (df + 1)) + 1

    def tfidf(self, term, doc_id):
        tf = self.term_freq(term, doc_id)
        if tf == 0:
            return 0.0
        return (1 + math.log(tf)) * self.idf(term)

    def vocabulary(self):
        return set(self.index.keys())

    @property
    def all_doc_ids(self):
        return list(self.doc_tokens.keys())


def build_index(corpus_path):
    with open(corpus_path, "r", encoding="utf-8") as f:
        documents = json.load(f)
    idx = InvertedIndex()
    idx.build(documents)
    return idx, documents
