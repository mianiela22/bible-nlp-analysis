"""
Step 8: Topic Modeling with LDA
================================
Uses Latent Dirichlet Allocation (LDA) to automatically discover
recurring themes across the Bible's 1,189 chapters.

LDA treats each chapter as a "document" and finds clusters of words
that tend to appear together — without being told what topics to look for.
The algorithm just sees word patterns. Yet it will naturally rediscover:

  - Sacrifice / ritual law (Leviticus, Numbers vocabulary)
  - War / conquest (Joshua, Judges, Samuel, Kings vocabulary)
  - Wisdom / instruction (Proverbs, Ecclesiastes vocabulary)
  - Prayer / praise (Psalms vocabulary)
  - Covenant / promise (Patriarchal narratives)
  - Prophecy / judgment (Isaiah, Jeremiah vocabulary)
  - Jesus's ministry (Gospels vocabulary)
  - Grace / faith (Pauline epistles vocabulary)
  - Apocalyptic / vision (Daniel, Revelation vocabulary)

This is the "unsupervised" proof of the Bible's theological coherence:
the machine finds the same themes theologians have identified for centuries.

Document unit: chapter (1,189 chapters, ~8–50 verses each)
Number of topics: 12 (N_TOPICS, adjustable)
Algorithm: sklearn LDA with online learning
"""

import csv
import json
import os
import re
from collections import defaultdict

import numpy as np
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

# ============================================================
# CONFIGURATION
# ============================================================

N_TOPICS = 12
RANDOM_SEED = 42
N_TOP_WORDS = 20       # words per topic stored in JSON
N_TOP_CHAPTERS = 6     # top chapters stored per topic

TOPIC_COLORS = [
    "#8B4513",  # saddle brown
    "#4169E1",  # royal blue
    "#2ecc71",  # emerald green
    "#e74c3c",  # red
    "#9370DB",  # medium purple
    "#DAA520",  # goldenrod
    "#DC143C",  # crimson
    "#2E8B57",  # sea green
    "#E67E22",  # pumpkin orange
    "#5F9EA0",  # cadet blue
    "#B8860B",  # dark goldenrod
    "#6A5ACD",  # slate blue
]

BOOK_ORDER = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
    "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah",
    "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah",
    "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
    "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews",
    "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John",
    "Jude", "Revelation",
]

# Stop words: removed from LDA vocabulary.
# Covers ultra-common English, KJV archaic forms, and numerals.
# We keep theologically meaningful nouns (israel, people, priest, etc.)
# because they HELP distinguish topics. What we remove is grammatical noise.
STOP_WORDS = [
    # English function words
    "the", "and", "of", "to", "in", "that", "is", "was", "for",
    "it", "with", "as", "his", "he", "be", "on", "are", "by", "at",
    "this", "from", "or", "had", "not", "but", "they", "have", "an",
    "were", "their", "all", "which", "we", "there", "been", "one",
    "would", "what", "out", "so", "up", "into", "said", "if", "then",
    "when", "no", "more", "him", "who", "me", "do", "than", "her",
    "come", "will", "them", "did", "my", "may", "you", "your", "our",
    "has", "its", "upon", "shall", "also", "am", "after", "before",
    "how", "because", "over", "such", "about", "these", "even",
    "can", "now", "she", "two", "three", "four", "five", "six",
    "us", "any", "down", "away", "only", "yet", "much", "again",
    "like", "way", "own", "among", "against", "between", "through",
    "without", "according", "every", "thus", "therefore", "moreover",
    "neither", "nor", "another", "other", "their", "first",
    # KJV archaic forms
    "thou", "thee", "thy", "thine", "ye", "hath", "doth", "art",
    "shalt", "wilt", "canst", "wouldest", "shouldest", "hast",
    "saith", "spake", "unto", "thereof", "therein", "therewith",
    "whereby", "whereof", "wherein", "nevertheless", "notwithstanding",
    "whosoever", "whatsoever", "yea", "nay", "lo", "behold", "thus",
    # Ultra-common Bible words that appear in virtually every topic
    # (too generic to help distinguish themes)
    "lord", "god", "said", "say", "came", "come", "went", "bring",
    "brought", "give", "given", "put", "set", "let", "know", "make",
    "made", "take", "taken", "send", "sent", "see", "seen", "hear",
    "heard", "go", "gone", "day", "days", "time", "times", "year",
    "years", "man", "men", "woman", "son", "hand", "place",
]


# ============================================================
# STEP A: Load Bible data
# ============================================================

def load_bible():
    """Load the parsed Bible CSV."""
    filepath = os.path.join("data", "processed", "kjv_bible.csv")
    with open(filepath, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows):,} verses")
    return rows


# ============================================================
# STEP B: Build chapter-level documents
# ============================================================

def build_chapter_documents(verses):
    """
    Aggregate all verses in each chapter into one document.
    Returns:
        documents:     list of chapter text strings (1,189 total)
        chapter_order: list of (book, chapter_num) tuples
        verses_by_chapter: dict (book, chapter) -> list of verse texts
    """
    chapter_texts = defaultdict(list)
    chapter_order = []
    seen = set()

    for verse in verses:
        key = (verse["book"], int(verse["chapter"]))
        chapter_texts[key].append(verse["text"])
        if key not in seen:
            seen.add(key)
            chapter_order.append(key)

    documents = []
    for key in chapter_order:
        # Join verses, lowercase, strip punctuation
        raw = " ".join(chapter_texts[key])
        raw = raw.lower()
        raw = re.sub(r"[^\w\s]", " ", raw)
        documents.append(raw)

    verses_by_chapter = {k: v for k, v in chapter_texts.items()}

    print(f"Built {len(documents)} chapter documents")
    return documents, chapter_order, verses_by_chapter


# ============================================================
# STEP C: Run LDA
# ============================================================

def run_lda(documents):
    """
    Vectorize chapters and run LDA.

    CountVectorizer settings:
      max_df=0.80  — ignore words in >80% of chapters (too generic)
      min_df=8     — word must appear in at least 8 chapters
      max_features=2500 — top vocabulary by frequency

    LDA settings:
      doc_topic_prior (alpha) = 0.1  — sparse per-chapter topic mix
      topic_word_prior (eta)  = 0.01 — sparse per-topic word distribution
      These priors make topics more focused and interpretable.
    """
    print(f"  Vectorizing with max_df=0.80, min_df=8, max_features=2500...")
    vectorizer = CountVectorizer(
        max_df=0.80,
        min_df=8,
        max_features=2500,
        stop_words=STOP_WORDS,
        token_pattern=r"\b[a-zA-Z]{3,}\b",  # only alphabetic, 3+ chars
    )
    dtm = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()
    print(f"  Vocabulary: {len(feature_names)} terms, matrix: {dtm.shape}")

    print(f"  Running LDA: {N_TOPICS} topics, seed={RANDOM_SEED}...")
    lda = LatentDirichletAllocation(
        n_components=N_TOPICS,
        random_state=RANDOM_SEED,
        max_iter=25,
        learning_method="online",
        doc_topic_prior=0.1,
        topic_word_prior=0.01,
        evaluate_every=5,
        perp_tol=0.1,
    )
    doc_topics = lda.fit_transform(dtm)  # shape: (n_chapters, n_topics)
    print(f"  LDA complete. doc_topics shape: {doc_topics.shape}")

    return lda, doc_topics, feature_names


# ============================================================
# STEP D: Extract topic information
# ============================================================

def extract_topic_words(lda, feature_names):
    """Get top words per topic with normalized weights."""
    topics = []
    for topic_weights in lda.components_:
        normalized = topic_weights / topic_weights.sum()
        top_indices = normalized.argsort()[::-1][:N_TOP_WORDS]
        topics.append([
            {"word": feature_names[i], "weight": round(float(normalized[i]), 6)}
            for i in top_indices
        ])
    return topics


def build_book_profiles(doc_topics, chapter_order):
    """
    Aggregate chapter-level topic distributions to book level.
    Each book gets a list of N_TOPICS weights summing to 1.
    """
    book_sums = defaultdict(lambda: np.zeros(N_TOPICS))
    book_counts = defaultdict(int)

    for i, (book, _chapter) in enumerate(chapter_order):
        book_sums[book] += doc_topics[i]
        book_counts[book] += 1

    book_profiles = {}
    for book in BOOK_ORDER:
        if book in book_sums:
            avg = book_sums[book] / book_counts[book]
            avg = avg / avg.sum()  # normalize
            book_profiles[book] = [round(float(w), 4) for w in avg]
        else:
            book_profiles[book] = [0.0] * N_TOPICS

    return book_profiles


def get_top_chapters_per_topic(doc_topics, chapter_order, verses_by_chapter):
    """For each topic, find the N_TOP_CHAPTERS chapters where it dominates."""
    top_per_topic = []
    for topic_idx in range(N_TOPICS):
        scores = doc_topics[:, topic_idx]
        top_indices = scores.argsort()[::-1][:N_TOP_CHAPTERS]
        chapters = []
        for i in top_indices:
            book, chapter = chapter_order[i]
            preview_verses = verses_by_chapter.get((book, chapter), [""])
            preview = preview_verses[0][:160] if preview_verses else ""
            chapters.append({
                "book": book,
                "chapter": chapter,
                "score": round(float(scores[i]), 4),
                "preview": preview,
            })
        top_per_topic.append(chapters)
    return top_per_topic


# ============================================================
# STEP E: Print findings (to help assign manual labels)
# ============================================================

def print_findings(topic_words, book_profiles, top_chapters):
    """Display topics so we can manually assign meaningful labels."""
    print(f"\n{'=' * 70}")
    print(f"  LDA TOPIC MODELING — {N_TOPICS} TOPICS DISCOVERED")
    print(f"{'=' * 70}")

    # Find dominant book per topic
    dominant_books = []
    for topic_idx in range(N_TOPICS):
        book_scores = {book: book_profiles[book][topic_idx] for book in BOOK_ORDER}
        top_books = sorted(book_scores.items(), key=lambda x: x[1], reverse=True)[:4]
        dominant_books.append(top_books)

    for topic_idx in range(N_TOPICS):
        words = [w["word"] for w in topic_words[topic_idx][:10]]
        print(f"\n  Topic {topic_idx:>2}:  {' · '.join(words[:6])}")
        print(f"   Books:  {', '.join(b for b, _ in dominant_books[topic_idx])}")
        print(f"   Top chapter: {top_chapters[topic_idx][0]['book']} {top_chapters[topic_idx][0]['chapter']}")

    print(f"\n{'=' * 70}")


# ============================================================
# STEP F: Save results as JSON
# ============================================================

def save_results(topic_words, book_profiles, top_chapters, doc_topics, chapter_order):
    """Save all topic modeling data for the website dashboard."""
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)

    # Build dominant-book summary per topic (top 5 books)
    topic_dominant_books = []
    for topic_idx in range(N_TOPICS):
        book_scores = {book: book_profiles[book][topic_idx] for book in BOOK_ORDER}
        top_books = sorted(book_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        topic_dominant_books.append([
            {"book": b, "weight": round(w, 4)} for b, w in top_books
        ])

    # Default topic labels derived from top words (users can rename in UI)
    default_labels = [
        " · ".join(w["word"] for w in topic_words[i][:3])
        for i in range(N_TOPICS)
    ]

    output = {
        "n_topics": N_TOPICS,
        "book_order": BOOK_ORDER,
        "topics": [
            {
                "id": i,
                "default_label": default_labels[i],
                "color": TOPIC_COLORS[i % len(TOPIC_COLORS)],
                "top_words": topic_words[i],
                "dominant_books": topic_dominant_books[i],
                "top_chapters": top_chapters[i],
            }
            for i in range(N_TOPICS)
        ],
        "book_profiles": book_profiles,
    }

    filepath = os.path.join("data", "processed", "topic_modeling.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    size_kb = os.path.getsize(filepath) / 1024
    print(f"\nSaved to {filepath}  ({size_kb:.1f} KB)")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  Step 8: Topic Modeling with LDA")
    print("=" * 70)

    print("\n--- Loading Bible data ---")
    verses = load_bible()

    print("\n--- Building chapter documents ---")
    documents, chapter_order, verses_by_chapter = build_chapter_documents(verses)

    print("\n--- Running LDA ---")
    lda, doc_topics, feature_names = run_lda(documents)

    print("\n--- Extracting topic information ---")
    topic_words = extract_topic_words(lda, feature_names)
    book_profiles = build_book_profiles(doc_topics, chapter_order)
    top_chapters = get_top_chapters_per_topic(doc_topics, chapter_order, verses_by_chapter)

    print_findings(topic_words, book_profiles, top_chapters)

    print("\n--- Saving results ---")
    save_results(topic_words, book_profiles, top_chapters, doc_topics, chapter_order)

    print("\n[DONE] Topic modeling complete!")
    print("\nReview the topics above and update the default labels in")
    print("TopicModelingTab.jsx or add a 'suggested_label' field to the JSON.")
