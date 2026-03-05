"""
Step 10: Command & Promise Identifier
=======================================
Detects two theological categories across all 31,102 KJV verses:

  COMMANDS  — what God asks of us (imperatives, moral directives)
  PROMISES  — what God pledges to us (divine assurances, covenants)

Pattern design philosophy:
  - KJV grammar is consistent and distinctive, making regex reliable
  - We favour precision over recall: only tag verses with clear signal
  - Each verse can be BOTH a command and a promise (e.g. "Trust in the
    LORD and he will give you the desires of your heart")
  - A confidence score (0.70 – 1.00) lets the UI filter for quality

Command categories:
  love_relationship   — love, forgive, honour relationships
  prayer_worship      — pray, worship, give thanks
  holiness            — be holy, flee sin, sanctify
  faith_trust         — trust, believe, fear not
  justice_compassion  — care for the poor, oppressed
  mission             — go, preach, make disciples
  obedience_general   — keep commandments, walk in God's ways

Promise categories:
  presence_protection — I am with you, never leave/forsake
  provision           — I will provide, bread, supply needs
  salvation           — everlasting life, saved, redeemed
  strength            — renewed strength, power given
  peace               — peace that passes understanding
  future_hope         — plans for a future/hope, new things
  conditional         — if...then promises (he that believeth shall...)

Output JSON structure:
  {
    "commands": [
      {
        "book": "Matthew", "chapter": 5, "verse": 44,
        "text": "But I say unto you, Love your enemies...",
        "category": "love_relationship",
        "confidence": 0.95,
        "testament": "NT"
      }, ...
    ],
    "promises": [...],
    "stats": {
      "total_commands": N,
      "total_promises": N,
      "by_category": {...},
      "by_book": {
        "Genesis": {"commands": N, "promises": N}, ...
      }
    },
    "categories": {
      "commands": [
        {"id": "love_relationship", "label": "Love & Relationships",
         "description": "Commands to love, forgive, and honour others",
         "color": "#e74c3c", "icon": "❤️"},
        ...
      ],
      "promises": [...]
    }
  }
"""

import csv
import json
import os
import re
from collections import defaultdict

# ============================================================
# PATTERN DEFINITIONS
# ============================================================

# --- COMMAND PATTERNS ---
# Each entry: (category, confidence, pattern_or_patterns)
COMMAND_PATTERNS = [

    # ── Love & Relationships ──────────────────────────────────────────
    ("love_relationship", 0.95,
     r"\blove (?:one another|your (?:neighbour|neighbor|enemies|brother|sister|wife|husband|children|parents))\b"),
    ("love_relationship", 0.90,
     r"\bforgive (?:one another|us|them|him|her|your brother|men their trespasses)\b"),
    ("love_relationship", 0.90,
     r"\bhonour (?:thy father|thy mother|your father|your mother|the king|all men)\b"),
    ("love_relationship", 0.85,
     r"\b(?:love|loving)(?:\s+\w+){0,3}\s+(?:thy|your) (?:neighbour|neighbor|enemies|brother)\b"),
    ("love_relationship", 0.85,
     r"\breconcile (?:thyself|yourself)\b|\bbear (?:one another|ye one another)"),
    ("love_relationship", 0.80,
     r"\bcomfort (?:one another|ye|the feeble|them that mourn|all that mourn)\b"),
    ("love_relationship", 0.80,
     r"\bkindness\b.{0,40}\bshew\b|\bshew\b.{0,40}\bkindness\b"),

    # ── Prayer & Worship ─────────────────────────────────────────────
    ("prayer_worship", 0.95,
     r"\bpray (?:without ceasing|always|for one another|for them|for your enemies)\b"),
    ("prayer_worship", 0.90,
     r"\b(?:give thanks|rejoice always|rejoice evermore|rejoice in the lord)\b"),
    ("prayer_worship", 0.90,
     r"\bworship (?:the lord|god|him|the father|in spirit)\b"),
    ("prayer_worship", 0.90,
     r"\bpraise (?:the lord|god|him|ye the lord|his name)\b"),
    ("prayer_worship", 0.85,
     r"\bcall (?:upon|on) (?:the lord|his name|god)\b"),
    ("prayer_worship", 0.85,
     r"\bthou shalt (?:worship|praise|pray|sing)\b"),
    ("prayer_worship", 0.80,
     r"\bsing (?:unto|praises|to) (?:the lord|god|him)\b"),
    ("prayer_worship", 0.80,
     r"\bmake (?:a joyful noise|melody)\b"),

    # ── Holiness & Avoiding Sin ───────────────────────────────────────
    ("holiness", 0.95,
     r"\bbe (?:ye |thou )?holy\b"),
    ("holiness", 0.90,
     r"\bflee (?:fornication|idolatry|youthful lusts|also youthful|sexual immorality|temptation|evil)\b"),
    ("holiness", 0.90,
     r"\bput (?:off|away|aside) (?:all |the old man|anger|malice|lying|bitterness|wrath)\b"),
    ("holiness", 0.90,
     r"\b(?:abstain|abstaining) from (?:all appearance|evil|fornication|idolatry|blood)\b"),
    ("holiness", 0.85,
     r"\bsanctify (?:yourselves|thyself|them|the congregation|a fast)\b"),
    ("holiness", 0.85,
     r"\bthou shalt (?:not kill|not steal|not commit|not bear false|not covet|not take the name)\b"),
    ("holiness", 0.80,
     r"\brepent (?:ye|and be baptized|of|from|therefore|and turn)\b"),
    ("holiness", 0.80,
     r"\bcleanseourselves|cleanse (?:your|thy) (?:hands|heart|soul|way)\b"),
    ("holiness", 0.80,
     r"\bcleanse (?:your|thy) (?:hands|heart|soul|way)\b"),
    ("holiness", 0.80,
     r"\bturn (?:from|ye from|away from) (?:evil|your wickedness|iniquity|idols)\b"),
    ("holiness", 0.75,
     r"\bwalk (?:in|not) (?:the spirit|truth|love|light|wisdom|newness|darkness)\b"),

    # ── Faith & Trust ─────────────────────────────────────────────────
    ("faith_trust", 0.95,
     r"\bfear not\b|\bbe not afraid\b|\bfear thou not\b"),
    ("faith_trust", 0.90,
     r"\btrust in the lord\b|\btrust (?:in|thou) (?:god|him|the lord)\b"),
    ("faith_trust", 0.90,
     r"\bbelieve (?:in|on) (?:him|jesus|the lord|god|the son|christ)\b"),
    ("faith_trust", 0.90,
     r"\bhave faith (?:in god|in the lord|in him)\b"),
    ("faith_trust", 0.85,
     r"\bbe (?:strong and|strong,) (?:of good courage|courageous)\b"),
    ("faith_trust", 0.85,
     r"\bfaint not\b|\bbe not discouraged\b|\bbe not dismayed\b"),
    ("faith_trust", 0.80,
     r"\brest (?:in|on|upon) (?:the lord|god|him|christ)\b"),
    ("faith_trust", 0.80,
     r"\bcommit (?:thy|your) (?:way|works|life) (?:unto|to) (?:the lord|god)\b"),

    # ── Justice & Compassion ──────────────────────────────────────────
    ("justice_compassion", 0.95,
     r"\bdo (?:justice|justly)\b|\bjudge (?:righteously|righteous judgment)\b"),
    ("justice_compassion", 0.90,
     r"\bfeed (?:the hungry|the poor|my sheep|my lambs)\b"),
    ("justice_compassion", 0.90,
     r"\bclothe (?:the naked)\b|\bvisit (?:the sick|the prisoner|them that are)\b"),
    ("justice_compassion", 0.90,
     r"\bdefend (?:the poor|the fatherless|the widow|the oppressed)\b"),
    ("justice_compassion", 0.85,
     r"\boppress not|oppress (?:not|no man)\b|\bdo no wrong\b"),
    ("justice_compassion", 0.85,
     r"\bliberate|set free|proclaim (?:liberty|freedom|release)\b"),
    ("justice_compassion", 0.80,
     r"\bshow mercy\b|\bbe merciful\b|\bshew mercy\b"),
    ("justice_compassion", 0.80,
     r"\bgive (?:to|unto) (?:the poor|the needy|him that asketh)\b"),

    # ── Mission & Evangelism ──────────────────────────────────────────
    ("mission", 0.95,
     r"\bgo (?:ye therefore|into all the world|preach|and preach|and teach|and make)\b"),
    ("mission", 0.95,
     r"\bmake disciples\b|\bpreach (?:the gospel|the word|the kingdom)\b"),
    ("mission", 0.90,
     r"\bbe (?:my )?witnesses\b|\bbe a witness\b"),
    ("mission", 0.85,
     r"\btell (?:it|them|the world|what god|what the lord)\b"),
    ("mission", 0.80,
     r"\blet (?:your|thy) light (?:shine|so shine)\b"),

    # ── General Obedience ─────────────────────────────────────────────
    ("obedience_general", 0.90,
     r"\bkeep (?:my|the|his|all) commandments\b"),
    ("obedience_general", 0.90,
     r"\bobey (?:god|the lord|my voice|his voice|your parents)\b"),
    ("obedience_general", 0.85,
     r"\bwalk in (?:my|his|the) (?:ways|statutes|commandments|law)\b"),
    ("obedience_general", 0.85,
     r"\bdo (?:all|whatsoever) (?:i|the lord|god|he) (?:command|commanded)\b"),
    ("obedience_general", 0.80,
     r"\bseek (?:ye|the lord|his face|first the kingdom|god)\b"),
    ("obedience_general", 0.80,
     r"\bsubmit (?:yourselves|thyself|to|unto) (?:god|the lord|one another|every ordinance)\b"),
]

# --- PROMISE PATTERNS ---
PROMISE_PATTERNS = [

    # ── Presence & Protection ─────────────────────────────────────────
    ("presence_protection", 0.99,
     r"\bi will (?:never leave|never forsake|not leave|not forsake) (?:thee|you)\b"),
    ("presence_protection", 0.95,
     r"\bi am with (?:thee|you)\b|\bthe lord (?:is|thy god is) with (?:thee|you)\b"),
    ("presence_protection", 0.90,
     r"\bhe shall (?:keep|preserve|protect|cover|defend) (?:thee|you|his saints|the righteous)\b"),
    ("presence_protection", 0.90,
     r"\bno weapon (?:formed|that is formed) against (?:thee|you) shall prosper\b"),
    ("presence_protection", 0.85,
     r"\bthe lord (?:shall|will) (?:protect|keep|preserve|defend|deliver|shield)\b"),
    ("presence_protection", 0.85,
     r"\bi will (?:be|become) (?:thy|your) (?:god|shield|help|strength|salvation)\b"),
    ("presence_protection", 0.80,
     r"\bunder (?:his|the shadow of the almighty|thy wings)\b"),
    ("presence_protection", 0.80,
     r"\bangels (?:shall|will) (?:keep|guard|charge over|bear)\b"),

    # ── Provision ─────────────────────────────────────────────────────
    ("provision", 0.95,
     r"\bi will (?:provide|supply|give|feed|satisfy) (?:thee|you|your|thy)\b"),
    ("provision", 0.90,
     r"\bmy god shall supply all your need\b|\bseek (?:ye )?first.{0,40}added unto you\b"),
    ("provision", 0.90,
     r"\bthe lord (?:will|shall) provide\b|\bjehovah[- ]jireh\b"),
    ("provision", 0.85,
     r"\bhe (?:shall|will) give (?:you|thee) (?:bread|food|rain|meat|water|thy daily)\b"),
    ("provision", 0.80,
     r"\bgive (?:you|thee|us) (?:this day|our daily) (?:bread|meat)\b"),
    ("provision", 0.75,
     r"\boverflowing|running over|pressed down|shaken together\b"),

    # ── Salvation & Forgiveness ───────────────────────────────────────
    ("salvation", 0.99,
     r"\beverlasting life\b|\beternal life\b"),
    ("salvation", 0.95,
     r"\bwhosoever (?:believeth|believes|calleth|shall call|confesseth) .{0,50}(?:shall be saved|have everlasting|not perish)\b"),
    ("salvation", 0.95,
     r"\bwhosoever will\b.{0,30}\bsave\b|\bsaved\b.{0,30}\bwhosoever\b"),
    ("salvation", 0.90,
     r"\bif (?:we|thou|you) confess (?:our|thy|your) sins.{0,60}(?:forgive|cleanse)\b"),
    ("salvation", 0.90,
     r"\bhe that believeth (?:in me|on me|on him|on the son)\b"),
    ("salvation", 0.90,
     r"\bi will forgive (?:their|your|thy) (?:sins|iniquity|transgressions|wickedness)\b"),
    ("salvation", 0.85,
     r"\bredeemed|redeem (?:thee|you|israel|them)\b.{0,30}\b(?:lord|god)\b"),
    ("salvation", 0.85,
     r"\bthe lord (?:is|shall be) my (?:salvation|redeemer|deliverer)\b"),
    ("salvation", 0.80,
     r"\bcall on (?:the name of the lord|him).{0,30}saved\b|\bsaved.{0,30}call on the name\b"),

    # ── Strength & Power ──────────────────────────────────────────────
    ("strength", 0.95,
     r"\bi can do all things through (?:christ|him)\b"),
    ("strength", 0.95,
     r"\bthey (?:that wait|that wait upon) the lord (?:shall|will) renew (?:their)?strength\b"),
    ("strength", 0.90,
     r"\bmy (?:grace|strength|power) (?:is|shall be) sufficient\b"),
    ("strength", 0.90,
     r"\bthe lord (?:is|shall be) my strength\b|\bstrengthened with (?:all|his) might\b"),
    ("strength", 0.85,
     r"\bi will strengthen (?:thee|you)\b|\bi will uphold (?:thee|you)\b"),
    ("strength", 0.85,
     r"\bthe lord (?:will|shall) (?:strengthen|uphold|sustain|establish)\b"),
    ("strength", 0.80,
     r"\bgreater is he that is in you\b|\bmore than conquerors\b"),

    # ── Peace & Rest ──────────────────────────────────────────────────
    ("peace", 0.95,
     r"\bpeace (?:that passeth|which passeth) all understanding\b"),
    ("peace", 0.90,
     r"\bmy peace i (?:give|leave) unto you\b"),
    ("peace", 0.90,
     r"\bthe lord (?:will|shall) give (?:thee|you|his people) peace\b"),
    ("peace", 0.85,
     r"\brest (?:for your souls|unto you|to the weary)\b|\bcome unto me.{0,30}rest\b"),
    ("peace", 0.85,
     r"\bi will give (?:thee|you|them) rest\b|\bgive you rest\b"),
    ("peace", 0.80,
     r"\bhe maketh me to lie down\b|\bstillness|be still.{0,20}know that i am god\b"),
    ("peace", 0.80,
     r"\bthou wilt keep (?:him|them) in perfect peace\b"),

    # ── Future Hope ───────────────────────────────────────────────────
    ("future_hope", 0.95,
     r"\bplans (?:to prosper|for (?:welfare|good)|for a future|for hope)\b|\bfuture and a hope\b"),
    ("future_hope", 0.95,
     r"\bfor i know the (?:plans|thoughts) i have for you\b"),
    ("future_hope", 0.90,
     r"\ball things work together for good\b"),
    ("future_hope", 0.90,
     r"\bi will (?:restore|rebuild|renew|make new|do a new thing|do great things)\b"),
    ("future_hope", 0.90,
     r"\bbehold i make all things new\b|\bnew (?:heaven|earth|jerusalem)\b"),
    ("future_hope", 0.85,
     r"\bthe latter (?:end|days|glory) (?:shall be|will be) greater\b"),
    ("future_hope", 0.85,
     r"\bweeping (?:may|shall) endure.{0,30}joy (?:cometh|comes) in the morning\b"),
    ("future_hope", 0.80,
     r"\bi am (?:the resurrection|the way|the truth|the life)\b"),
    ("future_hope", 0.80,
     r"\bhe (?:that|who) hath begun a good work\b"),

    # ── Conditional / "If-Then" Promises ─────────────────────────────
    ("conditional", 0.90,
     r"\bif (?:my people|thou|you|ye).{5,80}(?:i will|shall)\b"),
    ("conditional", 0.85,
     r"\bhe that (?:believeth|trusteth|seeketh|keepeth|doeth|walketh).{0,60}(?:shall|will)\b"),
    ("conditional", 0.85,
     r"\bwhosoever (?:shall|will|believeth|confesseth|calleth).{0,60}(?:shall|will)\b"),
    ("conditional", 0.80,
     r"\bif (?:ye|you) (?:abide|keep|love|walk|seek|obey).{0,60}(?:i will|shall|give|do)\b"),
    ("conditional", 0.80,
     r"\bsow.{0,30}reap|give.{0,30}given unto you\b"),
]

# ── Category metadata ─────────────────────────────────────────────────────────
CATEGORY_META = {
    "commands": [
        {"id": "love_relationship", "label": "Love & Relationships",
         "description": "Commands to love, forgive, and honour others",
         "color": "#e74c3c", "icon": "❤️"},
        {"id": "prayer_worship", "label": "Prayer & Worship",
         "description": "Commands to pray, praise, and worship God",
         "color": "#9b59b6", "icon": "🙏"},
        {"id": "holiness", "label": "Holiness",
         "description": "Commands to pursue holiness and flee sin",
         "color": "#3498db", "icon": "✨"},
        {"id": "faith_trust", "label": "Faith & Trust",
         "description": "Commands to trust God and overcome fear",
         "color": "#f39c12", "icon": "🌟"},
        {"id": "justice_compassion", "label": "Justice & Compassion",
         "description": "Commands to defend the poor and oppressed",
         "color": "#27ae60", "icon": "⚖️"},
        {"id": "mission", "label": "Mission",
         "description": "Commands to share the gospel and make disciples",
         "color": "#16a085", "icon": "🌍"},
        {"id": "obedience_general", "label": "Obedience",
         "description": "General commands to walk in God's ways",
         "color": "#8e44ad", "icon": "📜"},
    ],
    "promises": [
        {"id": "presence_protection", "label": "Presence & Protection",
         "description": "God's promise to be with us and protect us",
         "color": "#2980b9", "icon": "🛡️"},
        {"id": "provision", "label": "Provision",
         "description": "God's promise to supply our needs",
         "color": "#27ae60", "icon": "🌾"},
        {"id": "salvation", "label": "Salvation",
         "description": "Promises of forgiveness, redemption, and eternal life",
         "color": "#c0392b", "icon": "✝️"},
        {"id": "strength", "label": "Strength & Power",
         "description": "Promises of divine strength and ability",
         "color": "#e67e22", "icon": "💪"},
        {"id": "peace", "label": "Peace & Rest",
         "description": "Promises of God's peace and rest",
         "color": "#1abc9c", "icon": "☮️"},
        {"id": "future_hope", "label": "Future & Hope",
         "description": "Promises of a good future and eternal hope",
         "color": "#f1c40f", "icon": "🌅"},
        {"id": "conditional", "label": "Conditional Promises",
         "description": "If-then promises: blessings tied to obedience",
         "color": "#7f8c8d", "icon": "🔑"},
    ],
}

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


def compile_patterns(pattern_list):
    """Pre-compile all regex patterns for speed."""
    compiled = []
    for category, confidence, pattern in pattern_list:
        compiled.append((category, confidence, re.compile(pattern, re.IGNORECASE)))
    return compiled


def classify_verses(verses, command_patterns, promise_patterns):
    """
    Tag every verse that matches at least one pattern.
    A verse can be both a command and a promise.
    When multiple patterns match, keep the highest-confidence one per category.
    """
    commands = []
    promises = []

    for verse in verses:
        text = verse["text"]
        book = verse["book"]
        chapter = int(verse["chapter"])
        vnum = int(verse["verse"])
        testament = verse.get("testament", "OT")

        # Check command patterns
        best_cmd = {}  # category -> (confidence, pattern_hit)
        for cat, conf, pattern in command_patterns:
            if pattern.search(text):
                if cat not in best_cmd or conf > best_cmd[cat][0]:
                    best_cmd[cat] = (conf, pattern.pattern)

        for cat, (conf, _) in best_cmd.items():
            commands.append({
                "book": book,
                "chapter": chapter,
                "verse": vnum,
                "text": text,
                "category": cat,
                "confidence": conf,
                "testament": testament,
            })

        # Check promise patterns
        best_prom = {}
        for cat, conf, pattern in promise_patterns:
            if pattern.search(text):
                if cat not in best_prom or conf > best_prom[cat][0]:
                    best_prom[cat] = (conf, pattern.pattern)

        for cat, (conf, _) in best_prom.items():
            promises.append({
                "book": book,
                "chapter": chapter,
                "verse": vnum,
                "text": text,
                "category": cat,
                "confidence": conf,
                "testament": testament,
            })

    return commands, promises


def build_stats(commands, promises):
    """Aggregate counts by category and by book."""
    cmd_by_cat = defaultdict(int)
    prom_by_cat = defaultdict(int)
    by_book = {book: {"commands": 0, "promises": 0} for book in BOOK_ORDER}
    cmd_books = defaultdict(set)  # book -> set of (ch, v) to avoid double-counting
    prom_books = defaultdict(set)

    for c in commands:
        cmd_by_cat[c["category"]] += 1
        key = (c["chapter"], c["verse"])
        cmd_books[c["book"]].add(key)

    for p in promises:
        prom_by_cat[p["category"]] += 1
        key = (p["chapter"], p["verse"])
        prom_books[p["book"]].add(key)

    for book in BOOK_ORDER:
        if book in by_book:
            by_book[book]["commands"] = len(cmd_books.get(book, set()))
            by_book[book]["promises"] = len(prom_books.get(book, set()))

    # Unique verse counts (a verse can match multiple categories)
    unique_cmd_verses = len({(c["book"], c["chapter"], c["verse"]) for c in commands})
    unique_prom_verses = len({(p["book"], p["chapter"], p["verse"]) for p in promises})

    return {
        "total_commands": len(commands),
        "total_promises": len(promises),
        "unique_command_verses": unique_cmd_verses,
        "unique_promise_verses": unique_prom_verses,
        "by_category": {
            "commands": dict(cmd_by_cat),
            "promises": dict(prom_by_cat),
        },
        "by_book": by_book,
    }


def print_findings(commands, promises, stats):
    print(f"\n{'=' * 60}")
    print("  COMMAND & PROMISE IDENTIFIER — RESULTS")
    print(f"{'=' * 60}")
    print(f"\n  Commands tagged : {stats['total_commands']:,}  ({stats['unique_command_verses']:,} unique verses)")
    print(f"  Promises tagged : {stats['total_promises']:,}  ({stats['unique_promise_verses']:,} unique verses)")

    print(f"\n  Commands by category:")
    for cat, n in sorted(stats["by_category"]["commands"].items(), key=lambda x: -x[1]):
        print(f"    {cat:25s}  {n:>4}")

    print(f"\n  Promises by category:")
    for cat, n in sorted(stats["by_category"]["promises"].items(), key=lambda x: -x[1]):
        print(f"    {cat:25s}  {n:>4}")

    print(f"\n  Top 10 books by combined command + promise count:")
    book_totals = {
        b: stats["by_book"][b]["commands"] + stats["by_book"][b]["promises"]
        for b in BOOK_ORDER
    }
    top_books = sorted(book_totals.items(), key=lambda x: -x[1])[:10]
    for book, total in top_books:
        c = stats["by_book"][book]["commands"]
        p = stats["by_book"][book]["promises"]
        print(f"    {book:20s}  cmd={c:3}  prom={p:3}  total={total:3}")

    # Show a few example verses
    print(f"\n  Sample commands:")
    seen = set()
    count = 0
    for c in commands:
        key = (c["book"], c["chapter"], c["verse"])
        if key not in seen and c["confidence"] >= 0.95:
            seen.add(key)
            print(f"    [{c['category']}]  {c['book']} {c['chapter']}:{c['verse']}  {c['text'][:80]}")
            count += 1
            if count >= 5:
                break

    print(f"\n  Sample promises:")
    seen = set()
    count = 0
    for p in promises:
        key = (p["book"], p["chapter"], p["verse"])
        if key not in seen and p["confidence"] >= 0.95:
            seen.add(key)
            print(f"    [{p['category']}]  {p['book']} {p['chapter']}:{p['verse']}  {p['text'][:80]}")
            count += 1
            if count >= 5:
                break

    print(f"\n{'=' * 60}")


def save_results(commands, promises, stats):
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)
    output = {
        "commands": commands,
        "promises": promises,
        "stats": stats,
        "categories": CATEGORY_META,
        "book_order": BOOK_ORDER,
    }
    filepath = os.path.join("data", "processed", "commands_promises.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(',', ':'))
    size_kb = os.path.getsize(filepath) / 1024
    print(f"\nSaved to {filepath}  ({size_kb:.0f} KB)")


if __name__ == "__main__":
    print("=" * 60)
    print("  Step 10: Command & Promise Identifier")
    print("=" * 60)

    print("\n--- Loading Bible ---")
    verses = load_bible()
    print(f"  {len(verses):,} verses loaded")

    print("\n--- Compiling patterns ---")
    cmd_patterns = compile_patterns(COMMAND_PATTERNS)
    prom_patterns = compile_patterns(PROMISE_PATTERNS)
    print(f"  {len(cmd_patterns)} command patterns, {len(prom_patterns)} promise patterns")

    print("\n--- Classifying verses ---")
    commands, promises = classify_verses(verses, cmd_patterns, prom_patterns)

    print("\n--- Building stats ---")
    stats = build_stats(commands, promises)

    print_findings(commands, promises, stats)

    print("\n--- Saving ---")
    save_results(commands, promises, stats)

    print("\n[DONE]")
