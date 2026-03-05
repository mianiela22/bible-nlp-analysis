"""
Step 9: Verse-Level Sentiment for Color-Coded Reading
=======================================================
Builds a compact JSON storing every verse's sentiment score,
organized by book → chapter, so the website can render the
actual KJV text color-coded by emotional tone.

Color scale:
  Deep red   ← negative (compound ≤ -0.5)
  Orange-red ← mildly negative (-0.5 to -0.05)
  Parchment  ← neutral (-0.05 to 0.05)
  Light green← mildly positive (0.05 to 0.4)
  Deep green ← very positive (compound ≥ 0.4)

What this reveals:
  - Psalm 22: descent into desolation then pivots to praise
    (the psalm Jesus quotes from the cross)
  - Job 3–37: sustained dark, then 38–42 explodes positive
    when God speaks from the whirlwind
  - Romans: condemnation (ch.1-3) → justification (4-5)
    → assurance (8, "nothing can separate us") → doxology (11)
  - Lamentations: uniformly the darkest book in Scripture
  - Revelation: cycles of terror and glory, ending in pure gold

Saves: data/processed/verse_sentiment.json
Structure (compact for browser performance):
  {
    book_order: [...],
    chapter_counts: {Genesis: 50, ...},
    chapter_avg: {Genesis: {1: 0.05, 2: 0.12, ...}, ...},
    verses: {
      Genesis: {
        1: [[1, "In the beginning...", 0.0], ...]
      }
    }
  }
Each verse is [verse_num, text, compound_score].
"""

import csv
import json
import os
from collections import defaultdict

from nltk.sentiment import SentimentIntensityAnalyzer

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
    filepath = os.path.join("data", "processed", "kjv_bible.csv")
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def score_and_organize(verses):
    """
    Score every verse with VADER and organize into:
      verses_by_chapter[book][chapter] = list of [verse_num, text, compound]
    """
    sia = SentimentIntensityAnalyzer()
    verses_by_chapter = defaultdict(lambda: defaultdict(list))

    print(f"  Scoring {len(verses):,} verses...")
    for i, verse in enumerate(verses):
        if i % 5000 == 0:
            print(f"    {i:,} / {len(verses):,}")
        scores = sia.polarity_scores(verse["text"])
        compound = round(scores["compound"], 4)
        book = verse["book"]
        chapter = int(verse["chapter"])
        vnum = int(verse["verse"])
        verses_by_chapter[book][chapter].append([vnum, verse["text"], compound])

    return verses_by_chapter


def compute_chapter_averages(verses_by_chapter):
    """Average compound score per chapter, for the book arc display."""
    chapter_avg = {}
    chapter_counts = {}
    for book in BOOK_ORDER:
        if book not in verses_by_chapter:
            continue
        chapter_avg[book] = {}
        chapter_counts[book] = len(verses_by_chapter[book])
        for chapter, verse_list in verses_by_chapter[book].items():
            scores = [v[2] for v in verse_list]
            chapter_avg[book][chapter] = round(sum(scores) / len(scores), 4)
    return chapter_avg, chapter_counts


def print_findings(chapter_avg):
    """Print the most dramatic emotional arcs for verification."""
    print(f"\n{'=' * 60}")
    print("  MOST DRAMATIC CHAPTER-LEVEL ARCS")
    print(f"{'=' * 60}")

    interesting_books = [
        "Psalms", "Job", "Romans", "Lamentations",
        "Revelation", "Isaiah", "John", "Philippians",
    ]

    for book in interesting_books:
        if book not in chapter_avg:
            continue
        chapters = chapter_avg[book]
        if not chapters:
            continue
        scores = list(chapters.values())
        book_avg = round(sum(scores) / len(scores), 4)
        most_pos = max(chapters.items(), key=lambda x: x[1])
        most_neg = min(chapters.items(), key=lambda x: x[1])
        print(f"\n  {book:20s}  avg={book_avg:+.4f}")
        print(f"    Most positive: ch.{most_pos[0]}  ({most_pos[1]:+.4f})")
        print(f"    Most negative: ch.{most_neg[0]}  ({most_neg[1]:+.4f})")

    print(f"\n{'=' * 60}")


def save_results(verses_by_chapter, chapter_avg, chapter_counts):
    """Save compact JSON for the website."""
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)

    # Convert defaultdicts to plain dicts for JSON serialization
    verses_plain = {}
    for book in BOOK_ORDER:
        if book in verses_by_chapter:
            verses_plain[book] = {
                str(ch): verse_list
                for ch, verse_list in sorted(verses_by_chapter[book].items())
            }

    chapter_avg_plain = {
        book: {str(ch): score for ch, score in chapters.items()}
        for book, chapters in chapter_avg.items()
    }

    output = {
        "book_order": BOOK_ORDER,
        "chapter_counts": chapter_counts,
        "chapter_avg": chapter_avg_plain,
        "verses": verses_plain,
    }

    filepath = os.path.join("data", "processed", "verse_sentiment.json")
    # Compact JSON (no whitespace) to minimize file size
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(',', ':'))

    size_kb = os.path.getsize(filepath) / 1024
    print(f"\nSaved to {filepath}  ({size_kb:.0f} KB)")
    if size_kb > 4000:
        print("  Note: file is large — consider lazy-loading in the browser")


if __name__ == "__main__":
    print("=" * 60)
    print("  Step 9: Verse-Level Sentiment")
    print("=" * 60)

    print("\n--- Loading Bible ---")
    verses = load_bible()

    print("\n--- Scoring and organizing ---")
    verses_by_chapter = score_and_organize(verses)

    print("\n--- Computing chapter averages ---")
    chapter_avg, chapter_counts = compute_chapter_averages(verses_by_chapter)

    print_findings(chapter_avg)

    print("\n--- Saving ---")
    save_results(verses_by_chapter, chapter_avg, chapter_counts)

    print("\n[DONE]")
