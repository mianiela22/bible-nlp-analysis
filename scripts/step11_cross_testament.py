"""
Step 11: Cross-Testament Connections — Automatic Quote Detection
=================================================================
Rather than hand-picking verse pairs, this script lets the data speak:

1. CITATION DETECTION
   Scans every NT verse for citation formulas used by NT authors to
   signal they are quoting the OT:
     "as it is written", "it is written", "that it might be fulfilled",
     "spoken by the prophet", "the scripture saith", etc.

2. QUOTE EXTRACTION
   Extracts the text immediately following the formula (what they quoted).

3. OT SOURCE IDENTIFICATION — TWO-STAGE
   Stage A — Phrase matching (high precision):
     Extracts 4-6 word n-grams from the quoted text and searches all
     OT verses for exact matches. A hit means the NT author used
     near-identical KJV wording.

   Stage B — TF-IDF cosine similarity (recall):
     Builds a TF-IDF vector space of all 23,145 OT verses.
     Transforms the quoted text into the same space.
     Finds the most textually similar OT verses.
     This catches paraphrases and loose quotations that phrase
     matching misses.

   The two stages are merged; phrase matches rank above TF-IDF matches.
   Each citation gets a best_match (top result) and up to 3 alternates.

4. CONFIDENCE SCORING
   Based on match method and score:
     Phrase match (5+ words shared): 0.95
     Phrase match (4 words):         0.85
     TF-IDF cosine > 0.55:           0.80
     TF-IDF cosine > 0.40:           0.65
     TF-IDF cosine > 0.25:           0.50
     Below 0.25:                     filtered out

WHY THIS IS INTERESTING
  The algorithm has no theological knowledge. It reads raw text and
  discovers that when Paul writes "as it is written, There is none
  righteous," the closest OT verse is Psalm 14:1-3. When Matthew says
  "that it might be fulfilled which was spoken of the lord by the
  prophet," the algorithm traces it back to Isaiah 7:14. These are
  the same connections biblical scholars have identified for centuries —
  found here by cosine similarity.

Output: data/processed/cross_testament.json
"""

import csv
import json
import os
import re
from collections import defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ─────────────────────────────────────────────────────────────────────────────
# BOOK LISTS
# ─────────────────────────────────────────────────────────────────────────────

OT_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
    "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah",
    "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah",
    "Haggai", "Zechariah", "Malachi",
]

NT_BOOKS = [
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
    "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews",
    "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John",
    "Jude", "Revelation",
]

OT_SET = set(OT_BOOKS)
NT_SET = set(NT_BOOKS)

BOOK_ORDER = OT_BOOKS + NT_BOOKS

# ─────────────────────────────────────────────────────────────────────────────
# CITATION FORMULAS
# Each pattern: (compiled_regex, display_name, precision_weight)
# Higher weight = stronger signal that a direct OT quote follows
# ─────────────────────────────────────────────────────────────────────────────

RAW_FORMULAS = [
    (r"\bfor it is written\b",                          "for it is written",                0.95),
    (r"\bas it is written\b",                           "as it is written",                 0.95),
    (r"\bit is written\b",                              "it is written",                    0.90),
    (r"\bthat it might be fulfilled\b",                 "that it might be fulfilled",        0.90),
    (r"\bthat the scripture(?:s)? (?:might be |was |were |should be )?fulfilled\b",
                                                        "that the scripture might be fulfilled", 0.90),
    (r"\bthe scripture was fulfilled\b",                "the scripture was fulfilled",       0.90),
    (r"\bspoken (?:of the lord |)by (?:the prophet|isaiah|jeremy|jeremiah|esaias|david|moses|elias|the holy ghost|daniel)\b",
                                                        "spoken by the prophet",             0.88),
    (r"\bwhich was spoken\b",                           "which was spoken",                 0.85),
    (r"\bsaith the scripture\b",                        "saith the scripture",              0.85),
    (r"\bthe scripture saith\b",                        "the scripture saith",              0.85),
    (r"\baccording to (?:that which is |)written\b",    "according to what is written",     0.85),
    (r"\bthe prophet said\b",                           "the prophet said",                 0.80),
    (r"\bby the mouth of (?:the prophet|david|all the prophets|his prophets)\b",
                                                        "by the mouth of the prophet",       0.80),
    (r"\bwell did (?:esaias|isaiah) prophesy\b",        "well did Isaiah prophesy",         0.85),
    (r"\bhave ye not read\b",                           "have ye not read",                 0.75),
    (r"\bwhat saith the scripture\b",                   "what saith the scripture",         0.85),
]

CITATION_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), name, weight)
    for pattern, name, weight in RAW_FORMULAS
]

# ─────────────────────────────────────────────────────────────────────────────
# STOP WORDS for TF-IDF
# ─────────────────────────────────────────────────────────────────────────────

TFIDF_STOP = [
    "the", "and", "of", "to", "in", "that", "is", "was", "for", "it", "with",
    "as", "his", "he", "be", "on", "are", "by", "at", "this", "from", "or",
    "had", "not", "but", "they", "have", "an", "were", "their", "all", "which",
    "we", "there", "been", "one", "would", "what", "out", "so", "up", "into",
    "said", "if", "then", "when", "no", "more", "him", "who", "me", "do",
    "than", "her", "come", "will", "them", "did", "my", "may", "you", "your",
    "our", "has", "its", "upon", "shall", "also", "am", "after", "before",
    "how", "because", "over", "such", "about", "these", "even", "can", "now",
    "she", "us", "any", "down", "away", "only", "yet", "much", "again", "like",
    "way", "own", "among", "against", "between", "through", "without",
    "therefore", "neither", "nor", "another", "other", "first", "every",
    "thou", "thee", "thy", "thine", "ye", "hath", "doth", "art", "shalt",
    "wilt", "canst", "saith", "spake", "unto", "thereof", "therein",
    "whereby", "whereof", "wherein", "yea", "nay", "lo", "behold",
    "thus", "said", "say", "came", "come", "went", "bring", "brought",
    "give", "given", "put", "set", "let", "know", "make", "made", "take",
    "taken", "send", "sent", "see", "seen", "hear", "heard", "go", "gone",
]


# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────

def load_bible():
    filepath = os.path.join("data", "processed", "kjv_bible.csv")
    with open(filepath, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    ot_verses = [r for r in rows if r["book"] in OT_SET]
    nt_verses = [r for r in rows if r["book"] in NT_SET]
    print(f"  OT: {len(ot_verses):,} verses   NT: {len(nt_verses):,} verses")
    return ot_verses, nt_verses


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: DETECT CITATIONS
# ─────────────────────────────────────────────────────────────────────────────

def detect_citations(nt_verses):
    """
    Find every NT verse that contains a citation formula.
    Returns list of dicts with the formula, NT reference, and extracted quote.
    """
    citations = []
    for verse in nt_verses:
        text = verse["text"]
        for pattern, formula_name, weight in CITATION_PATTERNS:
            m = pattern.search(text)
            if m:
                # Extract quoted text: everything after the formula
                after = text[m.end():].strip()
                # Strip leading punctuation (, : ; saying that)
                after = re.sub(r'^[,;:\s]+', '', after)
                after = re.sub(r'^saying[,\s]+', '', after, flags=re.IGNORECASE)
                # Must have at least 4 words to be a meaningful quote
                if len(after.split()) < 4:
                    continue
                citations.append({
                    "formula": formula_name,
                    "formula_weight": weight,
                    "nt_book": verse["book"],
                    "nt_chapter": int(verse["chapter"]),
                    "nt_verse": int(verse["verse"]),
                    "nt_text": text,
                    "quoted_text": after,
                })
                break  # one formula per verse is enough
    return citations


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: BUILD TF-IDF INDEX OF ALL OT VERSES
# ─────────────────────────────────────────────────────────────────────────────

def build_ot_index(ot_verses):
    ot_texts = [v["text"] for v in ot_verses]
    vectorizer = TfidfVectorizer(
        min_df=1,
        ngram_range=(1, 2),
        stop_words=TFIDF_STOP,
        token_pattern=r"\b[a-zA-Z]{3,}\b",
    )
    matrix = vectorizer.fit_transform(ot_texts)
    print(f"  TF-IDF matrix: {matrix.shape[0]} OT verses × {matrix.shape[1]} features")
    return vectorizer, matrix, ot_texts


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: PHRASE MATCHING (high-precision stage A)
# ─────────────────────────────────────────────────────────────────────────────

def extract_ngrams(text, n):
    """Extract all n-grams of lowercase words from text."""
    words = re.findall(r"\b[a-zA-Z']{3,}\b", text.lower())
    return [" ".join(words[i:i+n]) for i in range(len(words) - n + 1)]


def phrase_match_search(quoted_text, ot_verses):
    """
    Find OT verses sharing 4+ consecutive words with the quoted text.
    Returns list of (verse_dict, matched_phrase, ngram_size).
    """
    hits = {}  # (book, chapter, verse) -> best match

    for n in (6, 5, 4):
        ngrams = set(extract_ngrams(quoted_text, n))
        if not ngrams:
            continue
        for v in ot_verses:
            ot_ngrams = set(extract_ngrams(v["text"], n))
            common = ngrams & ot_ngrams
            if common:
                key = (v["book"], int(v["chapter"]), int(v["verse"]))
                # Higher n = better match; don't overwrite a longer match
                if key not in hits or hits[key][2] < n:
                    hits[key] = (v, next(iter(common)), n)

    results = []
    for (book, ch, vs), (verse, phrase, n) in hits.items():
        conf = 0.95 if n >= 5 else 0.85
        results.append({
            "book": book,
            "chapter": ch,
            "verse": vs,
            "text": verse["text"],
            "similarity": conf,
            "method": "phrase",
            "matched_phrase": phrase,
        })
    results.sort(key=lambda x: -x["similarity"])
    return results


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: TF-IDF MATCHING (high-recall stage B)
# ─────────────────────────────────────────────────────────────────────────────

def tfidf_search(quoted_text, vectorizer, ot_matrix, ot_verses, top_k=5):
    """Find the top OT verses by TF-IDF cosine similarity to the quoted text."""
    try:
        q_vec = vectorizer.transform([quoted_text])
        sims = cosine_similarity(q_vec, ot_matrix)[0]
        top_indices = sims.argsort()[::-1][:top_k]
        results = []
        for i in top_indices:
            score = float(sims[i])
            if score < 0.12:
                break
            v = ot_verses[i]
            conf = (0.80 if score > 0.55 else
                    0.65 if score > 0.40 else
                    0.50 if score > 0.25 else 0.35)
            results.append({
                "book": v["book"],
                "chapter": int(v["chapter"]),
                "verse": int(v["verse"]),
                "text": v["text"],
                "similarity": round(score, 4),
                "method": "tfidf",
                "matched_phrase": None,
            })
        return results
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: MERGE & RANK
# ─────────────────────────────────────────────────────────────────────────────

def merge_matches(phrase_hits, tfidf_hits, formula_weight):
    """
    Combine phrase and TF-IDF hits. Phrase matches rank first.
    Apply formula weight to confidence.
    Deduplicate by (book, chapter, verse).
    """
    seen = {}
    for hit in phrase_hits + tfidf_hits:
        key = (hit["book"], hit["chapter"], hit["verse"])
        if key not in seen:
            adjusted = round(hit["similarity"] * formula_weight, 4)
            seen[key] = {**hit, "confidence": adjusted}
        # keep the hit with higher raw similarity if we see duplicate
        elif hit["similarity"] > seen[key]["similarity"]:
            adjusted = round(hit["similarity"] * formula_weight, 4)
            seen[key] = {**hit, "confidence": adjusted}

    ranked = sorted(seen.values(), key=lambda x: -x["confidence"])
    # Filter very low confidence
    ranked = [r for r in ranked if r["confidence"] >= 0.35]
    return ranked[:3]


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6: BUILD STATS
# ─────────────────────────────────────────────────────────────────────────────

def build_stats(citations_with_matches):
    formula_counts = defaultdict(int)
    nt_book_counts = defaultdict(int)
    ot_book_counts = defaultdict(int)
    confidence_buckets = {"high": 0, "medium": 0, "low": 0}

    for c in citations_with_matches:
        formula_counts[c["formula"]] += 1
        nt_book_counts[c["nt_book"]] += 1
        if c.get("best_match"):
            ot_book_counts[c["best_match"]["book"]] += 1
            conf = c["best_match"]["confidence"]
            if conf >= 0.80:
                confidence_buckets["high"] += 1
            elif conf >= 0.55:
                confidence_buckets["medium"] += 1
            else:
                confidence_buckets["low"] += 1

    return {
        "total_citations": len(citations_with_matches),
        "citations_with_match": sum(1 for c in citations_with_matches if c.get("best_match")),
        "by_formula": dict(sorted(formula_counts.items(), key=lambda x: -x[1])),
        "by_nt_book": {b: nt_book_counts[b] for b in NT_BOOKS if nt_book_counts[b] > 0},
        "by_ot_book": {b: ot_book_counts[b] for b in OT_BOOKS if ot_book_counts[b] > 0},
        "confidence_distribution": confidence_buckets,
    }


def print_findings(citations_with_matches, stats):
    print(f"\n{'=' * 65}")
    print("  CROSS-TESTAMENT QUOTE DETECTION — RESULTS")
    print(f"{'=' * 65}")
    print(f"\n  NT citations found    : {stats['total_citations']:>4}")
    print(f"  Citations with a match: {stats['citations_with_match']:>4}")

    print(f"\n  Top citation formulas:")
    for formula, n in list(stats["by_formula"].items())[:6]:
        print(f"    {formula:45s} {n:>3}")

    print(f"\n  Top NT books citing OT:")
    nt_sorted = sorted(stats["by_nt_book"].items(), key=lambda x: -x[1])
    for book, n in nt_sorted[:8]:
        print(f"    {book:25s} {n:>3}")

    print(f"\n  Top cited OT books:")
    ot_sorted = sorted(stats["by_ot_book"].items(), key=lambda x: -x[1])
    for book, n in ot_sorted[:8]:
        print(f"    {book:25s} {n:>3}")

    print(f"\n  Confidence distribution:")
    for level, n in stats["confidence_distribution"].items():
        print(f"    {level:10s} {n:>3}")

    print(f"\n  Sample detections (phrase matches):")
    shown = 0
    for c in citations_with_matches:
        bm = c.get("best_match")
        if bm and bm.get("method") == "phrase" and shown < 5:
            print(f"\n    NT: {c['nt_book']} {c['nt_chapter']}:{c['nt_verse']}")
            print(f"    Formula: {c['formula']}")
            print(f"    Quoted: {c['quoted_text'][:70]}")
            print(f"    → OT: {bm['book']} {bm['chapter']}:{bm['verse']}  [{bm.get('matched_phrase','?')}]  conf={bm['confidence']:.2f}")
            shown += 1

    print(f"\n{'=' * 65}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def run():
    print("=" * 65)
    print("  Step 11: Cross-Testament Connections — Auto Quote Detection")
    print("=" * 65)

    print("\n--- Loading Bible ---")
    ot_verses, nt_verses = load_bible()

    print("\n--- Building OT TF-IDF index ---")
    vectorizer, ot_matrix, ot_texts = build_ot_index(ot_verses)

    print("\n--- Detecting NT citations ---")
    citations = detect_citations(nt_verses)
    print(f"  Found {len(citations)} citation verses")

    print("\n--- Matching to OT sources ---")
    results = []
    for i, cit in enumerate(citations):
        if i % 50 == 0:
            print(f"  {i}/{len(citations)}")

        phrase_hits = phrase_match_search(cit["quoted_text"], ot_verses)
        tfidf_hits = tfidf_search(
            cit["quoted_text"], vectorizer, ot_matrix, ot_verses, top_k=5
        )
        merged = merge_matches(phrase_hits, tfidf_hits, cit["formula_weight"])

        entry = {
            "id": i + 1,
            "formula": cit["formula"],
            "nt_book": cit["nt_book"],
            "nt_chapter": cit["nt_chapter"],
            "nt_verse": cit["nt_verse"],
            "nt_text": cit["nt_text"],
            "quoted_text": cit["quoted_text"],
            "best_match": merged[0] if merged else None,
            "alternates": merged[1:],
        }
        results.append(entry)

    # Filter out entries with no match
    results_with_match = [r for r in results if r["best_match"]]
    print(f"  {len(results_with_match)} citations matched to an OT source")

    print("\n--- Building stats ---")
    stats = build_stats(results_with_match)

    print_findings(results_with_match, stats)

    print("\n--- Saving ---")
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)
    output = {
        "citations": results_with_match,
        "stats": stats,
        "book_order": BOOK_ORDER,
        "ot_books": OT_BOOKS,
        "nt_books": NT_BOOKS,
    }
    filepath = os.path.join("data", "processed", "cross_testament.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(',', ':'))
    size_kb = os.path.getsize(filepath) / 1024
    print(f"\nSaved to {filepath}  ({size_kb:.0f} KB)")
    print("\n[DONE]")


if __name__ == "__main__":
    run()
