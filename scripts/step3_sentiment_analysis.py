"""
Step 3: Sentiment Analysis
===========================
Analyzes the emotional tone across the entire Bible using VADER.
Scores every verse, then aggregates by chapter, book, and testament.

VADER (Valence Aware Dictionary and sEntiment Reasoner) gives each
text a score from -1 (most negative) to +1 (most positive).

Saves results as JSON for the website dashboard.
"""

import csv
import json
import os
from nltk.sentiment import SentimentIntensityAnalyzer

# ============================================================
# STEP A: Load Bible data
# ============================================================
def load_bible():
    """Load our parsed Bible CSV."""
    filepath = os.path.join("data", "processed", "kjv_bible.csv")
    with open(filepath, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows):,} verses")
    return rows


# ============================================================
# STEP B: Score every single verse
# ============================================================
def score_all_verses(verses):
    """
    Run VADER sentiment analysis on every verse in the Bible.
    
    VADER looks at each word and checks if it's positive, negative,
    or neutral, then combines them into an overall score.
    
    The compound score ranges from:
        -1.0 = extremely negative
         0.0 = neutral
        +1.0 = extremely positive
    
    General thresholds:
        compound >= 0.05  -> Positive
        compound <= -0.05 -> Negative
        otherwise         -> Neutral
    """
    sia = SentimentIntensityAnalyzer()
    
    scored_verses = []
    
    for verse in verses:
        scores = sia.polarity_scores(verse["text"])
        
        scored_verses.append({
            "book": verse["book"],
            "chapter": int(verse["chapter"]),
            "verse": int(verse["verse"]),
            "text": verse["text"],
            "testament": verse["testament"],
            "neg": round(scores["neg"], 4),
            "neu": round(scores["neu"], 4),
            "pos": round(scores["pos"], 4),
            "compound": round(scores["compound"], 4),
        })
    
    print(f"Scored {len(scored_verses):,} verses")
    return scored_verses


# ============================================================
# STEP C: Aggregate scores by chapter and book
# ============================================================
def aggregate_scores(scored_verses):
    """
    Average the sentiment scores at different levels:
    - By chapter (for detailed emotional arcs)
    - By book (for book-level comparisons)
    - By testament (OT vs NT overall mood)
    
    We also find the most positive and most negative verses!
    """
    # --- By Chapter ---
    chapter_scores = {}
    for v in scored_verses:
        key = (v["book"], v["chapter"])
        if key not in chapter_scores:
            chapter_scores[key] = []
        chapter_scores[key].append(v["compound"])
    
    chapter_results = []
    for (book, chapter), scores in chapter_scores.items():
        avg = sum(scores) / len(scores)
        chapter_results.append({
            "book": book,
            "chapter": chapter,
            "avg_sentiment": round(avg, 4),
            "num_verses": len(scores),
            "min_sentiment": round(min(scores), 4),
            "max_sentiment": round(max(scores), 4),
        })
    
    # --- By Book ---
    book_scores = {}
    for v in scored_verses:
        if v["book"] not in book_scores:
            book_scores[v["book"]] = {"compounds": [], "pos": [], "neg": []}
        book_scores[v["book"]]["compounds"].append(v["compound"])
        book_scores[v["book"]]["pos"].append(v["pos"])
        book_scores[v["book"]]["neg"].append(v["neg"])
    
    book_results = {}
    for book, data in book_scores.items():
        compounds = data["compounds"]
        book_results[book] = {
            "avg_sentiment": round(sum(compounds) / len(compounds), 4),
            "avg_positive": round(sum(data["pos"]) / len(data["pos"]), 4),
            "avg_negative": round(sum(data["neg"]) / len(data["neg"]), 4),
            "num_verses": len(compounds),
            "positive_verses": sum(1 for c in compounds if c >= 0.05),
            "negative_verses": sum(1 for c in compounds if c <= -0.05),
            "neutral_verses": sum(1 for c in compounds if -0.05 < c < 0.05),
        }
    
    # --- By Testament ---
    ot_scores = [v["compound"] for v in scored_verses if v["testament"] == "Old Testament"]
    nt_scores = [v["compound"] for v in scored_verses if v["testament"] == "New Testament"]
    
    testament_results = {
        "Old Testament": {
            "avg_sentiment": round(sum(ot_scores) / len(ot_scores), 4),
            "num_verses": len(ot_scores),
            "positive_pct": round(sum(1 for c in ot_scores if c >= 0.05) / len(ot_scores) * 100, 1),
            "negative_pct": round(sum(1 for c in ot_scores if c <= -0.05) / len(ot_scores) * 100, 1),
        },
        "New Testament": {
            "avg_sentiment": round(sum(nt_scores) / len(nt_scores), 4),
            "num_verses": len(nt_scores),
            "positive_pct": round(sum(1 for c in nt_scores if c >= 0.05) / len(nt_scores) * 100, 1),
            "negative_pct": round(sum(1 for c in nt_scores if c <= -0.05) / len(nt_scores) * 100, 1),
        }
    }
    
    # --- Most positive and negative verses ---
    sorted_by_sentiment = sorted(scored_verses, key=lambda x: x["compound"])
    
    most_negative = []
    for v in sorted_by_sentiment[:10]:
        most_negative.append({
            "book": v["book"],
            "chapter": v["chapter"],
            "verse": v["verse"],
            "text": v["text"][:150],
            "compound": v["compound"],
        })
    
    most_positive = []
    for v in sorted_by_sentiment[-10:]:
        most_positive.append({
            "book": v["book"],
            "chapter": v["chapter"],
            "verse": v["verse"],
            "text": v["text"][:150],
            "compound": v["compound"],
        })
    most_positive.reverse()
    
    return {
        "chapters": chapter_results,
        "books": book_results,
        "testaments": testament_results,
        "most_positive": most_positive,
        "most_negative": most_negative,
    }


# ============================================================
# STEP D: Print findings
# ============================================================
def print_findings(results):
    """Display the most interesting sentiment findings."""
    
    print(f"\n{'=' * 60}")
    print(f"  SENTIMENT ANALYSIS FINDINGS")
    print(f"{'=' * 60}")
    
    # Testament comparison
    print(f"\n  OLD TESTAMENT vs NEW TESTAMENT:")
    for testament, data in results["testaments"].items():
        print(f"\n    {testament}:")
        print(f"      Average sentiment: {data['avg_sentiment']:+.4f}")
        print(f"      Positive verses:   {data['positive_pct']}%")
        print(f"      Negative verses:   {data['negative_pct']}%")
    
    # Top 5 most positive books
    sorted_books = sorted(results["books"].items(), key=lambda x: x[1]["avg_sentiment"], reverse=True)
    
    print(f"\n  TOP 5 MOST POSITIVE BOOKS:")
    for book, data in sorted_books[:5]:
        bar = "+" * int(data["avg_sentiment"] * 50)
        print(f"    {book:20s} {data['avg_sentiment']:+.4f}  {bar}")
    
    # Top 5 most negative books
    print(f"\n  TOP 5 MOST NEGATIVE BOOKS:")
    for book, data in sorted_books[-5:]:
        bar = "-" * int(abs(data["avg_sentiment"]) * 50)
        print(f"    {book:20s} {data['avg_sentiment']:+.4f}  {bar}")
    
    # Most positive verses
    print(f"\n  TOP 5 MOST POSITIVE VERSES:")
    for v in results["most_positive"][:5]:
        print(f"    [{v['compound']:+.4f}] {v['book']} {v['chapter']}:{v['verse']}")
        print(f"      {v['text'][:100]}...")
    
    # Most negative verses
    print(f"\n  TOP 5 MOST NEGATIVE VERSES:")
    for v in results["most_negative"][:5]:
        print(f"    [{v['compound']:+.4f}] {v['book']} {v['chapter']}:{v['verse']}")
        print(f"      {v['text'][:100]}...")
    
    print(f"\n{'=' * 60}")


# ============================================================
# STEP E: Save results as JSON for the website
# ============================================================
def save_results(results):
    """Save all sentiment data as JSON for the dashboard."""
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)
    
    filepath = os.path.join("data", "processed", "sentiment_analysis.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nSaved results to {filepath}")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Step 3: Sentiment Analysis")
    print("=" * 60)
    
    # Load
    print("\n--- Loading Bible data ---")
    verses = load_bible()
    
    # Score every verse
    print("\n--- Scoring all verses (this may take a minute) ---")
    scored_verses = score_all_verses(verses)
    
    # Aggregate
    print("\n--- Aggregating scores ---")
    results = aggregate_scores(scored_verses)
    
    # Display findings
    print_findings(results)
    
    # Save
    print("\n--- Saving results ---")
    save_results(results)
    
    print("\n[DONE] Sentiment analysis complete!")
