"""
Step 1: Parse the KJV Bible into structured data
=================================================
Takes the raw text file and turns it into a clean CSV with columns:
    book, chapter, verse, text, testament

Strategy: Use the book HEADERS in the text to split by book,
then use regex to find chapter:verse patterns within each book.
"""

import re
import csv
import os

# ============================================================
# All 66 books mapped to their EXACT headers in the Gutenberg file
# ============================================================
BOOK_HEADERS = {
    "Genesis": "The First Book of Moses: Called Genesis",
    "Exodus": "The Second Book of Moses: Called Exodus",
    "Leviticus": "The Third Book of Moses: Called Leviticus",
    "Numbers": "The Fourth Book of Moses: Called Numbers",
    "Deuteronomy": "The Fifth Book of Moses: Called Deuteronomy",
    "Joshua": "The Book of Joshua",
    "Judges": "The Book of Judges",
    "Ruth": "The Book of Ruth",
    "1 Samuel": "The First Book of Samuel",
    "2 Samuel": "The Second Book of Samuel",
    "1 Kings": "The First Book of the Kings",
    "2 Kings": "The Second Book of the Kings",
    "1 Chronicles": "The First Book of the Chronicles",
    "2 Chronicles": "The Second Book of the Chronicles",
    "Ezra": "Ezra",
    "Nehemiah": "The Book of Nehemiah",
    "Esther": "The Book of Esther",
    "Job": "The Book of Job",
    "Psalms": "The Book of Psalms",
    "Proverbs": "The Proverbs",
    "Ecclesiastes": "Ecclesiastes",
    "Song of Solomon": "The Song of Solomon",
    "Isaiah": "The Book of the Prophet Isaiah",
    "Jeremiah": "The Book of the Prophet Jeremiah",
    "Lamentations": "The Lamentations of Jeremiah",
    "Ezekiel": "The Book of the Prophet Ezekiel",
    "Daniel": "The Book of Daniel",
    "Hosea": "Hosea",
    "Joel": "Joel",
    "Amos": "Amos",
    "Obadiah": "Obadiah",
    "Jonah": "Jonah",
    "Micah": "Micah",
    "Nahum": "Nahum",
    "Habakkuk": "Habakkuk",
    "Zephaniah": "Zephaniah",
    "Haggai": "Haggai",
    "Zechariah": "Zechariah",
    "Malachi": "Malachi",
    "Matthew": "The Gospel According to Saint Matthew",
    "Mark": "The Gospel According to Saint Mark",
    "Luke": "The Gospel According to Saint Luke",
    "John": "The Gospel According to Saint John",
    "Acts": "The Acts of the Apostles",
    "Romans": "The Epistle of Paul the Apostle to the Romans",
    "1 Corinthians": "The First Epistle of Paul the Apostle to the Corinthians",
    "2 Corinthians": "The Second Epistle of Paul the Apostle to the Corinthians",
    "Galatians": "The Epistle of Paul the Apostle to the Galatians",
    "Ephesians": "The Epistle of Paul the Apostle to the Ephesians",
    "Philippians": "The Epistle of Paul the Apostle to the Philippians",
    "Colossians": "The Epistle of Paul the Apostle to the Colossians",
    "1 Thessalonians": "The First Epistle of Paul the Apostle to the Thessalonians",
    "2 Thessalonians": "The Second Epistle of Paul the Apostle to the Thessalonians",
    "1 Timothy": "The First Epistle of Paul the Apostle to Timothy",
    "2 Timothy": "The Second Epistle of Paul the Apostle to Timothy",
    "Titus": "The Epistle of Paul the Apostle to Titus",
    "Philemon": "The Epistle of Paul the Apostle to Philemon",
    "Hebrews": "The Epistle of Paul the Apostle to the Hebrews",
    "James": "The General Epistle of James",
    "1 Peter": "The First Epistle General of Peter",
    "2 Peter": "The Second General Epistle of Peter",
    "1 John": "The First Epistle General of John",
    "2 John": "The Second Epistle General of John",
    "3 John": "The Third Epistle General of John",
    "Jude": "The General Epistle of Jude",
    "Revelation": "The Revelation of Saint John the Divine",
}

BOOKS_IN_ORDER = list(BOOK_HEADERS.keys())
OLD_TESTAMENT = BOOKS_IN_ORDER[:39]
NEW_TESTAMENT = BOOKS_IN_ORDER[39:]


def load_and_strip(filepath):
    """Load raw file and remove Gutenberg headers/footers."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    start_marker = "*** START OF THE PROJECT GUTENBERG EBOOK"
    start_idx = text.find(start_marker)
    if start_idx != -1:
        start_idx = text.index("\n", start_idx) + 1

    end_marker = "*** END OF THE PROJECT GUTENBERG EBOOK"
    end_idx = text.find(end_marker)
    if end_idx == -1:
        end_idx = len(text)

    cleaned = text[start_idx:end_idx].strip()
    print(f"Original: {len(text):,} chars -> Cleaned: {len(cleaned):,} chars")
    return cleaned


def find_book_positions(text):
    """
    Find where each book starts in the text.

    For LONG unique headers (like "The First Book of Moses: Called Genesis"),
    we find the last occurrence that isn't after "Otherwise Called" or
    "Commonly Called".

    For SHORT headers (single words like "Jonah", "Joel", "Ezra"),
    these names can appear inside verse text as people's names.
    So we look for the pattern where the name appears followed within
    a short distance by "1:1" — that's a real book header.
    """
    SHORT_HEADERS = {
        "Ezra", "Hosea", "Joel", "Amos", "Obadiah", "Jonah",
        "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
        "Zechariah", "Malachi",
    }

    positions = {}

    for book_name, header in BOOK_HEADERS.items():

        if book_name in SHORT_HEADERS:
            # For short names, find "Name\n\n...1:1" pattern
            pattern = re.compile(
                re.escape(header) + r'\s{2,}1:1\s',
            )
            match = pattern.search(text, 2000)  # Skip TOC
            if match:
                positions[book_name] = match.start()
            else:
                print(f"  WARNING: Could not find header for {book_name}")
        else:
            # For long unique headers, find last non-subtitle occurrence
            idx = 0
            candidates = []
            while True:
                idx = text.find(header, idx)
                if idx == -1:
                    break

                # Skip TOC entries
                if idx < 2000:
                    idx += 1
                    continue

                # Skip "Otherwise Called" / "Commonly Called" subtitles
                lookback = text[max(0, idx - 100):idx]
                if "Otherwise Called" in lookback or "Commonly Called" in lookback:
                    idx += 1
                    continue

                candidates.append(idx)
                idx += 1

            if candidates:
                positions[book_name] = candidates[-1]
            else:
                print(f"  WARNING: Could not find header for {book_name}")

    sorted_books = sorted(positions.items(), key=lambda x: x[1])
    print(f"Found positions for {len(sorted_books)}/66 books")

    return sorted_books


def extract_verses(text, book_positions):
    """
    For each book, extract the chunk of text between its header
    and the next book's header, then parse out individual verses.
    """
    all_verses = []
    verse_pattern = re.compile(r"(\d+):(\d+)\s+")

    for i, (book_name, start_pos) in enumerate(book_positions):
        if i + 1 < len(book_positions):
            end_pos = book_positions[i + 1][1]
        else:
            end_pos = len(text)

        book_text = text[start_pos:end_pos]

        # Remove the header line itself
        header = BOOK_HEADERS[book_name]
        book_text = book_text.replace(header, "", 1).strip()

        # Collapse newlines into spaces
        book_text = re.sub(r"\n+", " ", book_text)
        book_text = re.sub(r"\s+", " ", book_text)

        # Split by verse markers
        splits = verse_pattern.split(book_text)

        testament = "Old Testament" if book_name in OLD_TESTAMENT else "New Testament"

        j = 1
        while j + 2 < len(splits):
            chapter = int(splits[j])
            verse = int(splits[j + 1])
            verse_text = splits[j + 2].strip()

            if verse_text:
                all_verses.append({
                    "book": book_name,
                    "chapter": chapter,
                    "verse": verse,
                    "text": verse_text,
                    "testament": testament,
                })

            j += 3

    return all_verses


def save_to_csv(verses, filepath):
    """Save structured verses to CSV."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    fieldnames = ["book", "chapter", "verse", "text", "testament"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(verses)

    print(f"Saved {len(verses):,} verses to {filepath}")


def print_summary(verses):
    """Print a summary of what we parsed."""
    books = set(v["book"] for v in verses)
    ot = sum(1 for v in verses if v["testament"] == "Old Testament")
    nt = sum(1 for v in verses if v["testament"] == "New Testament")

    print(f"\n{'=' * 60}")
    print(f"  SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Total verses: {len(verses):,}")
    print(f"  Total books:  {len(books)}")
    print(f"  Old Testament: {ot:,} verses")
    print(f"  New Testament: {nt:,} verses")
    print(f"\n  First: {verses[0]['book']} {verses[0]['chapter']}:{verses[0]['verse']}")
    print(f"    {verses[0]['text'][:70]}...")
    print(f"  Last:  {verses[-1]['book']} {verses[-1]['chapter']}:{verses[-1]['verse']}")
    print(f"    {verses[-1]['text'][:70]}...")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    print("=" * 60)
    print("  Parsing the KJV Bible")
    print("=" * 60)

    raw_path = os.path.join("data", "raw", "kjv_bible_raw.txt")

    print("\n--- Loading and cleaning ---")
    text = load_and_strip(raw_path)

    print("\n--- Finding book positions ---")
    book_positions = find_book_positions(text)

    print("\n--- Extracting verses ---")
    verses = extract_verses(text, book_positions)

    print("\n--- Saving to CSV ---")
    csv_path = os.path.join("data", "processed", "kjv_bible.csv")
    save_to_csv(verses, csv_path)

    print_summary(verses)