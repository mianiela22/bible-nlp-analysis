"""
Step 7: Divine Names Analysis
==============================
Tracks the usage of divine names and titles across all 66 books of the Bible.

In the KJV, specific typographic and word choices map to distinct Hebrew/Greek names:

  LORD (all caps)  = YHWH / Yahweh — God's personal covenant name (Tetragrammaton)
  Lord             = Adonai / Kurios — Sovereign, Master
  God              = Elohim / Theos — Creator, Most High
  Jesus            = The incarnate Son of God ("YHWH saves")
  Christ           = The Messiah, the Anointed One (Greek: Christos)
  Holy Ghost       = The Third Person of the Trinity (KJV's term for Holy Spirit)
  Spirit of God    = OT pneumatology — the Spirit active before Pentecost
  Father           = God the Father, especially in NT (capital F as divine title)
  Almighty         = El Shaddai — God All-Sufficient
  LORD of hosts    = Yahweh Sabaoth — Lord of Armies / Heavenly Court

The theological gold here:
  - "LORD" almost vanishes in the NT — God's covenant name shifts to Jesus Christ
  - "Jesus" and "Christ" are NT-exclusive, but the OT knows the Messiah by other names
  - "Almighty" bookends both testaments — Job (OT) and Revelation (NT)
  - "LORD of hosts" concentrates in the prophets — God as the divine warrior
  - "Father" explodes in the NT, especially John — Jesus reveals God's relational nature

Saves results as JSON for the website dashboard.
"""

import csv
import json
import os
import re
import string
from collections import Counter

# ============================================================
# STOP WORDS — words too common to be theologically meaningful
# Includes archaic KJV forms so they don't pollute association lists
# ============================================================

STOP_WORDS = {
    # Common English function words
    'the', 'and', 'of', 'to', 'a', 'in', 'that', 'is', 'was', 'for',
    'it', 'with', 'as', 'his', 'he', 'be', 'on', 'are', 'by', 'at',
    'this', 'from', 'or', 'had', 'not', 'but', 'they', 'have', 'an',
    'were', 'their', 'all', 'which', 'we', 'there', 'been', 'one',
    'would', 'what', 'out', 'so', 'up', 'into', 'said', 'if', 'then',
    'when', 'no', 'more', 'him', 'who', 'me', 'do', 'than', 'her',
    'come', 'will', 'them', 'did', 'my', 'may', 'you', 'your', 'our',
    'has', 'its', 'upon', 'shall', 'also', 'am', 'after', 'before',
    'how', 'because', 'over', 'such', 'man', 'men', 'about', 'these',
    'made', 'can', 'now', 'two', 'she', 'even', 'day', 'three', 'four',
    'us', 'any', 'down', 'make', 'go', 'away', 'only', 'yet', 'much',
    'again', 'good', 'great', 'like', 'things', 'thing', 'way', 'own',
    'bring', 'brought', 'give', 'given', 'go', 'went', 'came', 'come',
    'put', 'set', 'let', 'say', 'know', 'see', 'take', 'send', 'speak',
    'among', 'against', 'between', 'through', 'without', 'according',
    'every', 'thus', 'therefore', 'moreover', 'also', 'neither', 'nor',
    # KJV archaic forms
    'thou', 'thee', 'thy', 'thine', 'ye', 'hath', 'doth', 'art',
    'shalt', 'wilt', 'canst', 'wouldest', 'shouldest', 'hast',
    'saith', 'spake', 'unto', 'thereof', 'therein', 'therewith',
    'whereby', 'whereof', 'wherein', 'nevertheless', 'notwithstanding',
    'whosoever', 'whatsoever', 'yea', 'nay', 'lo', 'behold', 'o',
    # Divine name components (avoid self-referential loops)
    'lord', 'god', 'jesus', 'christ', 'holy', 'ghost', 'spirit',
    'father', 'almighty', 'hosts', 'spirit', 'saith',
}

# ============================================================
# CONSTANTS
# ============================================================

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

OT_BOOKS = set(BOOK_ORDER[:39])

# ============================================================
# DIVINE NAMES — patterns are case-sensitive by default in Python re
# \bLord\b  matches "Lord" but NOT "LORD" (different case)
# \bLORD\b  matches "LORD" but NOT "Lord"
# ============================================================

DIVINE_NAMES = {
    "LORD": {
        "pattern": r"\bLORD\b",
        "description": "YHWH — God's personal covenant name, rendered in ALL CAPS in KJV",
        "short": "YHWH / LORD",
        "color": "#8B4513",
        "theology": (
            "The personal covenant name of God, revealed to Moses as 'I AM WHO I AM' (Exodus 3:14). "
            "Written in Hebrew as four consonants — YHWH (the Tetragrammaton). So sacred that "
            "Jewish readers substituted 'Adonai' when reading aloud. The KJV renders it in "
            "ALL CAPS to distinguish it from 'Lord' (Adonai). It appears almost exclusively "
            "in the Old Testament — showing God's intimate covenant relationship with Israel. "
            "Its near-absence in the NT is not silence — it's fulfillment. The NT writers "
            "pour the Tetragrammaton's weight into the name Jesus Christ."
        ),
    },
    "Lord": {
        "pattern": r"\bLord\b",
        "description": "Adonai / Kurios — Sovereign, Master",
        "short": "Lord / Adonai",
        "color": "#CD853F",
        "theology": (
            "A title of authority meaning 'master' or 'sovereign.' In the OT it's Adonai — "
            "a reverent alternative to YHWH. In the NT, Greek Kurios ('Lord') applied to Jesus "
            "is a profound theological claim: it was the exact word the Greek Old Testament "
            "(Septuagint) used to translate YHWH. When Thomas kneels and says 'My Lord and "
            "my God' (John 20:28), he is placing Jesus where only YHWH had stood. "
            "Watch how 'Lord' shifts from OT Adonai-worship to NT Christology."
        ),
    },
    "God": {
        "pattern": r"\bGod\b",
        "description": "Elohim / Theos — Creator, Most High",
        "short": "God / Elohim",
        "color": "#DAA520",
        "theology": (
            "The most universal name for the divine. Hebrew 'Elohim' is grammatically plural "
            "but consistently takes singular verbs when referring to Israel's God — a mystery "
            "the early church fathers saw as pointing toward the Trinity. It emphasizes God "
            "as the Creator and Ruler of all nations, not just Israel's covenant partner. "
            "In the NT, Greek 'Theos' continues this universal scope. 'God' appears in every "
            "book of the Bible — it is the common thread from Genesis 1:1 to Revelation 22:19."
        ),
    },
    "Jesus": {
        "pattern": r"\bJesus\b",
        "description": "The incarnate Son of God — 'YHWH saves'",
        "short": "Jesus",
        "color": "#4169E1",
        "theology": (
            "The Greek form of Hebrew 'Yeshua' (Joshua), meaning 'YHWH is salvation.' "
            "His very name is a theological declaration — the angel told Joseph: 'thou shalt "
            "call his name JESUS: for he shall save his people from their sins' (Matthew 1:21). "
            "The name is absent from the OT (though Joshua is the same name), then erupts "
            "in the NT. Its concentration in the Gospels and Acts shows the centrality of "
            "his earthly life. Paul and John use it in close tandem with 'Christ' and 'Lord.'"
        ),
    },
    "Christ": {
        "pattern": r"\bChrist\b",
        "description": "The Messiah — the Anointed One (Greek: Christos)",
        "short": "Christ / Messiah",
        "color": "#6495ED",
        "theology": (
            "The Greek translation of Hebrew 'Mashiach' (Messiah) — 'the anointed one.' "
            "In Israel, kings, priests, and prophets were anointed with oil for office. "
            "Jesus fulfills all three: Prophet (teaching God's word), Priest (offering himself), "
            "King (ruling forever). Paul's letters are saturated with 'Christ' and especially "
            "'in Christ' — a technical phrase meaning union with the Messiah. Notice how "
            "'Christ' spikes in Paul compared to the Gospels, where Jesus rarely used "
            "the title of himself openly (the 'Messianic Secret')."
        ),
    },
    "Holy Ghost": {
        "pattern": r"\bHoly Ghost\b",
        "description": "The Third Person of the Trinity (KJV uses 'Holy Ghost')",
        "short": "Holy Ghost",
        "color": "#9370DB",
        "theology": (
            "The KJV uses 'Holy Ghost' (89 times) where modern translations say 'Holy Spirit.' "
            "The Spirit is active in the OT — hovering over creation (Genesis 1:2), empowering "
            "judges and prophets — but remains somewhat anonymous there. The NT reveals the "
            "Spirit's full personhood. Acts is the book of the Holy Ghost: the Spirit descends "
            "at Pentecost, speaks, sends, and leads missionaries. Look at how 'Holy Ghost' "
            "concentrates in Luke-Acts vs the rest of the NT."
        ),
    },
    "Spirit of God": {
        "pattern": r"\bSpirit of God\b",
        "description": "The Spirit of God — OT pneumatology before Pentecost",
        "short": "Spirit of God",
        "color": "#7B68EE",
        "theology": (
            "The OT's primary way of describing the Spirit's activity. "
            "In the OT, the Spirit 'came upon' people temporarily and selectively — "
            "empowering Samson with strength, Bezalel with craftmanship (Exodus 31:3), "
            "and prophets with revelation. This contrasts with the NT promise that the Spirit "
            "would dwell permanently within every believer (John 14:17, Ezekiel 36:27 prophesied it). "
            "The Spirit of God in Genesis 1:2 is the same Spirit poured out at Pentecost — "
            "creator, sustainer, and renewer."
        ),
    },
    "Father": {
        "pattern": r"\bFather\b",
        "description": "God the Father — relational name especially in NT (includes some human references)",
        "short": "Father",
        "color": "#2E8B57",
        "theology": (
            "Jesus's primary address for God — 'Abba, Father' (Romans 8:15, Mark 14:36). "
            "While the OT occasionally calls God Israel's Father (Isaiah 63:16, Psalm 68:5), "
            "these are rare and corporate. The NT explodes with Father-language — especially "
            "in John's Gospel, where Jesus calls God 'Father' over 100 times. "
            "Jesus taught us to pray 'Our Father' — giving every believer access to the same "
            "relational intimacy he enjoyed. Note: capital-F 'Father' in KJV usually refers to "
            "God, though some verses use it for human patriarchs."
        ),
    },
    "Almighty": {
        "pattern": r"\bAlmighty\b",
        "description": "El Shaddai — God All-Sufficient, God of overwhelming power",
        "short": "Almighty",
        "color": "#B22222",
        "theology": (
            "El Shaddai, traditionally translated 'God Almighty.' "
            "First revealed to Abram: 'I am the Almighty God; walk before me' (Genesis 17:1). "
            "Strikingly concentrated in Job — that book of suffering uses 'Almighty' 31 times. "
            "When everything is stripped away, the sufferer still confesses: God is Almighty. "
            "Revelation reclaims the title in Greek ('Pantokrator') — it bookends both "
            "Testaments. The name that comforted the Patriarchs in tents becomes the "
            "throne-room cry of the redeemed in eternity."
        ),
    },
    "LORD of hosts": {
        "pattern": r"\bLORD of hosts\b",
        "description": "Yahweh Sabaoth — Lord of Armies / Heavenly Court",
        "short": "LORD of hosts",
        "color": "#DC143C",
        "theology": (
            "Yahweh Sabaoth — the commander of heaven's armies (both angelic and earthly). "
            "This title appears over 260 times and concentrates overwhelmingly in the prophets. "
            "Isaiah, Jeremiah, Zechariah, and Malachi use it relentlessly — asserting that "
            "despite Assyria or Babylon's military power, YHWH commands a greater army. "
            "It is a name of comfort for the oppressed and terror for the oppressor. "
            "When Isaiah sees the LORD in the temple (Isaiah 6), the seraphim cry: "
            "'Holy, holy, holy is the LORD of hosts.' Power and holiness together."
        ),
    },
}


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
# STEP B: Load book word totals (reuse from book_stats)
# ============================================================

def load_book_word_counts(verses):
    """Count total words per book from the verse data."""
    counts = {book: 0 for book in BOOK_ORDER}
    for v in verses:
        if v["book"] in counts:
            counts[v["book"]] += len(v["text"].split())
    return counts


# ============================================================
# STEP C: Analyze divine name usage
# ============================================================

def analyze_divine_names(verses, book_word_counts):
    """
    For each divine name, count occurrences by book and build stats.
    Also collect sample verses and compute word associations (co-occurrence).
    """
    # Pre-compile patterns for speed
    compiled = {
        name: re.compile(config["pattern"])
        for name, config in DIVINE_NAMES.items()
    }

    # Global word frequencies across the entire Bible (for specificity scoring)
    print("  Building global word frequency table...")
    global_word_counts = Counter()
    total_bible_words = 0
    for verse in verses:
        words = tokenize(verse["text"])
        global_word_counts.update(words)
        total_bible_words += len(words)

    # Storage
    by_book = {name: {book: 0 for book in BOOK_ORDER} for name in DIVINE_NAMES}
    all_sample_verses = {name: [] for name in DIVINE_NAMES}

    print(f"Scanning {len(verses):,} verses for {len(DIVINE_NAMES)} divine names...")

    for verse in verses:
        book = verse["book"]
        if book not in set(BOOK_ORDER):
            continue
        text = verse["text"]

        for name, pattern in compiled.items():
            count = len(pattern.findall(text))
            if count > 0:
                by_book[name][book] += count
                # Collect verse for sampling
                all_sample_verses[name].append({
                    "book": book,
                    "chapter": int(verse["chapter"]),
                    "verse": int(verse["verse"]),
                    "text": verse["text"],
                    "testament": verse["testament"],
                    "count": count,
                })

    # Build final results for each name
    results = {}
    for name, config in DIVINE_NAMES.items():
        book_counts = by_book[name]
        total = sum(book_counts.values())
        ot_count = sum(book_counts[b] for b in BOOK_ORDER[:39])
        nt_count = sum(book_counts[b] for b in BOOK_ORDER[39:])

        # Rate per 1,000 words per book
        book_rate = {}
        for book in BOOK_ORDER:
            words = book_word_counts[book]
            book_rate[book] = round(book_counts[book] / words * 1000, 3) if words > 0 else 0

        # Sample verses — spread-sample 6 across the full span
        matches = all_sample_verses[name]
        samples = spread_sample(matches, n=6)

        results[name] = {
            "description": config["description"],
            "short": config["short"],
            "color": config["color"],
            "theology": config["theology"],
            "total": total,
            "ot_count": ot_count,
            "nt_count": nt_count,
            "by_book": book_counts,
            "by_book_rate": book_rate,
            "sample_verses": [
                {
                    "book": v["book"],
                    "chapter": v["chapter"],
                    "verse": v["verse"],
                    "text": v["text"],
                    "testament": v["testament"],
                }
                for v in samples
            ],
            "associations": [],  # filled in below
        }

    # Compute word associations (co-occurrence with specificity)
    print("  Computing word associations (this takes ~10 seconds)...")
    associations = compute_associations(verses, compiled, global_word_counts, total_bible_words)
    for name in results:
        results[name]["associations"] = associations[name]

    return results


def tokenize(text):
    """Lowercase, strip punctuation, return list of meaningful words."""
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return [w for w in text.split() if len(w) > 2 and w not in STOP_WORDS]


def compute_associations(verses, compiled_patterns, global_word_counts, total_bible_words, top_n=40):
    """
    For each divine name, find the words that most distinctively appear
    in the same verse — i.e., high co-occurrence AND high specificity
    (more frequent in name-verses than in the Bible overall).

    Specificity score = rate_in_name_verses / rate_in_bible
    A score of 3.0 means the word appears 3x more often near this name
    than you'd expect from its general Bible frequency.

    Returns: dict of name -> list of {word, count, rate, specificity}
    """
    # Gather all verse texts that contain each name
    name_verse_words = {name: Counter() for name in compiled_patterns}
    name_verse_total_words = {name: 0 for name in compiled_patterns}

    for verse in verses:
        text = verse["text"]
        words = tokenize(text)
        for name, pattern in compiled_patterns.items():
            if pattern.search(text):
                name_verse_words[name].update(words)
                name_verse_total_words[name] += len(words)

    associations = {}
    for name in compiled_patterns:
        total_words_in_name_verses = name_verse_total_words[name]
        if total_words_in_name_verses == 0:
            associations[name] = []
            continue

        scored = []
        for word, count in name_verse_words[name].most_common(500):
            # Rate in name-verses (per 1000 words)
            rate_in_name = count / total_words_in_name_verses * 1000
            # Rate in whole Bible (per 1000 words)
            global_count = global_word_counts.get(word, 0)
            rate_global = global_count / total_bible_words * 1000 if total_bible_words > 0 else 0
            # Specificity: how much MORE common near this name
            specificity = rate_in_name / rate_global if rate_global > 0 else 0

            # Only include words with decent absolute count AND meaningful specificity
            if count >= 3 and specificity >= 1.2:
                scored.append({
                    "word": word,
                    "count": count,
                    "rate": round(rate_in_name, 3),
                    "specificity": round(specificity, 2),
                })

        # Sort by a combined score: specificity * log(count) — balances rarity vs frequency
        import math
        scored.sort(key=lambda x: x["specificity"] * math.log(x["count"] + 1), reverse=True)
        associations[name] = scored[:top_n]

    return associations


def spread_sample(items, n=6):
    """
    Pick n items spread evenly across a list (first, last, and evenly spaced middle).
    Prioritizes getting OT and NT representation when possible.
    """
    if not items:
        return []
    if len(items) <= n:
        return items

    # Try to get OT and NT representation
    ot = [v for v in items if v["testament"] == "Old Testament"]
    nt = [v for v in items if v["testament"] == "New Testament"]

    selected = []

    if ot and nt:
        # Take some from each
        ot_n = min(3, len(ot))
        nt_n = min(3, len(nt))
        ot_step = max(1, len(ot) // ot_n)
        nt_step = max(1, len(nt) // nt_n)
        selected = [ot[i * ot_step] for i in range(ot_n) if i * ot_step < len(ot)]
        selected += [nt[i * nt_step] for i in range(nt_n) if i * nt_step < len(nt)]
    else:
        # Just spread sample
        step = len(items) // n
        selected = [items[i * step] for i in range(n) if i * step < len(items)]

    return selected[:n]


# ============================================================
# STEP D: Print findings
# ============================================================

def print_findings(results):
    """Display interesting divine name statistics."""
    print(f"\n{'=' * 65}")
    print(f"  DIVINE NAMES ANALYSIS FINDINGS")
    print(f"{'=' * 65}")

    for name, data in results.items():
        ot_pct = round(data["ot_count"] / data["total"] * 100, 1) if data["total"] > 0 else 0
        nt_pct = round(data["nt_count"] / data["total"] * 100, 1) if data["total"] > 0 else 0
        print(f"\n  {name:20s}  total={data['total']:>6,}   OT={ot_pct:>5.1f}%  NT={nt_pct:>5.1f}%")

        # Top 5 books
        top5 = sorted(data["by_book"].items(), key=lambda x: x[1], reverse=True)[:5]
        for book, count in top5:
            if count > 0:
                print(f"    {book:25s} {count:>5,}")

    print(f"\n{'=' * 65}")


# ============================================================
# STEP E: Save results as JSON for the website
# ============================================================

def save_results(results, book_word_counts):
    """Save all divine name data as JSON for the dashboard."""
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)

    output = {
        "names": results,
        "book_order": BOOK_ORDER,
        "book_total_words": book_word_counts,
        "name_order": list(DIVINE_NAMES.keys()),
    }

    filepath = os.path.join("data", "processed", "divine_names.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    size_kb = os.path.getsize(filepath) / 1024
    print(f"\nSaved results to {filepath}  ({size_kb:.1f} KB)")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 65)
    print("  Step 7: Divine Names Analysis")
    print("=" * 65)

    print("\n--- Loading Bible data ---")
    verses = load_bible()

    print("\n--- Counting book word totals ---")
    book_word_counts = load_book_word_counts(verses)

    print("\n--- Analyzing divine names ---")
    results = analyze_divine_names(verses, book_word_counts)

    print_findings(results)

    print("\n--- Saving results ---")
    save_results(results, book_word_counts)

    print("\n[DONE] Divine names analysis complete!")
