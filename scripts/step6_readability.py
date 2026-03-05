"""
Step 6: Readability Analysis
==============================
Scores each book's reading difficulty using established formulas.

Flesch Reading Ease: 0-100 scale
  90-100 = Very Easy (5th grade)
  60-70  = Standard (8th-9th grade)
  30-50  = Difficult (college level)
  0-30   = Very Difficult (graduate level)

Flesch-Kincaid Grade Level:
  Estimates the US school grade needed to understand the text.
  Grade 8 = 8th grader can read it, Grade 16 = college graduate level.

We also compute:
  - Average sentence length (words per sentence)
  - Average syllable count per word
  - Average word length in characters
"""

import csv
import json
import re
import os

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


def load_bible():
    filepath = os.path.join("data", "processed", "kjv_bible.csv")
    with open(filepath, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows):,} verses")
    return rows


def count_syllables(word):
    """
    Estimate syllable count for an English word.

    This uses a simple heuristic:
    1. Count vowel groups (consecutive vowels = 1 syllable)
    2. Subtract 1 for silent 'e' at the end
    3. Minimum of 1 syllable per word

    Not perfect, but good enough for readability formulas!
    """
    word = word.lower().strip()
    if not word:
        return 0

    # Count vowel groups
    vowels = "aeiouy"
    count = 0
    prev_was_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel

    # Silent e
    if word.endswith("e") and count > 1:
        count -= 1

    # Special endings
    if word.endswith("le") and len(word) > 2 and word[-3] not in vowels:
        count += 1

    return max(1, count)


def get_sentences(text):
    """
    Split text into sentences.
    Bible verses often use : and ; as sentence breaks too.
    """
    sentences = re.split(r'[.!?;:]', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip().split()) > 1]


def get_words(text):
    """Get clean word list."""
    text = re.sub(r'[^\w\s]', '', text.lower())
    return [w for w in text.split() if w]


def compute_readability(verses):
    """
    Compute readability metrics for each book.

    Flesch Reading Ease = 206.835 - 1.015 * ASL - 84.6 * ASW
      where ASL = average sentence length (words)
            ASW = average syllables per word

    Flesch-Kincaid Grade = 0.39 * ASL + 11.8 * ASW - 15.59
    """
    # Group verses by book
    book_texts = {}
    for v in verses:
        book = v["book"]
        if book not in book_texts:
            book_texts[book] = []
        book_texts[book].append(v["text"])

    results = {}

    for book in BOOK_ORDER:
        if book not in book_texts:
            continue

        full_text = " ".join(book_texts[book])
        words = get_words(full_text)
        sentences = get_sentences(full_text)

        if not words or not sentences:
            continue

        total_syllables = sum(count_syllables(w) for w in words)

        # Key metrics
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = total_syllables / len(words)
        avg_word_length = sum(len(w) for w in words) / len(words)

        # Flesch Reading Ease
        flesch_ease = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        flesch_ease = max(0, min(100, flesch_ease))

        # Flesch-Kincaid Grade Level
        fk_grade = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
        fk_grade = max(0, fk_grade)

        # Difficulty label
        if flesch_ease >= 80:
            difficulty = "Easy"
        elif flesch_ease >= 60:
            difficulty = "Standard"
        elif flesch_ease >= 40:
            difficulty = "Moderate"
        elif flesch_ease >= 20:
            difficulty = "Difficult"
        else:
            difficulty = "Very Difficult"

        results[book] = {
            "testament": "Old Testament" if BOOK_ORDER.index(book) < 39 else "New Testament",
            "category": BOOK_CATEGORIES.get(book, "Unknown"),
            "flesch_ease": round(flesch_ease, 1),
            "fk_grade": round(fk_grade, 1),
            "difficulty": difficulty,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "avg_syllables_per_word": round(avg_syllables_per_word, 2),
            "avg_word_length": round(avg_word_length, 2),
            "total_words": len(words),
            "total_sentences": len(sentences),
        }

    return results


def print_findings(results):
    print(f"\n{'=' * 60}")
    print(f"  READABILITY FINDINGS")
    print(f"{'=' * 60}")

    # Easiest to read
    sorted_by_ease = sorted(results.items(), key=lambda x: x[1]["flesch_ease"], reverse=True)

    print(f"\n  TOP 5 EASIEST TO READ:")
    for book, data in sorted_by_ease[:5]:
        print(f"    {book:20s} Flesch: {data['flesch_ease']:>5.1f}  Grade: {data['fk_grade']:>4.1f}  ({data['difficulty']})")

    print(f"\n  TOP 5 HARDEST TO READ:")
    for book, data in sorted_by_ease[-5:]:
        print(f"    {book:20s} Flesch: {data['flesch_ease']:>5.1f}  Grade: {data['fk_grade']:>4.1f}  ({data['difficulty']})")

    # Average by category
    print(f"\n  READABILITY BY CATEGORY:")
    cat_scores = {}
    for book, data in results.items():
        cat = data["category"]
        if cat not in cat_scores:
            cat_scores[cat] = []
        cat_scores[cat].append(data["flesch_ease"])

    for cat, scores in sorted(cat_scores.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True):
        avg = sum(scores) / len(scores)
        print(f"    {cat:20s} Avg Flesch: {avg:>5.1f}")

    # OT vs NT
    ot_scores = [d["flesch_ease"] for d in results.values() if d["testament"] == "Old Testament"]
    nt_scores = [d["flesch_ease"] for d in results.values() if d["testament"] == "New Testament"]
    print(f"\n  OT avg readability: {sum(ot_scores)/len(ot_scores):.1f}")
    print(f"  NT avg readability: {sum(nt_scores)/len(nt_scores):.1f}")

    print(f"\n{'=' * 60}")


def save_results(results):
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)

    output = {
        "books": results,
        "book_order": BOOK_ORDER,
    }

    filepath = os.path.join("data", "processed", "readability.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved to {filepath}")


if __name__ == "__main__":
    print("=" * 60)
    print("  Step 6: Readability Analysis")
    print("=" * 60)

    print("\n--- Loading Bible data ---")
    verses = load_bible()

    print("\n--- Computing readability scores ---")
    results = compute_readability(verses)

    print_findings(results)

    print("\n--- Saving results ---")
    save_results(results)

    print("\n[DONE] Readability analysis complete!")
