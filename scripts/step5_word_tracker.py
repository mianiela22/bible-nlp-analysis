"""
Step 5: Word Usage Tracker
============================
For a set of important biblical words, tracks how frequently
they appear in each book across the Bible.

This powers the "Word Tracker" feature on the dashboard where
users can see how any word flows from Genesis to Revelation.

We pre-compute common words, but the dashboard will also
let users search any word on the fly.
"""

import csv
import json
import re
import os
from collections import Counter

# Words people would find interesting to track
TRACKED_WORDS = [
    # Core theological terms
    "god", "lord", "jesus", "christ", "spirit", "holy",
    # Emotions and virtues
    "love", "faith", "hope", "joy", "peace", "mercy",
    "grace", "truth", "wisdom", "fear",
    # Key themes
    "sin", "death", "life", "blood", "heaven", "earth",
    "prayer", "pray", "forgive", "forgiveness",
    "righteous", "wicked", "evil", "blessed",
    # People and groups
    "david", "moses", "israel", "jerusalem",
    # Actions
    "praise", "worship", "judge", "save", "heal",
    "king", "servant", "prophet",
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


def load_bible():
    """Load parsed Bible CSV."""
    filepath = os.path.join("data", "processed", "kjv_bible.csv")
    with open(filepath, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows):,} verses")
    return rows


def get_words_from_text(text):
    """Clean text and return lowercase word list."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.split()


def build_word_tracker(verses):
    """
    For each tracked word, count occurrences in every book.

    Also builds a complete word index so the dashboard can
    look up ANY word on the fly, not just our pre-selected ones.
    """
    # Build word counts per book
    book_word_counts = {}
    for book in BOOK_ORDER:
        book_word_counts[book] = Counter()

    # Also track total words per book (for computing rates)
    book_total_words = {}
    for book in BOOK_ORDER:
        book_total_words[book] = 0

    for verse in verses:
        book = verse["book"]
        words = get_words_from_text(verse["text"])
        book_word_counts[book].update(words)
        book_total_words[book] += len(words)

    # Build tracked word data
    tracked_results = {}
    for word in TRACKED_WORDS:
        word_data = []
        for book in BOOK_ORDER:
            count = book_word_counts[book].get(word, 0)
            total = book_total_words[book]
            # Rate per 1000 words (normalizes for book length)
            rate = round((count / total) * 1000, 2) if total > 0 else 0
            word_data.append({
                "book": book,
                "count": count,
                "rate": rate,
            })
        tracked_results[word] = word_data

    # Build a master vocabulary with total counts
    # (so the dashboard can show autocomplete suggestions)
    all_words = Counter()
    for book_counts in book_word_counts.values():
        all_words.update(book_counts)

    # Top 500 most common words as searchable vocabulary
    vocabulary = [
        {"word": word, "total": count}
        for word, count in all_words.most_common(500)
    ]

    # Also build a compact lookup: for every word that appears 5+ times,
    # store its per-book counts so the dashboard can chart ANY word
    all_word_tracker = {}
    for word, total_count in all_words.items():
        if total_count >= 5:  # Skip super rare words
            all_word_tracker[word] = {}
            for book in BOOK_ORDER:
                count = book_word_counts[book].get(word, 0)
                if count > 0:  # Only store non-zero to save space
                    all_word_tracker[word][book] = count

    return tracked_results, vocabulary, all_word_tracker, book_total_words


def print_findings(tracked_results):
    """Show interesting word tracking findings."""
    print(f"\n{'=' * 60}")
    print(f"  WORD TRACKER FINDINGS")
    print(f"{'=' * 60}")

    for word in ["love", "faith", "sin", "death", "king", "jesus"]:
        if word not in tracked_results:
            continue
        data = tracked_results[word]
        total = sum(d["count"] for d in data)
        top_book = max(data, key=lambda d: d["count"])
        ot_count = sum(d["count"] for d in data[:39])
        nt_count = sum(d["count"] for d in data[39:])

        print(f"\n  '{word}' — {total} total occurrences")
        print(f"    OT: {ot_count}  |  NT: {nt_count}")
        print(f"    Most frequent in: {top_book['book']} ({top_book['count']} times)")

    print(f"\n{'=' * 60}")


def save_results(tracked_results, vocabulary, all_word_tracker, book_total_words):
    """Save as JSON for the dashboard."""
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)

    output = {
        "tracked_words": tracked_results,
        "vocabulary": vocabulary,
        "all_words": all_word_tracker,
        "book_total_words": book_total_words,
        "book_order": BOOK_ORDER,
    }

    filepath = os.path.join("data", "processed", "word_tracker.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f)

    # Check file size
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"\nSaved to {filepath} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    print("=" * 60)
    print("  Step 5: Word Usage Tracker")
    print("=" * 60)

    print("\n--- Loading Bible data ---")
    verses = load_bible()

    print("\n--- Building word tracker ---")
    tracked, vocab, all_words, totals = build_word_tracker(verses)

    print(f"\n  Tracked {len(TRACKED_WORDS)} key words")
    print(f"  Built index for {len(all_words):,} searchable words")
    print(f"  Vocabulary list: {len(vocab)} words")

    print_findings(tracked)

    print("\n--- Saving results ---")
    save_results(tracked, vocab, all_words, totals)

    print("\n[DONE] Word tracker complete!")
"""
Step 5: Word Usage Tracker
============================
For a set of important biblical words, tracks how frequently
they appear in each book across the Bible.

This powers the "Word Tracker" feature on the dashboard where
users can see how any word flows from Genesis to Revelation.

We pre-compute common words, but the dashboard will also
let users search any word on the fly.
"""

import csv
import json
import re
import os
from collections import Counter

# Words people would find interesting to track
TRACKED_WORDS = [
    # Core theological terms
    "god", "lord", "jesus", "christ", "spirit", "holy",
    # Emotions and virtues
    "love", "faith", "hope", "joy", "peace", "mercy",
    "grace", "truth", "wisdom", "fear",
    # Key themes
    "sin", "death", "life", "blood", "heaven", "earth",
    "prayer", "pray", "forgive", "forgiveness",
    "righteous", "wicked", "evil", "blessed",
    # People and groups
    "david", "moses", "israel", "jerusalem",
    # Actions
    "praise", "worship", "judge", "save", "heal",
    "king", "servant", "prophet",
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


def load_bible():
    """Load parsed Bible CSV."""
    filepath = os.path.join("data", "processed", "kjv_bible.csv")
    with open(filepath, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows):,} verses")
    return rows


def get_words_from_text(text):
    """Clean text and return lowercase word list."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.split()


def build_word_tracker(verses):
    """
    For each tracked word, count occurrences in every book.

    Also builds a complete word index so the dashboard can
    look up ANY word on the fly, not just our pre-selected ones.
    """
    # Build word counts per book
    book_word_counts = {}
    for book in BOOK_ORDER:
        book_word_counts[book] = Counter()

    # Also track total words per book (for computing rates)
    book_total_words = {}
    for book in BOOK_ORDER:
        book_total_words[book] = 0

    for verse in verses:
        book = verse["book"]
        words = get_words_from_text(verse["text"])
        book_word_counts[book].update(words)
        book_total_words[book] += len(words)

    # Build tracked word data
    tracked_results = {}
    for word in TRACKED_WORDS:
        word_data = []
        for book in BOOK_ORDER:
            count = book_word_counts[book].get(word, 0)
            total = book_total_words[book]
            # Rate per 1000 words (normalizes for book length)
            rate = round((count / total) * 1000, 2) if total > 0 else 0
            word_data.append({
                "book": book,
                "count": count,
                "rate": rate,
            })
        tracked_results[word] = word_data

    # Build a master vocabulary with total counts
    # (so the dashboard can show autocomplete suggestions)
    all_words = Counter()
    for book_counts in book_word_counts.values():
        all_words.update(book_counts)

    # Top 500 most common words as searchable vocabulary
    vocabulary = [
        {"word": word, "total": count}
        for word, count in all_words.most_common(500)
    ]

    # Also build a compact lookup: for every word that appears 5+ times,
    # store its per-book counts so the dashboard can chart ANY word
    all_word_tracker = {}
    for word, total_count in all_words.items():
        if total_count >= 5:  # Skip super rare words
            all_word_tracker[word] = {}
            for book in BOOK_ORDER:
                count = book_word_counts[book].get(word, 0)
                if count > 0:  # Only store non-zero to save space
                    all_word_tracker[word][book] = count

    return tracked_results, vocabulary, all_word_tracker, book_total_words


def print_findings(tracked_results):
    """Show interesting word tracking findings."""
    print(f"\n{'=' * 60}")
    print(f"  WORD TRACKER FINDINGS")
    print(f"{'=' * 60}")

    for word in ["love", "faith", "sin", "death", "king", "jesus"]:
        if word not in tracked_results:
            continue
        data = tracked_results[word]
        total = sum(d["count"] for d in data)
        top_book = max(data, key=lambda d: d["count"])
        ot_count = sum(d["count"] for d in data[:39])
        nt_count = sum(d["count"] for d in data[39:])

        print(f"\n  '{word}' — {total} total occurrences")
        print(f"    OT: {ot_count}  |  NT: {nt_count}")
        print(f"    Most frequent in: {top_book['book']} ({top_book['count']} times)")

    print(f"\n{'=' * 60}")


def save_results(tracked_results, vocabulary, all_word_tracker, book_total_words):
    """Save as JSON for the dashboard."""
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)

    output = {
        "tracked_words": tracked_results,
        "vocabulary": vocabulary,
        "all_words": all_word_tracker,
        "book_total_words": book_total_words,
        "book_order": BOOK_ORDER,
    }

    filepath = os.path.join("data", "processed", "word_tracker.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f)

    # Check file size
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"\nSaved to {filepath} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    print("=" * 60)
    print("  Step 5: Word Usage Tracker")
    print("=" * 60)

    print("\n--- Loading Bible data ---")
    verses = load_bible()

    print("\n--- Building word tracker ---")
    tracked, vocab, all_words, totals = build_word_tracker(verses)

    print(f"\n  Tracked {len(TRACKED_WORDS)} key words")
    print(f"  Built index for {len(all_words):,} searchable words")
    print(f"  Vocabulary list: {len(vocab)} words")

    print_findings(tracked)

    print("\n--- Saving results ---")
    save_results(tracked, vocab, all_words, totals)

    print("\n[DONE] Word tracker complete!")