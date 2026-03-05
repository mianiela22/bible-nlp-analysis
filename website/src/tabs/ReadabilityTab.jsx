import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ScatterChart, Scatter, ZAxis
} from 'recharts'

const DIFFICULTY_COLORS = {
  'Easy': '#2ecc71',
  'Standard': '#f39c12',
  'Moderate': '#e67e22',
  'Difficult': '#e74c3c',
  'Very Difficult': '#c0392b',
}

const CATEGORY_COLORS = {
  'Pentateuch': '#8B4513',
  'Historical': '#CD853F',
  'Wisdom/Poetry': '#DAA520',
  'Major Prophets': '#B22222',
  'Minor Prophets': '#DC143C',
  'Gospels': '#4169E1',
  'Acts': '#6495ED',
  'Pauline Epistles': '#4682B4',
  'General Epistles': '#5F9EA0',
  'Apocalyptic': '#9370DB',
}

function ReadabilityTab({ data }) {
  const [sortBy, setSortBy] = useState('flesch_ease')
  const [view, setView] = useState('ranking')

  if (!data) return <p>Loading readability data...</p>

  const bookOrder = data.book_order

  const allBooks = bookOrder
    .filter(book => data.books[book])
    .map((book, i) => ({
      name: book,
      shortName: book.length > 12 ? book.substring(0, 10) + '..' : book,
      ...data.books[book],
      index: i,
    }))

  const sortedBooks = [...allBooks].sort((a, b) => {
    if (sortBy === 'flesch_ease') return b.flesch_ease - a.flesch_ease
    if (sortBy === 'fk_grade') return a.fk_grade - b.fk_grade
    return b.flesch_ease - a.flesch_ease
  })

  // Category averages
  const catMap = {}
  allBooks.forEach(b => {
    if (!catMap[b.category]) catMap[b.category] = []
    catMap[b.category].push(b.flesch_ease)
  })
  const catData = Object.entries(catMap)
    .map(([name, scores]) => ({
      name,
      avg_flesch: Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10,
    }))
    .sort((a, b) => b.avg_flesch - a.avg_flesch)

  // Journey view - readability across the Bible
  const journeyData = allBooks.map(b => ({
    ...b,
    book: b.name.length > 10 ? b.name.substring(0, 8) + '..' : b.name,
  }))

  // Find easiest and hardest
  const easiest = sortedBooks[0]
  const hardest = sortedBooks[sortedBooks.length - 1]

  // OT vs NT averages
  const otAvg = allBooks.filter(b => b.testament === 'Old Testament')
  const ntAvg = allBooks.filter(b => b.testament === 'New Testament')
  const otFlesch = Math.round(otAvg.reduce((s, b) => s + b.flesch_ease, 0) / otAvg.length * 10) / 10
  const ntFlesch = Math.round(ntAvg.reduce((s, b) => s + b.flesch_ease, 0) / ntAvg.length * 10) / 10

  return (
    <div className="tab-content">
      {/* Stats */}
      <div className="stats-row">
        <div className="stat-card" style={{ borderLeft: '4px solid #2ecc71' }}>
          <div className="stat-number">{easiest.name}</div>
          <div className="stat-label">Easiest to Read</div>
          <div className="stat-detail">Flesch: {easiest.flesch_ease} · Grade {easiest.fk_grade}</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '4px solid #e74c3c' }}>
          <div className="stat-number">{hardest.name}</div>
          <div className="stat-label">Hardest to Read</div>
          <div className="stat-detail">Flesch: {hardest.flesch_ease} · Grade {hardest.fk_grade}</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '4px solid #8B4513' }}>
          <div className="stat-number">{otFlesch}</div>
          <div className="stat-label">OT Avg Readability</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '4px solid #4169E1' }}>
          <div className="stat-number">{ntFlesch}</div>
          <div className="stat-label">NT Avg Readability</div>
        </div>
      </div>

      {/* Controls */}
      <div className="controls">
        <button className={'control-btn ' + (view === 'ranking' ? 'active' : '')} onClick={() => setView('ranking')}>
          Book Rankings
        </button>
        <button className={'control-btn ' + (view === 'journey' ? 'active' : '')} onClick={() => setView('journey')}>
          Readability Journey
        </button>
        <button className={'control-btn ' + (view === 'category' ? 'active' : '')} onClick={() => setView('category')}>
          By Category
        </button>
        <button className={'control-btn ' + (view === 'recommend' ? 'active' : '')} onClick={() => setView('recommend')}>
          Where to Start?
        </button>
      </div>

      {/* Ranking View */}
      {view === 'ranking' && (
        <div className="chart-container">
          <h3>All 66 Books — Flesch Reading Ease Score</h3>
          <p className="chart-description">Higher = easier to read. 80+ = Easy, 60-80 = Standard, below 60 = Difficult</p>
          <ResponsiveContainer width="100%" height={800}>
            <BarChart data={sortedBooks} layout="vertical" margin={{ left: 110 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[50, 90]} />
              <YAxis type="category" dataKey="name" width={105} style={{ fontSize: 11 }} />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const d = payload[0].payload
                    return (
                      <div className="custom-tooltip">
                        <strong>{d.name}</strong>
                        <p>Flesch Score: {d.flesch_ease}</p>
                        <p>Grade Level: {d.fk_grade}</p>
                        <p>Difficulty: {d.difficulty}</p>
                        <p>Avg sentence: {d.avg_sentence_length} words</p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Bar dataKey="flesch_ease">
                {sortedBooks.map((entry, index) => (
                  <Cell key={index} fill={DIFFICULTY_COLORS[entry.difficulty] || '#999'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Journey View */}
      {view === 'journey' && (
        <div className="chart-container">
          <h3>Reading Difficulty Across the Bible</h3>
          <p className="chart-description">How readability changes from Genesis to Revelation</p>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={journeyData} margin={{ bottom: 80 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="book"
                angle={-90}
                textAnchor="end"
                interval={0}
                style={{ fontSize: 9 }}
                height={80}
              />
              <YAxis domain={[50, 90]} />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const d = payload[0].payload
                    return (
                      <div className="custom-tooltip">
                        <strong>{d.name}</strong>
                        <p>Flesch: {d.flesch_ease} ({d.difficulty})</p>
                        <p>Grade: {d.fk_grade}</p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Bar dataKey="flesch_ease">
                {journeyData.map((entry, index) => (
                  <Cell key={index} fill={CATEGORY_COLORS[entry.category] || '#999'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Category View */}
      {view === 'category' && (
        <div className="chart-container">
          <h3>Average Readability by Category</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={catData} margin={{ bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-25} textAnchor="end" interval={0} style={{ fontSize: 12 }} />
              <YAxis domain={[60, 90]} />
              <Tooltip />
              <Bar dataKey="avg_flesch" name="Avg Flesch Score">
                {catData.map((entry, index) => (
                  <Cell key={index} fill={CATEGORY_COLORS[entry.name] || '#999'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recommendation View */}
      {view === 'recommend' && (
        <div className="recommend-section">
          <h3>Where Should You Start Reading?</h3>
          <p className="chart-description">Based on readability scores, here are our data-driven recommendations:</p>

          <div className="recommend-grid">
            <div className="recommend-card">
              <h4>New to the Bible?</h4>
              <p>Start with these easy-to-read narrative books:</p>
              <div className="recommend-list">
                {sortedBooks.filter(b =>
                  ['Ruth', 'Genesis', 'Jonah', 'Mark'].includes(b.name)
                ).map(b => (
                  <div key={b.name} className="recommend-item">
                    <strong>{b.name}</strong>
                    <span>Grade {b.fk_grade} · {b.difficulty}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="recommend-card">
              <h4>Want Poetry & Wisdom?</h4>
              <p>The easiest category overall:</p>
              <div className="recommend-list">
                {sortedBooks.filter(b => b.category === 'Wisdom/Poetry').map(b => (
                  <div key={b.name} className="recommend-item">
                    <strong>{b.name}</strong>
                    <span>Grade {b.fk_grade} · Flesch {b.flesch_ease}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="recommend-card">
              <h4>Ready for a Challenge?</h4>
              <p>These books have the densest language:</p>
              <div className="recommend-list">
                {sortedBooks.slice(-5).reverse().map(b => (
                  <div key={b.name} className="recommend-item">
                    <strong>{b.name}</strong>
                    <span>Grade {b.fk_grade} · {b.difficulty}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Insight */}
      <div className="insight-box">
        <h4>Key Insight</h4>
        <p>
          Surprisingly, the <strong>Old Testament is easier to read</strong> (Flesch {otFlesch})
          than the New Testament ({ntFlesch}). That's because much of the OT is narrative
          storytelling (short sentences, simple words), while the NT epistles contain
          complex theological arguments with longer sentences.
          <strong> Psalms</strong> is the easiest book — its poetic structure uses short,
          simple phrases. <strong>Jude</strong> is the hardest with dense theological vocabulary.
        </p>
      </div>
    </div>
  )
}

export default ReadabilityTab