import { useState } from 'react'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, ReferenceLine, Legend
} from 'recharts'

const POSITIVE_COLOR = '#2ecc71'
const NEGATIVE_COLOR = '#e74c3c'
const NEUTRAL_COLOR = '#95a5a6'
const OT_COLOR = '#8B4513'
const NT_COLOR = '#4169E1'

function SentimentTab({ data }) {
  const [view, setView] = useState('journey')

  if (!data) return <p>Loading sentiment data...</p>

  const bookOrder = [
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

  const journeyData = bookOrder
    .filter(book => data.books[book])
    .map((book, i) => ({
      book: book.length > 10 ? book.substring(0, 8) + '...' : book,
      fullName: book,
      sentiment: data.books[book].avg_sentiment,
      positive: data.books[book].avg_positive,
      negative: data.books[book].avg_negative,
      index: i,
      testament: i < 39 ? 'OT' : 'NT',
    }))

  const sortedBooks = [...journeyData].sort((a, b) => b.sentiment - a.sentiment)

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload
      return (
        <div className="custom-tooltip">
          <strong>{d.fullName || d.name}</strong>
          <p>Sentiment: {(d.sentiment || d['Avg Sentiment'] || 0).toFixed(4)}</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="tab-content">
      <div className="stats-row">
        <div className="stat-card" style={{ borderLeft: '4px solid ' + OT_COLOR }}>
          <div className="stat-number">{data.testaments['Old Testament'].avg_sentiment.toFixed(4)}</div>
          <div className="stat-label">OT Avg Sentiment</div>
          <div className="stat-detail">
            {data.testaments['Old Testament'].positive_pct}% positive · {data.testaments['Old Testament'].negative_pct}% negative
          </div>
        </div>
        <div className="stat-card" style={{ borderLeft: '4px solid ' + NT_COLOR }}>
          <div className="stat-number">{data.testaments['New Testament'].avg_sentiment.toFixed(4)}</div>
          <div className="stat-label">NT Avg Sentiment</div>
          <div className="stat-detail">
            {data.testaments['New Testament'].positive_pct}% positive · {data.testaments['New Testament'].negative_pct}% negative
          </div>
        </div>
      </div>

      <div className="controls">
        <button className={'control-btn ' + (view === 'journey' ? 'active' : '')} onClick={() => setView('journey')}>
          Emotional Journey
        </button>
        <button className={'control-btn ' + (view === 'ranking' ? 'active' : '')} onClick={() => setView('ranking')}>
          Book Rankings
        </button>
        <button className={'control-btn ' + (view === 'verses' ? 'active' : '')} onClick={() => setView('verses')}>
          Extreme Verses
        </button>
      </div>

      {view === 'journey' && (
        <div className="chart-container">
          <h3>Emotional Arc Across the Bible</h3>
          <p className="chart-description">
            Each point is a book's average sentiment score. Above zero = positive, below = negative.
          </p>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={journeyData} margin={{ bottom: 80 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="book"
                angle={-90}
                textAnchor="end"
                interval={0}
                style={{ fontSize: 9 }}
                height={80}
              />
              <YAxis domain={[-0.3, 0.6]} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={0} stroke="#666" strokeDasharray="3 3" />
              <Line
                type="monotone"
                dataKey="sentiment"
                stroke="#2C3E50"
                strokeWidth={2}
                dot={(props) => {
                  const { cx, cy, payload } = props
                  const color = payload.sentiment >= 0 ? POSITIVE_COLOR : NEGATIVE_COLOR
                  return <circle cx={cx} cy={cy} r={4} fill={color} stroke={color} />
                }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {view === 'ranking' && (
        <div className="chart-container">
          <h3>All 66 Books Ranked by Sentiment</h3>
          <ResponsiveContainer width="100%" height={800}>
            <BarChart data={sortedBooks} layout="vertical" margin={{ left: 100 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[-0.25, 0.55]} />
              <YAxis type="category" dataKey="fullName" width={95} style={{ fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine x={0} stroke="#666" />
              <Bar dataKey="sentiment">
                {sortedBooks.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={entry.sentiment >= 0 ? POSITIVE_COLOR : NEGATIVE_COLOR}
                    opacity={entry.testament === 'NT' ? 1 : 0.7}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {view === 'verses' && (
        <div className="verses-container">
          <div className="verses-column">
            <h3 style={{ color: POSITIVE_COLOR }}>Most Positive Verses</h3>
            {data.most_positive.map((v, i) => (
              <div key={i} className="verse-card positive">
                <div className="verse-ref">{v.book} {v.chapter}:{v.verse}</div>
                <div className="verse-score">Score: {v.compound.toFixed(4)}</div>
                <div className="verse-text">{v.text}</div>
              </div>
            ))}
          </div>
          <div className="verses-column">
            <h3 style={{ color: NEGATIVE_COLOR }}>Most Negative Verses</h3>
            {data.most_negative.map((v, i) => (
              <div key={i} className="verse-card negative">
                <div className="verse-ref">{v.book} {v.chapter}:{v.verse}</div>
                <div className="verse-score">Score: {v.compound.toFixed(4)}</div>
                <div className="verse-text">{v.text}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="insight-box">
        <h4>Key Insight</h4>
        <p>
          The New Testament averages <strong>+{data.testaments['New Testament'].avg_sentiment.toFixed(3)}</strong> sentiment
          compared to the Old Testament's <strong>+{data.testaments['Old Testament'].avg_sentiment.toFixed(3)}</strong>.
          <strong> Song of Solomon</strong> is the most positive OT book (it's a love poem!),
          while <strong>Lamentations</strong> and <strong>Nahum</strong> are the most negative
          — Lamentations literally grieves the destruction of Jerusalem.
        </p>
      </div>
    </div>
  )
}

export default SentimentTab