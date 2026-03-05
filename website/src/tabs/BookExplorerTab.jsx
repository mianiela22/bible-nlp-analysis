import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ScatterChart, Scatter, ZAxis, Legend
} from 'recharts'

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

function BookExplorerTab({ data }) {
  const [sortBy, setSortBy] = useState('total_words')
  const [filterCat, setFilterCat] = useState('all')

  if (!data) return <p>Loading book data...</p>

  const bookOrder = data.book_order
  const categories = Object.keys(data.categories)

  // Build chart data
  let chartBooks = bookOrder
    .filter(book => data.books[book])
    .map(book => ({
      name: book,
      shortName: book.length > 12 ? book.substring(0, 10) + '..' : book,
      ...data.books[book],
    }))

  // Apply category filter
  if (filterCat !== 'all') {
    chartBooks = chartBooks.filter(b => b.category === filterCat)
  }

  // Sort
  const sorted = [...chartBooks].sort((a, b) => b[sortBy] - a[sortBy])

  // Category summary
  const catData = Object.entries(data.categories)
    .map(([name, info]) => ({
      name,
      ...info,
    }))
    .sort((a, b) => b.total_words - a.total_words)

  // Scatter plot data: words vs unique words (vocabulary richness)
  const scatterData = bookOrder
    .filter(book => data.books[book])
    .map(book => ({
      name: book,
      total_words: data.books[book].total_words,
      unique_words: data.books[book].unique_words,
      category: data.books[book].category,
      num_verses: data.books[book].num_verses,
    }))

  return (
    <div className="tab-content">
      {/* Stats */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-number">66</div>
          <div className="stat-label">Books</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">1,189</div>
          <div className="stat-label">Chapters</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">31,102</div>
          <div className="stat-label">Verses</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">789,634</div>
          <div className="stat-label">Total Words</div>
        </div>
      </div>

      {/* Controls */}
      <div className="controls">
        <label>Sort by: </label>
        <select value={sortBy} onChange={e => setSortBy(e.target.value)} className="select-input">
          <option value="total_words">Word Count</option>
          <option value="num_verses">Verse Count</option>
          <option value="num_chapters">Chapter Count</option>
          <option value="avg_words_per_verse">Avg Verse Length</option>
          <option value="type_token_ratio">Vocabulary Richness</option>
          <option value="unique_words">Unique Words</option>
        </select>

        <label style={{ marginLeft: 20 }}>Category: </label>
        <select value={filterCat} onChange={e => setFilterCat(e.target.value)} className="select-input">
          <option value="all">All Categories</option>
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      {/* Book comparison chart */}
      <div className="chart-container">
        <h3>Books Compared by {
          sortBy === 'total_words' ? 'Word Count' :
          sortBy === 'num_verses' ? 'Verse Count' :
          sortBy === 'num_chapters' ? 'Chapter Count' :
          sortBy === 'avg_words_per_verse' ? 'Average Verse Length' :
          sortBy === 'type_token_ratio' ? 'Vocabulary Richness' :
          'Unique Words'
        }</h3>
        <ResponsiveContainer width="100%" height={Math.max(400, sorted.length * 22)}>
          <BarChart data={sorted} layout="vertical" margin={{ left: 110 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis type="category" dataKey="name" width={105} style={{ fontSize: 11 }} />
            <Tooltip
              formatter={(value) => {
                if (sortBy === 'type_token_ratio') return (value * 100).toFixed(1) + '%'
                if (sortBy === 'avg_words_per_verse') return value.toFixed(1)
                return value.toLocaleString()
              }}
            />
            <Bar dataKey={sortBy}>
              {sorted.map((entry, index) => (
                <Cell
                  key={index}
                  fill={CATEGORY_COLORS[entry.category] || '#999'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Category breakdown */}
      <div className="chart-container">
        <h3>By Category</h3>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={catData} margin={{ bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={-35} textAnchor="end" interval={0} style={{ fontSize: 11 }} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="total_words" name="Words" fill="#8B4513" />
            <Bar dataKey="total_verses" name="Verses" fill="#4169E1" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Insight */}
      <div className="insight-box">
        <h4>💡 Key Insight</h4>
        <p>
          <strong>Psalms</strong> is the longest book with 42,684 words across 150 chapters,
          while <strong>3 John</strong> is the shortest at just 294 words.
          Shorter books like <strong>Jude</strong> and <strong>Philemon</strong> have
          the richest vocabulary relative to their length — each word counts
          when you only have a few hundred!
        </p>
      </div>
    </div>
  )
}

export default BookExplorerTab