import { useState, useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, AreaChart, Area
} from 'recharts'

const OT_COLOR = '#8B4513'
const NT_COLOR = '#4169E1'
const ACCENT = '#DAA520'

function WordTrackerTab({ data }) {
  const [searchWord, setSearchWord] = useState('love')
  const [showRate, setShowRate] = useState(false)
  const [suggestions, setSuggestions] = useState([])

  if (!data) return <p>Loading word tracker data...</p>

  const bookOrder = data.book_order

  // Get chart data for the current word
  const chartData = useMemo(() => {
    const word = searchWord.toLowerCase().trim()
    if (!word) return []

    // Check tracked words first (pre-computed with rates)
    if (data.tracked_words[word]) {
      return data.tracked_words[word].map((d, i) => ({
        book: d.book.length > 10 ? d.book.substring(0, 8) + '..' : d.book,
        fullName: d.book,
        count: d.count,
        rate: d.rate,
        testament: i < 39 ? 'OT' : 'NT',
      }))
    }

    // Check all words index
    if (data.all_words[word]) {
      const wordCounts = data.all_words[word]
      return bookOrder.map((book, i) => ({
        book: book.length > 10 ? book.substring(0, 8) + '..' : book,
        fullName: book,
        count: wordCounts[book] || 0,
        rate: data.book_total_words[book]
          ? Math.round(((wordCounts[book] || 0) / data.book_total_words[book]) * 1000 * 100) / 100
          : 0,
        testament: i < 39 ? 'OT' : 'NT',
      }))
    }

    return []
  }, [searchWord, data, bookOrder])

  // Stats for current word
  const totalCount = chartData.reduce((sum, d) => sum + d.count, 0)
  const otCount = chartData.filter(d => d.testament === 'OT').reduce((sum, d) => sum + d.count, 0)
  const ntCount = chartData.filter(d => d.testament === 'NT').reduce((sum, d) => sum + d.count, 0)
  const peakBook = chartData.length > 0
    ? chartData.reduce((max, d) => d.count > max.count ? d : max, chartData[0])
    : null

  // Handle search input
  const handleSearch = (value) => {
    setSearchWord(value)
    const lower = value.toLowerCase().trim()
    if (lower.length >= 2) {
      const matches = data.vocabulary
        .filter(v => v.word.startsWith(lower))
        .slice(0, 8)
      setSuggestions(matches)
    } else {
      setSuggestions([])
    }
  }

  // Quick pick words
  const quickPicks = [
    { label: 'Love', word: 'love' },
    { label: 'Faith', word: 'faith' },
    { label: 'Sin', word: 'sin' },
    { label: 'Jesus', word: 'jesus' },
    { label: 'Death', word: 'death' },
    { label: 'Peace', word: 'peace' },
    { label: 'King', word: 'king' },
    { label: 'Mercy', word: 'mercy' },
    { label: 'Pray', word: 'pray' },
    { label: 'Holy', word: 'holy' },
  ]

  const dataKey = showRate ? 'rate' : 'count'

  return (
    <div className="tab-content">
      {/* Search */}
      <div className="search-section">
        <h3>Track any word across the Bible</h3>
        <p className="chart-description">
          Type a word to see how it flows from Genesis to Revelation
        </p>
        <div className="search-row">
          <div className="search-input-wrapper">
            <input
              type="text"
              value={searchWord}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Type a word..."
              className="search-input"
            />
            {suggestions.length > 0 && (
              <div className="suggestions">
                {suggestions.map((s, i) => (
                  <div
                    key={i}
                    className="suggestion-item"
                    onClick={() => {
                      setSearchWord(s.word)
                      setSuggestions([])
                    }}
                  >
                    {s.word} <span className="suggestion-count">({s.total.toLocaleString()})</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick picks */}
        <div className="quick-picks">
          {quickPicks.map(qp => (
            <button
              key={qp.word}
              className={'quick-pick ' + (searchWord === qp.word ? 'active' : '')}
              onClick={() => { setSearchWord(qp.word); setSuggestions([]) }}
            >
              {qp.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stats for current word */}
      {totalCount > 0 && (
        <div className="stats-row">
          <div className="stat-card">
            <div className="stat-number">{totalCount.toLocaleString()}</div>
            <div className="stat-label">Total "{searchWord}"</div>
          </div>
          <div className="stat-card" style={{ borderLeft: '4px solid ' + OT_COLOR }}>
            <div className="stat-number">{otCount.toLocaleString()}</div>
            <div className="stat-label">Old Testament</div>
          </div>
          <div className="stat-card" style={{ borderLeft: '4px solid ' + NT_COLOR }}>
            <div className="stat-number">{ntCount.toLocaleString()}</div>
            <div className="stat-label">New Testament</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{peakBook ? peakBook.fullName : '-'}</div>
            <div className="stat-label">Peak Book ({peakBook ? peakBook.count : 0}x)</div>
          </div>
        </div>
      )}

      {totalCount === 0 && searchWord && (
        <div className="insight-box">
          <p>No occurrences of "{searchWord}" found. Try another word!</p>
        </div>
      )}

      {/* Toggle */}
      <div className="controls">
        <button
          className={'control-btn ' + (!showRate ? 'active' : '')}
          onClick={() => setShowRate(false)}
        >
          Raw Count
        </button>
        <button
          className={'control-btn ' + (showRate ? 'active' : '')}
          onClick={() => setShowRate(true)}
        >
          Per 1,000 Words (normalized)
        </button>
      </div>

      {/* Chart */}
      {totalCount > 0 && (
        <div className="chart-container">
          <h3>"{searchWord}" — {showRate ? 'Rate per 1,000 words' : 'Raw count'} by book</h3>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={chartData} margin={{ bottom: 80 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="book"
                angle={-90}
                textAnchor="end"
                interval={0}
                style={{ fontSize: 9 }}
                height={80}
              />
              <YAxis />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const d = payload[0].payload
                    return (
                      <div className="custom-tooltip">
                        <strong>{d.fullName}</strong>
                        <p>Count: {d.count}</p>
                        <p>Rate: {d.rate} per 1,000 words</p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Area
                type="monotone"
                dataKey={dataKey}
                stroke={ACCENT}
                fill={ACCENT}
                fillOpacity={0.3}
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Insight */}
      <div className="insight-box">
        <h4>How to use this</h4>
        <p>
          Type any word to trace its usage across all 66 books of the Bible.
          Use <strong>"Per 1,000 Words"</strong> mode to normalize for book length —
          this shows the <em>concentration</em> of a word rather than just raw count,
          so shorter books like Philemon get a fair comparison against giants like Psalms.
        </p>
        <p style={{ marginTop: 8 }}>
          <strong>Try these:</strong> "faith" (almost exclusively NT!), "king" (peaks in 1-2 Kings),
          "love" (peaks in 1 John), "blood" (peaks in Leviticus)
        </p>
      </div>
    </div>
  )
}

export default WordTrackerTab