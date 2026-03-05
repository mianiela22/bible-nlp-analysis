"""
Step 2: Word Frequency Analysis
================================
Analyzes which words appear most frequently in the Bible,
compares Old vs New Testament, and breaks it down by book.

Saves results as JSON files that our website can load later.
"""

import csv
import re
import json
import os
from collections import Counter

# ============================================================
# STOP WORDS
# ============================================================
# Stop words are common words like "the", "and", "is" that appear
# everywhere but don't tell us anything meaningful.
# We remove them so we can see the INTERESTING words.

STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
    'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself',
    'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
    'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if',
    'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for',
    'with', 'about', 'against', 'between', 'through', 'during', 'before',
    'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
    'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'both',
    'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can',
    'will', 'just', 'should', 'now'
}

# KJV-specific archaic words that are basically stop words
# These are old English equivalents of common words
KJV_STOP_WORDS = {
    'shall', 'unto', 'thee', 'thou', 'thy', 'hath', 'ye', 'thereof',
    'upon', 'also', 'said', 'one', 'came', 'come', 'went', 'let',
    'may', 'even', 'made', 'like', 'every', 'thing', 'things',
    'say', 'saying', 'thus', 'saith', 'therefore', 'wherein',
    'wherefore', 'neither', 'hast', 'shalt', 'thine', 'doth',
    'forth', 'art', 'yet', 'yea', 'nay', 'lo', 'behold',
    'verily', 'whither', 'hence', 'thither', 'hither', 'whereas'
}

ALL_STOP_WORDS = STOP_WORDS | KJV_STOP_WORDS


# ============================================================
# STEP A: Load the CSV we created in Step 1
# ============================================================
def load_bible():
    """
    Load our parsed Bible CSV into a list of dictionaries.
    Each dict is one verse with keys: book, chapter, verse, text, testament
    """
    filepath = os.path.join("data", "processed", "kjv_bible.csv")
    with open(filepath, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows):,} verses")
    return rows


# ============================================================
# STEP B: Clean and tokenize text
# ============================================================
def clean_and_tokenize(text):
    """
    Turn a string of text into a clean list of words.

    Steps:
    1. Lowercase everything (so "God" and "god" count as the same word)
    2. Remove punctuation (periods, commas, colons, etc.)
    3. Split into individual words
    4. Remove stop words

    This is called TOKENIZATION - breaking text into tokens (words).
    """
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'\d+', '', text)       # Remove numbers
    words = text.split()
    return words


def remove_stops(words):
    """Remove stop words from a word list."""
    return [w for w in words if w not in ALL_STOP_WORDS]


# ============================================================
# STEP C: Analyze word frequencies
# ============================================================
def analyze_frequencies(verses):
    """
    Count how often each word appears in the entire Bible,
    in each testament, and in each book.

    We use Python's Counter class - it's basically a dictionary
    that counts things. Super useful for frequency analysis!
    """
    # Collect all words
    all_words = []
    ot_words = []
    nt_words = []
    book_words = {}  # {book_name: [words]}

    for verse in verses:
        words = clean_and_tokenize(verse["text"])

        all_words.extend(words)

        if verse["testament"] == "Old Testament":
            ot_words.extend(words)
        else:
            nt_words.extend(words)

        book = verse["book"]
        if book not in book_words:
            book_words[book] = []
        book_words[book].extend(words)

    # Now count! (with and without stop words)
    print(f"\nTotal words (with stops):    {len(all_words):,}")
    all_no_stops = remove_stops(all_words)
    print(f"Total words (without stops): {len(all_no_stops):,}")
    print(f"Unique words (without stops): {len(set(all_no_stops)):,}")

    # Count frequencies
    results = {
        "overall": {
            "total_words": len(all_words),
            "total_words_no_stops": len(all_no_stops),
            "unique_words": len(set(all_no_stops)),
            "top_50_with_stops": Counter(all_words).most_common(50),
            "top_50_no_stops": Counter(all_no_stops).most_common(50),
        },
        "old_testament": {
            "total_words": len(ot_words),
            "top_30": Counter(remove_stops(ot_words)).most_common(30),
        },
        "new_testament": {
            "total_words": len(nt_words),
            "top_30": Counter(remove_stops(nt_words)).most_common(30),
        },
        "by_book": {}
    }

    # Per-book analysis
    for book, words in book_words.items():
        no_stops = remove_stops(words)
        results["by_book"][book] = {
            "total_words": len(words),
            "total_words_no_stops": len(no_stops),
            "unique_words": len(set(no_stops)),
            "top_20": Counter(no_stops).most_common(20),
        }

    return results


# ============================================================
# STEP D: Print interesting findings
# ============================================================
def print_findings(results):
    """Display the most interesting results."""

    print(f"\n{'=' * 60}")
    print(f"  WORD FREQUENCY FINDINGS")
    print(f"{'=' * 60}")

    # Overall stats
    overall = results["overall"]
    print(f"\n  OVERALL BIBLE STATS:")
    print(f"    Total words:  {overall['total_words']:,}")
    print(f"    After removing stop words: {overall['total_words_no_stops']:,}")
    print(f"    Unique meaningful words: {overall['unique_words']:,}")

    # Top words with stop words (shows the raw language)
    print(f"\n  TOP 20 WORDS (including common words):")
    for word, count in overall["top_50_with_stops"][:20]:
        bar = "#" * (count // 1000)
        print(f"    {word:15s} {count:>6,}  {bar}")

    # Top words without stop words (the meaningful ones!)
    print(f"\n  TOP 20 MEANINGFUL WORDS (stop words removed):")
    for word, count in overall["top_50_no_stops"][:20]:
        bar = "#" * (count // 200)
        print(f"    {word:15s} {count:>6,}  {bar}")

    # Old vs New Testament comparison
    print(f"\n  OLD TESTAMENT vs NEW TESTAMENT:")
    print(f"    OT words: {results['old_testament']['total_words']:,}")
    print(f"    NT words: {results['new_testament']['total_words']:,}")

    print(f"\n    OT Top 10:                    NT Top 10:")
    ot_top = results["old_testament"]["top_30"][:10]
    nt_top = results["new_testament"]["top_30"][:10]
    for i in range(10):
        ot_word, ot_count = ot_top[i]
        nt_word, nt_count = nt_top[i]
        print(f"    {ot_word:12s} {ot_count:>5,}          {nt_word:12s} {nt_count:>5,}")

    # Top 5 longest books by word count
    print(f"\n  TOP 5 LONGEST BOOKS (by word count):")
    sorted_books = sorted(
        results["by_book"].items(),
        key=lambda x: x[1]["total_words"],
        reverse=True
    )
    for book, data in sorted_books[:5]:
        print(f"    {book:20s} {data['total_words']:>6,} words  "
              f"({data['unique_words']:,} unique)")

    # Most unique vocabulary (highest ratio of unique words)
    print(f"\n  RICHEST VOCABULARY (most diverse word usage):")
    vocab_richness = []
    for book, data in results["by_book"].items():
        if data["total_words_no_stops"] > 100:  # Skip tiny books
            ratio = data["unique_words"] / data["total_words_no_stops"]
            vocab_richness.append((book, ratio, data["unique_words"]))
    vocab_richness.sort(key=lambda x: x[1], reverse=True)
    for book, ratio, unique in vocab_richness[:5]:
        print(f"    {book:20s} {ratio:.1%} unique  ({unique:,} unique words)")

    print(f"\n{'=' * 60}")


# ============================================================
# STEP E: Save results as JSON for the website
# ============================================================
def save_results(results):
    """
    Save results as JSON files that our website can load.
    JSON is the standard format for web data.
    """
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)

    # Convert Counter tuples to lists for JSON serialization
    # (JSON doesn't understand Python tuples)
    def convert_for_json(obj):
        if isinstance(obj, list) and obj and isinstance(obj[0], tuple):
            return [{"word": w, "count": c} for w, c in obj]
        return obj

    json_results = {
        "overall": {
            "total_words": results["overall"]["total_words"],
            "total_words_no_stops": results["overall"]["total_words_no_stops"],
            "unique_words": results["overall"]["unique_words"],
            "top_50_with_stops": convert_for_json(results["overall"]["top_50_with_stops"]),
            "top_50_no_stops": convert_for_json(results["overall"]["top_50_no_stops"]),
        },
        "old_testament": {
            "total_words": results["old_testament"]["total_words"],
            "top_30": convert_for_json(results["old_testament"]["top_30"]),
        },
        "new_testament": {
            "total_words": results["new_testament"]["total_words"],
            "top_30": convert_for_json(results["new_testament"]["top_30"]),
        },
        "by_book": {}
    }

    for book, data in results["by_book"].items():
        json_results["by_book"][book] = {
            "total_words": data["total_words"],
            "total_words_no_stops": data["total_words_no_stops"],
            "unique_words": data["unique_words"],
            "top_20": convert_for_json(data["top_20"]),
        }

    filepath = os.path.join("data", "processed", "word_frequencies.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(json_results, f, indent=2)

    print(f"\nSaved results to {filepath}")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Step 2: Word Frequency Analysis")
    print("=" * 60)

    # Load
    print("\n--- Loading Bible data ---")
    verses = load_bible()

    # Analyze
    print("\n--- Analyzing word frequencies ---")
    results = analyze_frequencies(verses)

    # Display
    print_findings(results)

    # Save for website
    print("\n--- Saving results ---")
    save_results(results)

    print("\n[DONE] Word frequency analysis complete!")
