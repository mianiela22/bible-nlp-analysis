function AboutTab() {
  return (
    <div className="tab-content about-tab">
      <h2>About This Project</h2>
      <p>
        This dashboard applies <strong>Natural Language Processing</strong> (NLP) techniques
        to the <strong>King James Version</strong> of the Bible — one of the most influential
        texts in the English language.
      </p>

      <h3>What's Being Analyzed?</h3>
      <div className="about-grid">
        <div className="about-card">
          <h4>📊 Word Frequencies</h4>
          <p>
            We tokenized and cleaned 789,634 words, removing common stop words
            (like "the", "and", "of") plus KJV-specific archaic words
            ("thee", "thou", "unto") to reveal the most meaningful terms.
          </p>
        </div>
        <div className="about-card">
          <h4>💭 Sentiment Analysis</h4>
          <p>
            Every one of the 31,102 verses was scored using <strong>VADER</strong>
            (Valence Aware Dictionary and sEntiment Reasoner), which rates text
            from -1 (most negative) to +1 (most positive).
          </p>
        </div>
        <div className="about-card">
          <h4>📖 Book Statistics</h4>
          <p>
            Detailed metrics for all 66 books including word counts, vocabulary
            richness (type-token ratio), average verse lengths, and categorical
            comparisons across literary genres.
          </p>
        </div>
      </div>

      <h3>Methodology Notes</h3>
      <ul>
        <li>
          <strong>Data Source:</strong> KJV text from{' '}
          <a href="https://www.gutenberg.org/ebooks/10" target="_blank" rel="noreferrer">
            Project Gutenberg
          </a>{' '}
          (public domain)
        </li>
        <li>
          <strong>Sentiment Caveat:</strong> VADER was designed for modern English,
          so it may not perfectly capture the tone of archaic KJV language.
          Words like "smite" or "wrath" may be underrepresented in its lexicon.
        </li>
        <li>
          <strong>Languages:</strong> Python (data processing, NLP), React (dashboard)
        </li>
        <li>
          <strong>Libraries:</strong> NLTK, pandas, Vite, Recharts
        </li>
      </ul>

      <h3>About the Author</h3>
      <p>
        Built by <strong>Mirla Irias</strong> as a data science portfolio project
        combining faith and technology.
      </p>
      <p>
        University of Miami · Data Science & AI + Mathematics
      </p>
      <p>
        <a href="https://github.com/mianiela22/bible-nlp-analysis" target="_blank" rel="noreferrer">
          View on GitHub →
        </a>
      </p>
    </div>
  )
}

export default AboutTab