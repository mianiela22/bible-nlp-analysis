"""
Step 4: Book-by-Book Statistics
================================
Computes detailed stats for each book of the Bible:
- Word counts, verse counts, chapter counts
- Average verse length and word length
- Vocabulary richness (type-token ratio)
- Reading level estimates

This data powers the "Book Explorer" tab on the dashboard.
"""

import csv
import json
import re
import os
from collections import Counter

# ============================================================
# Book categories for grouping in the dashboard
# ============================================================
BOOK_CATEGORIES = {
    "Genesis": "Pentateuch", "Exodus": "Pentateuch",
    "Leviticus": "Pentateuch", "Numbers": "Pentateuch",
    "Deuteronomy": "Pentateuch",
    "Joshua": "Historical", "Judges": "Historical",
    "Ruth": "Historical", "1 Samuel": "Historical",
    "2 Samuel": "Historical", "1 Kings": "Historical",
    "2 Kings": "Historical", "1 Chronicles": "Historical",
    "2 Chronicles": "Historical", "Ezra": "Historical",
    "Nehemiah": "Historical", "Esther": "Historical",
    "Job": "Wisdom/Poetry", "Psalms": "Wisdom/Poetry",
    "Proverbs": "Wisdom/Poetry", "Ecclesiastes": "Wisdom/Poetry",
    "Song of Solomon": "Wisdom/Poetry",
    "Isaiah": "Major Prophets", "Jeremiah": "Major Prophets",
    "Lamentations": "Major Prophets", "Ezekiel": "Major Prophets",
    "Daniel": "Major Prophets",
    "Hosea": "Minor Prophets", "Joel": "Minor Prophets",
    "Amos": "Minor Prophets", "Obadiah": "Minor Prophets",
    "Jonah": "Minor Prophets", "Micah": "Minor Prophets",
    "Nahum": "Minor Prophets", "Habakkuk": "Minor Prophets",
    "Zephaniah": "Minor Prophets", "Haggai": "Minor Prophets",
    "Zechariah": "Minor Prophets", "Malachi": "Minor Prophets",
    "Matthew": "Gospels", "Mark": "Gospels",
    "Luke": "Gospels", "John": "Gospels",
    "Acts": "Acts",
    "Romans": "Pauline Epistles", "1 Corinthians": "Pauline Epistles",
    "2 Corinthians": "Pauline Epistles", "Galatians": "Pauline Epistles",
    "Ephesians": "Pauline Epistles", "Philippians": "Pauline Epistles",
    "Colossians": "Pauline Epistles",
    "1 Thessalonians": "Pauline Epistles",
    "2 Thessalonians": "Pauline Epistles",
    "1 Timothy": "Pauline Epistles", "2 Timothy": "Pauline Epistles",
    "Titus": "Pauline Epistles", "Philemon": "Pauline Epistles",
    "Hebrews": "General Epistles",
    "James": "General Epistles", "1 Peter": "General Epistles",
    "2 Peter": "General Epistles", "1 John": "General Epistles",
    "2 John": "General Epistles", "3 John": "General Epistles",
    "Jude": "General Epistles",
    "Revelation": "Apocalyptic",
}

# Book order (so the dashboard displays them in Bible order)
BOOKS_IN_ORDER = [
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


def get_words(text):
    """Clean text and return list of words."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    return [w for w in text.split() if w]


def compute_book_stats(verses):
    """
    Compute detailed statistics for each book.

    Stats we compute:
    - num_chapters: how many chapters
    - num_verses: how many verses
    - total_words: total word count
    - unique_words: vocabulary size
    - avg_words_per_verse: average verse length
    - avg_word_length: average characters per word
    - type_token_ratio: unique words / total words (vocabulary richness)
      Higher = more diverse vocabulary
    - longest_verse: the verse with the most words
    - shortest_verse: the verse with the fewest words
    """
    # Group verses by book
    book_verses = {}
    for v in verses:
        book = v["book"]
        if book not in book_verses:
            book_verses[book] = []
        book_verses[book].append(v)

    results = {}

    for book in BOOKS_IN_ORDER:
        if book not in book_verses:
            continue

        bv = book_verses[book]

        # Gather all words from this book
        all_words = []
        verse_lengths = []
        for v in bv:
            words = get_words(v["text"])
            all_words.extend(words)
            verse_lengths.append(len(words))

        # Count chapters
        chapters = set(int(v["chapter"]) for v in bv)

        # Find longest and shortest verses
        longest_idx = verse_lengths.index(max(verse_lengths))
        shortest_idx = verse_lengths.index(min(verse_lengths))
        longest_v = bv[longest_idx]
        shortest_v = bv[shortest_idx]

        # Average word length (in characters)
        avg_char_len = sum(len(w) for w in all_words) / len(all_words) if all_words else 0

        # Type-token ratio
        unique = set(all_words)
        ttr = len(unique) / len(all_words) if all_words else 0

        # Top 10 most common words (excluding common stop words)
        word_counts = Counter(all_words)

        results[book] = {
            "testament": bv[0]["testament"],
            "category": BOOK_CATEGORIES.get(book, "Unknown"),
            "book_number": BOOKS_IN_ORDER.index(book) + 1,
            "num_chapters": len(chapters),
            "num_verses": len(bv),
            "total_words": len(all_words),
            "unique_words": len(unique),
            "avg_words_per_verse": round(sum(verse_lengths) / len(verse_lengths), 1),
            "avg_word_length": round(avg_char_len, 2),
            "type_token_ratio": round(ttr, 4),
            "longest_verse": {
                "ref": f"{book} {longest_v['chapter']}:{longest_v['verse']}",
                "words": max(verse_lengths),
                "text": longest_v["text"][:200],
            },
            "shortest_verse": {
                "ref": f"{book} {shortest_v['chapter']}:{shortest_v['verse']}",
                "words": min(verse_lengths),
                "text": shortest_v["text"][:200],
            },
        }

    return results


def compute_category_stats(book_stats):
    """Aggregate stats by category (Pentateuch, Gospels, etc.)."""
    categories = {}

    for book, stats in book_stats.items():
        cat = stats["category"]
        if cat not in categories:
            categories[cat] = {
                "books": [],
                "total_words": 0,
                "total_verses": 0,
                "total_chapters": 0,
            }
        categories[cat]["books"].append(book)
        categories[cat]["total_words"] += stats["total_words"]
        categories[cat]["total_verses"] += stats["num_verses"]
        categories[cat]["total_chapters"] += stats["num_chapters"]

    # Compute averages
    for cat, data in categories.items():
        n = len(data["books"])
        data["num_books"] = n
        data["avg_words_per_book"] = round(data["total_words"] / n)
        data["avg_verses_per_book"] = round(data["total_verses"] / n)

    return categories


def print_findings(book_stats, category_stats):
    """Display interesting findings."""

    print(f"\n{'=' * 60}")
    print(f"  BOOK-BY-BOOK STATISTICS")
    print(f"{'=' * 60}")

    # Overall Bible stats
    total_words = sum(b["total_words"] for b in book_stats.values())
    total_verses = sum(b["num_verses"] for b in book_stats.values())
    total_chapters = sum(b["num_chapters"] for b in book_stats.values())

    print(f"\n  BIBLE TOTALS:")
    print(f"    66 books, {total_chapters:,} chapters, {total_verses:,} verses, {total_words:,} words")

    # Longest books
    sorted_by_words = sorted(book_stats.items(), key=lambda x: x[1]["total_words"], reverse=True)
    print(f"\n  TOP 5 LONGEST BOOKS:")
    for book, stats in sorted_by_words[:5]:
        print(f"    {book:20s} {stats['total_words']:>6,} words  {stats['num_chapters']:>3} ch  {stats['num_verses']:>4} verses")

    # Shortest books
    print(f"\n  TOP 5 SHORTEST BOOKS:")
    for book, stats in sorted_by_words[-5:]:
        print(f"    {book:20s} {stats['total_words']:>6,} words  {stats['num_chapters']:>3} ch  {stats['num_verses']:>4} verses")

    # Most verbose (longest average verse)
    sorted_by_avg = sorted(book_stats.items(), key=lambda x: x[1]["avg_words_per_verse"], reverse=True)
    print(f"\n  LONGEST AVERAGE VERSE LENGTH:")
    for book, stats in sorted_by_avg[:5]:
        print(f"    {book:20s} {stats['avg_words_per_verse']:>5.1f} words/verse")

    # Richest vocabulary
    sorted_by_ttr = sorted(book_stats.items(), key=lambda x: x[1]["type_token_ratio"], reverse=True)
    print(f"\n  RICHEST VOCABULARY (highest type-token ratio):")
    for book, stats in sorted_by_ttr[:5]:
        print(f"    {book:20s} {stats['type_token_ratio']:.4f}  ({stats['unique_words']:,} unique / {stats['total_words']:,} total)")

    # Category breakdown
    print(f"\n  BY CATEGORY:")
    for cat, data in sorted(category_stats.items(), key=lambda x: x[1]["total_words"], reverse=True):
        print(f"    {cat:20s} {data['num_books']:>2} books  {data['total_words']:>7,} words  {data['total_verses']:>5,} verses")

    print(f"\n{'=' * 60}")


def save_results(book_stats, category_stats):
    """Save as JSON for the website."""
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)

    output = {
        "books": book_stats,
        "categories": category_stats,
        "book_order": BOOKS_IN_ORDER,
    }

    filepath = os.path.join("data", "processed", "book_stats.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved to {filepath}")


if __name__ == "__main__":
    print("=" * 60)
    print("  Step 4: Book-by-Book Statistics")
    print("=" * 60)

    print("\n--- Loading Bible data ---")
    verses = load_bible()

    print("\n--- Computing book stats ---")
    book_stats = compute_book_stats(verses)

    print("\n--- Computing category stats ---")
    category_stats = compute_category_stats(book_stats)

    print_findings(book_stats, category_stats)

    print("\n--- Saving results ---")
    save_results(book_stats, category_stats)

    print("\n[DONE] Book statistics complete!")
